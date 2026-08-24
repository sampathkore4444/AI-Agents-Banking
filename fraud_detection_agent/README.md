# Real-Time Transaction Fraud Detection Agent

An AI agent for real-time transaction fraud detection using **RAG**, **MCP**, and **embeddings**. Analyzes transactions in real-time, flags suspicious activity, and takes action (block, alert, allow).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fraud Detection Agent                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Transaction  │  │   Velocity   │  │   Device     │         │
│  │  Monitoring   │  │   Checker    │  │   Tracker    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │   Account    │  │   Anomaly    │  │    Case      │         │
│  │  Takeover    │  │  Detection   │  │  Management  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │     Card     │  │ Notifications│  │    RAG       │         │
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
- **Fraud Regulations** — Reg E, Reg Z, BSA, CFPB guidelines
- **Fraud Typologies** — CNP fraud, ATO, identity theft, synthetic identity, BEC
- **Detection Rules** — Velocity, geo, amount, device, behavioral, merchant rules
- **Investigation Playbooks** — Step-by-step workflows for card fraud, ATO, disputes, SAR
- **Case Precedents** — Historical fraud cases and outcomes
- **Compliance Guidelines** — Customer rights, data retention, anti-tipping off
- **Chargeback Rules** — Visa/Mastercard dispute reason codes

### MCP Tools (35+ tools)

| Category | Tools | Description |
|----------|-------|-------------|
| **Transaction Monitoring** | `monitor_transaction`, `get_txn_details`, `get_txn_history`, `block_txn`, `unblock_txn`, `fraud_statistics` | Real-time transaction analysis and fraud scoring |
| **Card Management** | `freeze_card`, `unfreeze_card`, `replace_card`, `card_status`, `customer_cards`, `update_card_limits` | Card freeze/unfreeze, replacement, limits |
| **Velocity Checks** | `check_velocity`, `velocity_summary`, `update_limits` | Transaction rate limiting and velocity monitoring |
| **Device Tracking** | `register_device`, `check_device`, `device_history`, `flag_device`, `block_device` | Device fingerprinting and trust scoring |
| **Account Takeover** | `monitor_login`, `login_history`, `revoke_sessions`, `update_account_security`, `block_ip_address` | Login monitoring and credential protection |
| **Anomaly Detection** | `embed_txn`, `embed_behavior`, `detect_txn_anomaly`, `add_fraud_pattern`, `fraud_pattern_list` | ML-based anomaly detection using embeddings |
| **Case Management** | `create_fraud_case`, `update_fraud_case`, `resolve_fraud_case`, `get_fraud_case`, `customer_fraud_cases`, `open_fraud_cases`, `add_case_evidence`, `escalate_fraud_case`, `fraud_case_stats` | Full case lifecycle management |
| **Notifications** | `alert_customer_fraud`, `alert_card_blocked`, `alert_txn_blocked`, `alert_new_login`, `notification_history`, `compliance_alert` | Fraud alerts and compliance notifications |
| **RAG** | `knowledge_search` | Search fraud knowledge base |

### ML Embeddings
- **Transaction Embedding** — 128-dim vector from transaction features
- **Customer Behavior Profile** — Behavioral baseline for anomaly detection
- **Fraud Pattern Matching** — Compare against known fraud patterns
- **Anomaly Scoring** — Z-score analysis + embedding similarity

### Agent Capabilities
- **Guardrails** — Block/review/alert thresholds with validation
- **Human-in-the-Loop** — Approval for high-risk decisions (block card, close account)
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

# Fraud Detection Parameters
FRAUD_SCORE_THRESHOLD_BLOCK=85
FRAUD_SCORE_THRESHOLD_REVIEW=60
VELOCITY_LIMIT_DAILY_TRANSACTIONS=20
VELOCITY_LIMIT_DAILY_AMOUNT=50000
```

## Transaction Analysis Flow

```
Transaction Input
    │
    ├─→ Velocity Check (rate limits)
    │
    ├─→ Device Check (fingerprint, trust)
    │
    ├─→ Account Takeover Check (login anomalies)
    │
    ├─→ Anomaly Detection (ML embeddings)
    │
    ├─→ Fraud Scoring (combined score)
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
| 60-84 | High | Review + step-up auth |
| 85-100 | Critical | Block + notify + case |

## Project Structure

```
fraud_detection_agent/
├── server.py                    # MCP server with 35+ tools
├── rag_pipeline.py              # RAG engine (7 collections)
├── config.py                    # Settings
├── seed_knowledge.py            # Fraud knowledge base
├── compare_agents.py            # Compare Ollama/vLLM/SGLang
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py            # Guardrails, HITL, memory, streaming
│   ├── agent_ollama.py          # Ollama backend
│   ├── agent_vllm.py            # vLLM backend
│   └── agent_sglang.py          # SGLang backend
└── tools/
    ├── transaction_monitoring.py  # Real-time analysis
    ├── card_management.py         # Card operations
    ├── velocity_check.py          # Rate limiting
    ├── device_tracking.py         # Device fingerprinting
    ├── account_takeover.py        # ATO detection
    ├── anomaly_detection.py       # ML-based detection
    ├── notifications.py           # Alerts
    └── case_management.py         # Investigation
```

## Compliance

- **Reg E** — 10-day investigation, 45-day resolution, provisional credit
- **Reg Z** — 60-day dispute window, zero liability
- **BSA** — SAR filing for $5,000+ suspicious transactions
- **Anti-Tipping Off** — Never disclose SAR filing to subject
