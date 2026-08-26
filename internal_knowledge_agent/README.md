# Internal Knowledge Base Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for internal banking knowledge management, powered by a **RAG pipeline** for knowledge retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

**Covers use case 8.1: Internal Knowledge Base Agent (Bank-wide)** — allows employees to query internal knowledge in natural language.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  INTERNAL KNOWLEDGE BASE AGENT                              │
│                                                                             │
│  ┌──────────┐    ┌─────────────┐    ┌────────────────────────────────────┐ │
│  │ Employee │───▶│  LLM Core   │───▶│  MCP Tool Server                  │ │
│  │  Query   │    │  (ReAct     │◀───│  ├── knowledge_search             │ │
│  │          │◀───│   Agent)    │    │  ├── search_documents             │ │
│  │          │    │             │    │  ├── create_ticket                │ │
│  │          │    │  Options:   │    │  ├── lookup_employee              │ │
│  │          │    │  • Ollama   │    │  ├── check_system_status          │ │
│  │          │    │  • vLLM     │    │  ├── search_known_issues          │ │
│  │          │    │  • SGLang   │    │  ├── get_leave_balance            │ │
│  │          │    │             │    │  ├── get_benefits_info            │ │
│  └──────────┘    └──────┬──────┘    │  └── send_notification            │ │
│                         │           └────────────────────────────────────┘ │
│                         ▼                                                   │
│                  ┌──────────────┐                                           │
│                  │  RAG Engine  │                                           │
│                  │  (ChromaDB)  │                                           │
│                  │  • Products  │                                           │
│                  │  • SOPs      │                                           │
│                  │  • IT Help   │                                           │
│                  │  • HR Policy │                                           │
│                  │  • Compliance│                                           │
│                  │  • Processes │                                           │
│                  │  • Regulatory│                                           │
│                  │  • FAQ       │                                           │
│                  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed

### Knowledge Search

| Tool | Description |
|------|-------------|
| `knowledge_search` | RAG search across all 8 knowledge collections |

### Document Management

| Tool | Description |
|------|-------------|
| `search_internal_documents` | Search documents by keyword |
| `get_internal_document` | Get a specific document by ID |
| `list_internal_documents` | List all documents with filters |

### Ticketing (ServiceNow)

| Tool | Description |
|------|-------------|
| `create_support_ticket` | Create a new support ticket |
| `search_support_tickets` | Search tickets by keyword/filters |
| `get_ticket_details` | Get ticket details |
| `update_support_ticket` | Update ticket status/assignment |
| `get_ticket_statistics` | Get ticket counts |

### HR System (Workday)

| Tool | Description |
|------|-------------|
| `lookup_employee_info` | Look up employee by ID/name |
| `get_employee_leave_balance` | Get leave balances |
| `get_employee_benefits` | Get benefits enrollment info |
| `get_organization_chart` | Get org chart |

### ITSM

| Tool | Description |
|------|-------------|
| `check_system_status` | Check system status/uptime |
| `search_known_issues` | Search known IT issues |
| `get_troubleshooting_steps` | Get troubleshooting guide |

### Notifications

| Tool | Description |
|------|-------------|
| `send_employee_notification` | Send email/Slack/Teams notification |

## Knowledge Base (8 Collections)

| Collection | Content | Example Query |
|------------|---------|---------------|
| `product_details` | Savings, checking, credit cards, loans, mortgages | "What's the interest rate on savings?" |
| `standard_operating_procedures` | Account opening, dispute resolution, wire transfers | "How do I open a business account?" |
| `it_help_and_support` | Password reset, VPN, email, hardware, outages | "My VPN keeps disconnecting" |
| `hr_policies_and_benefits` | Leave, benefits, remote work, conduct, training | "How many vacation days do I get?" |
| `compliance_training` | AML red flags, fair lending, data privacy | "What are AML red flags?" |
| `process_guides` | Loan approval workflow, CRM entry, incident reporting | "What's the loan approval process?" |
| `regulatory_updates` | TRID, BSA/AML, FinCEN updates | "Any new compliance regulations?" |
| `faq_and_common_questions` | Hours, routing number, overdraft, fraud reporting | "What's the routing number?" |

## Quick Start

### 1. Install dependencies
```bash
cd internal_knowledge_agent
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Seed the knowledge base
```bash
python seed_knowledge.py
```

### 4. Start an LLM backend
```bash
# Option A: Ollama
ollama pull llama3.1:8b
ollama serve

# Option B: vLLM
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000

# Option C: SGLang
python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 30000
```

### 5. Run the agent
```bash
python -m llm.agent_ollama
python -m llm.agent_vllm
python -m llm.agent_sglang
python compare_agents.py
```

### 6. Or use MCP server mode
```bash
python server.py
```

## Project Structure

```
internal_knowledge_agent/
├── server.py                  # MCP server - 20 tool definitions
├── rag_pipeline.py            # RAG engine - ChromaDB + 8 collections
├── config.py                  # Settings from environment variables
├── seed_knowledge.py          # Seed script (40+ documents)
├── compare_agents.py          # Compare LLM backends
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
├── BANKING_USE_CASES_INTERNAL_KNOWLEDGE_ARCHITECTURE.md
├── llm/
│   ├── base_agent.py          # Base agent - ReAct loop, tools, guardrails
│   ├── agent_ollama.py        # Ollama backend
│   ├── agent_vllm.py          # vLLM backend
│   └── agent_sglang.py        # SGLang backend
└── tools/
    ├── document_management.py  # Document search and retrieval
    ├── ticketing_system.py     # ServiceNow ticket management
    ├── hr_system.py            # HR/employee queries
    ├── itsm.py                 # IT status and troubleshooting
    └── notifications.py        # Internal notifications
```

## Example Queries

| Employee Asks | Agent Does |
|---------------|-----------|
| "What's the interest rate on savings?" | Searches `product_details` collection |
| "How do I open a business account?" | Retrieves SOP from `standard_operating_procedures` |
| "My VPN keeps disconnecting" | Searches `it_help_and_support` + known issues |
| "How many vacation days do I have?" | Looks up employee + `hr_policies_and_benefits` |
| "What are the AML red flags?" | Retrieves from `compliance_training` |
| "Create a ticket for my laptop issue" | Creates ticket in ticketing system |
| "What's the bank's routing number?" | Retrieves from `faq_and_common_questions` |
| "Is the online banking system down?" | Checks system status via ITSM |

## Production Patterns

| # | Pattern | Class | Purpose |
|---|---------|-------|---------|
| 1 | Intent Routing | `IntentRouter` | Routes simple queries to RAG (no LLM) |
| 2 | Guardrails | `Guardrails` | Risk-based tool access control |
| 3 | Human-in-the-Loop | `HumanApprovalManager` | Pauses for high-risk actions |
| 4 | Memory Management | `ConversationMemory` | Token-aware conversation history |
| 5 | Error Handling | `ErrorHandler` | Retry with backoff |
| 6 | Observability | `AgentTracer` | Structured traces for every operation |

## Notes

- The RAG pipeline uses `all-MiniLM-L6-v2` embeddings — upgrade for production
- ChromaDB is ephemeral in development — use a hosted instance for persistence
- All tool calls are logged for audit trail compliance
- Without external API credentials, tools return simulated data
