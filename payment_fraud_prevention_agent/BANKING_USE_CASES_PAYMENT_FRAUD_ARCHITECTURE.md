# Payment Fraud Prevention Agent — Architecture

## High-Level Architecture

```
                          ┌─────────────────────────────────────────┐
                          │       PAYMENT FRAUD PREVENTION          │
                          │              AGENT SYSTEM               │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   PAYMENT INGESTION │          │   FRAUD DETECTION   │          │   RESPONSE &        │
│   LAYER             │          │   ENGINE            │          │   INVESTIGATION     │
│                     │          │                      │          │                     │
│ • Wire Transfers    │          │ • Rule Engine        │          │ • Block/Allow       │
│ • ACH Processing    │◄────────►│ • ML Scoring         │◄────────►│ • Case Management   │
│ • Check Clearing    │          │ • Sanctions Screen   │          │ • Notifications     │
│ • RTP/FedNow/Zelle  │          │ • Velocity Check     │          │ • Recalls           │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
           │                                  │                                  │
           └──────────────────────────────────┼──────────────────────────────────┘
                                              │
                                              ▼
                          ┌─────────────────────────────────────────┐
                          │              MCP SERVER                  │
                          │         (40+ Tools Exposed)              │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   RAG KNOWLEDGE     │          │   EMBEDDING         │          │   LLM AGENT         │
│   BASE              │          │   VECTOR DB         │          │   (Ollama/vLLM/     │
│                     │          │                      │          │    SGLang)          │
│ • Payment Policies  │          │ • Payment Embs       │          │                     │
│ • Wire Fraud        │          │ • Customer Profiles  │          │ • Guardrails        │
│ • ACH Fraud         │          │ • Fraud Patterns     │          │ • HITL              │
│ • BEC Schemes       │          │ • Anomaly Scores     │          │ • Memory            │
│ • Check Fraud       │          │                      │          │ • Streaming         │
│ • RTP Risks         │          │                      │          │ • Observability     │
│ • Playbooks         │          │                      │          │                     │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
```

## Detailed Component Flow

```
Step 1: Payment Initiated
    │
    ▼
Step 2: Amount Threshold Check
    │
    ├─ Wire ≥ $100,000 → BLOCK + dual approval required
    ├─ Wire ≥ $25,000 → REVIEW threshold
    ├─ ACH ≥ $50,000 → BLOCK threshold
    ├─ ACH ≥ $10,000 → REVIEW threshold
    ├─ RTP ≥ $25,000 → BLOCK threshold
    │
    ▼ Below thresholds
Step 3: Beneficiary Verification
    │
    ├─ Known payee → Lower risk score
    ├─ Name match only (different account) → Flag
    ├─ New beneficiary → Flag + enhanced monitoring
    ├─ High-risk country beneficiary → Flag
    │
    ▼
Step 4: Sanctions Screening
    │
    ├─ OFAC SDN match → BLOCK + report within 10 business days
    ├─ EU/UN sanctions match → BLOCK
    ├─ Sanctioned country → BLOCK
    │
    ▼ Clear
Step 5: Velocity Check
    │
    ├─ Daily wire count > 3 → Flag
    ├─ Daily wire amount > $100K → Flag
    ├─ Daily ACH count > 10 → Flag
    ├─ Daily ACH amount > $50K → Flag
    ├─ Hourly payments > 5 → Flag
    │
    ▼
Step 6: ML Anomaly Detection
    │
    ├─ Payment embedding vs customer profile
    ├─ Fraud pattern matching
    ├─ Amount z-score analysis
    │
    ▼
Step 7: Risk Score Calculation
    │
    ├─ Rule-based scoring (40%): thresholds, velocity, country
    ├─ ML-based scoring (35%): embedding similarity, anomaly
    ├─ Behavioral scoring (25%): profile match, time patterns
    │
    ▼ Combined risk score (0-100)
Step 8: Decision
    │
    ├─ Score ≥ 85 → BLOCK + create case + notify
    ├─ Score 60-84 → HOLD FOR REVIEW
    ├─ Score 40-59 → ALERT customer
    ├─ Score < 40 → ALLOW
    │
    ▼
Step 9: Guardrails Validation
    │
    ├─ Validate decision against thresholds
    ├─ Check business hours
    │
    ▼
Step 10: Human-in-the-Loop (if required)
    │
    ├─ High-value blocks → Approval queue
    │
    ▼
Step 11: Execute Action
    │
    ├─ Block/allow payment
    ├─ Send notifications
    ├─ Create investigation case
    └─ Log audit trail
```

## MCP Tool Definitions

### Payment Validation
```json
{
  "name": "validate_payment",
  "description": "Validate a payment in real-time for fraud indicators",
  "parameters": {
    "payment_id": {"type": "string", "required": true},
    "payer_account_id": {"type": "string", "required": true},
    "payer_name": {"type": "string", "required": true},
    "payee_name": {"type": "string", "required": true},
    "payee_account_id": {"type": "string"},
    "payee_bank_routing": {"type": "string", "required": true},
    "amount": {"type": "number", "required": true},
    "currency": {"type": "string", "required": true},
    "payment_type": {"type": "string", "enum": ["wire", "ach", "check", "rtp", "fednow", "zelle"]},
    "channel": {"type": "string", "enum": ["online", "mobile", "branch", "phone", "batch"]},
    "is_international": {"type": "boolean"},
    "beneficiary_country": {"type": "string"}
  }
}
```

### Beneficiary Verification
```json
{
  "name": "verify_beneficiary",
  "description": "Verify a beneficiary against known payees and risk indicators",
  "parameters": {
    "account_id": {"type": "string", "required": true},
    "payee_name": {"type": "string", "required": true},
    "payee_account_number": {"type": "string", "required": true},
    "payee_routing_number": {"type": "string", "required": true},
    "payee_bank_name": {"type": "string"},
    "payee_country": {"type": "string"},
    "payment_amount": {"type": "number"}
  }
}
```

### Velocity Check
```json
{
  "name": "check_velocity",
  "description": "Check payment velocity against configured limits",
  "parameters": {
    "account_id": {"type": "string", "required": true},
    "amount": {"type": "number", "required": true},
    "payment_type": {"type": "string", "required": true},
    "payment_id": {"type": "string", "required": true}
  }
}
```

## RAG Pipeline Detail

```
Step 1: Query Rewrite
    │
    ▼ "What is the procedure for BEC wire fraud investigation?"
    │
Step 2: Embed Query
    │
    ▼ [0.023, -0.156, 0.089, ...] (128-dim)
    │
Step 3: Search All Collections (7 parallel)
    │
    ├─ payment_fraud_policies
    ├─ wire_fraud_patterns  ← TOP HIT
    ├─ ach_fraud_typologies
    ├─ bec_schemes  ← TOP HIT
    ├─ check_fraud_rules
    ├─ rtp_fraud_risks
    └─ investigation_playbooks  ← TOP HIT
    │
Step 4: Merge & Rerank
    │
    ▼ Top 5 chunks by relevance score
    │
Step 6: Generate Response with Citations
    │
    ▼ "Based on our BEC investigation playbook, here are the steps..."
```

## Vector Database Schema

### Collections & Documents

| Collection | Documents | Description |
|------------|-----------|-------------|
| `payment_fraud_policies` | 5 | Wire, ACH, check, RTP, Reg E policies |
| `wire_fraud_patterns` | 4 | BEC invoice, CEO impersonation, account compromise, triangulation |
| `ach_fraud_typologies` | 4 | Unauthorized entries, payroll diversion, bill pay, check conversion |
| `bec_schemes` | 3 | Vendor compromise, attorney impersonation, real estate wire fraud |
| `check_fraud_rules` | 3 | Alteration, counterfeit, stolen checks |
| `rtp_fraud_risks` | 3 | APP fraud, money mules, impersonation |
| `investigation_playbooks` | 4 | Wire, BEC, check, ACH investigation workflows |

## Fraud Scoring Model

```
                    ┌──────────────────────────────┐
                    │   PAYMENT FRAUD SCORE (0-100) │
                    └──────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   RULE-BASED  │          │   ML-BASED    │          │   BEHAVIORAL  │
│   (40%)       │          │   (35%)       │          │   (25%)       │
│               │          │               │          │               │
│ • Thresholds  │          │ • Anomaly     │          │ • Profile     │
│ • Velocity    │          │   Detection   │          │   Match       │
│ • Country     │          │ • Pattern     │          │ • Time        │
│ • Amount      │          │   Matching    │          │   Pattern     │
│ • Round Num   │          │ • Clustering  │          │ • Frequency   │
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
| 40-59 | Medium | Alert customer | SMS/Email | No |
| 60-84 | High | Hold for review | SMS/Email/Push | Optional |
| 85-100 | Critical | Block payment | SMS/Email/Push | Yes |

## Payment Type Thresholds

| Payment Type | Review | Block | SAR Threshold |
|--------------|--------|-------|---------------|
| Wire (Domestic) | $25,000 | $100,000 | $5,000 |
| ACH | $10,000 | $50,000 | $5,000 |
| Check | $5,000 | $25,000 | $5,000 |
| RTP/FedNow | $10,000 | $25,000 | $5,000 |
| Zelle | $5,000 | $10,000 | $5,000 |

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
│  2. BSA COMPLIANCE                                              │
│     • SAR filing for $5,000+ suspicious activity                │
│     • 30-day filing deadline                                    │
│     • 5-year record retention                                   │
│                                                                 │
│  3. OFAC COMPLIANCE                                             │
│     • Screen all payment parties                                │
│     • Block/reject sanctioned parties                           │
│     • File blocking reports within 10 business days             │
│                                                                 │
│  4. NACHA COMPLIANCE                                            │
│     • Unauthorized ACH return within 60 days                    │
│     • Return reason codes (R05, R07, R10)                       │
│     • Same-day notification requirements                        │
│                                                                 │
│  5. BEC PREVENTION                                              │
│     • Out-of-band verification for bank detail changes          │
│     • Dual approval for high-value wires                        │
│     • Customer education on APP fraud                           │
│                                                                 │
│  6. AUDIT TRAIL                                                 │
│     • Log all payment decisions                                 │
│     • Record all screening results                              │
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
│  PAYMENT INGESTION                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Wire/    │───►│ Amount   │───►│Beneficiary│                  │
│  │ ACH/RTP  │    │ Check    │    │ Verify   │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  SCREENING                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │Sanctions │───►│Velocity  │───►│ ML       │                  │
│  │ Screen   │    │ Check    │    │ Anomaly  │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  SCORING                                                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │  Rule    │───►│   ML     │───►│Behavioral│                  │
│  │  Score   │    │  Score   │    │ Score    │                  │
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
| **Channel-specific thresholds** | Wire transfers carry higher risk than ACH; RTP is irrevocable |
| **Dual scoring (rules + ML)** | Rules catch known patterns, ML catches novel fraud |
| **128-dim embeddings** | Balance between expressiveness and computational cost |
| **Beneficiary verification** | First line of defense against BEC and invoice fraud |
| **Velocity limits** | Prevent rapid-fire fraud attempts across channels |
| **Out-of-band verification** | Critical for preventing BEC — always verify bank detail changes by phone |
| **7 RAG collections** | Separate collections for better retrieval precision per fraud type |
| **RTP-specific handling** | Irrevocable payments need stricter pre-validation |
| **Customer notification** | Transparency builds trust; customers are frontline detectors |
| **SAR auto-flag** | $5,000+ threshold triggers compliance workflow |
| **HITL for high-value blocks** | Prevents blocking legitimate high-value payments |
| **Audit trail logging** | All decisions, screenings, and actions logged for regulatory examination |
