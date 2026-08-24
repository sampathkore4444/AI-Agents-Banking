# KYC Onboarding Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered KYC (Know Your Customer) Onboarding Agent that uses **RAG** for regulatory knowledge retrieval and **MCP** for tool orchestration across identity verification, screening, and account creation systems.

```
Created  BANKING_USE_CASES_KYC_ARCHITECTURE.md  — a complete RAG + MCP architecture for a KYC Onboarding Agent. Here's what's inside:

What the file covers:

1. High-Level Architecture Diagram — Shows how the LLM core, RAG engine, MCP tool server, vector DB, and external APIs all connect

2. Detailed Step-by-Step Flow — Walks through the full 18-step KYC journey showing exactly when RAG retrieves vs when MCP calls tools:
- RAG: retrieves KYC rules, document schemas, risk typologies, past case precedents
- MCP: calls Jumio/Onfido (identity), OFAC (sanctions), Core Banking (account creation), Compliance System (case management)

3. MCP Tool Definitions — Full JSON schemas for 7 tools:
-  extract_document ,  verify_identity ,  screen_sanctions 
-  create_customer_profile ,  create_compliance_case 
-  send_notification ,  query_core_banking 

4. RAG Pipeline Detail — 6-stage pipeline: 
      
      Query Rewrite → Hybrid Search (BM25 + Semantic) → Reciprocal Rank Fusion → Cross-encoder Re-ranking → Context Assembly → Citation Attachment

5. Vector DB Schema — 5 collections with sample data:
    -  kyc_regulations
    -  product_policies
    -  document_schemas
    -  risk_typologies
    -  past_kyc_decisions 

6. Key Design Decisions — Why hybrid search, why MCP, why human-in-the-loop, etc.
```

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KYC ONBOARDING AGENT                               │
│                                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌───────────────────────────────┐    │
│  │           │    │              │    │       MCP Tool Server         │    │
│  │  Customer  │───▶│   LLM Core   │◀──▶│  ┌─────────┐ ┌──────────┐  │    │
│  │   Chat     │    │  (GPT-4o /   │    │  │ Identity│ │Sanctions   │  │    │
│  │  Interface │◀───│  Claude /    │    │  │ Verify  │ │Screening   │  │    │
│  │           │    │  Gemini)     │    │  └────┬────┘ └────┬─────┘  │    │
│  └───────────┘    └──────┬───────┘    │       │           │        │    │
│                          │             │  ┌────▼────┐ ┌────▼─────┐  │    │
│                          │             │  │Document │ │ Account  │  │    │
│                          ▼             │  │  OCR &  │ │ Creation │  │    │
│                   ┌──────────────┐     │  │Classify │ │  API     │  │    │
│                   │              │     │  └────┬────┘ └──────────┘  │    │
│                   │   RAG Engine │     │       │                     │    │
│                   │              │     │  ┌────▼────┐                │    │
│                   │  ┌────────┐  │     │  │Payment  │                │    │
│                   │  │Query   │  │     │  │Gateway  │                │    │
│                   │  │Rewrite │  │     │  └─────────┘                │    │
│                   │  └───┬────┘  │     └───────────────────────────────┘    │
│                   │      │       │                                         │
│                   │      ▼       │                                         │
│                   │  ┌────────┐  │     ┌───────────────────────────────┐    │
│                   │  │Hybrid  │  │     │       External APIs           │    │
│                   │  │Search  │  │     │  ┌─────────┐ ┌──────────┐    │    │
│                   │  │(BM25 + │  │     │  │Jumio /  │ │ OFAC /   │    │    │
│                   │  │Semantic)│  │     │  │ Onfido  │ │ EU Sanct.│    │    │
│                   │  └───┬────┘  │     │  └─────────┘ └──────────┘    │    │
│                   │      │       │     │  ┌─────────┐ ┌──────────┐    │    │
│                   │      ▼       │     │  │ Core    │ │ Regula-  │    │    │
│                   │  ┌────────┐  │     │  │ Banking │ │ tory DB  │    │    │
│                   │  │Re-rank │  │     │  │ System  │ │          │    │    │
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
              │  │  KYC Regulations │  │
              │  │  & Compliance    │  │
              │  │  Rules           │  │
              │  ├──────────────────┤  │
              │  │  Product Policies│  │
              │  │  & Eligibility   │  │
              │  ├──────────────────┤  │
              │  │  Risk Typologies │  │
              │  │  & Red Flags     │  │
              │  ├──────────────────┤  │
              │  │  Document Schemas│  │
              │  │  & Validation    │  │
              │  ├──────────────────┤  │
              │  │  Past KYC Cases  │  │
              │  │  & Decisions     │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

---

## Detailed Component Flow

### The KYC Onboarding Journey — Step by Step

```
CUSTOMER                  AGENT (LLM + RAG + MCP)              EXTERNAL SYSTEMS
────────                  ────────────────────────              ─────────────────

  │                              │                                    │
  │  1. "I want to open          │                                    │
  │      a business account"     │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  2. RAG: Retrieve KYC requirements │
  │                              │     for "business account" +       │
  │                              │     customer jurisdiction          │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → KYC rules for business      │
  │                              │     → Required documents list     │
  │                              │     → Risk categories             │
  │                              │                                    │
  │  3. "Please upload your      │                                    │
  │      business registration,  │                                    │
  │      tax ID, and proof of    │                                    │
  │      address"                │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │  4. [Uploads documents]      │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  5. MCP: Extract & classify docs  │
  │                              │──────┐                             │
  │                              │      │  POST /ocr/extract         │
  │                              │      │  (Jumio/Onfido API)        │
  │                              │◀─────┘                             │
  │                              │     → Extracted fields            │
  │                              │                                    │
  │                              │  6. RAG: Validate extracted data  │
  │                              │     against document schemas      │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → Expected fields per doc type│
  │                              │     → Validation rules            │
  │                              │                                    │
  │                              │  7. MCP: Identity verification    │
  │                              │──────┐                             │
  │                              │      │  POST /verify/identity     │
  │                              │      │  (Jumio/Onfido API)        │
  │                              │◀─────┘                             │
  │                              │     → Liveness check: PASS        │
  │                              │     → Document authenticity: PASS │
  │                              │     → Face match: PASS            │
  │                              │                                    │
  │                              │  8. MCP: Sanctions screening      │
  │                              │──────┐  (parallel with step 7)    │
  │                              │      │  POST /screen/sanctions    │
  │                              │      │  (OFAC/EU list API)        │
  │                              │◀─────┘                             │
  │                              │     → OFAC: CLEAR                 │
  │                              │     → EU Sanctions: CLEAR         │
  │                              │     → PEP Check: NOT_PEP          │
  │                              │                                    │
  │                              │  9. MCP: Adverse media screening  │
  │                              │──────┐                             │
  │                              │      │  POST /search/adverse-media │
  │                              │◀─────┘                             │
  │                              │     → No adverse findings         │
  │                              │                                    │
  │                              │  10. RAG: Risk assessment         │
  │                              │      based on all collected data  │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │      → Risk scoring rules         │
  │                              │      → Similar past cases         │
  │                              │      → Risk level: MEDIUM         │
  │                              │                                    │
  │                              │  11. Risk = MEDIUM → Human review │
  │                              │      MCP: Create compliance case  │
  │                              │──────┐                             │
  │                              │      │  POST /cases/create        │
  │                              │      │  (Compliance system API)   │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  12. "Your application is    │                                    │
  │      under review. We'll     │                                    │
  │      notify you within       │                                    │
  │      24 hours."              │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  ════════════════════════════════ COMPLIANCE OFFICER REVIEW ═══════════════
  │                              │                                    │
  │                              │  13. MCP: Officer retrieves case   │
  │                              │──────┐                             │
  │                              │      │  GET /cases/{id}           │
  │                              │◀─────┘                             │
  │                              │                                    │
  │                              │  14. RAG: Retrieve compliance     │
  │                              │      playbook for this risk type  │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │                                    │
  │                              │  15. Officer APPROVES             │
  │                              │──────┐                             │
  │                              │      │  PUT /cases/{id}/approve   │
  │                              │◀─────┘                             │
  │                              │                                    │
  │                              │  16. MCP: Create bank account     │
  │                              │──────┐                             │
  │                              │      │  POST /accounts/create     │
  │                              │      │  (Core Banking API)        │
  │                              │◀─────┘                             │
  │                              │     → Account #1234567890         │
  │                              │                                    │
  │                              │  17. MCP: Send welcome email +    │
  │                              │      set up initial credentials   │
  │                              │──────┐                             │
  │                              │      │  POST /notifications/send  │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  18. "Your account is        │                                    │
  │      ready! Account #        │                                    │
  │      1234567890"             │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
```

---

## MCP Tool Definitions

```jsonc
// mcp-server-kyc.json
{
  "mcpServers": {
    "kyc-onboarding": {
      "description": "KYC Onboarding MCP Server — tools for identity verification, screening, document processing, and account creation",
      "tools": [
        {
          "name": "extract_document",
          "description": "Extract structured data from uploaded KYC documents (IDs, tax filings, bank statements, proof of address)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_url": { "type": "string", "description": "URL or file reference to the uploaded document" },
              "document_type": {
                "type": "string",
                "enum": ["passport", "drivers_license", "national_id", "tax_id", "proof_of_address", "bank_statement", "articles_of_incorporation"],
                "description": "Expected document type for targeted extraction"
              }
            },
            "required": ["document_url", "document_type"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "extracted_fields": { "type": "object", "description": "Key-value pairs of extracted data" },
              "confidence_score": { "type": "number", "minimum": 0, "maximum": 1 },
              "ocr_quality": { "type": "string", "enum": ["high", "medium", "low"] }
            }
          }
        },
        {
          "name": "verify_identity",
          "description": "Perform identity verification including liveness check, document authenticity, and face matching",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_id": { "type": "string" },
              "document_image_url": { "type": "string" },
              "selfie_url": { "type": "string" },
              "extracted_data": { "type": "object", "description": "Data from extract_document tool" }
            },
            "required": ["customer_id", "document_image_url", "selfie_url"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "liveness_check": { "type": "string", "enum": ["pass", "fail"] },
              "document_authenticity": { "type": "string", "enum": ["authentic", "suspected_fraud", "fail"] },
              "face_match": { "type": "number", "description": "Face match confidence 0-1" },
              "overall_result": { "type": "string", "enum": ["verified", "rejected", "manual_review"] }
            }
          }
        },
        {
          "name": "screen_sanctions",
          "description": "Screen customer against global sanctions lists (OFAC, EU, UN, HMT) and PEP databases",
          "inputSchema": {
            "type": "object",
            "properties": {
              "full_name": { "type": "string" },
              "date_of_birth": { "type": "string" },
              "nationality": { "type": "string" },
              "aliases": { "type": "array", "items": { "type": "string" } }
            },
            "required": ["full_name", "date_of_birth", "nationality"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "ofac_result": { "type": "string", "enum": ["clear", "hit", "potential_match"] },
              "eu_sanctions_result": { "type": "string", "enum": ["clear", "hit", "potential_match"] },
              "un_sanctions_result": { "type": "string", "enum": ["clear", "hit", "potential_match"] },
              "pep_status": { "type": "string", "enum": ["not_pep", "domestic_pep", "foreign_pep", " international_organization"] },
              "adverse_media": { "type": "boolean" },
              "risk_level": { "type": "string", "enum": ["low", "medium", "high", "critical"] }
            }
          }
        },
        {
          "name": "create_customer_profile",
          "description": "Create or update a customer profile in the core banking system after KYC completion",
          "inputSchema": {
            "type": "object",
            "properties": {
              "personal_info": { "type": "object" },
              "address": { "type": "object" },
              "employment_info": { "type": "object" },
              "kyc_result": { "type": "string", "enum": ["approved", "approved_with_conditions", "rejected"] },
              "risk_rating": { "type": "string", "enum": ["low", "medium", "high"] },
              "documents_verified": { "type": "array", "items": { "type": "string" } }
            },
            "required": ["personal_info", "address", "kyc_result", "risk_rating"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "customer_id": { "type": "string" },
              "account_number": { "type": "string" },
              "status": { "type": "string", "enum": ["active", "pending_review", "restricted"] }
            }
          }
        },
        {
          "name": "create_compliance_case",
          "description": "Create a compliance review case for manual review by a compliance officer",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_id": { "type": "string" },
              "risk_level": { "type": "string" },
              "flags": { "type": "array", "items": { "type": "string" } },
              "summary": { "type": "string" },
              "priority": { "type": "string", "enum": ["low", "medium", "high", "urgent"] }
            },
            "required": ["customer_id", "risk_level", "summary"]
          }
        },
        {
          "name": "send_notification",
          "description": "Send notification to customer (email, SMS, in-app) or internal staff",
          "inputSchema": {
            "type": "object",
            "properties": {
              "recipient_type": { "type": "string", "enum": ["customer", "compliance_officer", "relationship_manager"] },
              "recipient_id": { "type": "string" },
              "channel": { "type": "string", "enum": ["email", "sms", "in_app"] },
              "template_id": { "type": "string" },
              "variables": { "type": "object" }
            },
            "required": ["recipient_type", "recipient_id", "channel", "template_id"]
          }
        },
        {
          "name": "query_core_banking",
          "description": "Query core banking system for customer data, account status, or transaction history",
          "inputSchema": {
            "type": "object",
            "properties": {
              "query_type": { "type": "string", "enum": ["customer_lookup", "account_status", "transaction_history"] },
              "identifier": { "type": "string", "description": "Customer ID, account number, or national ID" },
              "filters": { "type": "object" }
            },
            "required": ["query_type", "identifier"]
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
│  │  User Query  │  "What documents do I need for a UK           │
│  │              │   limited company account?"                   │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 1. QUERY    │  Rewrites for better retrieval:                │
│  │   REWRITE   │  "UK limited company business account KYC      │
│  │             │   required documents eligibility"              │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                   │
│  │ 2. HYBRID SEARCH                         │                   │
│  │                                          │                   │
│  │  ┌────────────┐    ┌────────────────┐    │                   │
│  │  │  BM25       │    │  Semantic      │    │                   │
│  │  │  (Keyword)  │    │  (Embedding)   │    │                   │
│  │  │            │    │                │    │                   │
│  │  │ "UK"       │    │  Vector        │    │                   │
│  │  │ "limited   │    │  Similarity    │    │                   │
│  │  │  company"  │    │  Search        │    │                   │
│  │  │ "business  │    │  (top-k=20)    │    │                   │
│  │  │  account"  │    │                │    │                   │
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
│          │ 3. RE-RANKING  │  Cross-encoder re-ranks top 20     │
│          │   (top-5)      │  → Best 5 chunks selected           │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│          │ 4. CONTEXT     │  Assembles retrieved chunks:        │
│          │   ASSEMBLY     │  - KYC regulation section           │
│          │                │  - Product policy excerpt           │
│          │                │  - Eligibility criteria              │
│          │                │  - Required documents list          │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│          │ 5. ANSWER      │  LLM generates answer with          │
│          │   GENERATION   │  citations and source references    │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│          │ 6. CITATION    │  Attach source document references  │
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
│  Collection: kyc_regulations                                    │
│  ─────────────────────────────                                  │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  reg_001     │  "Under the    │  [0.12,     │ {           │ │
│  │              │   Money Laundering│ -0.45,   │   "source": │ │
│  │              │   Regulations  │   0.78,     │   "FCA",    │ │
│  │              │   2017 (MLR),  │   ...],     │   "section":│ │
│  │              │   Regulation 28│             │   "28",     │ │
│  │              │   requires..." │             │   "type":   │ │
│  │              │                │             │   "kyc_reg" │ │
│  │              │                │             │ }           │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: product_policies                                   │
│  ──────────────────────────                                     │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  pol_001     │  "Business     │  [0.34,     │ {           │ │
│  │              │   Current Account│ -0.22,   │   "product":│ │
│  │              │   eligibility: │   0.91,     │   "biz_acct"│ │
│  │              │   1. UK limited│   ...],     │   "region": │ │
│  │              │   company 2.   │             │   "UK",     │ │
│  │              │   Registered   │             │   "version":│ │
│  │              │   office in UK │             │   "2024-Q3" │ │
│  │              │   3. ..."      │             │ }           │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: document_schemas                                   │
│  ──────────────────────────                                     │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  doc_001     │  "Passport     │  [0.56,     │ {           │ │
│  │              │   verification │   0.11,     │   "doc_type":│ │
│  │              │   schema:      │   0.88,     │   "passport"│ │
│  │              │   required:    │   ...],     │   "fields": │ │
│  │              │   - full_name  │             │   ["name",  │ │
│  │              │   - dob        │             │    "dob",   │ │
│  │              │   - nationality│             │    "national│ │
│  │              │   - expiry     │             │     ity"]   │ │
│  │              │   - photo"     │             │ }           │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: risk_typologies                                    │
│  ──────────────────────────                                     │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  risk_001    │  "High-risk    │  [0.72,     │ {           │ │
│  │              │   indicators   │  -0.33,     │   "risk":   │ │
│  │              │   for business │   0.45,     │   "high",   │ │
│  │              │   accounts:    │   ...],     │   "category":│ │
│  │              │   - Complex    │             │   "business"│ │
│  │              │   ownership    │             │   "applies":│ │
│  │              │   structures   │             │   ["UK","EU"│ │
│  │              │   - High-risk  │             │   ]         │ │
│  │              │   jurisdiction │             │ }           │ │
│  │              │   - ..."       │             │             │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: past_kyc_decisions                                 │
│  ───────────────────────────                                    │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  case_001    │  "Business     │  [0.28,     │ {           │ │
│  │              │   application  │  -0.67,     │   "decision":│ │
│  │              │   for UK Ltd,  │   0.54,     │   "approved"│ │
│  │              │   fintech      │   ...],     │   "risk":   │ │
│  │              │   sector,      │             │   "medium", │ │
│  │              │   beneficial   │             │   "sector": │ │
│  │              │   ownership    │             │   "fintech" │ │
│  │              │   disclosed..."│             │ }           │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
                    ┌───────────────────┐
                    │   Customer Input   │
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
            │  │ Vector  │  │   │  │ Jumio API │ │
            │  │ DB      │  │   │  ├───────────┤ │
            │  │         │  │   │  │ OFAC API  │ │
            │  │ → KYC   │  │   │  ├───────────┤ │
            │  │   Regs  │  │   │  │ Core      │ │
            │  │ → Policies│ │   │  │ Banking   │ │
            │  │ → Risk  │  │   │  ├───────────┤ │
            │  │   Rules │  │   │  │ Compliance│ │
            │  │ → Docs  │  │   │  │ System    │ │
            │  │   Schema│  │   │  ├───────────┤ │
            │  │ → Past  │  │   │  │Notificatn │ │
            │  │   Cases │  │   │  │ Service   │ │
            │  └─────────┘  │   │  └───────────┘ │
            └───────────────┘   └────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Customer Response   │
                    │  + Audit Trail       │
                    │  + Compliance Log    │
                    └─────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Hybrid Search** | BM25 + Semantic | Keyword search catches exact regulatory terms; semantic search handles paraphrased queries |
| **Re-ranking** | Cross-encoder | Precision is critical in compliance — re-rank top-20 to get best-5 |
| **MCP over direct API** | MCP protocol | Standardized tool interface; swap providers (Jumio ↔ Onfido) without changing agent logic |
| **Human-in-Loop** | Risk-based | Only medium/high risk cases require manual review; low risk auto-approves |
| **Audit Trail** | Every RAG + MCP call logged | Banking regulators require full traceability of AI decisions |
| **Citations** | Always included | Enables compliance officers to verify agent reasoning against source regulations |

---

*Architecture designed for KYC Onboarding Agent — August 2026*
