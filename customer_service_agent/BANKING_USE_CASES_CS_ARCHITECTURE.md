# Customer Service & Support Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Customer Service & Support Agent that uses **RAG** for knowledge retrieval and **MCP** for tool orchestration across FAQ, account info, disputes, complaints, and multilingual support.
>
> **Covers all 5 use cases: 1.1 FAQ, 1.2 Account Info, 1.3 Disputes, 1.4 Multilingual, 1.5 Complaints**

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                CUSTOMER SERVICE & SUPPORT AGENT                           │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  Customer │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Channel  │    │  (ReAct     │◀───│  ├── search_knowledge_base      │ │
│  │           │◀───│   Agent)    │    │  ├── get_balance                │ │
│  │  • Chat   │    │             │    │  ├── get_transactions           │ │
│  │  • Phone  │    │  Options:   │    │  ├── get_statements             │ │
│  │  • Email  │    │  • Ollama   │    │  ├── file_new_dispute           │ │
│  │  • Mobile │    │  • vLLM     │    │  ├── check_dispute_status       │ │
│  │           │    │  • SGLang   │    │  ├── log_new_complaint          │ │
│  └──────────┘    └──────┬──────┘    │  ├── detect_language_tool        │ │
│                         │           │  ├── translate                   │ │
│                         ▼           │  ├── escalate_to_agent           │ │
│                  ┌──────────────┐   │  ├── create_ticket               │ │
│                  │  RAG Engine  │   │  └── notify                      │ │
│                  │  (ChromaDB)  │   └──────────────────────────────────┘ │
│                  │              │                                         │
│                  │  • Banking FAQ│    ┌──────────────────────────────────┐ │
│                  │  • Products  │    │       External APIs              │ │
│                  │  • Fees      │    │  ┌──────────┐ ┌───────────┐     │ │
│                  │  • Disputes  │    │  │ Core     │ │ Translation│    │ │
│                  │  • Complaints│    │  │ Banking  │ │ API       │     │ │
│                  │  • Regulations│   │  │ API      │ │ (DeepL/   │     │ │
│                  │  • Playbooks │    │  └──────────┘ │ Google)   │     │ │
│                  └──────────────┘    │  ┌──────────┐ └───────────┘     │ │
│                                      │  │ CRM /    │ ┌───────────┐     │ │
│                                      │  │ Ticketing│ │ Contact   │     │ │
│                                      │  │ System   │ │ Center    │     │ │
│                                      │  └──────────┘ └───────────┘     │ │
│                                      └──────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Flows

### Flow 1: FAQ Query (Use Case 1.1)

```
CUSTOMER                  AGENT (LLM + RAG)                 SYSTEMS
────────                  ─────────────────                 ───────

  │  "How do I stop       │                                │
  │   a payment?"         │                                │
  │──────────────────────▶│                                │
  │                       │  1. Intent: SIMPLE             │
  │                       │     (FAQ question)             │
  │                       │──────┐                         │
  │                       │      │  Query Vector DB        │
  │                       │◀─────┘                         │
  │                       │     → FAQ doc: "stop payment"  │
  │                       │     → Policy: "$30 fee"        │
  │  "To stop a payment:  │                                │
  │   1. Log into banking │                                │
  │   2. Go to Payments   │                                │
  │   3. Click Stop..."   │                                │
  │◀──────────────────────│                                │
```

### Flow 2: Account Inquiry (Use Case 1.2)

```
CUSTOMER                  AGENT (LLM + MCP)                SYSTEMS
────────                  ─────────────────                 ───────

  │  "How much did I      │                                │
  │   spend on groceries  │                                │
  │   last month?"        │                                │
  │──────────────────────▶│                                │
  │                       │  1. MCP: get_balance()         │
  │                       │──────┐                         │
  │                       │      │  Core Banking API       │
  │                       │◀─────┘                         │
  │                       │     → $5,234.50                │
  │                       │                                │
  │                       │  2. MCP: get_transactions(     │
  │                       │     days=30,                   │
  │                       │     category="groceries")      │
  │                       │──────┐                         │
  │                       │      │  Core Banking API       │
  │                       │◀─────┘                         │
  │                       │     → 12 grocery transactions │
  │                       │     → Total: $487.23           │
  │  "Last month you      │                                │
  │   spent $487.23 on    │                                │
  │   groceries across    │                                │
  │   12 transactions."   │                                │
  │◀──────────────────────│                                │
```

### Flow 3: Dispute (Use Case 1.3)

```
CUSTOMER                  AGENT (LLM + RAG + MCP)          SYSTEMS
────────                  ─────────────────────             ───────

  │  "I was charged       │                                │
  │   twice for the       │                                │
  │   same purchase"      │                                │
  │──────────────────────▶│                                │
  │                       │  1. RAG: dispute process       │
  │                       │──────┐                         │
  │                       │      │  Query Vector DB        │
  │                       │◀─────┘                         │
  │                       │     → FCBA rules, timelines   │
  │                       │                                │
  │                       │  2. MCP: get_dispute_types()   │
  │                       │──────┐                         │
  │                       │◀─────┘                         │
  │                       │     → duplicate_charge type    │
  │                       │                                │
  │  "Let me help you     │                                │
  │   file a dispute.     │                                │
  │   Please provide..."  │                                │
  │◀──────────────────────│                                │
  │                       │                                │
  │  [Customer provides   │                                │
  │   transaction details]│                                │
  │──────────────────────▶│                                │
  │                       │                                │
  │                       │  3. MCP: file_new_dispute()    │
  │                       │──────┐                         │
  │                       │      │  Dispute API            │
  │                       │◀─────┘                         │
  │                       │     → DISP-A1B2C3D4            │
  │                       │     → Priority: medium         │
  │                       │     → SLA: 15 days             │
  │                       │                                │
  │                       │  4. MCP: notify(dispute_filed) │
  │                       │──────┐                         │
  │                       │      │  Notification API       │
  │                       │◀─────┘                         │
  │  "Your dispute has    │                                │
  │   been filed.         │                                │
  │   ID: DISP-A1B2C3D4   │                                │
  │   Expected resolution │                                │
  │   within 15 days."    │                                │
  │◀──────────────────────│                                │
```

### Flow 4: Multilingual Support (Use Case 1.4)

```
CUSTOMER (Spanish)       AGENT (LLM + MCP)                 SYSTEMS
──────────────────       ─────────────────                 ───────

  │  "¿Cuánto dinero      │                                │
  │   tengo en mi cuenta?"│                                │
  │──────────────────────▶│                                │
  │                       │  1. MCP: detect_language()     │
  │                       │──────┐                         │
  │                       │◀─────┘                         │
  │                       │     → Spanish (es)             │
  │                       │                                │
  │                       │  2. MCP: get_balance()         │
  │                       │──────┐                         │
  │                       │      │  Core Banking API       │
  │                       │◀─────┘                         │
  │                       │     → $5,234.50                │
  │                       │                                │
  │                       │  3. MCP: translate(            │
  │                       │     "Your balance is $5,234.50│
  │                       │     ", "en", "es")            │
  │                       │──────┐                         │
  │                       │      │  Translation API        │
  │                       │◀─────┘                         │
  │                       │     → "Su saldo es $5,234.50" │
  │  "Su saldo es         │                                │
  │   $5,234.50"          │                                │
  │◀──────────────────────│                                │
```

### Flow 5: Complaint (Use Case 1.5)

```
CUSTOMER                  AGENT (LLM + RAG + MCP)          SYSTEMS
────────                  ─────────────────────             ───────

  │  "I waited 45 minutes  │                                │
  │   on hold and nobody   │                                │
  │   helped me!"          │                                │
  │──────────────────────▶│                                │
  │                       │  1. MCP: log_new_complaint()   │
  │                       │     → Auto-categorized:        │
  │                       │       service_quality           │
  │                       │     → Priority: medium         │
  │                       │──────┐                         │
  │                       │      │  CRM API                │
  │                       │◀─────┘                         │
  │                       │     → CMP-X1Y2Z3W4             │
  │                       │                                │
  │                       │  2. RAG: wait times solution   │
  │                       │──────┐                         │
  │                       │      │  Query Vector DB        │
  │                       │◀─────┘                         │
  │                       │     → Callback option          │
  │                       │     → Direct line              │
  │                       │                                │
  │  "I sincerely apologize│                               │
  │   for the wait. We     │                               │
  │   offer a callback     │                               │
  │   option..."           │                               │
  │◀──────────────────────│                                │
  │                       │                                │
  │                       │  3. MCP: notify(acknowledged)  │
  │                       │──────┐                         │
  │                       │      │  Notification API       │
  │                       │◀─────┘                         │
```

---

## MCP Tool Definitions

### 1.1 Banking FAQ

```jsonc
{
  "name": "search_knowledge_base",
  "description": "Search banking FAQ, product info, and policies using RAG",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "collection": { "type": "string", "enum": ["all", "banking_faq", "product_information", "fee_schedules", "dispute_policies", "complaint_history", "regulatory_guidelines", "resolution_playbooks"] },
      "top_k": { "type": "integer" }
    },
    "required": ["query"]
  }
}
```

### 1.2 Account Information

```jsonc
{
  "name": "get_balance",
  "description": "Get current account balance and status",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "account_number": { "type": "string" }
    },
    "required": ["customer_id"]
  }
}

{
  "name": "get_transactions",
  "description": "Get recent transactions with optional category filtering",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "days": { "type": "integer" },
      "category_filter": { "type": "string", "enum": ["groceries", "restaurants", "utilities", "transportation", "entertainment", "shopping", "income", "transfer"] },
      "limit": { "type": "integer" }
    },
    "required": ["customer_id"]
  }
}
```

### 1.3 Dispute Resolution

```jsonc
{
  "name": "file_new_dispute",
  "description": "File dispute for unauthorized/incorrect transaction",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "account_number": { "type": "string" },
      "transaction_date": { "type": "string" },
      "transaction_amount": { "type": "number" },
      "dispute_type": { "type": "string", "enum": ["unauthorized_transaction", "duplicate_charge", "incorrect_amount", "product_not_received", "billing_error"] },
      "description": { "type": "string" },
      "merchant_name": { "type": "string" }
    },
    "required": ["customer_id", "account_number", "transaction_date", "transaction_amount", "dispute_type", "description"]
  }
}
```

### 1.4 Multilingual Support

```jsonc
{
  "name": "detect_language_tool",
  "description": "Detect the language of customer input",
  "inputSchema": {
    "type": "object",
    "properties": { "text": { "type": "string" } },
    "required": ["text"]
  }
}

{
  "name": "translate",
  "description": "Translate text between languages",
  "inputSchema": {
    "type": "object",
    "properties": {
      "text": { "type": "string" },
      "source_language": { "type": "string" },
      "target_language": { "type": "string" }
    },
    "required": ["text", "source_language", "target_language"]
  }
}
```

### 1.5 Complaint Management

```jsonc
{
  "name": "log_new_complaint",
  "description": "Log and auto-categorize customer complaints",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "description": { "type": "string" },
      "channel": { "type": "string", "enum": ["chat", "phone", "email", "branch"] },
      "category_hint": { "type": "string" }
    },
    "required": ["customer_id", "description"]
  }
}
```

### Escalation & Notifications

```jsonc
{
  "name": "escalate_to_agent",
  "description": "Transfer to human agent with context",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customer_id": { "type": "string" },
      "reason": { "type": "string" },
      "channel": { "type": "string" },
      "priority": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
      "context_summary": { "type": "string" },
      "customer_sentiment": { "type": "string", "enum": ["positive", "neutral", "frustrated", "angry"] }
    },
    "required": ["customer_id", "reason"]
  }
}
```

---

## Vector Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR DB COLLECTIONS                        │
│                                                                 │
│  Collection: banking_faq                                        │
│  ─────────────────────                                          │
│  │  "How do I stop a payment? You can stop a pending..."  │    │
│  │  Metadata: {topic: "stop_payment", source: "FAQ"}      │    │
│                                                                 │
│  Collection: product_information                                │
│  ────────────────────────────                                   │
│  │  "Personal Checking: No monthly fee with $500+..."     │    │
│  │  Metadata: {product: "personal_checking"}               │    │
│                                                                 │
│  Collection: fee_schedules                                      │
│  ───────────────────────                                        │
│  │  "Overdraft: $35 per item, max 3/day..."               │    │
│  │  Metadata: {topic: "penalty_fees"}                      │    │
│                                                                 │
│  Collection: dispute_policies                                   │
│  ──────────────────────────                                     │
│  │  "Dispute Process: Customer contacts us within..."      │    │
│  │  Metadata: {topic: "dispute_process"}                   │    │
│                                                                 │
│  Collection: complaint_history                                  │
│  ────────────────────────                                       │
│  │  "Resolution: Billing Error — Customer charged twice..."│    │
│  │  Metadata: {category: "billing", outcome: "resolved"}  │    │
│                                                                 │
│  Collection: regulatory_guidelines                              │
│  ───────────────────────────────                                │
│  │  "Fair Credit Billing Act: Customers have the right..." │    │
│  │  Metadata: {source: "FCBA"}                             │    │
│                                                                 │
│  Collection: resolution_playbooks                               │
│  ────────────────────────────                                   │
│  │  "Dispute Playbook: Step 1: Acknowledge customer..."    │    │
│  │  Metadata: {scenario: "dispute"}                        │    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Intent Routing** | Simple vs Complex | FAQ queries skip LLM, go direct to RAG |
| **Auto-Categorization** | Keyword + ML | Complaints/disputes auto-categorized for routing |
| **Escalation Routing** | Queue-based | Priority-based routing to specialized agents |
| **Multilingual** | Detect → Translate → Respond | Support 8+ languages with seamless handoff |
| **Dispute SLA** | Amount-based | Higher amounts get faster resolution |
| **Provisional Credit** | >$500 disputes | Regulatory requirement for large disputes |
| **Complaint Follow-up** | 24-hour SLA | Every complaint acknowledged within 24 hours |
| **Knowledge Freshness** | RAG over static | Always current, no retraining needed |

---

## Use Case Coverage

| Use Case | Tools | RAG Collections | Status |
|----------|-------|-----------------|--------|
| **1.1 FAQ Agent** | `search_knowledge_base` | banking_faq, product_information, fee_schedules | ✅ |
| **1.2 Account Info** | `get_balance`, `get_transactions`, `get_statements` | product_information | ✅ |
| **1.3 Dispute Resolution** | `file_new_dispute`, `check_dispute_status`, `update_dispute_status` | dispute_policies, regulatory_guidelines | ✅ |
| **1.4 Multilingual** | `detect_language_tool`, `translate`, `get_languages` | — | ✅ |
| **1.5 Complaint Management** | `log_new_complaint`, `check_complaint`, `update_complaint_status` | complaint_history, resolution_playbooks | ✅ |
| **Escalation** | `escalate_to_agent`, `create_ticket`, `check_agent_availability` | resolution_playbooks | ✅ |
| **Notifications** | `notify` | — | ✅ |

---

*Architecture designed for Customer Service & Support Agent (All 5 use cases) — August 2026*
