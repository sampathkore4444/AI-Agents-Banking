# Sathapana KYC Agent — End-to-End Flow

Documents the complete KYC onboarding journey implemented in
`sathapana_kyc_agent/`: what happens on every path, which tools fire in
what order, where human review, SLA enforcement and STR filing kick in, and
what is left in the audit trail and data store. It also covers the
production-hardening layers added on top of the core flow: DB-backed HITL
approvals, idempotent saga execution, hash-chained audit, PII-at-rest
encryption and the provider adapter layer.

```
                        ┌─────────────────────────────┐
                        │   Applicant / Branch officer │
                        └──────────────┬──────────────┘
                                       │ uploads docs + query
                                       ▼
   ┌──────────────┐    ┌───────────────────────────┐    ┌─────────────┐
   │  LLM (chat)  │───►│  Agent loop / Orchestrator │◄──►│ RAG pipeline │
   └──────────────┘    └───────────┬────────────────┘    └─────────────┘
                                   │                  (numpy | chromadb backend,
                                   │                   query expansion, reranker,
                                   │                   10-question golden eval)
                                   ▼
              ┌─────────────────────────────────────────┐
              │  ToolRegistry (15 MCP tools)            │
              │  execute_tool -> idempotency key        │
              │  (tool_call_log) + audit_log (hashed)   │
              └───┬───────────────┬─────────────────────┘
                  │ high-risk     │ every call
                  ▼               ▼
        ┌─────────────────┐  ┌──────────────┐
        │ ApprovalWorkflow│  │ integrations │   provider adapters
        │ (approval_reque │  │ sanctions /  │   (Stub <-> HTTP switch)
        │  sts, SLA)      │  │ identity /   │
        └────────┬────────┘  │ ocr / notify │
                 │           │ bakong /     │
                 ▼           │ camfiu(STR)  │
        ┌─────────────────┐  └──────────────┘
        │ OnboardingSaga  │
        │ (onboarding_ses │
        │  sions/steps,   │
        │  compensate)    │
        └────────┬────────┘
                 ▼
           ┌───────────────┐
           │ SQLite        │
           │ audit_log     │  hash-chained (entry_hash, prev_hash)
           │ customers     │  PII encrypted at rest (Fernet) +
           │ accounts      │  tokenized full_name ("tk:...")
           │ compliance_c  │  + CAMFIU STR record flow
           │ approval_requ │
           │ tool_call_log │
           └───────────────┘
```

---

## 1. Trigger & entry points

| Entry point | How it reaches the flow |
|-------------|--------------------------|
| `python main.py demo` | Deterministic `runner.py` — replays 3 scripted journeys through the real tools, through the saga and ApprovalWorkflow |
| `python main.py chat` | `OllamaAgent` ReAct loop calls the same tools via `BaseAgent.run()`; high-risk calls route through `ApprovalWorkflow` |
| `python main.py serve` | MCP server — stdio (default) or TCP (`--transport tcp`) with bearer-token auth; `tools/call` invokes any registered tool directly |
| `python main.py verify-audit` | Re-hashes the entire `audit_log` chain and reports tamper status |
| `python main.py eval-rag` | Runs the 10-question golden set (hit rate / recall / latency) |
| `python main.py providers` | Prints the active provider backend for each adapter (stub vs http) |
| pytest (`test_kyc_flow.py`, `test_production.py`) | 39 tests drive each step, plus production hardening (encryption, tamper, SLA, saga, rate limit, auth) |

---

## 2. The onboarding journey (runner.py)

Every journey runs the same 6-stage pipeline. Outputs from each stage feed
the next decision gate.

### Stage 0 — Retrieve regulatory context (RAG)

`knowledge_search(query=<type> sector KYC documents Cambodia, top_k=3)`

- Hybrid BM25 + semantic search across `nbc_regulations`, `product_policies`,
  `document_schemas`, `risk_typologies`, `past_kyc_decisions`.
- The query is expanded first (`rag_pipeline.expand_query`): domain acronyms
  (EDD, CDD, KYC, UBO, PEP, STR, AML/CFT, FATF...) and synonyms (gaming /
  gambling / casino junket) are appended so a compact query retrieves the
  right NBC/FATF chunks.
- Optional reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`, enabled via
  `RERANKER_ENABLED`) re-orders top candidates; the pipeline degrades
  gracefully if the model is missing.
- Returns `chunks` (text + score + collection), `assembled_context`,
  `results_count`. Logged as `rag_requirements`.

### Stage 1 — Document extraction & validation

`extract_and_classify_document(document_url, document_type)` per uploaded doc.

| Scenario | Documents |
|----------|-----------|
| retail_low_risk | national_id, family_book, proof_of_address |
| sme_medium_risk | business_registration, tax_certificate, bank_statement, collateral |
| casino_high_risk | business_registration, tax_certificate, bank_statement |

- Extraction and Khmer-OCR capability are provided by the OCR adapter
  (`integrations/ocr.py`); `EXTRACTION_SCHEMAS` lives there and the tool
  re-exports it.
- Output includes `extracted_fields`, `confidence_score`, `ocr_quality`,
  `khmer_ocr_supported`.
- `schema_validation.is_complete` = every canonical schema field present
  (validated against `EXTRACTION_SCHEMAS`, RAG consulted for evidence only).
- Unsupported doc type → returns `error` and the journey aborts.

### Stage 2 — Identity verification

`verify_customer_identity(customer_id, document_image_url, selfie_url, nationality)`

- Liveness, document authenticity and face match (via the identity adapter)
  produce `overall_result` (`verified` | `manual_review` | `rejected`).
- `rejected` → journey declines immediately (see gate 1).

### Stage 3 — Sanctions, PEP & beneficial ownership screening

`screen_customer_sanctions(full_name, date_of_birth, nationality)`

- Screening is delegated to the sanctions adapter (`integrations/sanctions.py`):
  `StubSanctionsProvider` (deterministic, hash-based) in dev, HTTP provider when
  `SANCTIONS_PROVIDER=http`.
- Lists: UN Consolidated (incl. UNSCR 1267/1989/1718), NBC/Cambodia, OFAC,
  EU, domestic Cambodian PEP list, adverse media.
- `onboarding_prohibited = un_result != "clear"`.
- `risk_level`: `critical` (UN hit) > `high` (other list hit) > `medium`
  (PEP or adverse) > `low`.

`screen_ubo(owners, risk_level)` — business customers only

- Capture threshold: **25%** default (FATF-aligned); **10%** risk-based when
  customer risk level is `high`/`critical` (`config.ubo_*_threshold_pct`).
- `decision`: `block` (owner on a list) | `verify` (unidentified ownership) |
  `clear`.
- Blocked owners → decline (see gate 1).

### Stage 4 — Risk assessment (RAG-informed)

`assess_kyc_risk(customer_type, jurisdiction, sector, identity_verified,
sanctions_clear, pep_status, adverse_media, business_complexity,
cash_intensive, ubo_screened)`

Risk score (additive, capped at 1.0):

| Factor | Add |
|--------|-----|
| Identity not verified | +0.40 |
| Sanctions not clear | +0.50 |
| PEP (domestic/foreign) | +0.25 |
| Adverse media | +0.15 |
| Casino / gaming / junket sector | +0.35 |
| Cash-intensive sector | +0.20 |
| Complex business structure | +0.10 |
| UBO not screened | +0.15 |

Levels: `high` ≥ 0.50 → `manual_review_required`; `medium` ≥ 0.25 →
`enhanced_due_diligence`; else `low` → `auto_approve_eligible`.
Retrieved NBC typologies are echoed back as cited context.

---

## 3. Decision gates (applied in `run_scenario`)

```
                     ┌───── result of stages 1–4 ─────┐
                     │                                │
              prohibited?                    identity rejected?
          (sanctions/UBO block)                   yes
                    │yes                             │
                    ▼                               ▼
              DECLINE                          DECLINE
              (STR if blocked)                 (no STR)
                    │                                │
                    └──────────────┬─────────────────┘
                                   ▼
                          risk.level from stage 4
        ┌────────────────┴──────────────┬───────────────┐
        │                               │               │
       low                            medium          high
        │                               │               │
        ▼                               ▼               ▼
   AUTO-APPROVE              HUMAN REVIEW            DECLINE
   create profile      open_compliance_case     open_compliance_case
   open account        update_case (officer     STR filed to CAMFIU
   register_bakong     -> approved w/ conds)    notify (rejected)
   notify (approved)   create profile +
                       open account + Bakong
```

All approve paths (low and medium) execute their ordered tool steps through the
**OnboardingSaga** (`workflow/onboarding.py`) with **functional step builders**,
so the generated `customer_id` and `account_id` flow between steps:

- Each step runs under an idempotency key `ob_session:NN_step` — `tool_call_log`
  guarantees a replayed/retried step never doubles a side effect.
- Each high-risk step (`create_customer_profile`, `open_account`, `update_case`)
  becomes an `approval_requests` row with a decision deadline
  (`decision_deadline = requested_at + SLA`, default `approval_sla_seconds`).
  The saga auto-approves them at decision time (the MLRO approve/reject UI or
  `expire_overdue` is the production human path).
- On any step failure the saga **compensates**: the session is marked
  `aborted`, pending approvals are rejected, and a failed step row is recorded.
  A session resumes because only steps with status `executed` are skipped.

### Gate A — Prohibited / failed identity → Decline

| Condition | STR to CAMFIU |
|-----------|---------------|
| UN/NBC sanctions hit (`onboarding_prohibited`) | No (fielded via case) |
| UBO owner block | No |
| Identity `rejected` | No |
| **Note:** the high-risk branch below always files one (with AML/CFT intent) | — |

### Gate B — Risk levels

| Level | Action taken | Artifacts |
|-------|--------------|-----------|
| **low** | Auto-approve | `create_customer_profile(kyc_result=approved, risk_rating=low)` → `open_account` (USD/KHR) → `register_bakong` → `notify_customer(kyc_approved)` |
| **medium** | HITL EDD review | `open_compliance_case(risk_level=medium)` → `update_case(status=approved, assigned_to=MLRO, decision=approved_with_conditions)` → profile with `kyc_result=approved_with_conditions` → account → Bakong |
| **high** | Decline + STR | `open_compliance_case(priority=urgent, file_str_to_camfiu=True, customer_pii=...)` → validated `STRRecord` filed to CAMFIU → STR ref `STR-XXXXXXXXXX` from the CAMFIU adapter → `notify_customer(kyc_rejected)` |

### Gate C — Account & currency rules

- `open_account` validates `account_type` ∈ (retail_savings, current,
  sme_loan, corporate) and `currency` ∈ (USD, KHR).
- Rejects opening for a customer missing from `customers` or with
  `kyc_result == rejected`.
- `register_bakong` links after account opening; returns `BKNG-…` from the
  Bakong adapter.

---

## 4. STR filing (CAMFIU)

High-risk declines and sanctions-triggered cases can file a Suspicious
Transaction Report via the CAMFIU adapter (`integrations/camfiu.py`):

- `build_str_record(case, customer, agent_id)` validates the record against
  pydantic models (`StrEntity`, `StrCustomer`, `StrAmount`, `STRRecord`) before
  filing; a missing customer identity or risk level returns
  `validation_error.missing_fields` instead of a malformed STR.
- `StubCamfiuReporter.file()` returns a deterministic `STR-reference`;
  `HttpCamfiuReporter` posts a real `GET/POST /str` submission.
- The `customer_pii` argument (`full_name`, `nationality`) lets a declined
  applicant (no customer row yet) still get a properly attributed STR.
- Filing is audited as `compliance file_str_camfiu`.

---

## 5. Data store & audit trail

### SQLite (`data/sathapana_kyc.db`)

| Table | Written by | Purpose |
|-------|------------|---------|
| `audit_log` | every tool + runner stage + saga/approvals | `ts`, `agent`, `action`, `detail` (JSON, PII-redacted), `status`, `prev_hash`, `entry_hash` (**hash chained**) |
| `customers` | `create_customer_profile` | customer_id, kyc_result, risk_rating, currency, type; **`full_name` stored tokenized (`tk:…`) and the real PII blob encrypted in `pii_encrypted` (Fernet)** |
| `accounts` | `open_account` | account_id, currency, account_type, status, bakong_id |
| `compliance_cases` | `create/update_compliance_case` | case_id, risk_level, flags, status, decision, STR ref |
| `approval_requests` | `ApprovalWorkflow.submit/decide` | pending HITL approvals, `decision_deadline`, decided_by/at, decision |
| `tool_call_log` | `ToolRegistry.invoke` | idempotency cache `(key → result)` so replays are deduplicated |
| `onboarding_sessions` / `onboarding_steps` | `OnboardingSaga` | saga state machine: status, error, per-step output/status |

- Audit rows are PII-redacted before storage (`crypto.redact_pii`) and each row
  is chained to its predecessor via `entry_hash = chain_hash(prev_hash, payload)`.
  `main.py verify-audit` re-computes the chain; a tampered row is reported with
  its id. Legacy rows created before the columns existed are counted and skipped.
- PII is read back only through `lookup_customer` / `get_customer_pii`, which
  decrypt and de-tokenize — the raw name never sits in plaintext in SQLite.

### Vector store (`data/vector_store/sathapana_kyc_*.npz/.json`)

- Default backend is the zero-dependency **numpy in-memory store** (brute-force
  cosine), seeded from `seed_knowledge.py`: `nbc_regulations` (7),
  `product_policies` (4), `document_schemas` (7), `risk_typologies` (5),
  `past_kyc_decisions` (4).
- `get_vector_store()` (`vector_store.py`) exposes the same 4-method API for
  numpy and ChromaDB; set `VECTOR_BACKEND=chromadb` to switch (a missing
  `chromadb` package raises an informative error, never a silent fallback).
  pgvector / Qdrant are drop-in production targets at the adapter boundary.
- Embeddings default to `all-MiniLM-L6-v2` (English content). For Khmer-script
  retrieval, set `EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2` and
  re-seed so collection dimensions match.
- RAG quality is tracked by `main.py eval-rag` against a 10-question golden set
  (hit rate / avg recall / avg latency).

### Audit entries produced by one retail journey

```
runner          onboarding_start
runner          rag_requirements
approvals       submit              create_customer_profile (HITL)
approvals       decide              approved (decision_deadline honoured)
onboarding      step_ok             create_customer_profile (saga)
approvals       submit              open_account (HITL)
approvals       decide              approved
onboarding      step_ok             open_account (saga)
bakong          register_bakong
onboarding      complete            OB-… session complete
runner          onboarding_approved
```

Decline + STR journey additionally logs:
```
compliance      create_compliance_case   (str_to_camfiu: true)
compliance      file_str_camfiu          → STR-XXXXXXXXXX
runner          onboarding_declined
```

---

## 6. Tool registry (MCP surface, risk levels)

| Tool | Risk | High-Risk guardrail |
|------|------|---------------------|
| knowledge_search | safe | — |
| get_document_schema | safe | — |
| assess_kyc_risk | safe | — |
| get_case | safe | — |
| extract_and_classify_document | low | — |
| notify_customer | low | — |
| verify_customer_identity | medium | — |
| screen_customer_sanctions | medium | — |
| screen_ubo | medium | — |
| register_bakong | medium | — |
| open_compliance_case | medium | — |
| **create_customer_profile** | **high** | ApprovalWorkflow HITL (DB-backed, SLA deadline) |
| **open_account** | **high** | ApprovalWorkflow HITL (DB-backed, SLA deadline) |
| **update_case** | **high** | ApprovalWorkflow HITL (DB-backed, SLA deadline) |

Guardrails (`llm/base_agent.py`): every high-risk call is routed through
`ApprovalWorkflow` (an approval request row with a decision deadline; overdue
requests are auto-decided by `expire_overdue`). PII (phone/email/ID numbers) is
redacted in audit detail, tool execution is idempotent per call via its
idempotency key, and every call is written to the hash-chained `audit_log`.
Agents never call an approved tool twice — a retried decision replays the
cached result instead of re-executing.

---

## 7. MCP protocol flow

`server.py` is a dependency-free MCP (JSON-RPC 2.0) server over **stdio**
(default) or **TCP** (`python main.py serve --transport tcp`), with hardening:

```
client ── initialize ────────────────►  {"protocolVersion","capabilities","serverInfo"}   (requires auth)
client ── tools/list ────────────────►  15 tools with inputSchema
client ── ping ──────────────────────►  {}
client ── tools/call {name,arguments}►  {"content":[{"type":"text","text":"<JSON>"}],"isError":false}
```

Hardening applied:

| Control | Implementation |
|---------|----------------|
| Bearer-token auth | `params.auth_token` / `authorization` verified with `hmac.compare_digest` against `KYC_MCP_AUTH_TOKEN` |
| Rate limiting | token-bucket `RateLimiter` (`MCP_RATE_LIMIT_RPM`) → `-32001` when exceeded |
| Payload cap | `MCP_MAX_PAYLOAD_BYTES` → `-32002` when exceeded |
| Transport | stdio or TCP; optional TLS via `MCP_TLS_CERT`/`MCP_TLS_KEY` |
| Idempotency passthrough | `tools/call` accepts `_idempotency_key` / `idempotency_key`, consistent with the tool registry |

Handlers are run through the same `ToolRegistry.invoke()` used by the runner
and the agent loop, so behaviour is identical on every surface.

---

## 8. Provider adapter layer

All external side effects are behind adapters in `integrations/` so the same
code runs against stubs (dev/CI) or real vendors (production) with zero code
changes — `integrations.get_providers()` resolves each backend from settings:

| Adapter | Stub backend | Production path |
|---------|--------------|-----------------|
| sanctions | deterministic hash-based screen | HTTP provider |
| identity | liveness/face stub | HTTP provider |
| ocr | simulated extraction + Khmer OCR flags | HTTP provider |
| notify | template-based notifications | HTTP provider |
| bakong | `BKNG-…` link stub | HTTP provider (`/link`) |
| camfiu | STR-record stub filing | HTTP provider (STR submission) |

`python main.py providers` prints the resolved backend for each adapter.
Swapping a real vendor is a config change plus an HTTP implementation of the
same method contract (see `integrations/base.py` for `post_json/get_json` and
retry helpers).

---

## 9. Verify the flow yourself

```bat
cd sathapana_kyc_agent

python main.py seed             rem seeds/reseeds the knowledge base (idempotent)
python main.py demo             rem runs all 3 journeys end to end
python main.py providers        rem shows active provider backends (stub/http)
python main.py verify-audit     rem checks the hash-chained audit trail
python main.py eval-rag         rem runs the 10-question RAG golden evaluation
python main.py serve            rem MCP server (stdio)
python main.py serve --transport tcp   rem MCP server over TCP (token auth)
python -m pytest -q             rem 39 tests: scenarios + production hardening
```

---

## 10. FAQ — Where is this useful if a teller already does this in core banking?

> **Q:** Tellers log into core banking (Temenos/OLB) and onboard customers doing
> the same steps the agent automates. Where does the agent actually add value?

**A:** The agent is not a duplicate of the teller workflow — it is a
**compliance copilot** that automates the rote/risk steps and makes every
teller behave like the best, MLRO-trained one. It is useful exactly at the
points where the manual loop falls short:

### Where the agent adds value over manual teller onboarding

| # | Value | What the agent does vs. the teller |
|---|-------|-------------------------------------|
| 1 | **Screening the teller never does** | Tellers don't systematically screen against UNSC/NBC/OFAC/EU + adverse media before opening. `screen_customer_sanctions` does it in one call; `screen_ubo` enforces the 25% / 10% ownership thresholds most business onboarding skips. |
| 2 | **Consistent regulation, branch-to-branch** | Teller judgment varies by person and branch — exactly what NBC inspections flag. The RAG-guided checks (EDD for domestic PEPs, casino/cash-intensive sectors, sanction prohibition) apply the same rule every time, with a cited source (`retrieved_rules`) so the teller can see *why*. |
| 3 | **Escalation without burden on the teller** | Medium risk → `open_compliance_case` → routed to the MLRO with flags and evidence. High risk → declined *and* a schema-validated STR to CAMFIU filed. Today the teller has neither the checklist nor the trigger to know "this is a CAMFIU case." The agent turns a gut feeling into a documented handoff. |
| 4 | **Tamper-evident audit trail for NBC record-keeping** | Every call is hash-chained into `audit_log` with arguments, result and agent. When the regulator asks "why was this customer onboarded on this date?", the full decision is reconstructed in seconds — and `verify-audit` proves it was not modified. Manual onboarding leaves paper and memory. |
| 5 | **Channel scalability — self-service & kiosk** | The same flow is exposed over MCP (`server.py`, stdio or authenticated TCP), so it runs in the branch, the mobile app, or a kiosk. A low-risk retail customer is onboarded with zero teller keystrokes; tellers only touch exceptions. Teller seats are expensive — not every onboarding needs one. |
| 6 | **Cross-branch continuity** | `lookup_customer` carries history (kyc_result, compliance case, products) with the customer (decrypted from encrypted storage), so the next branch never re-asks for documents they already provided. |
| 7 | **Faster teller training / less tribal knowledge** | New staff ramp faster — `knowledge_search` answers "what documents for an SME loan?" with the product policy instead of asking the senior teller. |

### Where the agent does NOT replace the teller (by design)

- Liveness/face judgment on edge cases.
- Senior-management approval for PEPs / EDD cases (HITL in `ApprovalWorkflow`).
- The human conversation with the customer.

The agent flags and routes; the officer decides. That partnership is the
intended operating model.

### Bottom line

The value is **screening consistency + mandatory checklist enforcement +
automatic STR/audit + distribution across channels** — layered on top of what
the teller already does, not as a replacement for it.

*Last updated: September 2026*