# Anti-Money Laundering (AML) Alert Agent — Architecture

## High-Level Architecture

```
                          ┌─────────────────────────────────────────┐
                          │         ANTI-MONEY LAUNDERING            │
                          │              ALERT AGENT                 │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   TRANSACTION       │          │   AML DETECTION     │          │   COMPLIANCE        │
│   INGESTION LAYER   │          │   ENGINE            │          │   RESPONSE LAYER    │
│                     │          │                      │          │                     │
│ • Core Banking      │          │ • Rule Engine        │          │ • SAR Filing        │
│ • Wire Transfer     │◄────────►│ • Structuring Detect │◄────────►│ • CTR Filing        │
│ • Cash Operations   │          │ • Sanctions Screen   │          │ • Case Management   │
│ • Correspondent     │          │ • PEP Screening      │          │ • Law Enforcement   │
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
│ • BSA/AML Regs      │          │ • Transaction Embs   │          │                     │
│ • Red Flag Types    │          │ • Behavioral Profiles│          │ • Guardrails        │
│ • SAR Guidelines    │          │ • PEP Risk Profiles  │          │ • HITL              │
│ • CTR Requirements  │          │ • Sanctions Matches  │          │ • Memory            │
│ • PEP Guidelines    │          │ • Typology Patterns  │          │ • Streaming         │
│ • BO Rules          │          │                      │          │ • Observability     │
│ • Sanctions Regs    │          │                      │          │                     │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
```

## Detailed Component Flow

```
Step 1: Transaction Arrives
    │
    ▼
Step 2: Threshold Check
    │
    ├─ Cash ≥ $10,000 → Flag for CTR filing
    │
    ▼ Below threshold
Step 3: Structuring Analysis
    │
    ├─ Multiple just-below-$10,000 transactions → STRUCTURING ALERT
    │
    ▼ No structuring pattern
Step 4: Country Risk Assessment
    │
    ├─ High-risk jurisdiction (FATF gray/black list) → Enhanced monitoring
    │
    ▼ Normal jurisdiction
Step 5: Sanctions Screening
    │
    ├─ OFAC SDN match → BLOCK + Report within 10 business days
    ├─ EU/UN sanctions match → BLOCK + Notify compliance
    │
    ▼ Clear
Step 6: PEP Screening
    │
    ├─ PEP identified → Enhanced Due Diligence required
    ├─ Foreign PEP + high-risk country → Senior management approval
    │
    ▼ No PEP
Step 7: Risk Score Calculation
    │
    ├─ Rule-based scoring (40%): thresholds, patterns, amounts
    ├─ ML-based scoring (35%): anomaly detection, embedding similarity
    ├─ Behavioral scoring (25%): profile match, time patterns
    │
    ▼ Combined risk score (0-100)
Step 8: Alert Generation
    │
    ├─ Score ≥ 80 → CRITICAL: Create case + SAR recommendation
    ├─ Score 60-79 → HIGH: Create case + assign investigator
    ├─ Score 40-59 → MEDIUM: Generate alert + enhanced monitoring
    ├─ Score < 40 → LOW: Log only
    │
    ▼
Step 9: Filing Decision
    │
    ├─ Suspicious activity ≥ $5,000 → SAR required (30-day deadline)
    ├─ Cash ≥ $10,000 → CTR required (15-day deadline)
    ├─ OFAC match → Blocking report (10 business days)
    │
    ▼
Step 10: Case Creation + Investigation
    │
    ├─ Assign investigator based on case type
    ├─ Collect evidence (transaction records, customer data)
    ├─ Document findings in investigation notes
    ├─ Escalate to compliance officer or law enforcement
    └─ Resolve case with SAR filing if warranted
```

## MCP Tool Definitions

### Transaction Monitoring
```json
{
  "name": "monitor_txn",
  "description": "Monitor a transaction for AML red flags including structuring, layering, and anomalies",
  "parameters": {
    "transaction_id": {"type": "string", "required": true},
    "customer_id": {"type": "string", "required": true},
    "amount": {"type": "number", "required": true},
    "currency": {"type": "string", "required": true},
    "transaction_type": {"type": "string", "enum": ["cash_deposit", "cash_withdrawal", "wire_transfer", "ach", "internal_transfer", "currency_exchange"]},
    "channel": {"type": "string", "enum": ["branch", "online", "mobile", "atm", "correspondent"]},
    "country": {"type": "string", "required": true},
    "counterparty_name": {"type": "string"},
    "counterparty_country": {"type": "string"}
  }
}
```

### Sanctions Screening
```json
{
  "name": "screen_individual",
  "description": "Screen an individual's name against OFAC SDN, EU, and UN sanctions lists",
  "parameters": {
    "name": {"type": "string", "required": true},
    "name_type": {"type": "string", "enum": ["individual", "entity", "vessel"]},
    "threshold": {"type": "number", "default": 0.85},
    "lists": {"type": "array", "items": {"type": "string"}}
  }
}
```

### SAR Creation
```json
{
  "name": "create_sar",
  "description": "Create a SAR with narrative. Deadline: 30 days from detection.",
  "parameters": {
    "customer_id": {"type": "string", "required": true},
    "customer_name": {"type": "string", "required": true},
    "customer_ssn_tin": {"type": "string", "required": true},
    "suspicious_activity_type": {"type": "string", "enum": ["structuring", "layering", "trade_based_ml", "shell_company", "terrorist_financing", "cyber_fraud", "other"]},
    "activity_description": {"type": "string", "required": true},
    "amount_involved": {"type": "number", "required": true}
  }
}
```

### Case Management
```json
{
  "name": "create_aml_case",
  "description": "Create an AML investigation case",
  "parameters": {
    "customer_id": {"type": "string", "required": true},
    "customer_name": {"type": "string", "required": true},
    "case_type": {"type": "string", "enum": ["structuring", "layering", "trade_based_ml", "shell_company", "terrorist_financing", "sanctions_violation", "pep_risk", "insider_threat"]},
    "description": {"type": "string", "required": true},
    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
  }
}
```

## RAG Pipeline Detail

```
Step 1: Query Rewrite
    │
    ▼ "What are the SAR filing requirements for structuring?"
    │
Step 2: Embed Query
    │
    ▼ [0.023, -0.156, 0.089, ...] (128-dim)
    │
Step 3: Search All Collections (7 parallel)
    │
    ├─ aml_regulations
    ├─ red_flag_typologies  ← TOP HIT
    ├─ sar_filing_guidelines  ← TOP HIT
    ├─ ctr_requirements
    ├─ pep_guidelines
    ├─ beneficial_ownership_rules
    └─ sanctions_regulations
    │
Step 4: Merge & Rerank
    │
    ▼ Top 5 chunks by relevance score
    │
Step 5: Assemble Context
    │
    ▼ "[1] (sar_filing) SAR Filing Requirements: A financial institution must file..."
    │
Step 6: Generate Response with Citations
    │
    ▼ "Under BSA requirements, a SAR must be filed when..."
```

## Vector Database Schema

### Collections & Documents

| Collection | Documents | Description |
|------------|-----------|-------------|
| `aml_regulations` | 5 | BSA, PATRIOT Act, CTA, OFAC, compliance programs |
| `red_flag_typologies` | 7 | Structuring, layering, TBML, shell companies, real estate, crypto, NRA |
| `sar_filing_guidelines` | 4 | Requirements, narrative, continuing SARs, VSD |
| `ctr_requirements` | 3 | Filing, aggregation, exemptions |
| `pep_guidelines` | 3 | Definition, EDD, risk assessment |
| `beneficial_ownership_rules` | 3 | CDD rule, UBO tracing, ongoing monitoring |
| `sanctions_regulations` | 5 | OFAC SDN, EU, UN, screening best practices, penalties |

### Embedding Dimensions

| Vector | Dimensions | Purpose |
|--------|------------|---------|
| Transaction Embedding | 128 | Transaction pattern representation |
| Behavioral Profile | 128 | Customer baseline for anomaly detection |
| PEP Risk Profile | 64 | Risk assessment representation |
| Typology Pattern | 128 | Known AML typology signatures |

## AML Scoring Model

```
                    ┌──────────────────────────────┐
                    │      AML RISK SCORE (0-100)  │
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
│ • Structuring │          │   Detection   │          │   Match       │
│ • Country     │          │ • Typology    │          │ • Time        │
│ • Amount      │          │   Matching    │          │   Pattern     │
│ • Round Num   │          │ • Clustering  │          │ • Frequency   │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │   COMBINED AML RISK SCORE     │
                    └──────────────────────────────┘
```

## Decision Matrix

| AML Score | Risk Level | Alert Level | Action | SAR Required | CTR Required |
|-----------|------------|-------------|--------|--------------|--------------|
| 0-39 | Low | None | Log only | No | If cash ≥ $10K |
| 40-59 | Medium | Medium | Enhanced monitoring | No | If cash ≥ $10K |
| 60-79 | High | High | Create case + assign | Yes if ≥ $5K | Yes if cash ≥ $10K |
| 80-100 | Critical | Critical | Create case + escalate | Yes | Yes |

## Compliance Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE CHECKPOINTS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. BSA COMPLIANCE                                              │
│     • SAR filing for $5,000+ suspicious activity                │
│     • 30-day filing deadline from detection                     │
│     • 5-year record retention                                   │
│     • Anti-tipping off (no disclosure to subject)               │
│                                                                 │
│  2. CTR COMPLIANCE                                              │
│     • CTR filing for $10,000+ cash transactions                 │
│     • 15-day filing deadline                                    │
│     • Aggregation of related transactions                       │
│     • Exemption documentation and review                        │
│                                                                 │
│  3. OFAC COMPLIANCE                                             │
│     • Screen all transactions against SDN list                  │
│     • Block/reject sanctioned parties                           │
│     • File blocking reports within 10 business days             │
│     • Strict liability — no intent required                     │
│                                                                 │
│  4. PEP COMPLIANCE                                              │
│     • Enhanced due diligence for all PEP relationships          │
│     • Senior management approval required                       │
│     • Source of funds and wealth verification                   │
│     • Ongoing monitoring for PEP status changes                 │
│                                                                 │
│  5. BENEFICIAL OWNERSHIP                                        │
│     • Identify 25%+ owners or controlling persons               │
│     • Verify identity and ownership                             │
│     • Maintain accurate records                                 │
│     • Update when changes occur                                 │
│                                                                 │
│  6. AUDIT TRAIL                                                 │
│     • Log all AML decisions                                     │
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
│  TRANSACTION INGESTION                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Core     │───►│ Threshold│───►│Structuring│                  │
│  │ Banking  │    │ Check    │    │ Analysis  │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  SCREENING                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │Sanctions │───►│   PEP    │───►│Country   │                  │
│  │ Screen   │    │ Screen   │    │ Risk     │                  │
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
│  FILING                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │   SAR    │───►│   CTR    │───►│ Blocking │                  │
│  │  Filing  │    │  Filing  │    │ Report   │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  INVESTIGATION                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │  Case    │───►│Evidence  │───►│Escalation│                  │
│  │ Creation │    │Collection│    │          │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **7 RAG collections** | Separate collections for better retrieval precision across regulation types |
| **Dual scoring (rules + ML)** | Rules catch known patterns (structuring), ML catches novel typologies |
| **128-dim embeddings** | Balance between expressiveness and computational cost for real-time screening |
| **Fuzzy matching (0.85 threshold)** | Catches name variations while limiting false positives |
| **30-day SAR deadline** | BSA regulatory requirement — automated tracking prevents missed deadlines |
| **90-day continuing SARs** | Regulatory requirement for ongoing suspicious activity |
| **Human-in-the-loop** | SAR filing and account blocking require compliance officer approval |
| **Anti-tipping off guardrails** | Federal crime to disclose SAR — agent cannot mention SAR to customer |
| **CEP aggregation** | Prevents structuring by analyzing transaction patterns across time windows |
| **OFAC strict liability** | No intent required — blocking is mandatory for SDN matches |
| **Beneficial ownership tracing** | CTA compliance requires identifying UBOs through ownership chains |
| **Audit trail logging** | All decisions, screenings, and actions logged for regulatory examination |
