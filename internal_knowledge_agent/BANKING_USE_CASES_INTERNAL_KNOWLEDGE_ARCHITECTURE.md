# Internal Knowledge Base Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Internal Knowledge Base Agent that uses **RAG** for knowledge retrieval and **MCP** for tool orchestration across document management, ticketing, HR, and IT systems.
>
> **Covers use case 8.1: Internal Knowledge Base Agent (Bank-wide).**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  INTERNAL KNOWLEDGE BASE AGENT                              │
│                                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────────────────────────┐  │
│  │           │    │              │    │       MCP Tool Server            │  │
│  │ Employee  │───▶│   LLM Core   │◀──▶│  ┌────────────┐ ┌───────────┐  │  │
│  │   Chat    │    │  (GPT-4o /   │    │  │ Knowledge  │ │ Document  │  │  │
│  │ Interface │◀───│  Claude /    │    │  │ Search     │ │ Management│  │  │
│  │           │    │  Gemini)     │    │  └────────────┘ └───────────┘  │  │
│  └───────────┘    └──────┬───────┘    │  ┌────────────┐ ┌───────────┐  │  │
│                          │             │  │ Ticketing  │ │ HR System │  │  │
│                          │             │  │ (ServiceNow│ │ (Workday) │  │  │
│                          ▼             │  └────────────┘ └───────────┘  │  │
│                   ┌──────────────┐     │  ┌────────────┐ ┌───────────┐  │  │
│                   │              │     │  │ ITSM       │ │ Notify    │  │  │
│                   │   RAG Engine │     │  │ (Status,   │ │ (Email,   │  │  │
│                   │              │     │  │  Issues)   │ │  Slack)   │  │  │
│                   │  ┌────────┐  │     │  └────────────┘ └───────────┘  │  │
│                   │  │Query   │  │     └──────────────────────────────────┘  │
│                   │  │Rewrite │  │                                          │
│                   │  └───┬────┘  │     ┌──────────────────────────────────┐  │
│                   │      │       │     │       External APIs              │  │
│                   │      ▼       │     │  ┌───────────┐ ┌───────────┐    │  │
│                   │  ┌────────┐  │     │  │ Document  │ │ ServiceNow│    │  │
│                   │  │Hybrid  │  │     │  │ Management│ │ Ticketing │    │  │
│                   │  │Search  │  │     │  └───────────┘ └───────────┘    │  │
│                   │  └───┬────┘  │     │  ┌───────────┐ ┌───────────┐    │  │
│                   │      │       │     │  │ Workday   │ │ ITSM      │    │  │
│                   │      ▼       │     │  │ HR System │ │ System    │    │  │
│                   │  ┌────────┐  │     │  └───────────┘ └───────────┘    │  │
│                   │  │Re-rank │  │     │  ┌───────────┐                  │  │
│                   │  └───┬────┘  │     │  │ Notificatn│                  │  │
│                   └──────┼───────┘     │  │ Service   │                  │  │
│                          │             │  └───────────┘                  │  │
└──────────────────────────┼─────────────┴──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     Vector Database     │
              │                        │
              │  ┌──────────────────┐  │
              │  │  Product Details │  │
              │  ├──────────────────┤  │
              │  │  SOPs            │  │
              │  ├──────────────────┤  │
              │  │  IT Help         │  │
              │  ├──────────────────┤  │
              │  │  HR Policies     │  │
              │  ├──────────────────┤  │
              │  │  Compliance      │  │
              │  ├──────────────────┤  │
              │  │  Process Guides  │  │
              │  ├──────────────────┤  │
              │  │  Regulatory      │  │
              │  ├──────────────────┤  │
              │  │  FAQ             │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

---

## Detailed Component Flow

### Employee Knowledge Query Journey

```
EMPLOYEE                 AGENT (LLM + RAG + MCP)              EXTERNAL SYSTEMS
────────                 ────────────────────────              ─────────────────

  │                              │                                    │
  │  1. "What's the interest    │                                    │
  │      rate on savings?"       │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  2. Intent: SIMPLE                 │
  │                              │     RAG: Search product_details    │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → High-Yield: 5.25% APY       │
  │                              │     → Standard: 4.10% APY          │
  │                              │                                    │
  │  3. "Standard Savings:      │                                    │
  │      4.10% APY up to        │                                    │
  │      $10K. High-Yield:      │                                    │
  │      5.25% APY. No monthly  │                                    │
  │      fee on High-Yield."    │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │

═══════════════════════════════ IT SUPPORT QUERY ══════════════════════════════

  │                              │                                    │
  │  4. "My VPN keeps            │                                    │
  │      disconnecting"          │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  5. Intent: COMPLEX                │
  │                              │     RAG: Search it_help_and_support│
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → VPN troubleshooting guide   │
  │                              │                                    │
  │                              │  6. MCP: Search known issues       │
  │                              │──────┐                             │
  │                              │      │  Search ISS-002             │
  │                              │◀─────┘                             │
  │                              │     → Known issue: VPN drops       │
  │                              │     → Workaround: US-WEST-1        │
  │                              │                                    │
  │  7. "There's a known issue  │                                    │
  │      with VPN (ISS-002).    │                                    │
  │      Try switching to       │                                    │
  │      US-WEST-1 server.      │                                    │
  │      Would you like me to   │                                    │
  │      create a ticket?"      │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │  8. "Yes, please create     │                                    │
  │      a ticket"               │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  9. MCP: Create ticket             │
  │                              │──────┐                             │
  │                              │      │  POST /tickets/create      │
  │                              │      │  (ServiceNow API)          │
  │                              │◀─────┘                             │
  │                              │     → TKT-A1B2C3 created          │
  │                              │                                    │
  │  10. "Ticket TKT-A1B2C3     │                                    │
  │       created. IT will      │                                    │
  │       follow up within      │                                    │
  │       24 hours."            │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │

═══════════════════════════════ HR QUERY ══════════════════════════════════════

  │                              │                                    │
  │  11. "How many vacation     │                                    │
  │       days do I have?"       │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  12. MCP: Lookup employee          │
  │                              │──────┐                             │
  │                              │      │  GET /employees/EMP-1234   │
  │                              │      │  (Workday API)             │
  │                              │◀─────┘                             │
  │                              │     → Employee: Sarah Johnson      │
  │                              │     → Hire date: 2018 (6 years)   │
  │                              │     → Annual leave: 22 days       │
  │                              │                                    │
  │                              │  13. MCP: Get leave balance        │
  │                              │──────┐                             │
  │                              │◀─────┘                             │
  │                              │     → Available: 22 days          │
  │                              │                                    │
  │  14. "Hi Sarah! With 6      │                                    │
  │       years of service,     │                                    │
  │       you have 22 annual    │                                    │
  │       leave days. Current   │                                    │
  │       balance: 22 days."    │                                    │
  │◀─────────────────────────────│                                    │
```

---

## MCP Tool Definitions

```jsonc
// mcp-server-knowledge-base.json
{
  "mcpServers": {
    "internal-knowledge-base": {
      "description": "Internal Knowledge Base MCP Server",
      "tools": [
        {
          "name": "knowledge_search",
          "description": "Search internal knowledge base (products, SOPs, IT, HR, compliance)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "query": { "type": "string" },
              "collection": { "type": "string", "enum": ["all", "product_details", "standard_operating_procedures", "it_help_and_support", "hr_policies_and_benefits", "compliance_training", "process_guides", "regulatory_updates", "faq_and_common_questions"] },
              "top_k": { "type": "integer", "default": 5 }
            },
            "required": ["query"]
          }
        },
        {
          "name": "search_internal_documents",
          "description": "Search internal documents by keyword",
          "inputSchema": {
            "type": "object",
            "properties": { "query": { "type": "string" }, "category": { "type": "string" }, "max_results": { "type": "integer" } },
            "required": ["query"]
          }
        },
        {
          "name": "create_support_ticket",
          "description": "Create a new support ticket (IT, HR, facilities)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "title": { "type": "string" },
              "description": { "type": "string" },
              "category": { "type": "string", "enum": ["IT Support", "Hardware", "HR", "Facilities", "Security"] },
              "priority": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
              "employee_id": { "type": "string" }
            },
            "required": ["title", "description", "category"]
          }
        },
        {
          "name": "lookup_employee_info",
          "description": "Look up employee by ID, name, or email",
          "inputSchema": {
            "type": "object",
            "properties": { "identifier": { "type": "string" } },
            "required": ["identifier"]
          }
        },
        {
          "name": "get_employee_leave_balance",
          "description": "Get employee's current leave balances",
          "inputSchema": {
            "type": "object",
            "properties": { "employee_id": { "type": "string" } },
            "required": ["employee_id"]
          }
        },
        {
          "name": "check_system_status",
          "description": "Check status of banking systems",
          "inputSchema": {
            "type": "object",
            "properties": { "system_name": { "type": "string" } }
          }
        },
        {
          "name": "search_known_issues",
          "description": "Search known IT issues and workarounds",
          "inputSchema": {
            "type": "object",
            "properties": { "query": { "type": "string" }, "severity": { "type": "string" } },
            "required": ["query"]
          }
        },
        {
          "name": "send_employee_notification",
          "description": "Send internal notification (email, Slack, Teams)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "recipient_id": { "type": "string" },
              "channel": { "type": "string", "enum": ["email", "slack", "teams"] },
              "template_id": { "type": "string" },
              "variables": { "type": "object" }
            },
            "required": ["recipient_id", "channel", "template_id"]
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
│  │  Employee    │  "How many vacation days do I get?"           │
│  │  Query       │                                              │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 1. QUERY    │  Rewrites: "HR policy annual leave accrual    │
│  │   REWRITE   │   employee vacation days service years"        │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                   │
│  │ 2. HYBRID SEARCH                         │                   │
│  │  BM25 (keyword) + Semantic (embedding)   │                   │
│  │  Searches all 8 collections              │                   │
│  └──────┬───────────────────────────────────┘                   │
│         │                                                       │
│         ▼                                                       │
│  ┌────────────────┐                                             │
│  │ 3. RE-RANKING  │  Score-based re-ranking → top 5             │
│  └───────┬────────┘                                             │
│          │                                                      │
│          ▼                                                      │
│  ┌────────────────┐                                             │
│  │ 4. CONTEXT     │  Assembles: HR policy excerpt +             │
│  │   ASSEMBLY     │  leave accrual rules + FAQ                  │
│  └───────┬────────┘                                             │
│          │                                                      │
│          ▼                                                      │
│  ┌────────────────┐                                             │
│  │ 5. ANSWER      │  "With 6 years, you accrue 20 days/year"   │
│  └───────┬────────┘                                             │
│          │                                                      │
│          ▼                                                      │
│  ┌────────────────┐                                             │
│  │ 6. CITATION    │  Source: HR Department, Policy v2024-Q3     │
│  └────────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Vector Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR DB COLLECTIONS                        │
│                                                                 │
│  Collection: product_details                                    │
│  Content: Savings, checking, credit cards, loans, mortgages     │
│  Documents: 9 products with rates, fees, eligibility            │
│                                                                 │
│  Collection: standard_operating_procedures                      │
│  Content: Account opening, dispute resolution, wire transfers   │
│  Documents: 5 SOPs with step-by-step procedures                 │
│                                                                 │
│  Collection: it_help_and_support                                │
│  Content: Password reset, VPN, email, hardware, outages         │
│  Documents: 5 help articles with troubleshooting steps          │
│                                                                 │
│  Collection: hr_policies_and_benefits                           │
│  Content: Leave, benefits, remote work, conduct, training       │
│  Documents: 5 policy documents with detailed rules              │
│                                                                 │
│  Collection: compliance_training                                │
│  Content: AML red flags, fair lending, data privacy             │
│  Documents: 3 training materials with requirements              │
│                                                                 │
│  Collection: process_guides                                     │
│  Content: Loan approval, CRM entry, incident reporting          │
│  Documents: 3 process guides with SLAs                          │
│                                                                 │
│  Collection: regulatory_updates                                 │
│  Content: TRID, BSA/AML, FinCEN updates                         │
│  Documents: 2 regulatory alerts with deadlines                  │
│                                                                 │
│  Collection: faq_and_common_questions                           │
│  Content: Hours, routing number, overdraft, fraud reporting     │
│  Documents: 4 FAQs with answers                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **8 Knowledge Collections** | Domain-separated | Products, SOPs, IT, HR, Compliance, Processes, Regulatory, FAQ — each with different access patterns |
| **Hybrid Search** | BM25 + Semantic | Keyword for exact policy numbers; semantic for paraphrased employee queries |
| **MCP Protocol** | Standardized tools | Swap ServiceNow for Jira, Workday for SAP without changing agent logic |
| **Simple → RAG Only** | No LLM for simple queries | "What's the routing number?" doesn't need LLM — direct RAG is faster and cheaper |
| **Ticket Creation** | Low-risk (auto-execute) | Creating a ticket is safe — no approval needed |
| **Audit Trail** | Every tool call logged | Banking regulators require traceability of internal knowledge access |
| **Citations** | Always included | Employees need to verify information against source policies |

---

*Architecture designed for Internal Knowledge Base Agent (Use Case 8.1) — August 2026*
