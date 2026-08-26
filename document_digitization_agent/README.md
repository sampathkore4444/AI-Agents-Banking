# Document Digitization & Extraction Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for document digitization and extraction in banking, powered by a **RAG pipeline** for document processing knowledge retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

**Covers use case 10.1: Document Digitization & Extraction Agent** — extracts structured data from unstructured banking documents (invoices, contracts, statements, KYC documents).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DOCUMENT DIGITIZATION & EXTRACTION AGENT                      │
│                                                                             │
│  ┌──────────┐    ┌─────────────┐    ┌────────────────────────────────────┐ │
│  │  User     │───▶│  LLM Core   │───▶│  MCP Tool Server                  │ │
│  │  Query    │    │  (ReAct     │◀───│  ├── knowledge_search             │ │
│  │           │◀───│   Agent)    │    │  ├── classify_document            │ │
│  │           │    │             │    │  ├── extract_document             │ │
│  │           │    │  Options:   │    │  ├── extract_table_data          │ │
│  │           │    │  • Ollama   │    │  ├── extract_mrz_data            │ │
│  │           │    │  • vLLM     │    │  ├── validate_document_data      │ │
│  │           │    │  • SGLang   │    │  ├── cross_validate_documents    │ │
│  │           │    │             │    │  ├── process_document (E2E)      │ │
│  │           │    │             │    │  ├── enrich_invoice              │ │
│  │           │    │             │    │  ├── enrich_bank_statement       │ │
│  │           │    │             │    │  ├── enrich_contract             │ │
│  │           │    │             │    │  ├── enrich_financial_statement  │ │
│  │           │    │             │    │  ├── batch_classify_documents    │ │
│  │           │    │             │    │  └── notify_customer             │ │
│  └──────────┘    └──────┬──────┘    └────────────────────────────────────┘ │
│                         │                                                   │
│                         ▼                                                   │
│                  ┌──────────────┐                                           │
│                  │  RAG Engine  │                                           │
│                  │  (ChromaDB)  │                                           │
│                  │  • Classification│                                       │
│                  │  • Schemas   │                                           │
│                  │  • Validation│                                           │
│                  │  • OCR Best  │                                           │
│                  │  • Past Cases│                                           │
│                  │  • Standards │                                           │
│                  │  • Templates │                                           │
│                  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed

### Classification & Routing

| Tool | Description |
|------|-------------|
| `classify_document` | Classify a single document into a category using embeddings |
| `batch_classify_documents` | Classify multiple documents in a batch |
| `get_supported_document_types` | List all supported document types and metadata |

### OCR & Extraction

| Tool | Description |
|------|-------------|
| `extract_document` | Extract structured data from a document via OCR |
| `extract_table_from_document` | Extract tabular data from a specific page |
| `extract_mrz_data` | Extract Machine Readable Zone from passports/IDs |

### Validation & Cross-Validation

| Tool | Description |
|------|-------------|
| `validate_document_data` | Validate extracted fields against schemas and business rules |
| `cross_validate_multiple_documents` | Cross-validate data across related documents |

### Data Enrichment

| Tool | Description |
|------|-------------|
| `enrich_invoice` | Vendor verification, tax calculation, duplicate detection |
| `enrich_bank_statement` | Cash flow analysis, spending categories, creditworthiness |
| `enrich_contract` | Risk scoring, missing clause detection, renewal tracking |
| `enrich_financial_statement` | Ratio analysis, health scoring, benchmarking |

### Batch Processing

| Tool | Description |
|------|-------------|
| `batch_process_documents` | Full pipeline for multiple docs: classify → extract → validate → enrich |
| `batch_extract_documents` | Fast batch extraction only (no validation/enrichment) |
| `batch_validate_documents` | Validate multiple extracted datasets at once |

### End-to-End Processing

| Tool | Description |
|------|-------------|
| `process_document` | Full pipeline for single doc: classify → extract → validate → enrich |
| `knowledge_search` | RAG search over document processing knowledge base |
| `notify_customer` | Send processing status notifications |

## Supported Document Types

| Document Type | Category | Key Fields | Pipeline |
|---------------|----------|------------|----------|
| **Invoice** | Accounts Payable | vendor, number, date, line items, total | financial_extraction |
| **Contract** | Legal | parties, effective_date, terms, value | legal_extraction |
| **Bank Statement** | Financial | account, period, balances, transactions | financial_extraction |
| **Tax Return** | Financial | taxpayer, AGI, taxable_income, refund | financial_extraction |
| **Payslip** | Financial | employee, gross_pay, deductions, net_pay | financial_extraction |
| **Proof of Address** | KYC | name, address, provider, date | kyc_extraction |
| **Identity Document** | KYC | name, DOB, document_number, expiry | kyc_extraction |
| **Financial Statement** | Financial | company, assets, liabilities, equity | financial_extraction |
| **Loan Application** | Lending | borrower, loan_type, amount, property | lending_extraction |
| **Corporate Resolution** | Legal | company, date, action, signatories | legal_extraction |

## Document Processing Flow

```
Customer: "Process this invoice from GlobalTech Inc."
    │
    ├── 1. classify_document(url)
    │      → Document type: invoice (confidence: 0.92)
    │
    ├── 2. knowledge_search("invoice extraction schema")
    │      → Retrieved: required fields, validation rules
    │
    ├── 3. extract_document(url, "invoice")
    │      → Extracted 9 fields, confidence: 0.88
    │
    ├── 4. validate_document_data("invoice", extracted_fields)
    │      → Valid: line items match totals, dates valid
    │
    ├── 5. enrich_invoice(extracted_fields)
    │      → Added: vendor_verified, tax_rate, BSA_check
    │
    └── 6. notify_customer(customer_id, "doc_processed")
           → Notification sent
```

## Quick Start

### 1. Install dependencies

```bash
cd document_digitization_agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your OCR provider credentials
```

See `.env.example` for all available options. At minimum, configure one OCR provider (AWS Textract or Google Vision).

### 3. Seed the knowledge base

```bash
python seed_knowledge.py
```

### 4. Start an LLM backend

**Option A: Ollama (easiest)**
```bash
# Install: https://ollama.ai
ollama pull llama3.1:8b
ollama serve  # starts on port 11434
```

**Option B: vLLM (high performance)**
```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

**Option C: SGLang (structured output)**
```bash
pip install sglang
python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 30000
```

### 5. Run the agent

```bash
# Interactive mode
python -m llm.agent_ollama    # Uses Ollama
python -m llm.agent_vllm      # Uses vLLM
python -m llm.agent_sglang    # Uses SGLang

# Compare all three
python compare_agents.py
```

### 6. Configure OCR provider (optional)

The agent works out of the box with simulated data. For real OCR, configure one or both providers:

**Option A: AWS Textract**
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

**Option B: Google Cloud Vision**
```bash
# Create a service account at https://console.cloud.google.com/iam-admin/serviceaccounts
# Download the JSON key file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

**Option C: Both (auto-fallback)**
```bash
# Set both — tries Textract first, falls back to Google Vision
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

**Or use a `.env` file:**
```env
# OCR Provider: "textract" | "google_vision" | "auto"
OCR_PROVIDER=auto

# AWS Textract
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Google Cloud Vision
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

| Provider | Best For | Cost |
|----------|----------|------|
| **AWS Textract** | Invoices, forms, tables, IDs | ~$0.015/page |
| **Google Vision** | General text, MRZ, fast OCR | ~$0.005/page |
| **Auto (both)** | Production with fallback | Depends on usage |

### 7. Or use MCP server mode

```bash
python server.py  # Starts MCP server on stdio
```

## Batch Processing

Process multiple documents efficiently with built-in concurrency control:

### Full Batch Pipeline

```python
# Process 50 documents through the full pipeline
result = await batch_process_documents(
    document_urls=[
        "https://storage.example.com/invoice-001.pdf",
        "https://storage.example.com/statement-001.pdf",
        "https://storage.example.com/contract-001.pdf",
        # ... up to 100s of documents
    ],
    auto_validate=True,
    auto_enrich=True,
    max_concurrent=5,  # Limit concurrent OCR calls
)
```

### Batch with Forced Type

```python
# Skip classification — all docs are invoices
result = await batch_process_documents(
    document_urls=[...],
    document_type="invoice",
)
```

### Fast Batch Extraction

```python
# Extract only (no validation/enrichment) — faster
result = await batch_extract_only(
    document_urls=[...],
    document_types={
        "https://.../inv.pdf": "invoice",
        "https://.../stmt.pdf": "bank_statement",
    },
)
```

### Batch Response Format

```json
{
  "batch_id": "a1b2c3d4e5f6",
  "total_documents": 50,
  "summary": {
    "status_distribution": {
      "processed": 42,
      "validation_failed": 4,
      "ocr_failed": 2,
      "error": 2
    },
    "type_distribution": {
      "invoice": 15,
      "bank_statement": 12,
      "contract": 8,
      "payslip": 10,
      "tax_return": 5
    },
    "average_confidence": 0.847,
    "validation_stats": { "validated": 48, "valid": 44, "invalid": 4 },
    "enrichment_stats": { "enriched": 44 }
  },
  "documents": [
    {
      "document_url": "https://.../inv-001.pdf",
      "document_type": "invoice",
      "status": "processed",
      "extraction": { "confidence": 0.92, "provider": "textract" },
      "validation": { "is_valid": true },
      "enrichment": { "enrichments_applied": ["vendor_verified", "tax_rate"] }
    },
    ...
  ]
}
```

### Concurrency Limits

| Documents | Recommended Concurrency | Notes |
|-----------|------------------------|-------|
| 1-10 | 5 | Default, safe for most APIs |
| 10-50 | 5-10 | Monitor API rate limits |
| 50-100 | 10-20 | Use with Textract async batch |
| 100+ | 20 | Consider SQS queue for production |

## Project Structure

```
document_digitization_agent/
├── server.py                  # MCP server — 18 tool definitions
├── rag_pipeline.py            # RAG engine — ChromaDB + hybrid search
├── config.py                  # Settings from environment variables
├── .env.example               # Environment variables template (copy to .env)
├── seed_knowledge.py          # Seed script for vector DB (30+ docs)
├── compare_agents.py          # Compare all 3 LLM backends
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── llm/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent — ReAct loop, tools, memory, guardrails
│   ├── agent_ollama.py        # Ollama integration (local, free)
│   ├── agent_vllm.py          # vLLM integration (high throughput)
│   └── agent_sglang.py        # SGLang integration (structured output)
└── tools/
    ├── __init__.py
    ├── ocr_extraction.py      # OCR + data extraction (Textract + Google Vision)
    ├── document_classification.py  # Document type detection
    ├── data_validation.py     # Schema + business rule validation
    ├── data_enrichment.py     # Context enrichment + analysis
    ├── batch_processing.py    # Batch classify + extract + validate
    └── notifications.py       # Customer notifications
```

## Knowledge Base (7 Collections)

| Collection | Content | Documents |
|------------|---------|-----------|
| `document_classification` | Document type detection rules, category metadata | 10 |
| `extraction_schemas` | Required fields, data types per document type | 6 |
| `validation_rules` | Business rules, cross-field consistency checks | 6 |
| `ocr_best_practices` | Quality thresholds, preprocessing, MRZ, tables | 4 |
| `past_extraction_decisions` | Successful, reviewed, rejected extraction cases | 5 |
| `industry_document_standards` | ISO 20022, UBL, IFRS, US GAAP, BSA | 5 |
| `banking_document_templates` | Standard document packages for common workflows | 3 |

## Data Validation Features

### Per-Document Validation

- **Invoice**: Line item totals, tax calculation, due date logic, BSA thresholds
- **Bank Statement**: Balance reconciliation, transaction consistency, NSF detection
- **Tax Return**: AGI/taxable income logic, W-2 cross-validation, YoY comparison
- **Payslip**: Net pay calculation, YTD consistency, deduction reasonableness
- **Contract**: Missing clause detection, value thresholds, signature verification

### Cross-Document Validation

- Name consistency across document packages
- Income verification (payslip ↔ tax return ↔ bank statement)
- Date range alignment
- Amount reconciliation

## Data Enrichment Features

### Invoice Enrichment
- Vendor verification (known/unknown vendor scoring)
- Payment terms normalization (Net 30/60/90)
- Tax rate calculation and validation
- Currency conversion to USD equivalent
- BSA/CTR threshold detection
- Duplicate invoice detection hash

### Bank Statement Enrichment
- Cash flow analysis (savings rate, spending ratio)
- Transaction categorization (income, housing, food, utilities, other)
- Irregularity detection (NSF fees, large withdrawals)
- Creditworthiness scoring (0-100)
- Minimum balance analysis

### Contract Enrichment
- Risk scoring (missing clauses, high value, jurisdiction)
- Contract end date calculation
- Renewal reminder scheduling
- Legal review requirement detection

### Financial Statement Enrichment
- Liquidity ratios (debt-to-asset, equity multiplier)
- Profitability ratios (net margin, ROA, ROE)
- Financial health scoring (0-100)
- Industry benchmarking preparation

## Production Patterns

Same as KYC and Loan Agents — see `llm/base_agent.py`:

| # | Pattern | Class | Purpose |
|---|---------|-------|---------|
| 1 | Intent Routing | `IntentRouter` | Routes simple queries to RAG (no LLM) |
| 2 | Guardrails | `Guardrails` | Risk-based tool access control + output safety |
| 3 | Human-in-the-Loop | `HumanApprovalManager` | Pauses for approval on high-risk actions |
| 4 | Memory Management | `ConversationMemory` | Token-aware history with summarization |
| 5 | Error Handling | `ErrorHandler` | Retry with backoff, fallback strategies |
| 6 | Observability | `AgentTracer` | Structured traces for every operation |

## LLM Backends

| Backend | Best For | Setup | Speed |
|---------|----------|-------|-------|
| **Ollama** | Local dev, privacy | `ollama serve` | ~2-5s |
| **vLLM** | Production, high throughput | `vllm serve <model>` | ~0.5-2s |
| **SGLang** | Structured output, caching | `sglang.launch_server` | ~0.3-1.5s |

## Extending

### Add a new document type

```python
# 1. Add to seed_knowledge.py
DOCUMENT_CLASSIFICATION.append({
    "id": "cls_new_type_001",
    "text": "Your document classification description...",
    "metadata": {"doc_type": "new_type", "category": "your_category"},
})

# 2. Add extraction schema
EXTRACTION_SCHEMAS.append({
    "id": "schema_new_type_001",
    "text": "Your extraction schema description...",
    "metadata": {"doc_type": "new_type", "fields": ["field1", "field2"]},
})

# 3. Add validation rules
VALIDATION_RULES.append({
    "id": "val_new_type_001",
    "text": "Your validation rules...",
    "metadata": {"rule_type": "new_type", "priority": "high"},
})

# 4. Add to server.py classification routing
# 5. Add extraction tool if custom processing needed
```

### Add a new enrichment tool

```python
# In tools/data_enrichment.py
async def enrich_new_document_type(extracted_fields: dict) -> dict:
    """Enrich extracted data for new document type."""
    enriched = dict(extracted_fields)
    enrichment_metadata = {}
    # Your enrichment logic here
    return {
        "enrichment_id": str(uuid.uuid4()),
        "original_fields": extracted_fields,
        "enriched_fields": enriched,
        "enrichment_metadata": enrichment_metadata,
        "enriched_at": datetime.utcnow().isoformat(),
    }
```

### Switch vector database

Replace ChromaDB with Pinecone, Weaviate, Qdrant, or pgvector by updating
`rag_pipeline.py`. The MCP tool interface stays the same.

## OCR Integration

The agent supports **two OCR providers** with automatic fallback:

### AWS Textract
- `AnalyzeDocument` — General documents (TABLES + FORMS features)
- `AnalyzeExpense` — Invoices and receipts (vendor, line items, totals)
- `AnalyzeID` — Passports and ID documents (name, DOB, doc number)
- Best for: Structured banking documents, forms, tables

### Google Cloud Vision
- `document_text_detection` — Full document text with layout
- `text_detection` — Fast text extraction
- Best for: General text, MRZ codes, quick extraction

### Auto-fallback Flow
```
Document URL
    │
    ├── 1. Download document (HTTP/S3/local file)
    │
    ├── 2. Try AWS Textract
    │      ├── Invoice → AnalyzeExpense
    │      ├── ID doc → AnalyzeID + AnalyzeDocument
    │      └── Other → AnalyzeDocument (TABLES + FORMS)
    │
    ├── 3. If Textract fails → Fall back to Google Vision
    │      ├── document_text_detection
    │      └── Parse key:value pairs from text
    │
    └── 4. Map OCR output → schema fields
           ├── Alias matching ("total" → "total_amount")
           ├── Type parsing (currency strings → floats)
           └── Per-field confidence scoring
```

### Field Mapping

The agent maps common OCR key names to schema fields automatically:

| Schema Field | OCR Aliases |
|-------------|-------------|
| `total_amount` | total, amount_due, grand_total, balance_due |
| `invoice_number` | invoice_no, invoice #, inv_number, reference |
| `gross_pay` | gross, gross_pay, gross_salary, total_earnings |
| `opening_balance` | opening_balance, beginning_balance, start_balance |
| *(and 30+ more field mappings)* | |

## Notes

- The RAG pipeline uses `all-MiniLM-L6-v2` embeddings — upgrade to `text-embedding-3-large` for production accuracy
- ChromaDB is ephemeral in development — use a hosted instance for persistence
- All tool calls are logged for audit trail compliance
- For production, consider adding: rate limiting, authentication, monitoring, alerting
- Memory management uses character-based token estimation — use `tiktoken` for accurate counting
- The `compare_agents.py` script runs the same query across all 3 backends for benchmarking
- For multi-user production systems, configure batching and scheduling in vLLM/SGLang
- Without OCR credentials, the agent returns structured error responses — configure at least one provider for real extraction
- Document classification uses simulated embeddings — production uses trained document embedding models
