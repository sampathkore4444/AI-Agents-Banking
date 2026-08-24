# Payment Reconciliation Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for payment reconciliation in banking, powered by a **RAG pipeline** for reconciliation rules and standards retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

**Covers all 7.2 Payment Reconciliation Agent capabilities.**

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                   PAYMENT RECONCILIATION AGENT                            │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  Analyst  │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Query    │    │  (ReAct     │◀───│  ├── knowledge_search           │ │
│  │           │◀───│   Agent)    │    │  ├── run_auto_match             │ │
│  │           │    │             │    │  ├── import_statement            │ │
│  │           │    │  Options:   │    │  ├── get_ledger                 │ │
│  │           │    │  • Ollama   │    │  ├── investigate_disc            │ │
│  │           │    │  • vLLM     │    │  ├── resolve_disc                │ │
│  │           │    │  • SGLang   │    │  ├── find_similar               │ │
│  │           │    │             │    │  ├── post_adjustment             │ │
│  │           │    │             │    │  ├── gen_recon_report            │ │
│  └──────────┘    └──────┬──────┘    │  └── ... (30+ tools)             │ │
│                         │           └──────────────────────────────────┘ │
│                         ▼                                                │
│                  ┌──────────────┐                                         │
│                  │  RAG Engine  │                                         │
│                  │  (ChromaDB)  │                                         │
│                  │  • Rules     │                                         │
│                  │  • Standards │                                         │
│                  │  • Exceptions│                                         │
│                  │  • GAAP/SOX  │                                         │
│                  │  • Patterns  │                                         │
│                  │  • Regs      │                                         │
│                  └──────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed

### Payment Matching
| Tool | Description |
|------|-------------|
| `run_auto_match` | Auto-match bank entries to ledger entries (exact, fuzzy, semantic) |
| `match_payment` | Match single payment, return ranked candidates |

### Bank Statement Import
| Tool | Description |
|------|-------------|
| `import_statement` | Import bank statements (MT940, BAI2, ISO 20022, CSV) |
| `get_bank_data` | Retrieve bank entries with filters |
| `parse_statement` | Parse raw statement data into structured entries |

### Ledger Management
| Tool | Description |
|------|-------------|
| `get_ledger` | Retrieve ledger entries with filters |
| `get_account_balance` | Get current balance for an account |
| `create_journal` | Create journal entry (adjustments) |
| `reverse_ledger_entry` | Reverse an existing entry |

### Exception Handling
| Tool | Description |
|------|-------------|
| `create_recon_exception` | Create new exception item |
| `get_exception` | Get exception details |
| `get_exceptions` | Get exception queue with filters |
| `resolve_recon_exception` | Resolve an exception |
| `escalate_recon_exception` | Escalate to higher authority |
| `exception_aging` | Aging report for open exceptions |

### Discrepancy Resolution
| Tool | Description |
|------|-------------|
| `find_discrepancies` | Analyze matched pairs for amount mismatches |
| `investigate_disc` | Investigate discrepancy, suggest causes |
| `resolve_disc` | Resolve (adjust_ledger, write_off, bank_notification) |
| `discrepancy_report` | Generate discrepancy report |

### Payment Embedding
| Tool | Description |
|------|-------------|
| `embed_inv` | Create invoice embedding for semantic matching |
| `embed_pay` | Create payment embedding for semantic matching |
| `find_similar` | Find similar invoices using embedding similarity |
| `embed_cp` | Embed counterparty name with aliases |

### Accounting System
| Tool | Description |
|------|-------------|
| `post_adjustment` | Post adjusting entry to GL |
| `get_adjustments` | Get posted adjustments |
| `gen_recon_report` | Generate formal reconciliation report |
| `check_gl_sync` | Check GL sync status |

### Notifications
| Tool | Description |
|------|-------------|
| `notify_recon` | Send reconciliation notification |
| `alert_exception` | Send exception escalation alert |

### Knowledge
| Tool | Description |
|------|-------------|
| `knowledge_search` | RAG search over rules, standards, exceptions |

## Reconciliation Flow

```
Analyst: "Reconcile January for account 1000-OPERATING"
    │
    ├── 1. import_statement(1000-OPERATING, "MT940", "2026-01-31", 125000, 150000)
    │
    ├── 2. get_ledger(1000-OPERATING, "2026-01-01", "2026-01-31")
    │
    ├── 3. run_auto_match(bank_entries, ledger_entries, threshold=0.95)
    │      → 95% match rate, 2 unmatched bank, 1 unmatched ledger
    │
    ├── 4. find_discrepancies(matched_pairs)  ← amount mismatches
    │      → 1 discrepancy: $1.00 difference on INV-2024-004
    │
    ├── 5. investigate_disc("DISC-xxx")  ← suggest causes
    │      → "Rounding difference" or "ACH fee"
    │
    ├── 6. resolve_disc("DISC-xxx", "write_off", description="ACH rounding")
    │
    ├── 7. post_adjustment("1000-OPERATING", 1.00, "write_off", ...)
    │
    ├── 8. gen_recon_report("1000-OPERATING", "2026-01")
    │      → Balanced, all items reconciled
    │
    └── 9. notify_recon("finance_team", "reconciliation_complete", ...)
```

## Quick Start

```bash
cd payment_reconciliation_agent
pip install -r requirements.txt
python seed_knowledge.py

# Start an LLM backend
ollama serve  # or vllm serve / sglang

# Run the agent
python -m llm.agent_ollama
```

## Project Structure

```
payment_reconciliation_agent/
├── server.py              # MCP server with 30+ tools
├── rag_pipeline.py        # RAG engine (7 collections)
├── config.py              # Settings
├── seed_knowledge.py      # Seed reconciliation knowledge (20+ docs)
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
    ├── payment_matching.py        # Auto-matching engine
    ├── ledger_management.py       # Ledger entries & balances
    ├── bank_statement.py          # Statement import & parsing
    ├── exception_handling.py      # Exception queue & aging
    ├── discrepancy_resolution.py  # Investigation & resolution
    ├── payment_embedding.py       # Semantic matching embeddings
    ├── notifications.py           # Alerts & reports
    └── accounting_system.py       # GL integration & reports
```

## Knowledge Base (7 Collections)

| Collection | Content | Documents |
|------------|---------|-----------|
| `reconciliation_rules` | Matching criteria, workflows, three-way match | 4 |
| `payment_standards` | BAI2, ISO 20022, MT940, NACHA format specs | 4 |
| `exception_handling` | Categories, aging, escalation, timing differences | 3 |
| `accounting_standards` | GAAP, SOX, materiality thresholds | 2 |
| `past_discrepancies` | Duplicate ACH, FX mismatch, check fraud cases | 3 |
| `matching_patterns` | Reference matching, amount-based matching rules | 2 |
| `regulatory_requirements` | AML/BSA, Basel III operational risk | 2 |

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-format Import** | MT940, BAI2, ISO 20022/CAMT.053, CSV |
| **Three-tier Matching** | Exact → Fuzzy → Semantic (embedding-based) |
| **Exception Aging** | 0-3, 4-7, 8-14, 15-30, 31+ day buckets |
| **Discrepancy Investigation** | Auto-suggest causes based on amount patterns |
| **Embedding Matching** | Semantic similarity for unmatched payments |
| **SOX Compliance** | Segregation of duties, audit trails, management review |
| **Adjusting Entries** | Bank fees, FX adjustments, error corrections, write-offs |

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

## Notes

- Tool stubs return deterministic results — swap for real APIs in production
- Payment embedding uses synthetic vectors — production uses trained models
- Statement parsers are simplified — production uses full MT940/BAI2/ISO20022 parsers
- Auto-matching engine uses rule-based scoring — production uses ML for fuzzy matching
- Embedding-based matching is simulated — production uses sentence transformers
- GL integration is stubbed — production connects to SAP, Oracle, or NetSuite
