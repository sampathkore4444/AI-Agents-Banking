# Payment Fraud Prevention Agent

An AI agent for payment fraud prevention using **RAG**, **MCP**, and **embeddings**. Validates outgoing payments in real-time, detects anomalies (wrong beneficiary, unusual amounts), and prevents unauthorized transfers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                Payment Fraud Prevention Agent                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Payment     │  │  Beneficiary │  │  Sanctions   │         │
│  │  Validation   │  │ Verification │  │  Screening   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │   Velocity   │  │   Payment    │  │    Case      │         │
│  │    Check     │  │  Embedding   │  │  Management  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐         │                  │
│  │Notifications │  │    RAG       │         │                  │
│  │              │  │   Engine     │         │                  │
│  └──────────────┘  └──────────────┘         │                  │
│                                              │                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM Agent (Ollama/vLLM/SGLang)             │   │
│  │  • Guardrails • HITL • Memory • Streaming • Tracing     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### RAG Knowledge Base (7 collections)
- **Payment Fraud Policies** — Wire, ACH, check, RTP fraud prevention policies
- **Wire Fraud Patterns** — BEC, CEO impersonation, account compromise
- **ACH Fraud Typologies** — Unauthorized entries, payroll diversion, bill payment redirection
- **BEC Schemes** — Vendor compromise, attorney impersonation, real estate wire fraud
- **Check Fraud Rules** — Alteration, counterfeiting, stolen checks
- **RTP Fraud Risks** — Authorized push payment fraud, money mules, impersonation
- **Investigation Playbooks** — Wire, BEC, check, ACH fraud investigation workflows

### MCP Tools (40+ tools)

| Category | Tools | Description |
|----------|-------|-------------|
| **Payment Validation** | `validate_payment`, `get_payment_details`, `get_payment_history`, `block_payment`, `approve_payment`, `fraud_alerts`, `payment_statistics` | Real-time payment fraud scoring across all channels |
| **Beneficiary Verification** | `verify_beneficiary`, `add_payee`, `list_payees`, `remove_payee`, `beneficiary_risk` | Beneficiary name matching, account validation, risk profiling |
| **Sanctions Screening** | `screen_parties`, `sanctions_history`, `sanctions_lists` | OFAC/EU/UN screening for all payment parties |
| **Velocity Checks** | `check_velocity`, `velocity_summary`, `update_limits` | Payment rate limiting across channels |
| **Payment Embeddings** | `embed_payment`, `build_profile`, `detect_anomaly`, `add_pattern`, `match_pattern`, `fraud_pattern_list` | ML-based payment pattern analysis and anomaly detection |
| **Notifications** | `alert_payment_blocked`, `alert_payment_review`, `fraud_confirmation`, `ops_alert`, `notification_history` | Customer and operations alerts |
| **Case Management** | `create_case`, `update_fraud_case`, `add_case_evidence`, `escalate_fraud_case`, `resolve_fraud_case`, `get_fraud_case`, `account_cases`, `open_cases`, `case_statistics` | Full investigation case lifecycle |
| **RAG** | `knowledge_search` | Search payment fraud knowledge base |

### ML Embeddings
- **Payment Embedding** — 128-dim vector from payment features (amount, type, channel, timing)
- **Customer Payment Profile** — Behavioral baseline for anomaly detection
- **Fraud Pattern Matching** — Compare against known fraud signatures
- **Anomaly Detection** — Z-score analysis + embedding similarity

### Agent Capabilities
- **Guardrails** — Amount thresholds per payment type, velocity limits, validation
- **Human-in-the-Loop** — Approval for high-value blocks, SAR filing
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
ollama serve
ollama pull llama3.1:8b
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

# Payment Fraud Parameters
WIRE_THRESHOLD_REVIEW=25000
WIRE_THRESHOLD_BLOCK=100000
ACH_THRESHOLD_REVIEW=10000
ACH_THRESHOLD_BLOCK=50000
VELOCITY_LIMIT_DAILY_WIRES=3
VELOCITY_LIMIT_DAILY_WIRE_AMOUNT=100000
VELOCITY_LIMIT_DAILY_ACH=10
VELOCITY_LIMIT_DAILY_ACH_AMOUNT=50000
VELOCITY_LIMIT_HOURLY_PAYMENTS=5
FRAUD_SCORE_THRESHOLD_BLOCK=85
FRAUD_SCORE_THRESHOLD_REVIEW=60
```

## Payment Validation Flow

```
Payment Input
    │
    ├─→ Amount Threshold Check (per payment type)
    │
    ├─→ Beneficiary Verification (known payee, name match)
    │
    ├─→ Sanctions Screening (OFAC, EU, UN)
    │
    ├─→ Velocity Check (daily/hourly limits)
    │
    ├─→ Risk Score Calculation
    │
    ├─→ Decision (allow/alert/review/block)
    │
    ├─→ Guardrails (validate decision)
    │
    └─→ Action (notify, block, case creation)
```

## Fraud Scoring

| Score Range | Risk Level | Action |
|-------------|------------|--------|
| 0-39 | Low | Allow |
| 40-59 | Medium | Alert customer |
| 60-84 | High | Hold for review |
| 85-100 | Critical | Block + notify + case |

## Payment Type Thresholds

| Payment Type | Review Threshold | Block Threshold |
|--------------|------------------|-----------------|
| Wire (Domestic) | $25,000 | $100,000 |
| ACH | $10,000 | $50,000 |
| Check | $5,000 | $25,000 |
| RTP/FedNow | $10,000 | $25,000 |
| Zelle | $5,000 | $10,000 |

## Project Structure

```
payment_fraud_prevention_agent/
├── server.py                    # MCP server with 40+ tools
├── rag_pipeline.py              # RAG engine (7 collections)
├── config.py                    # Settings
├── seed_knowledge.py            # Payment fraud knowledge base
├── compare_agents.py            # Compare Ollama/vLLM/SGLang
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py            # Guardrails, HITL, memory, streaming
│   ├── agent_ollama.py          # Ollama backend
│   ├── agent_vllm.py            # vLLM backend
│   └── agent_sglang.py          # SGLang backend
└── tools/
    ├── payment_validation.py    # Real-time payment scoring
    ├── beneficiary_verification.py  # Beneficiary verification
    ├── sanctions_screening.py   # OFAC/EU/UN screening
    ├── velocity_check.py        # Payment rate limiting
    ├── payment_embedding.py     # ML pattern analysis
    ├── notifications.py         # Alerts
    └── case_management.py       # Investigation workflow
```

## Compliance

- **Reg E** — 10-day investigation, 45-day resolution, provisional credit
- **BSA** — SAR filing for $5,000+ suspicious activity
- **NACHA** — ACH return rules, unauthorized entry timeframes
- **OFAC** — SDN screening for all payment parties
- **BEC Prevention** — Out-of-band verification for beneficiary changes
