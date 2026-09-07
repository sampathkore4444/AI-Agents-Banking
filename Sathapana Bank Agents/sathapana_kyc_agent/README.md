# Sathapana Bank — KYC Onboarding Agent (RAG + MCP)

End-to-end implementation of a KYC onboarding agent localized for
**Sathapana Bank PLC (Cambodia)**, regulated by the **National Bank of
Cambodia (NBC)** under the Kingdom of Cambodia **Law on Anti-Money
Laundering and Combating the Financing of Terrorism (2020)**.

Built on the same agent pattern as the rest of this workspace
(`kyc_agent`, `aml_alert_agent`, …) but fully self-contained so it runs
with the packages already available in this environment (numpy,
sentence-transformers, sqlite3, pytest, ollama client).

## What's in the box

| Component | File | Notes |
|-----------|------|-------|
| Settings | `config.py` | NBC thresholds, UBO 25% / risk-based 10%, USD/KHR, provider & MCP settings |
| Vector store | `vector_store.py` | `get_vector_store()` backend factory (numpy default / chromadb) |
| RAG pipeline | `rag_pipeline.py` | BM25 + semantic hybrid search, query expansion, optional cross-encoder rerank, citations |
| RAG evaluation | `rag_eval.py` | Golden-question set (`main.py eval-rag`) |
| NBC knowledge | `seed_knowledge.py` | AML/CFT Law 2020, NBC docs (Khmer NID, family book, MoC/tax certs), Cambodia risk typologies, Sathapana products, prior decisions |
| Provider adapters | `integrations/` | `sanctions` / `identity` / `ocr` / `notify` / `bakong` / `camfiu` — each stub vs HTTP (`same interface`) |
| Crypto / secrets | `security/crypto.py` | Fernet PII encryption, HMAC tokenization, hash-chain salt, `.env` bootstrap |
| Tools | `tools/` | documents (Khmer), identity, sanctions/UBO (NBC+UNSC+OFAC+EU+domestic PEP), core banking (PII encrypted), compliance (validated STR→CAMFIU), notifications, Bakong |
| Audit / persistence | `db.py` | SQLite: hash-chained tamper-evident audit log (`verify-audit`), customers, accounts (USD/KHR), compliance cases, approvals, saga sessions, idempotency cache |
| Workflows | `workflow/` | DB-backed HITL `approvals.py` (SLA expiry), `onboarding.py` saga (idempotent steps + compensation) |
| Agent loop | `llm/base_agent.py` | Guardrails, approval workflow, memory, audit, ReAct loop |
| LLM backends | `llm/agent_ollama.py` | Local Ollama (tool-calling) |
| E2E runner | `runner.py` | Deterministic, no-LLM demo of 3 journeys through the saga |
| MCP server | `server.py` | MCP JSON-RPC server over stdio or TCP+TLS, with auth token, rate limit, payload cap |
| HTTP / OpenAPI | `api_server.py` | REST + auto-generated OpenAPI 3.0 spec and Swagger UI (tools, approvals, cases, audit) |
| CLI | `main.py` | `seed` / `demo` / `chat` / `serve` (stdio\|tcp) / `serve-api` / `eval-rag` / `verify-audit` / `providers` |
| Packaging | `Dockerfile`, `docker-compose.yml` | Debian-slim image with the embedding model pre-cached; repo bind-mounted for `.env` keys + `data/` persistence |

## Quick start

```bat
cd sathapana_kyc_agent

python main.py seed     rem populate NBC/Sathapana knowledge base (idempotent)
python main.py eval-rag rem golden-set retrieval evaluation (hit-rate / recall)
python main.py demo     rem run low / medium / high-risk onboarding end-to-end
python main.py verify-audit   rem tamper-evident audit chain check
python main.py chat     rem interactive chat (requires Ollama + model)
python main.py serve    rem MCP stdio server (default)
python main.py serve --transport tcp   rem TCP with optional TLS + auth
python main.py serve-api --port 8000   rem HTTP REST + Swagger UI (http://127.0.0.1:8000/)
python -m pytest        rem run tests
```

Keys are bootstrapped automatically into `.env` the first time crypto is used
(`KYC_ENCRYPTION_KEY`, `TOKENIZATION_KEY`, `HASH_CHAIN_SALT`); copy
`.env.example` for a full template. Production provider endpoints are also
pointed at via `.env`. Keep `.env` out of VCS (already in `.gitignore`).

### Demo journeys

`runner.py` executes the full onboarding flow for three scenarios:

1. **Retail low-risk** (individual, USD savings) → auto-approve + Bakong.
2. **SME medium-risk** (KHR, cash-intensive fuel trading, domestic PEP) →
   compliance case → officer approval with conditions.
3. **Casino high-risk** (adverse media, gambling sector) → declined and
   STR filed to CAMFIU.

Every step is appended to the SQLite audit trail (`data/sathapana_kyc.db`).

## MCP protocol

`server.py` implements the MCP spec over stdio using only the standard
library (JSON-RPC 2.0, newline-delimited). Supported methods:
`initialize`, `tools/list`, `tools/call`, `ping`, notifications.

Exposed tools (all in `tools/`):

- `knowledge_search`, `get_document_schema`, `assess_kyc_risk`
- `extract_and_classify_document`, `verify_customer_identity`
- `screen_customer_sanctions`, `screen_ubo`
- `lookup_customer`, `create_customer_profile`, `open_account`
- `register_bakong`, `open_compliance_case`, `get_case`, `update_case`
- `notify_customer`

To connect from any MCP client, register it as a stdio server:

```
mcpServers:
  sathapana-kyc:
    command: python
    args: [<path>/sathapana_kyc_agent/server.py]
    cwd: <path>/sathapana_kyc_agent
```

## HTTP API & Swagger

`api_server.py` exposes the same toolbox over REST with an auto-generated
OpenAPI 3.0 document (stdlib-only, no new dependencies):

```
python main.py serve-api --port 8000
```

| URL | What it is |
|-----|------------|
| `http://127.0.0.1:8000/` | Swagger UI (interactive, click **Authorize** to set the token) |
| `http://127.0.0.1:8000/openapi.json` | The spec, generated from `ToolRegistry` inputSchema |
| `POST /api/v1/tools/{tool}` | Invoke any registered tool (`{"arguments": {...}}`) |
| `GET /api/v1/approvals/pending` | HITL approval queue |
| `POST /api/v1/approvals/{id}/decide` | Approve / approve_with_conditions / reject (executes on approval) |
| `GET /api/v1/cases/{id}` | Compliance case |
| `GET /api/v1/audit/verify` · `GET /api/v1/audit/last` | Tamper check + recent audit entries |
| `GET /api/v1/health` · `GET /api/v1/providers` | Liveness + active provider backends |

Auth uses the same `KYC_MCP_AUTH_TOKEN` from `.env`, sent as
`Authorization: Bearer <token>`; `/` and `/openapi.json` are unauthenticated
so Swagger UI can discover the spec before you authorize.

## Run it: without Docker

Plain Python on the host (Python 3.11+). All state lives in
`data/` and keys in `.env` (auto-bootstrapped on first crypto use).

| Action | Command |
|--------|---------|
| Install deps (once) | `python -m pip install -r requirements.txt` |
| Seed knowledge base (once) | `python main.py seed` |
| **Start** REST API + Swagger UI | `python main.py serve-api --port 8000` |
| Open the API in a browser | `http://127.0.0.1:8000/` |
| **Stop** REST API | `Ctrl+C` |
| **Start** MCP server (stdio) | `python main.py serve` |
| **Start** MCP server (TCP) | `python main.py serve --transport tcp` |
| **Stop** MCP server | `Ctrl+C` |
| Run the E2E demo | `python main.py demo` |
| Verify audit chain / RAG eval | `python main.py verify-audit` / `python main.py eval-rag` |

Windows note: run from `sathapana_kyc_agent/`; use `py` instead of `python`
if `python` is not on PATH.

## Run it: with Docker

A `-slim` Linux image with torch and the embedding model pre-cached, so it
runs offline. The repo is **bind-mounted at `/app`** — the host's `.env`
(crypto keys), `data/` (SQLite + vector store) and code are shared with the
container, so a container restart never re-keys or re-seeds anything.

```bat
cd sathapana_kyc_agent
```

| Action | Command |
|--------|---------|
| Build image (once) | `docker build -t sathapana-kyc-agent:latest .` |
| **Start** REST API + Swagger UI (compose) | `docker compose up -d --build` |
| **Start** REST API + Swagger UI (docker run) | `docker run -d --name sathapana-kyc -p 8000:8000 -v "${PWD}:/app" -w /app sathapana-kyc-agent:latest` |
| Status / logs | `docker compose ps` / `docker compose logs -f` |
| Open the API in a browser | `http://127.0.0.1:8000/` |
| **Stop** (compose) | `docker compose down` |
| **Stop** (docker run) | `docker stop sathapana-kyc` |
| Remove stopped container | `docker rm sathapana-kyc` |
| One-off commands (demo / verify / eval) | `docker compose run --rm kyc-agent python main.py demo`<br>`docker compose run --rm kyc-agent python main.py verify-audit` |
| Interactive MCP (stdio) | `docker run -it --rm -v "${PWD}:/app" -w /app sathapana-kyc-agent:latest python main.py serve` |
| MCP over TCP | `docker run -d --rm -p 8888:8888 -e MCP_PORT=8888 -v "${PWD}:/app" -w /app sathapana-kyc-agent:latest python main.py serve --transport tcp` |

Notes:

- Keep the image name/server port in sync across `docker build`, `docker run`
  and `docker-compose.yml` (`127.0.0.1:8000:8000` binds localhost only).
- Set the auth token before exposing anything off-host:
  add `KYC_MCP_AUTH_TOKEN=...` to `.env` (already mounted into the container).
- The build downloads torch (large image, slow first `pip install`);
  subsequent rebuilds are cached. To use a different embedding model,
  rebuild with `docker build --build-arg EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2 .`.

## Cambodia / NBC localization (vs. the generic `kyc_agent`)

- Regulatory content is NBC + AML/CFT Law 2020, not UK/FCA.
- Document schemas cover Khmer national ID, family/residence book,
  Ministry of Commerce registration, tax/patent certificates, collateral
  (land titles); Khmer-script OCR flagged.
- Screening covers UN Consolidated List, NBC/Cambodia sanctions, OFAC/EU,
  plus domestic Cambodian PEPs.
- Beneficial ownership screening applies 25% default and a risk-based 10%
  threshold for high-risk customers.
- Cambodia risk typologies: casino/gaming & junkets, cash-intensive
  sectors (gold, money changers, real estate), cross-border corridors,
  domestic PEPs.
- Bakong linkage tool added for post-onboarding mobile-money onboarding.
- Accounts are opened in USD or KHR.
- Every RAG retrieval and tool call is audited (NBC record-keeping).
- Suspicious cases file an STR to CAMFIU.

## Production swap points

| Reference implementation | Production |
|--------------------------|------------|
| `integrations/*` stub providers | Live vendor APIs (set `*_PROVIDER=http` + URL/token in `.env`) |
| `vector_store.py` (numpy) | `VECTOR_BACKEND=chromadb` or pgvector / Qdrant |
| `all-MiniLM-L6-v2` | `paraphrase-multilingual-MiniLM-L12-v2` or OCR-friendly multilingual embedder for Khmer |
| Cross-encoder rerank (disabled) | Enable `RERANKER_ENABLED=true` in `.env` |
| SQLite audit | Central audit/logging platform with retention (chain still verifiable via `main.py verify-audit`) |

*Last updated: September 2026*