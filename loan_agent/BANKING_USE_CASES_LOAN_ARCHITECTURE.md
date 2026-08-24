# Loan Application Processing Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Loan Application Processing Agent that uses **RAG** for regulatory knowledge retrieval and **MCP** for tool orchestration across credit checking, income verification, document processing, underwriting, **bank statement analysis**, **alternative credit data**, **ML customer embedding**, and **decision explainability**.
>
> **Covers both 3.1 Loan Application Processing AND 3.2 Credit Scoring & Risk Assessment.**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOAN APPLICATION PROCESSING AGENT                        │
│                                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │           │    │              │    │       MCP Tool Server            │   │
│  │  Customer  │───▶│   LLM Core   │◀──▶│  ┌──────────┐ ┌───────────┐   │   │
│  │   Chat     │    │  (GPT-4o /   │    │  │ Credit   │ │ Income    │   │   │
│  │  Interface │◀───│  Claude /    │    │  │ Bureau   │ │ Verify    │   │   │
│  │           │    │  Gemini)     │    │  └──────────┘ └───────────┘   │   │
│  └───────────┘    └──────┬───────┘    │  ┌──────────┐ ┌───────────┐   │   │
│                          │             │  │ Document │ │ App Mgmt  │   │   │
│                          │             │  │ OCR      │ │ & Risk    │   │   │
│                          ▼             │  └──────────┘ └───────────┘   │   │
│                   ┌──────────────┐     │  ┌──────────┐ ┌───────────┐   │   │
│                   │              │     │  │ Bank Stmt│ │ Alt Data  │   │   │
│                   │   RAG Engine │     │  │ Analysis │ │ (Rent,    │   │   │
│                   │              │     │  └──────────┘ │ Utilities)│   │   │
│                   │  ┌────────┐  │     │  ┌──────────┐ └───────────┘   │   │
│                   │  │Query   │  │     │  │ ML       │ ┌───────────┐   │   │
│                   │  │Rewrite │  │     │  │ Embed    │ │ Explain   │   │   │
│                   │  └───┬────┘  │     │  │ Profile  │ │ Decision  │   │   │
│                   │      │       │     │  └──────────┘ └───────────┘   │   │
│                   │      ▼       │     │  ┌──────────┐                 │   │
│                   │  ┌────────┐  │     │  │ Notify   │                 │   │
│                   │  │Hybrid  │  │     │  │ Customer │                 │   │
│                   │  │Search  │  │     │  └──────────┘                 │   │
│                   │  │(BM25 + │  │     └──────────────────────────────────┘   │
│                   │  │Semantic)│  │                                          │
│                   │  └───┬────┘  │     ┌──────────────────────────────────┐   │
│                   │      │       │     │       External APIs              │   │
│                   │      ▼       │     │  ┌──────────┐ ┌───────────┐    │   │
│                   │  ┌────────┐  │     │  │ Experian │ │ IRS TTO   │    │   │
│                   │  │Re-rank │  │     │  │ Equifax  │ │ (Tax      │    │   │
│                   │  └───┬────┘  │     │  │ TransUn. │ │ Transcrpt)│    │   │
│                   │      │       │     │  └──────────┘ └───────────┘    │   │
│                   └──────┼───────┘     │  ┌──────────┐ ┌───────────┐    │   │
│                          │             │  │ Rent /   │ │ Plaid /   │    │   │
│                          │             │  │ Utility  │ │ Finicity  │    │   │
│                          │             │  │ Payment  │ │ (Alt Data)│    │   │
│                          │             │  └──────────┘ └───────────┘    │   │
│                          │             │  ┌──────────┐ ┌───────────┐    │   │
│                          │             │  │ Loan     │ │ Payment   │    │   │
│                          │             │  │Originate │ │ Gateway   │    │   │
│                          │             │  │ System   │ │           │    │   │
│                          │             │  └──────────┘ └───────────┘    │   │
│                          │             └──────────────────────────────────┘   │
│                   │      │       │                                         │
│                   │      ▼       │     ┌───────────────────────────────┐    │
│                   │  ┌────────┐  │     │       External APIs           │    │
│                   │  │Hybrid  │  │     │  ┌─────────┐ ┌──────────┐    │    │
│                   │  │Search  │  │     │  │Experian │ │ IRS TTO  │    │    │
│                   │  │(BM25 + │  │     │  │Equifax  │ │ (Tax     │    │    │
│                   │  │Semantic)│  │     │  │TransUnion││ Transcrpt)│   │    │
│                   │  └───┬────┘  │     │  └─────────┘ └──────────┘    │    │
│                   │      │       │     │  ┌─────────┐ ┌──────────┐    │    │
│                   │      ▼       │     │  │Loan     │ │ Payment  │    │    │
│                   │  ┌────────┐  │     │  │Originate│ │ Gateway  │    │    │
│                   │  │Re-rank │  │     │  │System   │ │          │    │    │
│                   │  └───┬────┘  │     │  └─────────┘ └──────────┘    │    │
│                   │      │       │     └───────────────────────────────┘    │
│                   └──────┼───────┘                                         │
│                          │                                                 │
└──────────────────────────┼─────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     Vector Database     │
              │                        │
              │  ┌──────────────────┐  │
              │  │  Loan            │  │
              │  │  Regulations     │  │
              │  ├──────────────────┤  │
              │  │  Product         │  │
              │  │  Policies        │  │
              │  ├──────────────────┤  │
              │  │  Eligibility     │  │
              │  │  Criteria        │  │
              │  ├──────────────────┤  │
              │  │  Underwriting    │  │
              │  │  Guidelines      │  │
              │  ├──────────────────┤  │
              │  │  Past Loan       │  │
              │  │  Decisions       │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

---

## Detailed Component Flow

### The Loan Application Journey — Step by Step

```
CUSTOMER                  AGENT (LLM + RAG + MCP)              EXTERNAL SYSTEMS
────────                  ────────────────────────              ─────────────────

  │                              │                                    │
  │  1. "I want to apply for     │                                    │
  │      a $350,000 mortgage"    │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  2. Intent: COMPLEX                │
  │                              │     RAG: Retrieve mortgage         │
  │                              │     requirements                   │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → Conventional mortgage rules │
  │                              │     → Credit score requirements   │
  │                              │     → DTI guidelines              │
  │                              │                                    │
  │  3. "Let me create your      │                                    │
  │      application. I'll need  │                                    │
  │      your credit info..."    │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │  4. [Provides name, DOB,     │                                    │
  │      SSN last 4, address]    │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  5. MCP: Create application       │
  │                              │──────┐                             │
  │                              │      │  POST /applications/create │
  │                              │◀─────┘                             │
  │                              │     → App ID: LOAN-A1B2C3D4       │
  │                              │                                    │
  │                              │  6. MCP: Pull credit report       │
  │                              │──────┐                             │
  │                              │      │  POST /credit/report       │
  │                              │      │  (Experian API)            │
  │                              │◀─────┘                             │
  │                              │     → Score: 742                  │
  │                              │     → DTI: 31%                    │
  │                              │     → No derogatory marks         │
  │                              │                                    │
  │                              │  7. MCP: Verify income            │
  │                              │──────┐                             │
  │                              │      │  POST /income/verify       │
  │                              │      │  (Employer + Tax API)      │
  │                              │◀─────┘                             │
  │                              │     → Verified: $125,000/yr       │
  │                              │     → Confidence: 0.95            │
  │                              │                                    │
  │  8. "Please upload your      │                                    │
  │      paystubs and tax        │                                    │
  │      returns"                │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │  9. [Uploads documents]      │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  10. MCP: Verify paystub          │
  │                              │──────┐                             │
  │                              │      │  POST /documents/verify    │
  │                              │◀─────┘                             │
  │                              │     → Gross: $10,416/mo           │
  │                              │     → No anomalies                │
  │                              │                                    │
  │                              │  11. MCP: Verify tax return       │
  │                              │──────┐                             │
  │                              │      │  POST /documents/verify    │
  │                              │◀─────┘                             │
  │                              │     → AGI: $125,000               │
  │                              │     → Matches claimed income      │
  │                              │                                    │
  │                              │  12. MCP: Calculate affordability │
  │                              │──────┐                             │
  │                              │      │  Local calculation         │
  │                              │◀─────┘                             │
  │                              │     → Monthly payment: $2,156     │
  │                              │     → Front-end ratio: 18.4%     │
  │                              │     → Back-end ratio: 31.0%      │
  │                              │     → Passes DTI check: YES      │
  │                              │                                    │
  │                              │  13. MCP: Assess risk             │
  │                              │──────┐                             │
  │                              │      │  POST /risk/assess         │
  │                              │◀─────┘                             │
  │                              │     → Risk score: 15/100          │
  │                              │     → Risk level: LOW             │
  │                              │     → Decision: AUTO_APPROVE      │
  │                              │     → Rate: 6.25%                 │
  │                              │                                    │
  │                              │  14. MCP: Update application      │
  │                              │     status to "approved"          │
  │                              │──────┐                             │
  │                              │      │  PUT /applications/{id}    │
  │                              │◀─────┘                             │
  │                              │                                    │
  │                              │  15. MCP: Send approval email     │
  │                              │──────┐                             │
  │                              │      │  POST /notifications/send  │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  16. "Congratulations!       │                                    │
  │      Your mortgage is        │                                    │
  │      approved for $350,000   │                                    │
  │      at 6.25% APR.           │                                    │
  │      Monthly payment:        │                                    │
  │      $2,156"                 │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
```

---

## MCP Tool Definitions

```jsonc
// mcp-server-loan.json
{
  "mcpServers": {
    "loan-application": {
      "description": "Loan Application Processing MCP Server — tools for credit checking, income verification, document processing, underwriting, bank statement analysis, alternative data, ML embedding, and decision explainability",
      "tools": [
        {
          "name": "create_application",
          "description": "Create a new loan application with customer and loan details",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_id": { "type": "string" },
              "loan_type": { "type": "string", "enum": ["conventional", "fha", "va", "auto", "personal"] },
              "loan_amount": { "type": "number" },
              "purpose": { "type": "string" },
              "term_months": { "type": "integer" },
              "property_address": { "type": "object" }
            },
            "required": ["customer_id", "loan_type", "loan_amount", "purpose", "term_months"]
          }
        },
        {
          "name": "check_credit",
          "description": "Pull credit report from bureau (Experian, Equifax, TransUnion)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_name": { "type": "string" },
              "date_of_birth": { "type": "string" },
              "ssn_last_four": { "type": "string" },
              "address": { "type": "object" }
            },
            "required": ["customer_name", "date_of_birth", "ssn_last_four"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "credit_score": { "type": "integer" },
              "credit_grade": { "type": "string" },
              "payment_history": { "type": "string" },
              "credit_utilization": { "type": "number" },
              "total_debt": { "type": "number" },
              "derogatory_marks": { "type": "integer" }
            }
          }
        },
        {
          "name": "verify_income",
          "description": "Verify customer income through employer verification, tax transcripts, or bank statements",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_id": { "type": "string" },
              "annual_income_claimed": { "type": "number" },
              "employment_type": { "type": "string", "enum": ["employed", "self_employed", "retired", "other"] },
              "employer_name": { "type": "string" },
              "tax_year": { "type": "integer" }
            },
            "required": ["customer_id", "annual_income_claimed"]
          }
        },
        {
          "name": "verify_document",
          "description": "Extract and verify data from loan documents (payslips, tax returns, bank statements)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_url": { "type": "string" },
              "document_type": { "type": "string", "enum": ["payslip", "bank_statement", "tax_return", "employment_letter", "id_document", "proof_of_address"] },
              "expected_values": { "type": "object" }
            },
            "required": ["document_url", "document_type"]
          }
        },
        {
          "name": "calculate_affordability",
          "description": "Calculate loan affordability (DTI ratios, monthly payment, total cost)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "annual_income": { "type": "number" },
              "monthly_debts": { "type": "number" },
              "loan_amount": { "type": "number" },
              "interest_rate": { "type": "number" },
              "term_months": { "type": "integer" }
            },
            "required": ["annual_income", "monthly_debts", "loan_amount", "interest_rate", "term_months"]
          }
        },
        {
          "name": "assess_risk",
          "description": "Assess loan risk and recommend underwriting decision (approve/decline/manual review)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "credit_score": { "type": "integer" },
              "annual_income": { "type": "number" },
              "loan_amount": { "type": "number" },
              "loan_to_value": { "type": "number" },
              "debt_to_income": { "type": "number" },
              "employment_type": { "type": "string" },
              "loan_type": { "type": "string" }
            },
            "required": ["credit_score", "annual_income", "loan_amount", "loan_to_value", "debt_to_income"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "risk_score": { "type": "integer" },
              "risk_level": { "type": "string", "enum": ["low", "medium", "elevated", "high"] },
              "decision": { "type": "string", "enum": ["auto_approve", "approve_with_conditions", "manual_underwriting_required", "decline"] },
              "suggested_rate": { "type": "number" },
              "conditions": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        {
          "name": "update_application",
          "description": "Update loan application status, documents, or decisions",
          "inputSchema": {
            "type": "object",
            "properties": {
              "application_id": { "type": "string" },
              "status": { "type": "string", "enum": ["submitted", "document_collection", "under_review", "approved", "declined", "closing"] },
              "documents_received": { "type": "array", "items": { "type": "string" } },
              "underwriting_decision": { "type": "string" },
              "notes": { "type": "string" }
            },
            "required": ["application_id"]
          }
        },
        {
          "name": "notify_customer",
          "description": "Send application status notification to customer",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_id": { "type": "string" },
              "template_id": { "type": "string", "enum": ["application_received", "documents_needed", "application_approved", "application_declined", "application_under_review"] },
              "channel": { "type": "string", "enum": ["email", "sms", "in_app"] },
              "variables": { "type": "object" }
            },
            "required": ["customer_id", "template_id"]
          }
        }
      ]
    }
  }
}
```

### NEW Tools (3.2 Credit Scoring & Risk Assessment)

```jsonc
// Additional tools for 3.2
{
  "name": "analyze_bank_statement",
  "description": "Deep analysis of bank statements: transaction categorization, spending patterns, irregularity detection",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "statement_url": { "type": "string" },
      "statement_months": { "type": "integer" }
    },
    "required": ["customer_id", "statement_url"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "income_analysis": { "type": "object" },
      "expense_analysis": { "type": "object" },
      "cash_flow": { "type": "object" },
      "irregularities": { "type": "array" },
      "creditworthiness_score": { "type": "integer" }
    }
  }
}

{
  "name": "check_alternative_credit_data",
  "description": "Check alternative credit data (rent, utilities, phone, employment) for thin-file customers",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "data_types": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["customer_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "data": { "type": "object" },
      "alternative_credit_score": { "type": "number" },
      "sufficient_data": { "type": "boolean" }
    }
  }
}

{
  "name": "embed_profile",
  "description": "Create ML embedding of customer financial profile for clustering and risk prediction",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "credit_score": { "type": "integer" },
      "annual_income": { "type": "number" },
      "debt_to_income": { "type": "number" },
      "loan_to_value": { "type": "number" },
      "employment_years": { "type": "integer" },
      "credit_history_years": { "type": "integer" }
    },
    "required": ["customer_id", "credit_score", "annual_income", "debt_to_income", "loan_to_value"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "profile_embedding": { "type": "array" },
      "cluster": { "type": "string" },
      "default_probability": { "type": "number" },
      "similar_historical_profiles": { "type": "array" }
    }
  }
}

{
  "name": "explain_loan_decision",
  "description": "Generate ECOA-compliant decision explanation with adverse action reasons",
  "inputSchema": {
    "type": "object",
    "properties": {
      "application_id": { "type": "string" },
      "decision": { "type": "string" },
      "credit_score": { "type": "integer" },
      "dti_ratio": { "type": "number" },
      "ltv_ratio": { "type": "number" },
      "risk_factors": { "type": "array", "items": { "type": "string" } },
      "income_verified": { "type": "boolean" },
      "employment_type": { "type": "string" }
    },
    "required": ["application_id", "decision", "credit_score", "dti_ratio", "ltv_ratio"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "explanation": { "type": "string" },
      "factor_details": { "type": "array" },
      "adverse_action_reasons": { "type": "array" },
      "improvement_steps": { "type": "array" },
      "ecoa_notice": { "type": "string" }
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
│  │  User Query  │  "What's the minimum credit score for         │
│  │              │   an FHA mortgage?"                           │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 1. QUERY    │  Rewrites for better retrieval:                │
│  │   REWRITE   │  "FHA mortgage minimum credit score            │
│  │             │   eligibility requirements"                    │
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
│  │  │ "FHA"      │    │  Vector        │    │                   │
│  │  │ "mortgage" │    │  Similarity    │    │                   │
│  │  │ "credit    │    │  Search        │    │                   │
│  │  │  score"    │    │  (top-k=20)    │    │                   │
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
│          │   ASSEMBLY     │  - FHA policy excerpt               │
│          │                │  - Credit score tiers               │
│          │                │  - Eligibility criteria             │
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
│  Collection: loan_regulations                                   │
│  ─────────────────────────────                                  │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  reg_tila_001│  "The Truth in │  [0.12,     │ {           │  │
│  │              │   Lending Act  │  -0.45,     │  "source":  │  │
│  │              │   requires..." │   0.78,     │  "CFPB",    │  │
│  │              │                │   ...],     │  "section": │  │
│  │              │                │             │  "TILA"     │  │
│  │              │                │             │ }           │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: product_policies                                   │
│  ──────────────────────────                                     │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  pol_fha_001 │  "FHA Mortgage │  [0.34,     │ {           │  │
│  │              │   Requirements:│  -0.22,     │  "product": │  │
│  │              │   1. Minimum   │   0.91,     │  "fha"      │  │
│  │              │   credit score:│   ...],     │  "version": │  │
│  │              │   500..."      │             │  "2024-Q3"  │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: eligibility_criteria                               │
│  ──────────────────────────                                     │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  elig_001    │  "Credit Score │  [0.56,     │ {           │  │
│  │              │   Tiers:       │   0.11,     │  "topic":   │  │
│  │              │   Tier 1 (750+)│   0.88,     │  "credit_   │  │
│  │              │   Best rates..."│  ...],     │  "tiers"    │  │
│  │              │                │             │ }           │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: underwriting_guidelines                            │
│  ───────────────────────────────                                │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  uw_dti_001  │  "Debt-to-Income│ [0.72,     │ {           │  │
│  │              │   Ratio:       │  -0.33,     │  "topic":   │  │
│  │              │   Front-end    │   0.45,     │  "dti"      │  │
│  │              │   maximum 28%..."│  ...],    │ }           │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: past_loan_decisions                                │
│  ───────────────────────────                                    │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  case_appr_1 │  "Approved:    │ [0.28,      │ {           │  │
│  │              │   Conventional │  -0.67,     │  "decision":│  │
│  │              │   mortgage,    │   0.54,     │  "approved" │  │
│  │              │   credit 742..."│  ...],     │  "risk":    │  │
│  │              │                │             │  "low"      │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: fair_lending_guidelines ← NEW (3.2)                │
│  ────────────────────────────────────                           │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  fair_lend_1 │  "ECOA Adverse │ [0.45,      │ {           │  │
│  │              │   Action Notice│  -0.28,     │  "source":  │  │
│  │              │   Requirements:│   0.67,     │  "CFPB",    │  │
│  │              │   When denying..."│ ...],    │  "type":    │  │
│  │              │                │             │  "adverse"  │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
│                                                                 │
│  Collection: credit_scoring_models ← NEW (3.2)                 │
│  ──────────────────────────────────                             │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐  │
│  │  id          │  text_chunk    │  embedding  │  metadata   │  │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤  │
│  │  fico_001    │  "FICO Score   │ [0.62,      │ {           │  │
│  │              │   Components:  │  -0.15,     │  "source":  │  │
│  │              │   Payment      │   0.83,     │  "FICO",    │  │
│  │              │   History 35%..."│  ...],    │  "model":   │  │
│  │              │                │             │  "FICO 8"   │  │
│  └──────────────┴────────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
                    ┌───────────────────┐
                    │   Customer Input   │
                    │  "Apply for        │
                    │   mortgage"        │
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
            │  │ Vector  │  │   │  │ Credit    │ │
            │  │ DB      │  │   │  │ Bureau    │ │
            │  │         │  │   │  ├───────────┤ │
            │  │ → Loan  │  │   │  │ Income    │ │
            │  │   Regs  │  │   │  │ Verify    │ │
            │  │ → Policies│ │  │  ├───────────┤ │
            │  │ → Eligib│  │   │  │ Document  │ │
            │  │ → Under │  │   │  │ Verify    │ │
            │  │   writing│ │  │  ├───────────┤ │
            │  │ → Past  │  │   │  │ App Mgmt  │ │
            │  │   Cases │  │   │  ├───────────┤ │
            │  └─────────┘  │   │  │ Risk      │ │
            │               │   │  │ Assess    │ │
            └───────────────┘   │  ├───────────┤ │
                                │  │ Notify    │ │
                                │  └───────────┘ │
                                └────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Customer Response   │
                    │  "Approved at 6.25%" │
                    │  + Audit Trail       │
                    │  + Compliance Log    │
                    └─────────────────────┘
```

---

## Risk Scoring Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISK SCORING BREAKDOWN                       │
│                                                                 │
│  Credit Score Factor (0-35 points):                             │
│  ├─ 750+: 5 points    (Excellent)                              │
│  ├─ 700-749: 10 points (Good)                                   │
│  ├─ 650-699: 20 points (Fair)                                   │
│  ├─ 600-649: 30 points (Below Average)                          │
│  └─ <600: 35 points   (Poor)                                    │
│                                                                 │
│  DTI Factor (0-25 points):                                      │
│  ├─ ≤28%: 0 points     (Ideal)                                 │
│  ├─ 29-36%: 10 points  (Moderate)                               │
│  ├─ 37-43%: 20 points  (High)                                   │
│  └─ >43%: 25 points    (Very High)                              │
│                                                                 │
│  LTV Factor (0-20 points):                                      │
│  ├─ ≤80%: 0 points     (Strong equity)                         │
│  ├─ 81-90%: 10 points  (Moderate)                               │
│  ├─ 91-95%: 15 points  (High)                                   │
│  └─ >95%: 20 points    (Very High)                              │
│                                                                 │
│  Employment Factor (0-10 points):                               │
│  ├─ Employed: 0 points                                          │
│  ├─ Self-employed: 5 points                                     │
│  └─ Other: 10 points                                            │
│                                                                 │
│  Loan Type Factor (0-10 points):                                │
│  ├─ Conventional: 0 points                                      │
│  ├─ FHA: 5 points                                               │
│  └─ Other: 10 points                                            │
│                                                                 │
│  DECISION THRESHOLDS:                                           │
│  ├─ 0-15: AUTO_APPROVE (Low Risk)                               │
│  ├─ 16-35: APPROVE_WITH_CONDITIONS (Medium Risk)               │
│  ├─ 36-55: MANUAL_UNDERWRITING_REQUIRED (Elevated Risk)        │
│  └─ 56+: DECLINE (High Risk)                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Hybrid Search** | BM25 + Semantic | Keyword search catches regulation numbers; semantic handles paraphrased queries |
| **Re-ranking** | Cross-encoder | Precision is critical for underwriting decisions |
| **MCP over direct API** | MCP protocol | Standardized; swap credit bureaus without changing agent logic |
| **Risk Scoring** | Rule-based (expandable to ML) | Transparent, auditable decisions required by regulators |
| **Human-in-Loop** | Risk-based | Only elevated/high risk cases require manual review |
| **Affordability Calc** | Local computation | Deterministic, auditable, no LLM hallucination risk |
| **Bank Statement Analysis** | Transaction categorization | Deep spending analysis catches irregularities missed by credit report |
| **Alternative Data** | Multi-source (rent, utilities, phone) | Enables credit scoring for thin-file customers (~50M Americans) |
| **ML Embedding** | 128-dim profile vector | Clusters customers by risk profile; predicts default probability |
| **Explainability** | ECOA-compliant | Regulatory requirement for adverse action notices; builds trust |
| **Fair Lending RAG** | Separate collection | Ensures agent retrieves current fair lending rules before decisions |
| **Audit Trail** | Every RAG + MCP call logged | Regulators require full traceability of credit decisions |

---

*Architecture designed for Loan Application Processing Agent (3.1 + 3.2 Credit Scoring & Risk Assessment) — August 2026*
