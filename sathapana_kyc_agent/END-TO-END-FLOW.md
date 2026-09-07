# Sathapana KYC Agent — End-to-End Flow

Documents the complete KYC onboarding journey implemented in
`sathapana_kyc_agent/`: what happens on every path, which tools fire in
what order, where human review and STR filing kick in, and what is left
in the audit trail and data store.

```
                       ┌─────────────────────────────┐
                       │   Applicant / Branch officer │
                       └──────────────┬──────────────┘
                                      │ uploads docs + query
                                      ▼
   ┌──────────────┐    ┌───────────────────────────┐    ┌─────────────┐
   │  LLM (chat)  │───►│  Agent loop / Orchestrator │◄──►│ RAG pipeline │
   └──────────────┘    └───────────┬────────────────┘    └─────────────┘
                                   │                                             
                                   ▼
              ┌─────────────────────────────────────────┐
              │  MCP tools (ToolRegistry)                │
              │  1  extract_and_classify_document        │
              │  2  verify_customer_identity             │
              │  3  screen_customer_sanctions            │
              │  4  screen_ubo                           │
              │  5  assess_kyc_risk                      │
              │  6  create_customer_profile  [HITL]      │
              │  7  open_account            [HITL]       │
              │  8  register_bakong                      │
              │  9  open_compliance_case / update_case   │
              └───┬───────────────────┬──────────────────┘
                  │                   │
                  ▼                   ▼
          ┌───────────────┐   ┌───────────────┐
          │ SQLite        │   │ Vector store  │
          │ audit_log     │   │ 5 collections │
          │ customers     │   └───────────────┘
          │ accounts      │
          │ compliance_c  │
          └───────────────┘
```

---

## 1. Trigger & entry points

| Entry point | How it reaches the flow |
|-------------|--------------------------|
| `python main.py demo` | Deterministic `runner.py` — replays 3 scripted journeys through the real tools |
| `python main.py chat` | `OllamaAgent` ReAct loop calls the same tools via `BaseAgent.run()` |
| `python main.py serve` | MCP stdio server — `tools/call` invokes any registered tool directly |
| pytest (`test_kyc_flow.py`) | Unit + scenario tests drive each step end to end |

---

## 2. The onboarding journey (runner.py)

Every journey runs the same 6-stage pipeline. Outputs from each stage
feed the next decision gate.

### Stage 0 — Retrieve regulatory context (RAG)

`knowledge_search(query=<type> sector KYC documents Cambodia, top_k=3)`

- Hybrid BM25 + semantic search across `nbc_regulations`, `product_policies`,
  `document_schemas`, `risk_typologies`, `past_kyc_decisions`.
- Returns `chunks` (text + score + collection), `assembled_context`,
  `results_count`. Logged as `rag_requirements`.

### Stage 1 — Document extraction & validation

`extract_and_classify_document(document_url, document_type)` per uploaded doc.

| Scenario | Documents |
|----------|-----------|
| retail_low_risk | national_id, family_book, proof_of_address |
| sme_medium_risk | business_registration, tax_certificate, bank_statement, collateral |
| casino_high_risk | business_registration, tax_certificate, bank_statement |

- Simulated OCR produces `extracted_fields`, `confidence_score`,
  `ocr_quality`, `khmer_ocr_supported`.
- `schema_validation.is_complete` = every canonical schema field present
  (validated against `EXTRACTION_SCHEMAS`, RAG consulted for evidence only).
- Unsupported doc type → returns `error` and the journey aborts.

### Stage 2 — Identity verification

`verify_customer_identity(customer_id, document_image_url, selfie_url, nationality)`

- `liveness_check`, `document_authenticity`, `face_match` → `overall_result`
  (`verified` | `manual_review` | `rejected`).
- `rejected` → journey declines immediately (see gate 1).

### Stage 3 — Sanctions, PEP & beneficial ownership screening

`screen_customer_sanctions(full_name, date_of_birth, nationality)`

- Lists: UN Consolidated (incl. UNSCR 1267/1989/1718), NBC/Cambodia,
  OFAC, EU, domestic Cambodian PEP list, adverse media.
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
   register_bakong     → approved w/ conds)     notify (rejected)
   notify (approved)   create profile +
                       open account + Bakong
```

### Gate A — Prohibited / failed identity → Decline

| Condition | STR to CAMFIU |
|-----------|---------------|
| UN/NBC sanctions hit (`onboarding_prohibited`) | No (fielded via case) |
| UBO owner block | No |
| Identity `rejected` | No |
| **Note:** sanctions hit with blocked/forced screening may open a
  compliance case with `file_str_to_camfiu`; the high-risk branch below
  always files one | — |

### Gate B — Risk levels

| Level | Action taken | Artifacts |
|-------|--------------|-----------|
| **low** | Auto-approve | `create_customer_profile(kyc_result=approved, risk_rating=low)` → `open_account` (USD/KHR) → `register_bakong` → `notify_customer(kyc_approved)` |
| **medium** | HITL EDD review | `open_compliance_case(risk_level=medium)` → `update_case(status=approved, assigned_to=MLRO, decision=approved_with_conditions)` → profile with `kyc_result=approved_with_conditions` → account → Bakong |
| **high** | Decline + STR | `open_compliance_case(priority=urgent, file_str_to_camfiu=True)` → STR ref `STR-XXXXXXXXXX` from CAMFIU → `notify_customer(kyc_rejected)` |

### Gate C — Account & currency rules

- `open_account` validates `account_type` ∈ (retail_savings, current,
  sme_loan, corporate) and `currency` ∈ (USD, KHR).
- Rejects opening for a customer missing from `customers` or with
  `kyc_result == rejected`.
- `register_bakong` links after account opening; returns `BKNG-…`.

---

## 4. Demo scenarios → expected outcomes

| Scenario | Screening | Risk factors | Risk | Outcome (asserted in tests) |
|----------|-----------|--------------|------|------------------------------|
| `retail_low_risk` — Cambodian individual, USD savings | clean, not PEP | none | **0.00 low** | approved + account + Bakong |
| `sme_medium_risk` — Ratanak Trading, KHR, fuel trader | clean, **domestic PEP** | PEP + cash-intensive | **0.45 medium** | approved_with_conditions via CASE |
| `casino_high_risk` — Lucky Dragon Gaming | clean, adverse media | gambling + cash + adverse | **0.70 high** | declined + STR filed |

Demo outcome summary (from `runner.run_demo()`):

```
retail_low_risk     -> approved
sme_medium_risk     -> approved_with_conditions
casino_high_risk    -> declined  (reason: high risk / EDD unsatisfied,
                                  str_filed_camfiu: True)
```

---

## 5. Data store & audit trail

### SQLite (`data/sathapana_kyc.db`)

| Table | Written by | Purpose |
|-------|------------|---------|
| `audit_log` | every tool + runner stage | `ts`, `agent`, `action`, `detail` (JSON), `status` |
| `customers` | `create_customer_profile` | customer_id, kyc_result, risk_rating, currency, type |
| `accounts` | `open_account` | account_id, currency, account_type, status, bakong_id |
| `compliance_cases` | `create/update_compliance_case` | case_id, risk_level, flags, status, decision, STR ref |

### Vector store (`data/vector_store/sathapana_kyc_*.npz/.json`)

`nbc_regulations` (7), `product_policies` (4), `document_schemas` (7),
`risk_typologies` (5), `past_kyc_decisions` (4).

### Audit entries produced by one retail journey

```
runner          onboarding_start
runner          rag_requirements
core_banking    create_customer_profile   ← only gate A/B passes
core_banking    open_account
bakong          register_bakong
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
| **create_customer_profile** | **high** | officer approval (HITL) |
| **open_account** | **high** | officer approval (HITL) |
| **update_case** | **high** | officer approval (HITL) |

Guardrails (`llm/base_agent.py`): every high-risk call requests approval
via `ApprovalManager`; sensitive output (card/phone/email/ID numbers) is
redacted by `Guardrails`; every call is written to `audit_log`.

---

## 7. MCP protocol flow

`server.py` is a dependency-free MCP (JSON-RPC 2.0) server over stdio:

```
client ── initialize ────────────────►  {"protocolVersion","capabilities","serverInfo"}
client ── tools/list ────────────────►  15 tools with inputSchema
client ── ping ──────────────────────►  {}
client ── tools/call {name,arguments}►  {"content":[{"type":"text","text":"<JSON>"}],"isError":false}
```

Handlers are run through the same `ToolRegistry.invoke()` used by the
runner and the agent loop, so behaviour is identical on every surface.

---

## 8. Verify the flow yourself

```bat
cd sathapana_kyc_agent

python main.py seed          rem seeds/reseeds the knowledge base (idempotent)
python main.py demo          rem runs all 3 journeys end to end
python main.py serve         rem MCP server (stdio)
python -m pytest -q          rem 23 tests incl. all scenarios + MCP handlers
```

---

## 9. FAQ — Where is this useful if a teller already does this in core banking?

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
| 3 | **Escalation without burden on the teller** | Medium risk → `open_compliance_case` → routed to the MLRO with flags and evidence. High risk → declined *and* an STR reference to CAMFIU filed. Today the teller has neither the checklist nor the trigger to know "this is a CAMFIU case." The agent turns a gut feeling into a documented handoff. |
| 4 | **Automatic audit trail for NBC record-keeping** | Every call is time-stamped into `audit_log` with arguments, result and agent. When the regulator asks "why was this customer onboarded on this date?", the full decision is reconstructed in seconds. Manual onboarding leaves paper and memory. |
| 5 | **Channel scalability — self-service & kiosk** | The same flow is exposed over MCP (`server.py`), so it runs in the branch, the mobile app, or a kiosk. A low-risk retail customer is onboarded with zero teller keystrokes; tellers only touch exceptions. Teller seats are expensive — not every onboarding needs one. |
| 6 | **Cross-branch continuity** | `lookup_customer` carries history (kyc_result, compliance case, products) with the customer, so the next branch never re-asks for documents they already provided. |
| 7 | **Faster teller training / less tribal knowledge** | New staff ramp faster — `knowledge_search` answers "what documents for an SME loan?" with the product policy instead of asking the senior teller. |

### Where the agent does NOT replace the teller (by design)

- Liveness/face judgment on edge cases.
- Senior-management approval for PEPs / EDD cases (HITL in `ApprovalManager`).
- The human conversation with the customer.

The agent flags and routes; the officer decides. That partnership is the
intended operating model.

### Bottom line

The value is **screening consistency + mandatory checklist enforcement +
automatic STR/audit + distribution across channels** — layered on top of what
the teller already does, not as a replacement for it.

*Last updated: September 2026*