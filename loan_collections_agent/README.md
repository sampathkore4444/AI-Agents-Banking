# Loan Collections Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for loan collections in banking, powered by a **RAG pipeline** for regulatory knowledge retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

**Covers all 3.3 Loan Collections Agent capabilities.**

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                      LOAN COLLECTIONS AGENT                               │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  User     │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Query    │    │  (ReAct     │◀───│  ├── knowledge_search           │ │
│  │           │◀───│   Agent)    │    │  ├── get_account                │ │
│  │           │    │             │    │  ├── recommend_strategy         │ │
│  │           │    │  Options:   │    │  ├── create_plan                │ │
│  │           │    │  • Ollama   │    │  ├── offer_settlement           │ │
│  │           │    │  • vLLM     │    │  ├── check_compliance           │ │
│  │           │    │  • SGLang   │    │  ├── embed_profile              │ │
│  │           │    │             │    │  ├── notify_borrower            │ │
│  │           │    │             │    │  ├── process_collections_payment│ │
│  │           │    │             │    │  └── ... (25+ tools)            │ │
│  └──────────┘    └──────┬──────┘    └──────────────────────────────────┘ │
│                         │                                                │
│                         ▼                                                │
│                  ┌──────────────┐                                         │
│                  │  RAG Engine  │                                         │
│                  │  (ChromaDB)  │                                         │
│                  │  • FDCPA     │                                         │
│                  │  • Strategies│                                         │
│                  │  • Negotiation│                                        │
│                  │  • Compliance│                                         │
│                  │  • Past Cases│                                         │
│                  │  • Hardship  │                                         │
│                  └──────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed

### Account Management
| Tool | Description |
|------|-------------|
| `get_account` | Look up a delinquent account by ID |
| `search_account_by_borrower` | Find all accounts for a borrower |
| `get_portfolio` | Get summary of delinquent portfolio |
| `update_account` | Update account status, stage, or hardship flag |

### Collections Strategy
| Tool | Description |
|------|-------------|
| `recommend_collection_strategy` | Recommend optimal strategy based on debtor profile |
| `embed_profile` | ML embedding of debtor profile for clustering |

### Payment Scheduling
| Tool | Description |
|------|-------------|
| `create_plan` | Create payment plan (standard, graduated, hardship, etc.) |
| `get_plan` | Get payment plan details |
| `make_payment` | Record payment against a plan |
| `restructure_plan` | Modify existing payment plan |
| `offer_settlement` | Create settlement offer |
| `check_program_eligibility` | Check eligibility for programs |

### Compliance
| Tool | Description |
|------|-------------|
| `check_compliance` | Validate contact action against FDCPA/TCPA/state laws |
| `check_disclosure` | Check required disclosure compliance |
| `log_action` | Log collection action for audit trail |
| `compliance_report` | Generate compliance report |

### Phone Calls
| Tool | Description |
|------|-------------|
| `start_call` | Initiate outbound call with FDCPA-compliant script |
| `log_call_outcome` | Record call result (promised_to_pay, disputed_debt, etc.) |
| `schedule_call` | Schedule follow-up callback |
| `get_call_log` | Get call history for an account |
| `get_callbacks` | Get scheduled callbacks |
| `drop_voicemail` | Leave FDCPA-compliant voicemail |
| `call_stats` | Get call statistics and KPIs |

### Notifications
| Tool | Description |
|------|-------------|
| `notify_borrower` | Send FDCPA-compliant notification |
| `send_validation_not` | Send FDCPA-required validation notice |
| `send_demand` | Send formal demand letter |

### Payments
| Tool | Description |
|------|-------------|
| `process_collections_payment` | Process payment for collections account |
| `enable_autopay` | Set up automatic payments |
| `get_payments` | Get payment history |

### Knowledge
| Tool | Description |
|------|-------------|
| `knowledge_search` | RAG search over FDCPA, strategies, compliance |

## Collections Flow

```
Borrower: "My mortgage is 45 days late and I just lost my job"
    │
    ├── 1. get_account(account_id)
    │
    ├── 2. knowledge_search("FDCPA mortgage forbearance requirements")
    │
    ├── 3. recommend_collection_strategy(...)
    │
    ├── 4. check_program_eligibility(account_id, "forbearance")
    │
    ├── 5. check_compliance(account_id, "phone", ...)
    │
    ├── 6. embed_profile(account_id, ...)  ← ML strategy matching
    │
    ├── 7. notify_borrower(account_id, "hardship_inquiry", "email")
    │
    ├── 8. create_plan(account_id, "hardship", 950, 6)  ← interest-only
    │
    ├── 9. log_action(account_id, "forbearance_enrolled", ...)
    │
    └── 10. notify_borrower(account_id, "forbearance_approved", "mail")
```

## Quick Start

```bash
cd loan_collections_agent
pip install -r requirements.txt
python seed_knowledge.py

# Start an LLM backend
ollama serve  # or vllm serve / sglang

# Run the agent
python -m llm.agent_ollama
```

## Project Structure

```
loan_collections_agent/
├── server.py              # MCP server with 25+ tools
├── rag_pipeline.py        # RAG engine (7 collections)
├── config.py              # Settings
├── seed_knowledge.py      # Seed collections knowledge (30+ docs)
├── compare_agents.py      # Compare LLM backends
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py      # Base agent with production patterns
│   ├── agent_ollama.py    # Ollama
│   ├── agent_vllm.py      # vLLM
│   └── agent_sglang.py    # SGLang
└── tools/
    ├── __init__.py
    ├── account_management.py      # Delinquent account management
    ├── payment_scheduling.py      # Payment plans & settlement
    ├── collections_strategy.py    # Strategy recommendation
    ├── compliance_checker.py      # FDCPA/TCPA/FCRA compliance
    ├── debtor_embedding.py        # ML profile embedding
    ├── notifications.py           # FDCPA-compliant communications
    └── payment_gateway.py         # Payment processing
```

## Knowledge Base (7 Collections)

| Collection | Content | Documents |
|------------|---------|-----------|
| `fdcpa_regulations` | FDCPA overview, communication restrictions, validation notice, prohibited conduct, cease & desist, dispute rights, penalties | 7 |
| `collection_strategies` | Early-stage (1-30 days), mid-stage (31-90), late-stage (91-180), charge-off (180+), debtor segmentation | 5 |
| `negotiation_frameworks` | Payment plan structuring, settlement negotiation, hardship assessment, de-escalation techniques | 4 |
| `compliance_guidelines` | TCPA, state-specific laws, FCRA credit reporting, UDAAP unfair practices | 4 |
| `past_resolution_cases` | Mortgage forbearance success, auto loan settlement, personal loan workout, credit card charge-off failure | 4 |
| `hardship_programs` | Forbearance, loan modification, deferment | 3 |
| `communication_templates` | (Loaded from notification tool) | 0 |

## FDCPA Compliance Features

| Requirement | Implementation |
|-------------|----------------|
| Contact hours (8AM-9PM) | `check_compliance` validates contact time |
| Max 3 attempts/day | `check_compliance` tracks daily attempts |
| Validation notice (5 days) | `send_validation_not` sends compliant notice |
| Cease & desist | `check_compliance` blocks contact after C&D |
| Attorney representation | `check_compliance` routes through attorney |
| Dispute handling | Knowledge base includes dispute rights |
| Proper identification | All communications include debt collector identification |

## Production Patterns

Same as KYC and Loan Agents — see `llm/base_agent.py`:

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

## Sample Delinquent Accounts (Seeded)

| Account | Borrower | Product | Balance | Days Past Due | Stage |
|---------|----------|---------|---------|---------------|-------|
| ACCT-10001 | Sarah Johnson | Mortgage | $185,000 | 45 | Mid-stage |
| ACCT-10002 | Michael Chen | Auto Loan | $18,500 | 75 | Mid-stage |
| ACCT-10003 | Emily Rodriguez | Personal Loan | $11,200 | 120 | Late-stage |

## Phone Call Features

| Feature | Description |
|---------|-------------|
| **FDCPA Scripts** | Stage-specific call scripts (early/mid/late) with required disclosures |
| **Compliance Checklist** | Pre-call validation (hours, attempts, C&D, attorney) |
| **Outcome Tracking** | 11 outcome types with automated follow-up scheduling |
| **Voicemail Drops** | FDCPA-compliant voicemail with debt collection disclosure |
| **Callback Scheduling** | Schedule follow-ups with reason tracking |
| **Call Statistics** | Promise-to-pay rate, contact rate, duration metrics |
| **Critical Outcomes** | Auto-flag disputed debts and cease-desist requests |

## Notes

- Tool stubs return deterministic results — swap for real APIs in production
- Debtor embedding uses synthetic profiles — production uses trained models (XGBoost, LightGBM)
- Compliance checker uses rule-based validation — production integrates with compliance management systems
- Payment gateway is simulated — production connects to actual payment processors
- Collection strategies use rule-based scoring — production uses ML clustering for strategy matching
- FDCPA compliance is enforced at the tool level — production adds real-time monitoring
