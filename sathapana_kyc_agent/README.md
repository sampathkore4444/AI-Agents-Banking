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
| Settings | `config.py` | NBC thresholds, UBO 25% / risk-based 10%, USD/KHR |
| Vector store | `vector_store.py` | Persistent cosine-similarity store (numpy + JSON) |
| RAG pipeline | `rag_pipeline.py` | BM25 + semantic hybrid search, rank fusion, citations |
| NBC knowledge | `seed_knowledge.py` | AML/CFT Law 2020, NBC docs (Khmer NID, family book, MoC/tax certs), Cambodia risk typologies, Sathapana products, prior decisions |
| Tools | `tools/` | documents (Khmer), identity, sanctions/UBO (NBC+UNSC+OFAC+EU+domestic PEP), core banking, compliance (STR→CAMFIU), notifications, Bakong |
| Audit / persistence | `db.py` | SQLite: audit trail, customers, accounts (USD/KHR), compliance cases |
| Agent loop | `llm/base_agent.py` | Guardrails, human-in-the-loop, memory, audit, ReAct loop |
| LLM backends | `llm/agent_ollama.py` | Local Ollama (tool-calling) |
| E2E runner | `runner.py` | Deterministic, no-LLM demo of 3 journeys |
| MCP server | `server.py` | Dependency-free MCP JSON-RPC server over stdio |
| CLI | `main.py` | `seed` / `demo` / `chat` / `serve` |

## Quick start

```bat
cd sathapana_kyc_agent

python main.py seed     rem populate NBC/Sathapana knowledge base
python main.py demo     rem run low / medium / high-risk onboarding end-to-end
python main.py chat     rem interactive chat (requires Ollama + model)
python main.py serve    rem MCP stdio server
python -m pytest        rem run tests
```

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
| `vector_store.py` (numpy) | ChromaDB / pgvector / Qdrant |
| `all-MiniLM-L6-v2` | `paraphrase-multilingual-MiniLM-L12-v2` or OCR-friendly multilingual embedder for Khmer |
| Stub tools | Jumio/SmileID, live Bakong member API, CAMFIU gateway, core banking (Temenos/OLB) |
| SQLite audit | Central audit/logging platform with retention |
| `runner.py` | Keep as acceptance-test harness |

*Last updated: September 2026*