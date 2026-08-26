# Document Digitization & Extraction Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Document Digitization & Extraction Agent that uses **RAG** for document processing knowledge retrieval and **MCP** for tool orchestration across OCR, classification, validation, enrichment, and storage systems.
>
> **Covers use case 10.1: Document Digitization & Extraction Agent.**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                DOCUMENT DIGITIZATION & EXTRACTION AGENT                         │
│                                                                                 │
│  ┌───────────┐    ┌──────────────┐    ┌────────────────────────────────────┐   │
│  │           │    │              │    │       MCP Tool Server              │   │
│  │  Bank     │───▶│   LLM Core   │◀──▶│  ┌────────────┐ ┌─────────────┐  │   │
│  │  Staff /  │    │  (GPT-4o /   │    │  │  Document  │ │  OCR / Data │  │   │
│  │  Customer │◀───│  Claude /    │    │  │  Classify  │ │  Extraction │  │   │
│  │  Chat     │    │  Gemini)     │    │  └────────────┘ └─────────────┘  │   │
│  └───────────┘    └──────┬───────┘    │  ┌────────────┐ ┌─────────────┐  │   │
│                          │             │  │  Data      │ │  Data       │  │   │
│                          │             │  │  Validate  │ │  Enrichment │  │   │
│                          │             │  └────────────┘ └─────────────┘  │   │
│                          ▼             │  ┌────────────┐ ┌─────────────┐  │   │
│                   ┌──────────────┐     │  │  Table /   │ │  Customer   │  │   │
│                   │              │     │  │  MRZ       │ │  Notify     │  │   │
│                   │   RAG Engine │     │  │  Extract   │ │             │  │   │
│                   │              │     │  └────────────┘ └─────────────┘  │   │
│                   │  ┌────────┐  │     └────────────────────────────────────┘   │
│                   │  │Query   │  │                                              │
│                   │  │Rewrite │  │     ┌────────────────────────────────────┐   │
│                   │  └───┬────┘  │     │       External APIs                │   │
│                   │      │       │     │  ┌───────────┐ ┌────────────────┐  │   │
│                   │      ▼       │     │  │ AWS       │ │ Google Vision  │  │   │
│                   │  ┌────────┐  │     │  │ Textract  │ │ / Azure Form   │  │   │
│                   │  │Hybrid  │  │     │  └───────────┘ │ Recognizer     │  │   │
│                   │  │Search  │  │     │  ┌───────────┐ └────────────────┘  │   │
│                   │  │(BM25 + │  │     │  │ Database  │ ┌────────────────┐  │   │
│                   │  │Semantic)│  │     │  │ Write API │ │ Document       │  │   │
│                   │  └───┬────┘  │     │  └───────────┘ │ Storage (S3)   │  │   │
│                   │      │       │     │  ┌───────────┐ └────────────────┘  │   │
│                   │      ▼       │     │  │ BSA/AML   │ ┌────────────────┐  │   │
│                   │  ┌────────┐  │     │  │ Threshold │ │ Notification   │  │   │
│                   │  │Re-rank │  │     │  │ Check     │ │ Service        │  │   │
│                   │  └───┬────┘  │     │  └───────────┘ └────────────────┘  │   │
│                   └──────┼───────┘     └────────────────────────────────────┘   │
│                          │                                                      │
└──────────────────────────┼──────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     Vector Database     │
              │                        │
              │  ┌──────────────────┐  │
              │  │  Document        │  │
              │  │  Classification  │  │
              │  ├──────────────────┤  │
              │  │  Extraction      │  │
              │  │  Schemas         │  │
              │  ├──────────────────┤  │
              │  │  Validation      │  │
              │  │  Rules           │  │
              │  ├──────────────────┤  │
              │  │  OCR Best        │  │
              │  │  Practices       │  │
              │  ├──────────────────┤  │
              │  │  Past Extraction │  │
              │  │  Decisions       │  │
              │  ├──────────────────┤  │
              │  │  Industry        │  │
              │  │  Standards       │  │
              │  ├──────────────────┤  │
              │  │  Banking Doc     │  │
              │  │  Templates       │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

---

## Detailed Component Flow

### Document Processing Journey — Step by Step

```
USER                    AGENT (LLM + RAG + MCP)                EXTERNAL SYSTEMS
────                    ────────────────────────                ─────────────────

  │                              │                                    │
  │  1. "Process this invoice    │                                    │
  │      from GlobalTech Inc."   │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  2. Intent: COMPLEX                │
  │                              │     RAG: Retrieve extraction       │
  │                              │     schemas for invoices           │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → Invoice schema (9 fields)    │
  │                              │     → Validation rules             │
  │                              │     → BSA thresholds               │
  │                              │                                    │
  │                              │  3. MCP: Classify document         │
  │                              │──────┐                             │
  │                              │      │  Embedding similarity       │
  │                              │◀─────┘                             │
  │                              │     → Type: invoice (0.92 conf)    │
  │                              │     → Pipeline: financial_extraction│
  │                              │                                    │
  │                              │  4. MCP: OCR extraction            │
  │                              │──────┐                             │
  │                              │      │  POST /ocr/extract          │
  │                              │      │  (AWS Textract API)         │
  │                              │◀─────┘                             │
  │                              │     → vendor: GlobalTech Inc.      │
  │                              │     → invoice_number: INV-2024-0892│
  │                              │     → total: $24,500.00            │
  │                              │     → confidence: 0.88             │
  │                              │                                    │
  │                              │  5. RAG: Retrieve validation       │
  │                              │     rules for invoices             │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → Business rules retrieved     │
  │                              │                                    │
  │                              │  6. MCP: Validate extracted data   │
  │                              │──────┐                             │
  │                              │      │  Local validation           │
  │                              │◀─────┘                             │
  │                              │     → Line items match totals ✓    │
  │                              │     → Dates valid ✓                │
  │                              │     → Currency USD ✓               │
  │                              │     → Total > $10K → BSA flag ⚠️   │
  │                              │                                    │
  │                              │  7. MCP: Enrich invoice data       │
  │                              │──────┐                             │
  │                              │      │  Vendor verify + tax calc   │
  │                              │◀─────┘                             │
  │                              │     → Vendor verified: true        │
  │                              │     → Tax rate: 8.16%              │
  │                              │     → BSA threshold: exceeded      │
  │                              │                                    │
  │                              │  8. MCP: Notify customer           │
  │                              │──────┐                             │
  │                              │      │  POST /notifications/send   │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  9. "Invoice processed       │                                    │
  │      successfully.           │                                    │
  │      9 fields extracted.     │                                    │
  │      Total: $24,500.00.      │                                    │
  │      BSA review required."   │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │

═════════════════════════════ BATCH PROCESSING ═══════════════════════════════

  │                              │                                    │
  │  10. "Classify and process   │                                    │
  │       these 50 documents"    │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  11. MCP: Batch classify           │
  │                              │──────┐                             │
  │                              │      │  Embedding similarity       │
  │                              │◀─────┘                             │
  │                              │     → 15 invoices, 10 statements,  │
  │                              │     → 8 contracts, 7 payslips,     │
  │                              │     → 10 KYC documents             │
  │                              │                                    │
  │                              │  12. Process each by type:         │
  │                              │      Invoices → financial pipeline │
  │                              │      Contracts → legal pipeline    │
  │                              │      KYC docs → kyc pipeline      │
  │                              │                                    │
  │  13. "Batch complete.        │                                    │
  │       42 auto-processed,     │                                    │
  │       6 need review,         │                                    │
  │       2 rejected (quality)." │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
```

---

## MCP Tool Definitions

```jsonc
// mcp-server-document-digitization.json
{
  "mcpServers": {
    "document-digitization": {
      "description": "Document Digitization & Extraction MCP Server — tools for classification, OCR extraction, validation, enrichment, and document management",
      "tools": [
        {
          "name": "classify_document",
          "description": "Classify a document into a category using document embeddings",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_url": { "type": "string", "description": "URL or file reference to the document" },
              "hint": { "type": "string", "description": "Optional hint about expected document type" }
            },
            "required": ["document_url"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "document_type": { "type": "string", "enum": ["invoice", "contract", "bank_statement", "tax_return", "payslip", "proof_of_address", "identity_document", "financial_statement", "loan_application", "corporate_resolution"] },
              "category": { "type": "string", "enum": ["accounts_payable", "legal", "financial", "kyc", "lending"] },
              "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
              "extraction_pipeline": { "type": "string" }
            }
          }
        },
        {
          "name": "extract_document",
          "description": "Extract structured data from a document using OCR",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_url": { "type": "string" },
              "document_type": { "type": "string", "enum": ["invoice", "contract", "bank_statement", "tax_return", "payslip", "proof_of_address", "identity_document", "financial_statement", "loan_application", "corporate_resolution"] },
              "page_range_start": { "type": "integer" },
              "page_range_end": { "type": "integer" }
            },
            "required": ["document_url", "document_type"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "extracted_fields": { "type": "object" },
              "field_confidences": { "type": "object" },
              "overall_confidence": { "type": "number" },
              "ocr_quality": { "type": "string", "enum": ["high", "medium", "low"] },
              "pages_processed": { "type": "integer" }
            }
          }
        },
        {
          "name": "extract_table_data",
          "description": "Extract tabular data from a specific page of a document",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_url": { "type": "string" },
              "page_number": { "type": "integer", "default": 1 }
            },
            "required": ["document_url"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "tables_found": { "type": "integer" },
              "tables": { "type": "array", "items": { "type": "object" } }
            }
          }
        },
        {
          "name": "extract_mrz",
          "description": "Extract Machine Readable Zone from passport or ID document",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_url": { "type": "string" }
            },
            "required": ["document_url"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "mrz_found": { "type": "boolean" },
              "parsed_data": { "type": "object" },
              "checksum_valid": { "type": "boolean" },
              "confidence": { "type": "number" }
            }
          }
        },
        {
          "name": "validate_document_data",
          "description": "Validate extracted fields against schema rules and business logic",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_type": { "type": "string" },
              "extracted_fields": { "type": "object" },
              "schema_rules": { "type": "object", "description": "Optional custom validation rules override" }
            },
            "required": ["document_type", "extracted_fields"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "is_valid": { "type": "boolean" },
              "errors": { "type": "array" },
              "warnings": { "type": "array" },
              "recommendation": { "type": "string", "enum": ["auto_accept", "accept_with_review", "reject_or_manual_review"] }
            }
          }
        },
        {
          "name": "cross_validate_documents",
          "description": "Cross-validate data across multiple related documents",
          "inputSchema": {
            "type": "object",
            "properties": {
              "documents": { "type": "array", "items": { "type": "object" } }
            },
            "required": ["documents"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "is_consistent": { "type": "boolean" },
              "discrepancies": { "type": "array" }
            }
          }
        },
        {
          "name": "enrich_invoice",
          "description": "Enrich extracted invoice data with vendor verification, tax calculation, duplicate detection",
          "inputSchema": {
            "type": "object",
            "properties": {
              "extracted_fields": { "type": "object" }
            },
            "required": ["extracted_fields"]
          }
        },
        {
          "name": "enrich_bank_statement",
          "description": "Enrich bank statement data with cash flow analysis, spending categories, creditworthiness",
          "inputSchema": {
            "type": "object",
            "properties": {
              "extracted_fields": { "type": "object" }
            },
            "required": ["extracted_fields"]
          }
        },
        {
          "name": "enrich_contract",
          "description": "Enrich contract data with risk scoring, missing clause detection, renewal tracking",
          "inputSchema": {
            "type": "object",
            "properties": {
              "extracted_fields": { "type": "object" }
            },
            "required": ["extracted_fields"]
          }
        },
        {
          "name": "enrich_financial_statement",
          "description": "Enrich financial statement data with ratio analysis and health scoring",
          "inputSchema": {
            "type": "object",
            "properties": {
              "extracted_fields": { "type": "object" }
            },
            "required": ["extracted_fields"]
          }
        },
        {
          "name": "process_document",
          "description": "End-to-end document processing: classify → extract → validate → enrich",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_url": { "type": "string" },
              "document_type": { "type": "string", "description": "Optional — auto-classified if not provided" },
              "auto_enrich": { "type": "boolean", "default": true }
            },
            "required": ["document_url"]
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "document_type": { "type": "string" },
              "classification": { "type": "object" },
              "extraction": { "type": "object" },
              "validation": { "type": "object" },
              "enrichment": { "type": "object" },
              "status": { "type": "string", "enum": ["processed", "needs_review", "rejected"] }
            }
          }
        },
        {
          "name": "batch_classify_documents",
          "description": "Classify multiple documents in a batch",
          "inputSchema": {
            "type": "object",
            "properties": {
              "document_urls": { "type": "array", "items": { "type": "string" } }
            },
            "required": ["document_urls"]
          }
        },
        {
          "name": "notify_customer",
          "description": "Send processing status notification to customer",
          "inputSchema": {
            "type": "object",
            "properties": {
              "customer_id": { "type": "string" },
              "template_id": { "type": "string", "enum": ["doc_received", "doc_processed", "doc_needs_review", "doc_rejected", "extraction_complete", "validation_failed", "batch_complete"] },
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

---

## RAG Pipeline Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                             │
│                                                                 │
│  ┌─────────────┐                                                │
│  │  User Query  │  "What fields do I need to extract from       │
│  │              │   a bank statement?"                           │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 1. QUERY    │  Rewrites for better retrieval:                │
│  │   REWRITE   │  "bank statement extraction schema required    │
│  │             │   fields validation rules"                     │
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
│  │  │ "bank"     │    │  Vector        │    │                   │
│  │  │ "statement"│    │  Similarity    │    │                   │
│  │  │ "extraction│    │  Search        │    │                   │
│  │  │  schema"   │    │  (top-k=20)    │    │                   │
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
│          │   ASSEMBLY     │  - Extraction schema excerpt        │
│          │                │  - Validation rules                 │
│          │                │  - Past extraction decisions        │
│          │                │  - OCR best practices               │
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
│  Collection: document_classification                            │
│  ───────────────────────────────────                            │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  cls_001     │  "Invoice      │  [0.12,     │ {           │ │
│  │              │   classification│  -0.45,     │  "doc_type":│ │
│  │              │   Invoices     │   0.78,     │  "invoice", │ │
│  │              │   typically    │   ...],     │  "category":│ │
│  │              │   contain      │             │  "accounts_ │ │
│  │              │   vendor name, │             │   payable"  │ │
│  │              │   invoice      │             │ }           │ │
│  │              │   number...\"  │             │             │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: extraction_schemas                                 │
│  ─────────────────────────────                                  │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  schema_001  │  "Invoice      │  [0.34,     │ {           │ │
│  │              │   extraction   │  -0.22,     │  "doc_type":│ │
│  │              │   schema —     │   0.91,     │  "invoice", │ │
│  │              │   Required     │   ...],     │  "fields":  │ │
│  │              │   fields:      │             │  ["vendor", │ │
│  │              │   vendor_name  │             │   "number", │ │
│  │              │   ...\"        │             │   "date"]   │ │
│  │              │                │             │ }           │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: validation_rules                                   │
│  ──────────────────────────                                     │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  val_001     │  "Invoice-     │  [0.56,     │ {           │ │
│  │              │   specific     │   0.11,     │  "rule_type":│ │
│  │              │   validation   │   0.88,     │  "invoice", │ │
│  │              │   rules:       │   ...],     │  "priority":│ │
│  │              │   1. Invoice   │             │  "high"     │ │
│  │              │   number must  │             │ }           │ │
│  │              │   be unique...\"│            │             │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: ocr_best_practices                                 │
│  ─────────────────────────────                                  │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  ocr_001     │  "OCR quality  │  [0.72,     │ {           │ │
│  │              │   assessment:  │  -0.33,     │  "topic":   │ │
│  │              │   Confidence   │   0.45,     │  "ocr_      │ │
│  │              │   thresholds — │   ...],     │  "quality"  │ │
│  │              │   High >=0.85  │             │ }           │ │
│  │              │   ...\"        │             │             │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: past_extraction_decisions                          │
│  ────────────────────────────────────                           │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  case_001    │  "Successful   │  [0.28,     │ {           │ │
│  │              │   extraction:  │  -0.67,     │  "decision":│ │
│  │              │   Vendor       │   0.54,     │  "auto_     │ │
│  │              │   invoice from │   ...],     │  "processed"│ │
│  │              │   GlobalTech   │             │  "doc_type":│ │
│  │              │   Inc. OCR     │             │  "invoice"  │ │
│  │              │   confidence   │             │ }           │ │
│  │              │   0.92...\"    │             │             │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: industry_document_standards                        │
│  ──────────────────────────────────────                         │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  std_001     │  "ISO 20022    │  [0.45,     │ {           │ │
│  │              │   Financial    │  -0.28,     │  "standard":│ │
│  │              │   Messaging    │   0.67,     │  "ISO 20022"│ │
│  │              │   Standards...\"│  ...],     │ }           │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
│                                                                 │
│  Collection: banking_document_templates                         │
│  ──────────────────────────────────────                         │
│  ┌──────────────┬────────────────┬─────────────┬─────────────┐ │
│  │  id          │  text_chunk    │  embedding   │  metadata    │ │
│  ├──────────────┼────────────────┼─────────────┼─────────────┤ │
│  │  tmpl_001    │  "Loan appli-  │  [0.62,     │ {           │ │
│  │              │   cation doc   │  -0.15,     │  "template":│ │
│  │              │   package      │   0.83,     │  "loan_     │ │
│  │              │   template —   │   ...],     │  "applica-  │ │
│  │              │   Standard     │             │  "tion"     │ │
│  │              │   documents    │             │ }           │ │
│  │              │   required...\" │            │             │ │
│  └──────────────┴────────────────┴─────────────┴─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
                    ┌───────────────────┐
                    │   User Input       │
                    │  "Process this     │
                    │   document"        │
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
            │  │ Vector  │  │   │  │ Classify  │ │
            │  │ DB      │  │   │  ├───────────┤ │
            │  │         │  │   │  │ OCR       │ │
            │  │ → Class │  │   │  │ Extract   │ │
            │  │ → Schema│  │   │  ├───────────┤ │
            │  │ → Valid │  │   │  │ Validate  │ │
            │  │ → OCR   │  │   │  ├───────────┤ │
            │  │ → Cases │  │   │  │ Enrich    │ │
            │  │ → Std   │  │   │  ├───────────┤ │
            │  │ → Tmpl  │  │   │  │ Notify    │ │
            │  └─────────┘  │   │  └───────────┘ │
            └───────────────┘   └────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  User Response       │
                    │  "Extracted 9 fields │
                    │   Confidence: 0.88"  │
                    │  + Audit Trail       │
                    │  + Compliance Log    │
                    └─────────────────────┘
```

---

## Document Type Routing

```
                        ┌──────────────────┐
                        │  Document Input   │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Classification   │
                        │  (Embedding)      │
                        └────────┬─────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
    ┌──────▼──────┐    ┌────────▼────────┐    ┌───────▼───────┐
    │  Financial   │    │  Legal          │    │  KYC          │
    │  Documents   │    │  Documents      │    │  Documents    │
    └──────┬──────┘    └────────┬────────┘    └───────┬───────┘
           │                    │                     │
    ┌──────┼──────┐    ┌───────┼───────┐    ┌────────┼────────┐
    │      │      │    │       │       │    │        │        │
    ▼      ▼      ▼    ▼       ▼       ▼    ▼        ▼        ▼
  Invoice  Bank   Tax  Contract Corp  Res  Passport  ID     Proof
  Payslip  Stmnt  Ret  Service  Board      Licence  Card    Address
                                  Res
    │      │      │    │       │       │    │        │        │
    └──────┼──────┘    └───────┼───────┘    └────────┼────────┘
           │                    │                     │
           ▼                    ▼                     ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  Financial    │    │  Legal       │    │  KYC         │
    │  Extraction   │    │  Extraction  │    │  Extraction  │
    │  Pipeline     │    │  Pipeline    │    │  Pipeline    │
    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Hybrid Search** | BM25 + Semantic | Keyword search catches exact field names and regulation codes; semantic handles paraphrased queries |
| **Re-ranking** | Score-based (cross-encoder in production) | Precision is critical — wrong extraction = wrong data in banking systems |
| **MCP over direct API** | MCP protocol | Standardized tool interface; swap OCR providers (AWS Textract ↔ Google Vision) without changing agent logic |
| **Classification First** | Embedding-based routing | Auto-classify documents before extraction ensures correct schema and pipeline selection |
| **Per-field Confidence** | Individual confidence scores | Allows targeted manual review — re-check low-confidence fields only |
| **Business Rule Validation** | Local computation | Deterministic, auditable — no LLM hallucination in financial calculations |
| **Cross-document Validation** | Related document cross-check | Catches inconsistencies across document packages (e.g., payslip income ≠ tax return) |
| **Data Enrichment** | Type-specific enrichment | Invoice enrichment ≠ bank statement enrichment; each has domain-specific analysis |
| **BSA Threshold Detection** | Automatic flagging | Regulatory requirement — flag transactions > $10,000 for CTR filing |
| **Batch Processing** | Parallel classification + sequential extraction | Classify all documents first, then batch-extract by type for efficiency |
| **Audit Trail** | Every RAG + MCP call logged | Banking regulators require full traceability of data extraction decisions |
| **Graceful Degradation** | Confidence-based routing | High confidence → auto-process; Medium → accept with review; Low → reject and re-scan |

---

*Architecture designed for Document Digitization & Extraction Agent (Use Case 10.1) — August 2026*
