# Real-Time Transaction Fraud Detection Agent — Architecture

## High-Level Architecture

```
                          ┌─────────────────────────────────────────┐
                          │         REAL-TIME FRAUD DETECTION        │
                          │              AGENT SYSTEM                │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   TRANSACTION       │          │   FRAUD DETECTION    │          │   INVESTIGATION     │
│   INGESTION LAYER   │          │   ENGINE             │          │   & RESPONSE LAYER  │
│                     │          │                      │          │                     │
│ • Payment Gateway   │          │ • Rule Engine        │          │ • Case Management   │
│ • Card Network      │◄────────►│ • ML Scoring         │◄────────►│ • Alert System      │
│ • Core Banking      │          │ • RAG Compliance     │          │ • Card Operations   │
│ • Mobile App        │          │ • Embedding Match    │          │ • Notifications     │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
           │                                  │                                  │
           └──────────────────────────────────┼──────────────────────────────────┘
                                              │
                                              ▼
                          ┌─────────────────────────────────────────┐
                          │              MCP SERVER                  │
                          │         (35+ Tools Exposed)              │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   RAG KNOWLEDGE     │          │   EMBEDDING         │          │   LLM AGENT         │
│   BASE              │          │   VECTOR DB         │          │   (Ollama/vLLM/     │
│                     │          │                      │          │    SGLang)          │
│ • Fraud Regs        │          │ • Transaction Embs   │          │                     │
│ • Typologies        │          │ • Customer Profiles  │          │ • Guardrails        │
│ • Detection Rules   │          │ • Fraud Patterns     │          │ • HITL              │
│ • Playbooks         │          │ • Device Fingerprints│          │ • Memory            │
│ • Case Precedents   │          │                      │          │ • Streaming         │
│ • Compliance        │          │                      │          │ • Observability     │
│ • Chargeback Rules  │          │                      │          │                     │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
```

## Detailed Component Flow

```
Step 1: Transaction Arrives
    │
    ▼
Step 2: Velocity Check (rate limits)
    │
    ├─ FAIL → Block transaction, alert customer
    │
    ▼ PASS
Step 3: Device Fingerprint Check
    │
    ├─ Unknown Device → Step-up authentication
    │
    ▼ Known Device
Step 4: Account Takeover Detection
    │
    ├─ ATO Indicators → Block + notify customer
    │
    ▼ No ATO
Step 5: Transaction Fraud Scoring
    │
    ├─ Amount anomaly check
    ├─ Geographic velocity check
    ├─ Merchant category risk check
    ├─ Time-of-day analysis
    ├─ ML embedding similarity
    │
    ▼
Step 6: Combined Fraud Score
    │
    ├─ Score ≥ 85 → BLOCK + Create case + Notify
    ├─ Score 60-84 → REVIEW + Step-up auth
    ├─ Score 40-59 → ALERT customer
    ├─ Score < 40 → ALLOW
    │
    ▼
Step 7: Guardrails Validation
    │
    ├─ Validate decision against thresholds
    ├─ Check business hours
    ├─ Verify compliance requirements
    │
    ▼
Step 8: Human-in-the-Loop (if required)
    │
    ├─ High-risk decisions → Approval queue
    │
    ▼
Step 9: Execute Action
    │
    ├─ Block transaction/card
    ├─ Send notifications
    ├─ Create investigation case
    ├─ Log audit trail
    │
    ▼
Step 10: Investigation (if flagged)
    │
    ├─ Gather evidence
    ├─ Cross-reference accounts
    ├─ Contact cardholder
    ├─ File chargeback/SAR
    └─ Resolve case
```

## MCP Tool Definitions

### Transaction Monitoring
```json
{
  "name": "monitor_transaction",
  "description": "Analyze a transaction in real-time for fraud indicators",
  "parameters": {
    "transaction_id": {"type": "string", "required": true},
    "customer_id": {"type": "string", "required": true},
    "amount": {"type": "number", "required": true},
    "currency": {"type": "string", "required": true},
    "merchant_id": {"type": "string", "required": true},
    "merchant_category": {"type": "string", "required": true},
    "channel": {"type": "string", "enum": ["card_present", "card_not_present", "online", "mobile"]},
    "country": {"type": "string", "required": true},
    "ip_address": {"type": "string"},
    "device_id": {"type": "string"}
  }
}
```

### Card Management
```json
{
  "name": "freeze_card",
  "description": "Freeze a card immediately to prevent further fraud",
  "parameters": {
    "card_id": {"type": "string", "required": true},
    "reason": {"type": "string", "required": true},
    "fraud_case_id": {"type": "string"}
  }
}
```

### Velocity Check
```json
{
  "name": "check_velocity",
  "description": "Check transaction velocity against rate limits",
  "parameters": {
    "customer_id": {"type": "string", "required": true},
    "amount": {"type": "number", "required": true},
    "transaction_id": {"type": "string", "required": true}
  }
}
```

### Case Management
```json
{
  "name": "create_fraud_case",
  "description": "Create a new fraud case",
  "parameters": {
    "customer_id": {"type": "string", "required": true},
    "case_type": {"type": "string", "enum": ["card_fraud", "account_takeover", "identity_theft", "synthetic_identity", "insider_fraud", "wire_fraud"]},
    "description": {"type": "string", "required": true},
    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
    "related_transactions": {"type": "array"},
    "related_cards": {"type": "array"}
  }
}
```

## RAG Pipeline Detail

```
Step 1: Query Rewrite
    │
    ▼ "What's the procedure for card fraud investigation?"
    │
Step 2: Embed Query
    │
    ▼ [0.023, -0.156, 0.089, ...] (128-dim)
    │
Step 3: Search All Collections (7 parallel)
    │
    ├─ fraud_regulations (cosine similarity)
    ├─ fraud_typologies
    ├─ detection_rules
    ├─ investigation_playbooks  ← TOP HIT
    ├─ case_precedents
    ├─ compliance_guidelines
    └─ chargeback_rules
    │
Step 4: Merge & Rerank
    │
    ▼ Top 5 chunks by relevance score
    │
Step 5: Assemble Context
    │
    ▼ "[1] (playbook) Card Fraud Investigation Playbook: Step 1: Pull last 30 days..."
    │
Step 6: Generate Response with Citations
    │
    ▼ "Based on our investigation playbook, here are the steps..."
```

## Vector Database Schema

### Collections & Documents

| Collection | Documents | Description |
|------------|-----------|-------------|
| `fraud_regulations` | 5 | Reg E, Reg Z, BSA, CFPB guidelines |
| `fraud_typologies` | 7 | CNP, counterfeit, ATO, identity, synthetic, insider, BEC |
| `detection_rules` | 8 | Velocity, geo, amount, device, behavioral, merchant, EMV rules |
| `investigation_playbooks` | 4 | Card fraud, ATO, dispute, SAR playbooks |
| `case_precedents` | 5 | Historical cases with outcomes |
| `compliance_guidelines` | 4 | Customer rights, data retention, tipping off, provisional credit |
| `chargeback_rules` | 6 | Visa/MC dispute reason codes |

### Embedding Dimensions

| Vector | Dimensions | Purpose |
|--------|------------|---------|
| Transaction Embedding | 128 | Transaction pattern representation |
| Customer Profile | 128 | Behavioral baseline |
| Fraud Pattern | 128 | Known fraud signatures |
| Device Fingerprint | 64 | Device trust representation |

## Fraud Scoring Model

```
                    ┌──────────────────────────────┐
                    │      FRAUD SCORE (0-100)      │
                    └──────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   RULE-BASED  │          │   ML-BASED    │          │   BEHAVIORAL  │
│   (40%)       │          │   (35%)       │          │   (25%)       │
│               │          │               │          │               │
│ • Velocity    │          │ • Anomaly     │          │ • Profile     │
│ • Amount      │          │   Detection   │          │   Match       │
│ • Geo         │          │ • Pattern     │          │ • Time        │
│ • Device      │          │   Matching    │          │   Pattern     │
│ • Merchant    │          │ • Clustering  │          │ • Frequency   │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │   COMBINED FRAUD SCORE        │
                    └──────────────────────────────┘
```

## Decision Matrix

| Fraud Score | Risk Level | Action | Notification | Case Required |
|-------------|------------|--------|--------------|---------------|
| 0-39 | Low | Allow | None | No |
| 40-59 | Medium | Alert | SMS/Email | No |
| 60-84 | High | Review + Step-up Auth | SMS/Email/Push | Optional |
| 85-100 | Critical | Block + Freeze Card | SMS/Email/Push | Yes |

## Compliance Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE CHECKPOINTS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. REG E COMPLIANCE                                            │
│     • 10-day investigation window                               │
│     • 45-day resolution (90 for new accounts)                   │
│     • Provisional credit within 10 business days                │
│     • Written notice of investigation results                   │
│                                                                 │
│  2. REG Z COMPLIANCE                                            │
│     • 60-day dispute window                                     │
│     • Zero liability for unauthorized charges                   │
│     • 30-day acknowledgment                                     │
│     • 90-day resolution                                         │
│                                                                 │
│  3. BSA COMPLIANCE                                              │
│     • SAR filing for $5,000+ suspicious transactions            │
│     • 30-day filing deadline                                    │
│     • 5-year record retention                                   │
│     • Anti-tipping off (no disclosure to subject)               │
│                                                                 │
│  4. AUDIT TRAIL                                                 │
│     • Log all fraud decisions                                   │
│     • Record all tool calls                                     │
│     • Track investigation steps                                 │
│     • Maintain evidence chain                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    END-TO-END DATA FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRANSACTION INGESTION                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Payment  │───►│ Velocity │───►│ Device   │                  │
│  │ Gateway  │    │ Check    │    │ Check    │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  FRAUD ANALYSIS                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Amount   │───►│ ML       │───►│ Behavioral│                  │
│  │ Check    │    │ Scoring  │    │ Match    │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  DECISION                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Score    │───►│ Guard-   │───►│ HITL     │                  │
│  │ Combine  │    │ rails    │    │ (if req) │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  ACTION                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Block/   │───►│ Notify   │───►│ Case     │                  │
│  │ Allow    │    │ Customer │    │ Create   │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Dual scoring (rules + ML)** | Rules catch known patterns, ML catches novel fraud |
| **128-dim embeddings** | Balance between expressiveness and computational cost |
| **Cosine similarity** | Normalized, scale-invariant, fast to compute |
| **4-tier scoring (0-100)** | Granular enough for nuanced decisions |
| **Human-in-the-loop** | Critical decisions need human oversight |
| **7 RAG collections** | Separate collections for better retrieval precision |
| **Device trust scoring** | New devices are inherently riskier |
| **Velocity limits** | Prevent rapid-fire fraud attempts |
| **SAR auto-flag** | $5,000+ threshold triggers compliance workflow |
| **Anti-tipping off** | Legal requirement — never disclose investigations |
