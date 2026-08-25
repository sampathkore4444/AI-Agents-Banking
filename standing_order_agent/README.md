# Standing Order & Bill Payment Agent

A banking AI agent that helps customers set up, modify, and cancel recurring payments and bill pay schedules using MCP tools, RAG, and embeddings.

## Overview

This agent implements **Section 7.4** of the banking AI use cases:
> *Helps customers set up, modify, or cancel recurring payments and bill pay schedules.*

### Capabilities

| Capability | Technique |
|---|---|
| **Recurring Payment Management** | MCP Tools — CRUD for standing orders |
| **Biller Directory** | MCP Tools — Search, verify, and manage billers |
| **Payment Scheduling** | MCP Tools — Calendar integration, execution, retry logic |
| **Natural Language Understanding** | Embeddings — Parse "Pay my rent on the 1st" into structured API calls |
| **Policy Retrieval** | RAG — Standing order policies, limits, compliance rules |
| **Payment Reminders** | MCP Tools — Multi-channel notifications |
| **Pattern Detection** | Embeddings — Detect recurring payment patterns from history |
| **Regulatory Compliance** | RAG — Reg E, NACHA, UDAAP requirements |

## Architecture

```
standing_order_agent/
├── server.py                    # MCP server with 40+ tools
├── rag_pipeline.py              # RAG engine (7 collections)
├── config.py                    # Settings
├── seed_knowledge.py            # 34 standing order documents
├── compare_agents.py            # Compare Ollama/vLLM/SGLang
├── requirements.txt
├── README.md
├── BANKING_USE_CASES_STANDING_ORDER_ARCHITECTURE.md
├── llm/
│   ├── base_agent.py            # Guardrails, HITL, memory, streaming
│   ├── agent_ollama.py          # Ollama
│   ├── agent_vllm.py            # vLLM
│   └── agent_sglang.py          # SGLang
└── tools/
    ├── standing_order_management.py  # CRUD for standing orders
    ├── biller_directory.py           # Biller search and verification
    ├── payment_scheduling.py         # Execution, retry, calendar
    ├── calendar_api.py               # Reminders and notifications
    ├── notifications.py              # Multi-channel alerts
    ├── customer_profile.py           # Customer billing profiles
    └── payment_embedding.py          # Intent parsing, pattern detection
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the knowledge base
python seed_knowledge.py

# Run the MCP server
python server.py
```

## MCP Tools (40+)

### Standing Order Management
- `create_order` — Create a new standing order
- `get_order` — Get standing order details
- `update_order` — Modify amount, frequency, payee, dates
- `cancel_order` — Cancel a standing order
- `pause_order` — Pause temporarily
- `resume_order` — Resume a paused order
- `list_orders` — List with filters
- `upcoming_payments` — Payments due in N days
- `order_statistics` — Standing order stats

### Biller Directory
- `search_biller` — Fuzzy search by name/category
- `get_biller_details` — Full biller info
- `verify_biller_tool` — Verify for customer account
- `add_biller_tool` — Add new biller
- `biller_categories` — List categories
- `list_billers` — Billers in category

### Payment Scheduling
- `execution_calendar` — Calendar view of upcoming payments
- `payment_dates` — Calculate future payment dates
- `process_payment` — Process a scheduled payment
- `retry_payment` — Retry failed payment
- `payment_history_tool` — Execution history
- `holiday_calendar` — Fed holiday calendar

### Calendar & Reminders
- `create_reminder` — Set up payment reminders
- `reminders` — View reminders
- `calendar_event` — Create calendar event
- `calendar_events` — View events

### Notifications
- `notify_setup` — Standing order confirmation
- `notify_modification` — Change notice
- `notify_cancellation` — Cancellation notice
- `notify_payment_failed` — Failed payment alert
- `notify_suspension` — Suspension notice
- `notify_amount_change` — Biller amount change alert
- `daily_summary_tool` — Daily activity summary
- `notification_log` — Notification history

### Customer Profile
- `customer_profile` — Full customer info
- `customer_accounts` — Customer accounts
- `search_customer` — Search customers
- `billing_summary` — Billing overview
- `account_balance` — Balance check

### Payment Embeddings (ML)
- `parse_intent` — Natural language → structured intent
- `embed_pattern` — Create payment pattern embedding
- `match_patterns` — Match against known patterns
- `detect_patterns` — Detect recurring patterns from history

### Knowledge Retrieval
- `knowledge_search` — Search standing order knowledge base

## Knowledge Base (7 Collections)

| Collection | Documents | Content |
|---|---|---|
| standing_order_policies | 5 | Creation, modification, cancellation, execution, limits |
| biller_directory | 7 | Utilities, mortgage, insurance, subscriptions, loans, telecom, government |
| payment_schedules | 6 | Daily, weekly, monthly, quarterly, annual, custom rules |
| recurring_payment_rules | 5 | Amount, account, payee, timing, failure handling |
| compliance_requirements | 4 | Reg E, NACHA, UDAAP, BSA/AML |
| customer_billing_knowledge | 5 | Rent, utility, subscription, savings, troubleshooting scenarios |
| operational_playbooks | 4 | Creation, modification, failure resolution, dispute workflows |

## LLM Backends

| Backend | Model | Use Case |
|---|---|---|
| **Ollama** | llama3.1:8b | Development, local testing |
| **vLLM** | Llama-3.1-8B-Instruct | Production, high throughput |
| **SGLang** | Llama-3.1-8B-Instruct | Structured output, batch processing |

## Agent Patterns

- **Guardrails** — Amount limits ($50K single, $100K daily), approval thresholds ($10K review, $25K approval), frequency validation
- **Human-in-the-Loop** — Approval for high-value creates, large amount changes, payee changes
- **Memory** — Billing context retention, customer conversation history
- **Streaming** — Real-time status updates for payment processing

## Compliance

- **Reg E** — Consumer protection for electronic fund transfers, stop payment rights
- **NACHA** — ACH authorization requirements, return timeframes
- **UDAAP** — Fair treatment, clear disclosures, easy cancellation
- **BSA/AML** — Structuring detection, SAR filing for suspicious recurring patterns
