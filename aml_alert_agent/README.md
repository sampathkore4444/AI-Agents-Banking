# Anti-Money Laundering (AML) Alert Agent

An AI agent for AML compliance using **RAG**, **MCP**, and **embeddings**. Monitors transactions for AML red flags, generates Suspicious Activity Reports (SARs), and escalates to compliance officers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AML Alert Agent                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Transaction  │  │  Sanctions   │  │     PEP      │         │
│  │  Monitoring   │  │  Screening   │  │  Screening   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │     SAR      │  │     CTR      │  │  Beneficial  │         │
│  │  Management  │  │  Management  │  │  Ownership   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │     Case     │  │Notifications │  │    RAG       │         │
│  │  Management  │  │              │  │   Engine     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM Agent (Ollama/vLLM/SGLang)             │   │
│  │  • Guardrails • HITL • Memory • Streaming • Tracing     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### RAG Knowledge Base (7 collections)
- **AML Regulations** — BSA, PATRIOT Act, CTA, OFAC, compliance programs
- **Red Flag Typologies** — Structuring, layering, trade-based ML, shell companies, crypto, real estate
- **SAR Filing Guidelines** — Requirements, narrative best practices, continuing SARs, VSD
- **CTR Requirements** — Filing, aggregation, exemptions
- **PEP Guidelines** — Definition, EDD, risk assessment framework
- **Beneficial Ownership Rules** — CDD, UBO identification, ongoing monitoring
- **Sanctions Regulations** — OFAC SDN, EU, UN sanctions, screening best practices

### MCP Tools (40+ tools)

| Category | Tools | Description |
|----------|-------|-------------|
| **Transaction Monitoring** | `monitor_txn`, `get_txn_details`, `get_txn_history`, `block_txn`, `analyze_structuring`, `get_alerts`, `aml_statistics` | AML red flag detection and structuring analysis |
| **Sanctions Screening** | `screen_individual`, `screen_entity`, `screen_vessel`, `screen_txn`, `sanctions_screening_history`, `sanctions_lists` | OFAC SDN, EU, UN screening with fuzzy matching |
| **PEP Screening** | `screen_pep`, `get_pep_info`, `assess_pep_risk`, `get_rca`, `pep_screening_history` | PEP identification, risk assessment, RCA tracking |
| **SAR Management** | `create_sar`, `update_sar`, `file_sar`, `create_continuing_sar`, `get_sar_details`, `list_sars`, `sar_statistics` | Full SAR lifecycle with narrative generation |
| **CTR Management** | `file_ctr`, `check_txn_aggregation`, `create_ctr_exemption`, `list_ctr_exemptions`, `revoke_ctr_exemption`, `ctr_statistics` | CTR filing, aggregation, exemption management |
| **Beneficial Ownership** | `identify_bo`, `verify_bo`, `trace_ubo`, `update_bo`, `get_bo_owners`, `pending_bo_verifications` | BO identification, verification, UBO tracing |
| **Case Management** | `create_aml_case`, `update_aml_case`, `add_case_evidence`, `escalate_aml_case`, `resolve_aml_case`, `get_aml_case`, `customer_cases`, `open_cases`, `escalated_cases`, `case_statistics` | Full investigation case lifecycle |
| **Notifications** | `send_aml_alert`, `sar_filing_notification`, `ctr_filing_notification`, `escalation_notification`, `deadline_reminder`, `continuing_sar_reminder`, `notification_history` | Compliance alerts and reminders |
| **RAG** | `knowledge_search` | Search AML knowledge base |

### ML Embeddings
- **Transaction Embedding** — 128-dim vector from transaction features
- **Behavioral Profile** — Customer baseline for anomaly detection
- **Typology Matching** — Compare against known AML patterns
- **PEP Risk Profile** — Risk assessment embedding

### Agent Capabilities
- **Guardrails** — SAR/CTR thresholds, filing deadlines, validation
- **Human-in-the-Loop** — Approval for SAR filing, account blocking
- **Memory** — Investigation context tracking
- **Streaming** — Real-time analysis output
- **Observability** — Trace IDs for audit trail

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Knowledge Base
```bash
python seed_knowledge.py
```

### 3. Run with Ollama
```bash
# Start Ollama
ollama serve

# Pull model
ollama pull llama3.1:8b

# Run agent
python -m llm.agent_ollama
```

### 4. Or Run MCP Server
```bash
python server.py
```

### 5. Compare Backends
```bash
python compare_agents.py
```

## Configuration

Create a `.env` file:
```env
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o

# AML Parameters
SAR_THRESHOLD_AMOUNT=5000
CTR_THRESHOLD_AMOUNT=10000
SAR_FILING_DEADLINE_DAYS=30
CTR_FILING_DEADLINE_DAYS=15
STRUCTURING_THRESHOLD_AMOUNT=10000
STRUCTURING_MAX_TRANSACTIONS=3
```

## Transaction Monitoring Flow

```
Transaction Input
    │
    ├─→ Threshold Check (CTR $10,000+)
    │
    ├─→ Structuring Analysis (just-below patterns)
    │
    ├─→ Country Risk Check (high-risk jurisdictions)
    │
    ├─→ Amount Anomaly (deviation from baseline)
    │
    ├─→ Sanctions Screening (OFAC, EU, UN)
    │
    ├─→ PEP Screening (politically exposed)
    │
    ├─→ Risk Score Calculation
    │
    ├─→ Alert Generation (if score ≥ 40)
    │
    ├─→ SAR/CTR Decision
    │
    └─→ Case Creation + Escalation
```

## AML Alert Levels

| Risk Score | Alert Level | Action |
|------------|-------------|--------|
| 0-39 | Low | Log only |
| 40-59 | Medium | Generate alert, enhanced monitoring |
| 60-79 | High | Create case, assign investigator |
| 80-100 | Critical | Create case + SAR recommendation + escalate |

## Filing Deadlines

| Report | Deadline | Threshold |
|--------|----------|-----------|
| SAR | 30 days from detection | $5,000+ suspicious activity |
| CTR | 15 calendar days | $10,000+ cash transaction |
| Continuing SAR | Every 90 days | Ongoing suspicious activity |
| Blocking Report | 10 business days | OFAC SDN match |

## Project Structure

```
aml_alert_agent/
├── server.py                    # MCP server with 40+ tools
├── rag_pipeline.py              # RAG engine (7 collections)
├── config.py                    # Settings
├── seed_knowledge.py            # AML knowledge base
├── compare_agents.py            # Compare Ollama/vLLM/SGLang
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py            # Guardrails, HITL, memory, streaming
│   ├── agent_ollama.py          # Ollama backend
│   ├── agent_vllm.py            # vLLM backend
│   └── agent_sglang.py          # SGLang backend
└── tools/
    ├── transaction_monitoring.py  # AML red flag detection
    ├── sanctions_screening.py     # OFAC/EU/UN screening
    ├── pep_screening.py           # PEP identification
    ├── sar_management.py          # SAR lifecycle
    ├── ctr_management.py          # CTR filing
    ├── beneficial_ownership.py    # BO identification/verification
    ├── case_management.py         # Investigation workflow
    └── notifications.py           # Compliance alerts
```

## Compliance

- **BSA** — SAR for $5,000+ suspicious activity, CTR for $10,000+ cash
- **PATRIOT Act** — Enhanced due diligence, CIP requirements
- **OFAC** — SDN screening, blocking reports (strict liability)
- **Corporate Transparency Act** — Beneficial ownership reporting
- **Anti-Tipping Off** — Never disclose SAR filing to subject (federal crime)
- **Record Retention** — SARs: 5 years, CTRs: 5 years, case files: 7 years
