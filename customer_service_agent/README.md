# Customer Service & Support Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for banking customer service & support, powered by **RAG** for knowledge retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

**Covers all 5 use cases from BANKING_USE_CASES.md Section 1:**
- 1.1 Intelligent Banking FAQ Agent
- 1.2 Account Information Agent
- 1.3 Dispute Resolution Agent
- 1.4 Multilingual Banking Support Agent
- 1.5 Complaint Management Agent

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                CUSTOMER SERVICE & SUPPORT AGENT                           │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  Customer │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Query    │    │  (ReAct     │◀───│  ├── search_knowledge_base      │ │
│  │           │◀───│   Agent)    │    │  ├── get_balance                │ │
│  │           │    │             │    │  ├── get_transactions           │ │
│  │           │    │  Options:   │    │  ├── file_new_dispute           │ │
│  │           │    │  • Ollama   │    │  ├── log_new_complaint          │ │
│  │           │    │  • vLLM     │    │  ├── detect_language_tool       │ │
│  │           │    │  • SGLang   │    │  ├── translate                  │ │
│  │           │    │             │    │  ├── escalate_to_agent          │ │
│  │           │    │             │    │  └── notify                     │ │
│  └──────────┘    └──────┬──────┘    └──────────────────────────────────┘ │
│                         │                                                │
│                         ▼                                                │
│                  ┌──────────────┐                                         │
│                  │  RAG Engine  │                                         │
│                  │  (ChromaDB)  │                                         │
│                  │  • Banking FAQ│                                        │
│                  │  • Products  │                                         │
│                  │  • Fees      │                                         │
│                  │  • Disputes  │                                         │
│                  │  • Complaints│                                         │
│                  │  • Regulations│                                       │
│                  │  • Playbooks │                                         │
│                  └──────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed (20 Tools)

### 1.1 Banking FAQ
| Tool | Description |
|------|-------------|
| `search_knowledge_base` | RAG search over FAQ, products, policies |

### 1.2 Account Information
| Tool | Description |
|------|-------------|
| `get_balance` | Current balance and account status |
| `get_transactions` | Recent transactions with category filtering |
| `get_statements` | Available account statements |

### 1.3 Dispute Resolution
| Tool | Description |
|------|-------------|
| `file_new_dispute` | File dispute for unauthorized/incorrect transaction |
| `check_dispute_status` | Get dispute status and timeline |
| `update_dispute_status` | Update dispute with notes/resolution |
| `get_dispute_types_list` | Available dispute categories |

### 1.4 Multilingual Support
| Tool | Description |
|------|-------------|
| `detect_language_tool` | Detect customer's language |
| `translate` | Translate between languages |
| `get_languages` | List supported languages |

### 1.5 Complaint Management
| Tool | Description |
|------|-------------|
| `log_new_complaint` | Log and auto-categorize complaints |
| `check_complaint` | Get complaint details |
| `update_complaint_status` | Update complaint status/assignment |
| `get_complaint_types` | Available complaint categories |

### Escalation & Notifications
| Tool | Description |
|------|-------------|
| `escalate_to_agent` | Transfer to human agent |
| `create_ticket` | Create support ticket for follow-up |
| `check_agent_availability` | Check available agents |
| `notify` | Send email/SMS notifications |

## Customer Interaction Flows

### FAQ Flow (1.1)
```
Customer: "How do I stop a payment?"
    │
    ├── 1. detect_language_tool("How do I stop a payment?")
    │
    ├── 2. search_knowledge_base("stop payment")
    │
    └── 3. Respond with step-by-step instructions
```

### Account Inquiry Flow (1.2)
```
Customer: "How much did I spend on groceries last month?"
    │
    ├── 1. get_balance(customer_id)
    │
    ├── 2. get_transactions(customer_id, days=30, category_filter="groceries")
    │
    └── 3. Summarize spending by category
```

### Dispute Flow (1.3)
```
Customer: "I was charged twice for the same purchase"
    │
    ├── 1. search_knowledge_base("dispute process")
    │
    ├── 2. get_dispute_types_list()
    │
    ├── 3. file_new_dispute(customer_id, account, date, amount, "duplicate_charge", desc)
    │
    ├── 4. notify(customer_id, "dispute_filed")
    │
    └── 5. Explain timeline and next steps
```

### Multilingual Flow (1.4)
```
Customer (Spanish): "¿Cuánto dinero tengo en mi cuenta?"
    │
    ├── 1. detect_language_tool("¿Cuánto dinero tengo en mi cuenta?") → Spanish
    │
    ├── 2. get_balance(customer_id)
    │
    ├── 3. translate("Your balance is $5,234.50", "en", "es")
    │
    └── 4. Respond in Spanish
```

### Complaint Flow (1.5)
```
Customer: "I waited 45 minutes on hold and nobody helped me"
    │
    ├── 1. log_new_complaint(customer_id, description, "phone")
    │   → Auto-categorized: service_quality, priority: medium
    │
    ├── 2. search_knowledge_base("wait times callback")
    │
    ├── 3. Offer callback option / direct line
    │
    └── 4. notify(customer_id, "complaint_acknowledged")
```

## Quick Start

```bash
cd customer_service_agent
pip install -r requirements.txt
python seed_knowledge.py

# Start an LLM backend
ollama serve

# Run the agent
python -m llm.agent_ollama
```

## Project Structure

```
customer_service_agent/
├── server.py              # MCP server (20 tools)
├── rag_pipeline.py        # RAG engine (7 collections)
├── config.py              # Settings
├── seed_knowledge.py      # Seed 30+ documents
├── compare_agents.py      # Compare LLM backends
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py      # Base agent with production patterns
│   ├── agent_ollama.py
│   ├── agent_vllm.py
│   └── agent_sglang.py
└── tools/
    ├── __init__.py
    ├── account_info.py           # Balance, transactions, statements
    ├── dispute_management.py     # File, track, update disputes
    ├── complaint_management.py   # Log, categorize, resolve complaints
    ├── escalation.py             # Human agent handoff, tickets
    ├── translation.py            # Language detection, translation
    └── notifications.py          # Email, SMS notifications
```

## Knowledge Base (7 Collections)

| Collection | Content | Documents |
|------------|---------|-----------|
| `banking_faq` | Common questions and answers | 8 |
| `product_information` | Account types, features, eligibility | 7 |
| `fee_schedules` | Account, transaction, penalty fees | 3 |
| `dispute_policies` | Process, timelines, requirements | 3 |
| `complaint_history` | Past resolutions and precedents | 4 |
| `regulatory_guidelines` | FCBA, EFTA, TISA, GLBA | 4 |
| `resolution_playbooks` | Step-by-step resolution guides | 3 |

## Production Patterns

Same as KYC & Loan agents — see `llm/base_agent.py`:

| Pattern | Class |
|---------|-------|
| Intent Routing | `IntentRouter` |
| Guardrails | `Guardrails` |
| Human-in-the-Loop | `HumanApprovalManager` |
| Memory Management | `ConversationMemory` |
| Error Handling | `ErrorHandler` |
| Observability | `AgentTracer` |

## LLM Backends

| Backend | Best For | Speed |
|---------|----------|-------|
| **Ollama** | Local dev | ~2-5s |
| **vLLM** | Production | ~0.5-2s |
| **SGLang** | Structured output | ~0.3-1.5s |

## Notes

- Tool stubs return deterministic results — swap for real APIs in production
- Dispute filing has automatic priority assignment based on amount and type
- Complaint categorization uses keyword matching — production uses ML classification
- Translation stub returns placeholder — integrate DeepL/Google Translate for real use
- Escalation routing is queue-based — production integrates with contact center platforms
