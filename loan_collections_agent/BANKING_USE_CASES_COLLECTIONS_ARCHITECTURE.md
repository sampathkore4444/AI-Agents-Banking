# Loan Collections Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Loan Collections Agent that uses **RAG** for regulatory knowledge retrieval and **MCP** for tool orchestration across account management, collection strategies, payment scheduling, settlement negotiation, compliance checking, debtor profile embedding, and FDCPA-compliant communications.
>
> **Covers all 3.3 Loan Collections Agent capabilities.**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LOAN COLLECTIONS AGENT                                │
│                                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────────────────────────┐  │
│  │           │    │              │    │       MCP Tool Server            │  │
│  │  Collector │───▶│   LLM Core   │◀──▶│  ┌──────────┐ ┌───────────┐   │  │
│  │   Chat     │    │  (GPT-4o /   │    │  │ Account  │ │ Strategy  │   │  │
│  │  Interface │◀───│  Claude /    │    │  │ Mgmt     │ │ Recommend │   │  │
│  │           │    │  Gemini)     │    │  └──────────┘ └───────────┘   │  │
│  └───────────┘    └──────┬───────┘    │  ┌──────────┐ ┌───────────┐   │  │
│                          │             │  │ Payment  │ │ Compliance│   │  │
│                          │             │  │ Scheduling│ │ Checker   │   │  │
│                          ▼             │  └──────────┘ └───────────┘   │  │
│                   ┌──────────────┐     │  ┌──────────┐ ┌───────────┐   │  │
│                   │              │     │  │ Debtor   │ │ Settlement│   │  │
│                   │   RAG Engine │     │  │ Embedding│ │ Offers    │   │  │
│                   │              │     │  └──────────┘ └───────────┘   │  │
│                   │  ┌────────┐  │     │  ┌──────────┐ ┌───────────┐   │  │
│                   │  │Query   │  │     │  │ Notify   │ │ Payment   │   │  │
│                   │  │Rewrite │  │     │  │ Borrower │ │ Gateway   │   │  │
│                   │  └───┬────┘  │     │  └──────────┘ └───────────┘   │  │
│                   │      │       │     │  ┌──────────┐                 │  │
│                   │      ▼       │     │  │ Audit    │                 │  │
│                   │  ┌────────┐  │     │  │ Logging  │                 │  │
│                   │  │Hybrid  │  │     │  └──────────┘                 │  │
│                   │  │Search  │  │     └──────────────────────────────────┘  │
│                   │  │(BM25 + │  │                                          │
│                   │  │Semantic)│  │     ┌──────────────────────────────────┐  │
│                   │  └───┬────┘  │     │       External APIs              │  │
│                   │      │       │     │  ┌──────────┐ ┌───────────┐    │  │
│                   │      ▼       │     │  │ Core     │ │ Payment   │    │  │
│                   │  ┌────────┐  │     │  │ Banking  │ │ Gateway   │    │  │
│                   │  │Re-rank │  │     │  │ System   │ │ (ACH,Card)│    │  │
│                   │  └───┬────┘  │     │  └──────────┘ └───────────┘    │  │
│                   │      │       │     │  ┌──────────┐ ┌───────────┐    │  │
│                   └──────┼───────┘     │  │ SMS/Email│ │ Credit    │    │  │
│                          │             │  │ Service  │ │ Bureau    │    │  │
│                          │             │  └──────────┘ └───────────┘    │  │
│                          │             │  ┌──────────┐ ┌───────────┐    │  │
│                          │             │  │ Skip     │ │ Legal     │    │  │
│                          │             │  │ Tracing  │ │ System    │    │  │
│                          │             │  └──────────┘ └───────────┘    │  │
│                          │             └──────────────────────────────────┘  │
│                          │                                                  │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     Vector Database     │
              │                        │
              │  ┌──────────────────┐  │
              │  │  FDCPA           │  │
              │  │  Regulations     │  │
              │  ├──────────────────┤  │
              │  │  Collection      │  │
              │  │  Strategies      │  │
              │  ├──────────────────┤  │
              │  │  Negotiation     │  │
              │  │  Frameworks      │  │
              │  ├──────────────────┤  │
              │  │  Compliance      │  │
              │  │  Guidelines      │  │
              │  ├──────────────────┤  │
              │  │  Past Resolution │  │
              │  │  Cases           │  │
              │  ├──────────────────┤  │
              │  │  Hardship        │  │
              │  │  Programs        │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

---

## Detailed Component Flow

### The Collections Journey — Step by Step

```
COLLECTOR                  AGENT (LLM + RAG + MCP)              EXTERNAL SYSTEMS
──────────                  ────────────────────────              ─────────────────

  │                              │                                    │
  │  1. "My borrower Sarah       │                                    │
  │      Johnson is 45 days      │                                    │
  │      past due on her         │                                    │
  │      mortgage"               │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  2. Intent: COMPLEX                │
  │                              │     RAG: Retrieve FDCPA            │
  │                              │     mortgage delinquency rules     │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → FDCPA communication rules   │
  │                              │     → Mortgage-specific loss       │
  │                              │       mitigation requirements     │
  │                              │     → Early-stage strategies      │
  │                              │                                    │
  │  3. "Let me look up her      │                                    │
  │      account details..."     │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │                              │  4. MCP: Look up account           │
  │                              │──────┐                             │
  │                              │      │  GET /accounts/ACCT-10001   │
  │                              │◀─────┘                             │
  │                              │     → Balance: $185,000            │
  │                              │     → Days past due: 45           │
  │                              │     → Stage: mid_stage             │
  │                              │     → Collateral: $320,000         │
  │                              │                                    │
  │  5. "Based on her profile,   │                                    │
  │      here's what I           │                                    │
  │      recommend..."           │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │                              │  6. MCP: Recommend strategy        │
  │                              │──────┐                             │
  │                              │      │  POST /strategy/recommend  │
  │                              │◀─────┘                             │
  │                              │     → Stage: Mid-Stage (31-90)    │
  │                              │     → Primary: Hardship assessment │
  │                              │     → Actions: Weekly outreach,    │
  │                              │       evaluate forbearance         │
  │                              │     → Recovery probability: 70%   │
  │                              │                                    │
  │                              │  7. MCP: Check forbearance         │
  │                              │     eligibility                    │
  │                              │──────┐                             │
  │                              │      │  GET /eligibility/forbear. │
  │                              │◀─────┘                             │
  │                              │     → Eligible: YES               │
  │                              │     → Conditions: Hardship docs,  │
  │                              │       3-month trial payment       │
  │                              │                                    │
  │                              │  8. MCP: Embed debtor profile      │
  │                              │──────┐                             │
  │                              │      │  POST /embed/profile       │
  │                              │◀─────┘                             │
  │                              │     → Cluster: moderate_risk      │
  │                              │     → Default prob: 0.32          │
  │                              │     → Similar cases: 3 matches    │
  │                              │                                    │
  │                              │  9. MCP: Check compliance          │
  │                              │     (phone contact)                │
  │                              │──────┐                             │
  │                              │      │  POST /compliance/check    │
  │                              │◀─────┘                             │
  │                              │     → Compliant: YES              │
  │                              │     → Hour: 10:00 AM (OK)        │
  │                              │     → Daily attempts: 1/3         │
  │                              │                                    │
  │  10. "I'll reach out to      │                                    │
  │      Sarah. Let me send      │                                    │
  │      her a hardship          │                                    │
  │      inquiry email..."       │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │                              │  11. MCP: Send hardship inquiry    │
  │                              │──────┐                             │
  │                              │      │  POST /notifications/send  │
  │                              │      │  (FDCPA-compliant)         │
  │                              │◀─────┘                             │
  │                              │                                    │
  │                              │  12. MCP: Log collection action    │
  │                              │──────┐                             │
  │                              │      │  POST /actions/log         │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  13. "Sarah called back —    │                                    │
  │      she lost her job.       │                                    │
  │      Let's set up a          │                                    │
  │      forbearance plan..."    │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  14. MCP: Create payment plan      │
  │                              │     (interest-only, 6 months)      │
  │                              │──────┐                             │
  │                              │      │  POST /plans/create        │
  │                              │◀─────┘                             │
  │                              │     → Plan ID: PP-A1B2C3D4        │
  │                              │     → $950/month (interest-only)  │
  │                              │     → 6 months duration           │
  │                              │                                    │
  │                              │  15. MCP: Send forbearance         │
  │                              │     approval notice                │
  │                              │──────┐                             │
  │                              │      │  POST /notifications/send  │
  │                              │◀─────┘                             │
  │                              │                                    │
  │                              │  16. MCP: Update account           │
  │                              │     (hardship_flag, plan_active)   │
  │                              │──────┐                             │
  │                              │      │  PUT /accounts/ACCT-10001  │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  17. "Done. Sarah is now     │                                    │
  │      on a 6-month interest-  │                                    │
  │      only forbearance plan   │                                    │
  │      at $950/month.          │                                    │
  │      Recovery probability:   │                                    │
  │      70%. Next review in     │                                    │
  │      90 days."               │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
```

---

## MCP Tool Definitions

```jsonc
// mcp-server-collections.json
{
  "mcpServers": {
    "loan-collections": {
      "description": "Loan Collections MCP Server — tools for account management, strategy recommendation, payment scheduling, compliance checking, debtor embedding, and FDCPA-compliant communications",
      "tools": [
        {
          "name": "get_account",
          "description": "Look up a delinquent account by ID with full delinquency details",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" }
            },
            "required": ["account_id"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" },
              "borrower_name": { "type": "string" },
              "product_type": { "type": "string" },
              "current_balance": { "type": "number" },
              "delinquency_days": { "type": "integer" },
              "collection_stage": { "type": "string" },
              "collateral": { "type": "object" },
              "hardship_flag": { "type": "boolean" }
            }
          }
        },
        {
          "name": "recommend_collection_strategy",
          "description": "Recommend optimal collection strategy based on debtor profile and past resolution patterns",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" },
              "borrower_name": { "type": "string" },
              "delinquency_days": { "type": "integer" },
              "product_type": { "type": "string", "enum": ["mortgage", "auto_loan", "personal_loan", "credit_card"] },
              "outstanding_balance": { "type": "number" },
              "monthly_payment": { "type": "number" },
              "has_collateral": { "type": "boolean" },
              "has_hardship": { "type": "boolean" },
              "previous_contact_outcome": { "type": "string" }
            },
            "required": ["account_id", "borrower_name", "delinquency_days", "product_type", "outstanding_balance", "monthly_payment", "has_collateral", "has_hardship"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "recommended_strategy": { "type": "object" },
              "strategy_score": { "type": "object" },
              "similar_resolution_cases": { "type": "array" },
              "escalation_needed": { "type": "boolean" }
            }
          }
        },
        {
          "name": "create_plan",
          "description": "Create a payment plan (standard, graduated, hardship, settlement)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" },
              "plan_type": { "type": "string", "enum": ["standard", "graduated", "interest_only", "hardship", "settlement"] },
              "monthly_amount": { "type": "number" },
              "total_months": { "type": "integer" },
              "start_date": { "type": "string" },
              "interest_rate": { "type": "number" }
            },
            "required": ["account_id", "plan_type", "monthly_amount", "total_months"]
          }
        },
        {
          "name": "offer_settlement",
          "description": "Create a settlement offer with discount percentage and payment terms",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" },
              "settlement_amount": { "type": "number" },
              "settlement_percentage": { "type": "number" },
              "payment_terms": { "type": "string" },
              "deadline_days": { "type": "integer" }
            },
            "required": ["account_id", "settlement_amount", "settlement_percentage", "payment_terms"]
          }
        },
        {
          "name": "check_compliance",
          "description": "Validate a proposed contact action against FDCPA, TCPA, FCRA, and state laws",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" },
              "contact_method": { "type": "string", "enum": ["phone", "email", "sms", "mail", "automated_call"] },
              "contact_time": { "type": "string" },
              "borrower_state": { "type": "string" },
              "daily_attempts": { "type": "integer" },
              "weekly_attempts": { "type": "integer" },
              "cease_desist_received": { "type": "boolean" },
              "attorney_represented": { "type": "boolean" },
              "validation_notice_sent": { "type": "boolean" }
            },
            "required": ["account_id", "contact_method"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "compliant": { "type": "boolean" },
              "violations": { "type": "array" },
              "warnings": { "type": "array" },
              "recommendation": { "type": "string" }
            }
          }
        },
        {
          "name": "embed_profile",
          "description": "Create ML embedding of debtor profile for clustering and strategy matching",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" },
              "borrower_name": { "type": "string" },
              "delinquency_days": { "type": "integer" },
              "outstanding_balance": { "type": "number" },
              "monthly_payment": { "type": "number" },
              "annual_income": { "type": "number" },
              "debt_to_income": { "type": "number" },
              "has_collateral": { "type": "boolean" },
              "credit_score": { "type": "integer" },
              "previous_delinquencies": { "type": "integer" }
            },
            "required": ["account_id", "borrower_name", "delinquency_days", "outstanding_balance", "monthly_payment"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "risk_cluster": { "type": "object" },
              "default_probability": { "type": "number" },
              "similar_historical_profiles": { "type": "array" },
              "resolution_probabilities": { "type": "object" }
            }
          }
        },
        {
          "name": "notify_borrower",
          "description": "Send FDCPA-compliant notification via email, SMS, or mail",
          "inputSchema": {
            "type": "object",
            "properties": {
              "recipient_id": { "type": "string" },
              "template_id": { "type": "string", "enum": ["payment_reminder", "past_due_notice", "hardship_inquiry", "payment_plan_offer", "demand_letter", "settlement_offer", "forbearance_approved", "validation_notice", "payment_confirmation", "plan_confirmation"] },
              "channel": { "type": "string", "enum": ["email", "sms", "mail", "phone"] },
              "variables": { "type": "object" }
            },
            "required": ["recipient_id", "template_id"]
          }
        },
        {
          "name": "process_collections_payment",
          "description": "Process a payment for a delinquent account (regular, catch-up, settlement, partial)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_id": { "type": "string" },
              "amount": { "type": "number" },
              "payment_method": { "type": "string", "enum": ["card", "ach", "wire", "check", "cash"] },
              "payment_type": { "type": "string", "enum": ["regular", "catch_up", "settlement", "partial"] },
              "plan_id": { "type": "string" }
            },
            "required": ["account_id", "amount", "payment_method"]
          }
        }
      ]
    }
  }
}
```

---

## RAG Pipeline Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                             │
│                                                                 │
│  ┌─────────────┐                                                │
│  │  Collector   │  "What are the FDCPA rules for                │
│  │  Query       │   mortgage collections?"                      │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 1. QUERY    │  Rewrites for better retrieval:                │
│  │   REWRITE   │  "FDCPA mortgage delinquency communication     │
│  │             │   restrictions compliance rules"               │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                   │
│  │ 2. HYBRID SEARCH                         │                   │
│  │                                          │                   │
│  │  ┌────────────┐    ┌────────────────┐    │                   │
│  │  │  BM25      │    │  Semantic      │    │                   │
│  │  │  (Keyword) │    │  (Embedding)   │    │                   │
│  │  │            │    │                │    │                   │
│  │  │ "FDCPA"    │    │  Vector        │    │                   │
│  │  │ "mortgage" │    │  Similarity    │    │                   │
│  │  │ "compliance"│   │  Search        │    │                   │
│  │  └─────┬──────┘    └───────┬────────┘    │                   │
│  │        │                   │             │                   │
│  │        └───────┬───────────┘             │                   │
│  │                │                         │                   │
│  │                ▼                         │                   │
│  │        ┌──────────────┐                  │                   │
│  │        │   Reciprocal  │                 │                   │
│  │        │   Rank Fusion │                 │                   │
│  │        └───────┬──────┘                  │                   │
│  └────────────────┼─────────────────────────┘                   │
│                   │                                             │
│                   ▼                                             │
│          ┌────────────────┐                                     │
│  │ 3. RE-RANKING  │  Cross-encoder re-ranks top 20              │
│          │   (top-5)      │  → Best 5 chunks selected           │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│  │ 4. CONTEXT     │  Assembles retrieved chunks:                │
│          │   ASSEMBLY     │  - FDCPA communication rules        │
│          │                │  - Mortgage loss mitigation reqs    │
│          │                │  - Early-stage strategies           │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│  │ 5. ANSWER      │  LLM generates answer with                  │
│          │   GENERATION   │  citations and source references    │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│  │ 6. CITATION    │  Attach source document references          │
│          │   ATTACHMENT   │  for audit trail and compliance     │
│          └────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Vector Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR DB COLLECTIONS                        │
│                                                                 │
│  Collection: fdcpa_regulations                                  │
│  ─────────────────────────────                                  │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  fdcpa_001   │  "Fair Debt    │  [0.12,     │ {           │  │
│  │              │   Collection   │  -0.45,     │  "source":  │  │
│  │              │   Practices Act│   0.78,     │  "CFPB",    │  │
│  │              │   (15 U.S.C.   │   ...],     │  "section": │  │
│  │              │   § 1692)..."  │             │  "15 USC    │  │
│  │              │                │             │   1692"     │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: collection_strategies                              │
│  ────────────────────────────                                   │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  strat_001   │  "Early-Stage  │  [0.34,     │ {           │  │
│  │              │   Collections  │  -0.22,     │  "strategy":│  │
│  │              │   (1-30 days): │   0.91,     │  "early_    │  │
│  │              │   Focus on     │   ...],     │  "stage"    │  │
│  │              │   reminder..." │             │ }           │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: negotiation_frameworks                             │
│  ────────────────────────────                                   │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  neg_001     │  "Payment Plan │  [0.56,     │ {           │  │
│  │              │   Structuring: │   0.11,     │  "framework":│  │
│  │              │   Key          │   0.88,     │  "payment_  │  │
│  │              │   principles..."│  ...],     │  "plan"     │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: compliance_guidelines                              │
│  ────────────────────────────                                   │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  comp_001    │  "TCPA         │  [0.72,     │ {           │  │
│  │              │   Compliance   │  -0.33,     │  "source":  │  │
│  │              │   for          │   0.45,     │  "FCC",     │  │
│  │              │   Collections: │   ...],     │  "regulation│  │
│  │              │   Telephone..."│             │  : "TCPA"   │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: past_resolution_cases                              │
│  ────────────────────────────                                   │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  case_001    │  "Successful   │  [0.28,     │ {           │  │
│  │              │   Resolution   │  -0.67,     │  "resolution│  │
│  │              │   — Mortgage   │   0.54,     │  ": "forbear│  │
│  │              │   Delinquency  │   ...],     │  "ance",    │  │
│  │              │   (62 days)..."│             │  "outcome": │  │
│  │              │                │             │  "success"  │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: hardship_programs                                  │
│  ──────────────────────────                                     │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  hard_001    │  "Forbearance  │  [0.45,     │ {           │  │
│  │              │   Program:     │  -0.28,     │  "program": │  │
│  │              │   Definition:  │   0.67,     │  "forbear"  │  │
│  │              │   Temporary    │   ...],     │  "ance",    │  │
│  │              │   reduction..."│             │  "type":    │  │
│  │              │                │             │  "temp"     │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## FDCPA Compliance Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FDCPA COMPLIANCE ENGINE                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              PRE-CONTACT CHECKS                         │    │
│  │                                                         │    │
│  │  ✓ Contact hour check (8:00 AM - 9:00 PM)              │    │
│  │  ✓ Daily attempt limit (max 3/day)                      │    │
│  │  ✓ Weekly attempt limit (max 7/week)                    │    │
│  │  ✓ Cease & desist status                                │    │
│  │  ✓ Attorney representation status                       │    │
│  │  ✓ Validation notice sent?                              │    │
│  │  ✓ State-specific restrictions                          │    │
│  └─────────────────────┬───────────────────────────────────┘    │
│                        │                                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              CONTACT METHOD CHECKS                      │    │
│  │                                                         │    │
│  │  Phone:    Hours OK? Attempts OK? DNC status?           │    │
│  │  Email:    Consent documented? Opt-out honored?         │    │
│  │  SMS:      Prior express consent? TCPA compliant?       │    │
│  │  Mail:     No misleading envelope? Debt collector ID?   │    │
│  └─────────────────────┬───────────────────────────────────┘    │
│                        │                                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              REQUIRED DISCLOSURES                       │    │
│  │                                                         │    │
│  │  Initial Contact:                                      │    │
│  │  ├─ "This is an attempt to collect a debt"             │    │
│  │  ├─ Debt collector identification                       │    │
│  │  └─ Purpose of communication                           │    │
│  │                                                         │    │
│  │  Within 5 Days:                                        │    │
│  │  ├─ Amount of debt                                     │    │
│  │  ├─ Name of creditor                                   │    │
│  │  ├─ 30-day dispute rights                              │    │
│  │  └─ Verification rights                                │    │
│  │                                                         │    │
│  │  Settlement Offer:                                     │    │
│  │  ├─ Settlement amount and terms                         │    │
│  │  ├─ Tax implications (1099-C)                           │    │
│  │  └─ Release of liability language                       │    │
│  └─────────────────────┬───────────────────────────────────┘    │
│                        │                                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              AUDIT LOG                                  │    │
│  │                                                         │    │
│  │  Every action logged with:                              │    │
│  │  ├─ Account ID                                         │    │
│  │  ├─ Action type and details                             │    │
│  │  ├─ Collector ID                                       │    │
│  │  ├─ Compliance check result                             │    │
│  │  ├─ Timestamp                                          │    │
│  │  └─ Retention: 7 years                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
                    ┌───────────────────┐
                    │   Collector Input  │
                    │  "Borrower is      │
                    │   45 days late"    │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │    LLM Core       │
                    │  (Orchestration)  │
                    └────┬───────────┬──┘
                         │           │
            ┌────────────▼──┐   ┌───▼────────────┐
            │   RAG Engine  │   │  MCP Tool Server│
            │               │   │                │
            │  ┌─────────┐  │   │  ┌───────────┐ │
            │  │ Vector  │  │   │  │ Account   │ │
            │  │ DB      │  │   │  │ Mgmt      │ │
            │  │         │  │   │  ├───────────┤ │
            │  │ → FDCPA │  │   │  │ Strategy  │ │
            │  │ → Strat.│  │   │  │ Recommend │ │
            │  │ → Negot.│  │   │  ├───────────┤ │
            │  │ → Compl.│  │   │  │ Payment   │ │
            │  │ → Cases │  │   │  │ Scheduling│ │
            │  │ → Hardsh│  │   │  ├───────────┤ │
            │  └─────────┘  │   │  │ Compliance│ │
            │               │   │  │ Checker   │ │
            └───────────────┘   │  ├───────────┤ │
                                │  │ Debtor    │ │
                                │  │ Embedding │ │
                                │  ├───────────┤ │
                                │  │ Notify    │ │
                                │  │ Borrower  │ │
                                │  ├───────────┤ │
                                │  │ Payment   │ │
                                │  │ Gateway   │ │
                                │  └───────────┘ │
                                └────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Collector Response  │
                    │  "Strategy: hardship │
                    │   forbearance,       │
                    │   $950/mo, 6 months" │
                    │  + Audit Trail       │
                    │  + Compliance Log    │
                    └─────────────────────┘
```

---

## Strategy Decision Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│               COLLECTIONS STRATEGY DECISION TREE                │
│                                                                 │
│  Delinquency Days                                               │
│  ├─ 1-30 (Early Stage)                                         │
│  │   ├─ Automated reminders (email/SMS)                         │
│  │   ├─ Personal call within 3 business days                    │
│  │   ├─ Offer self-service payment portal                       │
│  │   └─ Goal: Restore to current status                         │
│  │                                                              │
│  ├─ 31-90 (Mid Stage)                                          │
│  │   ├─ Weekly outreach (alternating channels)                  │
│  │   ├─ Evaluate hardship program eligibility                   │
│  │   ├─ Discuss deferment or modified payment plan              │
│  │   ├─ Begin credit reporting (after 30 days)                  │
│  │   └─ Goal: Establish payment arrangement                     │
│  │                                                              │
│  ├─ 91-180 (Late Stage)                                        │
│  │   ├─ Bi-weekly formal outreach                               │
│  │   ├─ Send formal demand letter (certified mail)              │
│  │   ├─ Evaluate settlement at 30-50% discount                  │
│  │   ├─ Assess collateral (secured loans)                       │
│  │   ├─ Skip tracing if contact lost                            │
│  │   ├─ Legal review for litigation                             │
│  │   └─ Goal: Recover maximum amount                             │
│  │                                                              │
│  └─ 180+ (Charge-Off / Recovery)                               │
│      ├─ Internal recovery (6-12 months)                         │
│      ├─ Third-party collection (25-50% commission)              │
│      ├─ Debt sale (5-20 cents on dollar)                        │
│      ├─ Litigation (if statute permits)                         │
│      └─ Goal: Maximize recovery from written-off debt           │
│                                                                 │
│  Product-Specific Adjustments:                                  │
│  ├─ Mortgage: Reg X loss mitigation required, dual tracking     │
│  ├─ Auto Loan: Assess vehicle value, repossession vs. workout   │
│  ├─ Personal Loan: Unsecured, settlement more viable            │
│  └─ Credit Card: Hardship programs, balance transfer options    │
│                                                                 │
│  Risk Score Modifiers:                                          │
│  ├─ + Collateral: Recovery probability +15%                     │
│  ├─ + Hardship claimed: Recovery probability +10%               │
│  ├─ + Previous delinquencies: Risk score +5 per occurrence      │
│  └─ + High DTI (>50%): Risk score +15                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Hybrid Search** | BM25 + Semantic | Keyword catches regulation numbers; semantic handles paraphrased collector queries |
| **Re-ranking** | Cross-encoder | Precision critical for compliance — wrong answer = FDCPA violation |
| **MCP over direct API** | MCP protocol | Standardized; swap notification providers, payment gateways without changing agent logic |
| **Strategy Recommendation** | Embedding-based matching | Matches debtor profiles against successful past resolutions for personalized approach |
| **Compliance Checking** | Pre-contact validation | Every contact action validated against FDCPA/TCPA/state laws BEFORE execution |
| **Audit Logging** | Every action logged | FDCPA requires documentation; 7-year retention for regulatory examination |
| **Hardship Assessment** | Structured framework | Consistent evaluation prevents UDAAP violations; documented decision process |
| **Settlement Authority** | Tiered (20/40/50/70%) | Clear escalation path; prevents unauthorized discounts; tracks approval chain |
| **Debtor Embedding** | 128-dim profile vector | Clusters debtors by recovery probability; matches to optimal strategy |
| **Human-in-Loop** | Risk-based (restructure_plan) | Payment plan modifications are high-risk; require supervisor approval |
| **Communication Templates** | FDCPA-compliant | Pre-approved language prevents violations; consistent messaging |
| **State Law Awareness** | State-specific checks | Rosenthal Act (CA), NY licensing, statute of limitations vary by state |

---

*Architecture designed for Loan Collections Agent (3.3) — August 2026*
