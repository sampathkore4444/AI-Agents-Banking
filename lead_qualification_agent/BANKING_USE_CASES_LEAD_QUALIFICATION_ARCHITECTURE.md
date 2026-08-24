# Lead Qualification Agent — Architecture

## High-Level Architecture

```
                          ┌─────────────────────────────────────────┐
                          │       LEAD QUALIFICATION AGENT           │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   LEAD INTAKE       │          │   QUALIFICATION     │          │   ROUTING &         │
│   LAYER             │          │   ENGINE            │          │   CONVERSION        │
│                     │          │                      │          │                     │
│ • Web Forms         │◄────────►│ • Lead Scoring       │◄────────►│ • Tier Assignment   │
│ • Chat              │          │ • BANT/CHAMP/MEDDIC  │          │ • Advisor Matching  │
│ • Referrals         │          │ • Intent Analysis    │          │ • Calendar Booking  │
│ • Phone             │          │ • Eligibility Check  │          │ • Follow-up         │
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
│ • Qualification     │          │ • Intent Embeddings   │          │                     │
│ • Playbooks         │          │ • Lead Profiles      │          │ • Guardrails        │
│ • Scoring Models    │          │ • Conversion Pattern │          │ • HITL              │
│ • Conversion        │          │   Matching           │          │ • Memory            │
│ • Eligibility       │          │                      │          │ • Streaming         │
│ • Compliance        │          │                      │          │ • TCPA Compliance   │
│ • Competitor Intel  │          │                      │          │                     │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
```

## Detailed Component Flow

```
Step 1: Lead Arrives (web/chat/phone/referral)
    │
    ▼
Step 2: Capture Information
    │
    ├─ Name, email, phone
    ├─ Source (how they found us)
    ├─ Product interest
    ├─ Basic demographics
    │
    ▼
Step 3: Auto-Score Lead
    │
    ├─ Demographic scoring (age, income, credit)
    ├─ Behavioral scoring (pages, calculator, app started)
    ├─ Intent scoring (source, urgency signals)
    │
    ▼
Step 4: Qualify Against Framework
    │
    ├─ BANT: Budget, Authority, Need, Timeline
    ├─ CHAMP: Challenges, Authority, Money, Prioritization
    ├─ MEDDIC: Metrics, Economic Buyer, Decision Criteria...
    │
    ▼
Step 5: Check Product Eligibility
    │
    ├─ Credit score minimum
    ├─ Income requirement
    ├─ Age requirement
    │
    ▼
Step 6: Assign Tier
    │
    ├─ Hot (80-100) → Senior Advisor
    ├─ Warm (60-79) → Sales Team
    ├─ Cool (40-59) → Nurture Campaign
    ├─ Cold (0-39) → Database
    │
    ▼
Step 7: Route & Execute Playbook
    │
    ├─ Book consultation (if hot)
    ├─ Send follow-up materials
    ├─ Start nurture sequence
    └─ Log in CRM
```

## MCP Tool Definitions

### Create Lead
```json
{
  "name": "create_lead",
  "description": "Create a new lead from inbound inquiry",
  "parameters": {
    "lead_id": {"type": "string", "required": true},
    "first_name": {"type": "string", "required": true},
    "last_name": {"type": "string", "required": true},
    "email": {"type": "string", "required": true},
    "phone": {"type": "string", "required": true},
    "source": {"type": "string", "enum": ["website", "chat", "phone", "referral", "webinar", "outbound"]},
    "product_interest": {"type": "string", "required": true},
    "demographics": {"type": "object"},
    "behavior": {"type": "object"}
  }
}
```

### Evaluate Lead
```json
{
  "name": "evaluate_lead",
  "description": "Evaluate a lead against a qualification framework",
  "parameters": {
    "lead": {"type": "object", "required": true},
    "framework": {"type": "string", "enum": ["BANT", "CHAMP", "MEDDIC"], "default": "BANT"}
  }
}
```

### Book Consultation
```json
{
  "name": "book_consultation",
  "description": "Book a consultation with an advisor",
  "parameters": {
    "lead_id": {"type": "string", "required": true},
    "advisor_id": {"type": "string"},
    "product_interest": {"type": "string", "required": true},
    "preferred_date": {"type": "string", "required": true},
    "preferred_time": {"type": "string", "required": true},
    "channel": {"type": "string", "enum": ["phone", "video", "in_person"]}
  }
}
```

## RAG Pipeline Detail

```
Step 1: Query Rewrite
    │
    ▼ "What should I ask a mortgage lead?"
    │
Step 2: Embed Query
    │
    ▼ [0.023, -0.156, 0.089, ...] (128-dim)
    │
Step 3: Search All Collections (7 parallel)
    │
    ├─ qualification_criteria (finds BANT framework)
    ├─ sales_playbooks (finds mortgage playbook)
    ├─ lead_scoring_models (scoring rules)
    ├─ conversion_patterns (what works)
    ├─ product_eligibility (mortgage requirements)
    ├─ compliance_rules (TCPA requirements)
    └─ competitor_intelligence (counter-strategies)
    │
Step 4: Merge & Rerank
    │
    ▼ Top 5 chunks by relevance
    │
Step 5: Assemble Context
    │
    ▼ "[1] (playbook) Mortgage Buyer Playbook: Step 1: Confirm pre-qualification..."
    │
Step 6: Generate Response with Playbook
```

## Vector Database Schema

| Collection | Documents | Description |
|------------|-----------|-------------|
| `qualification_criteria` | 4 | BANT, CHAMP, MEDDIC, Tiering |
| `sales_playbooks` | 4 | Inbound, outbound, referral, digital |
| `lead_scoring_models` | 3 | Demographic, behavioral, firmographic |
| `conversion_patterns` | 3 | High-intent, nurture, referral patterns |
| `product_eligibility` | 6 | Requirements by product |
| `compliance_rules` | 4 | TCPA, DNC, consent, fair lending |
| `competitor_intelligence` | 3 | Chase, BofA, online banks |

## Lead Scoring Model

```
                    ┌──────────────────────────────┐
                    │      LEAD SCORE (0-100)       │
                    └──────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  DEMOGRAPHIC  │          │  BEHAVIORAL   │          │    INTENT     │
│  (35%)        │          │  (35%)        │          │    (30%)      │
│               │          │               │          │               │
│ • Age         │          │ • Pages Viewed│          │ • Source      │
│ • Income      │          │ • Calculator  │          │ • Product     │
│ • Credit      │          │ • Application │          │ • Urgency     │
│ • Homeowner   │          │ • Engagement  │          │ • Competitor  │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │   COMBINED SCORE → TIER       │
                    └──────────────────────────────┘
```

## Routing Decision Matrix

| Score | Tier | Routing | SLA | Follow-up |
|-------|------|---------|-----|-----------|
| 80-100 | Hot | Senior Advisor | 1 hour | Phone + Email |
| 60-79 | Warm | Sales Team | 24 hours | Email + SMS |
| 40-59 | Cool | Nurture Campaign | 7 days | Drip sequence |
| 0-39 | Cold | Database | 30 days | Monthly newsletter |

## Compliance Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TCPA COMPLIANCE CHECKPOINTS                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DNC CHECK                                                   │
│     • Check National DNC Registry before calling                │
│     • Check state DNC lists                                      │
│     • Maintain internal DNC list                                 │
│                                                                 │
│  2. TIME RESTRICTIONS                                            │
│     • Calls allowed 8am-9pm lead's local time                   │
│     • No calls on Sundays (varies by state)                     │
│                                                                 │
│  3. CONSENT                                                     │
│     • Record verbal consent with timestamp                      │
│     • Keep signed/digital consent forms                          │
│     • Online checkboxes must be un-checked by default           │
│                                                                 │
│  4. DISCLOSURE                                                  │
│     • Identify yourself and bank at start of call               │
│     • Provide opt-out mechanism                                  │
│     • State purpose of call                                     │
│                                                                 │
│  5. FAIR LENDING                                                 │
│     • Same qualification criteria for all leads                 │
│     • No steering to higher-cost products                       │
│     • Document all qualification decisions                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Three scoring models** | Demographic, behavioral, intent capture different signals |
| **7 RAG collections** | Separate concerns for better retrieval |
| **BANT/CHAMP/MEDDIC** | Industry-standard frameworks for qualification |
| **4-tier routing** | Match response effort to lead quality |
| **Speed to lead < 5 min** | 5x higher conversion with fast response |
| **Playbook-driven** | Consistent, repeatable qualification process |
| **TCPA guardrails** | Legal compliance for all outreach |
| **CRM integration** | Full audit trail and conversion tracking |
| **Conversation analysis** | Real-time intent detection during live chats |
| **Referral weighting** | Referred leads convert 3x higher |
