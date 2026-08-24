# Cross-Border Payment Assistant Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for cross-border payments in banking, powered by a **RAG pipeline** for correspondent banking knowledge and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

**Covers all 7.3 Cross-Border Payment Assistant Agent capabilities.**

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│               CROSS-BORDER PAYMENT ASSISTANT AGENT                        │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  Customer │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Chat     │    │  (ReAct     │◀───│  ├── get_rate                   │ │
│  │           │◀───│   Agent)    │    │  ├── track_wire                 │ │
│  │           │    │             │    │  ├── find_correspondent          │ │
│  │           │    │  Options:   │    │  ├── screen_entity               │ │
│  │           │    │  • Ollama   │    │  ├── check_compliance            │ │
│  │           │    │  • vLLM     │    │  ├── get_regulations             │ │
│  │           │    │  • SGLang   │    │  ├── get_quote                   │ │
│  └──────────┘    └──────┬──────┘    │  └── ... (20+ tools)             │ │
│                         │           └──────────────────────────────────┘ │
│                         ▼                                                │
│                  ┌──────────────┐                                         │
│                  │  RAG Engine  │                                         │
│                  │  (ChromaDB)  │                                         │
│                  │  • Corresp.  │                                         │
│                  │  • SWIFT     │                                         │
│                  │  • Countries │                                         │
│                  │  • Fees      │                                         │
│                  │  • FX Rules  │                                         │
│                  │  • Compliance│                                         │
│                  └──────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed

### FX Rates
| Tool | Description |
|------|-------------|
| `get_rate` | Get current exchange rate with customer markup |
| `compare_fx_rates` | Compare rates across online, branch, wire, broker |
| `get_history_rate` | Get historical exchange rate |

### SWIFT gpi Tracking
| Tool | Description |
|------|-------------|
| `track_wire` | Track payment using SWIFT gpi UETR |
| `send_wire` | Initiate cross-border wire transfer |
| `wire_history` | Get transaction history |

### Correspondent Banks
| Tool | Description |
|------|-------------|
| `find_correspondent` | Find correspondent banks for a currency |
| `get_route` | Determine optimal routing path |
| `lookup_bic` | Get BIC/SWIFT code details |

### Sanctions & Compliance
| Tool | Description |
|------|-------------|
| `screen_entity` | Screen against OFAC, EU, UN sanctions |
| `check_compliance` | Full compliance check (Travel Rule, country risk) |
| `required_info` | Determine required payment information |

### Country Regulations
| Tool | Description |
|------|-------------|
| `get_regulations` | Get cross-border regulations by country |
| `check_controls` | Check capital controls |

### Payment Quotes
| Tool | Description |
|------|-------------|
| `get_quote` | Generate all-in cost quote |
| `compare_payment_options` | Compare wire vs express vs FX broker |

### Knowledge & Notifications
| Tool | Description |
|------|-------------|
| `knowledge_search` | RAG search over correspondent banking knowledge |
| `notify_customer` | Send payment status notifications |

## Cross-Border Payment Flow

```
Customer: "I need to send $25,000 to a supplier in the UK"
    │
    ├── 1. knowledge_search("UK cross-border payment requirements")
    │
    ├── 2. get_rate("USD", "GBP", 25000)
    │      → Mid-market: 0.7900, Customer rate: 0.7861
    │      → Converted: £19,652.50
    │
    ├── 3. find_correspondent("USD", "US", "GB")
    │      → Recommended: JPMorgan Chase (CHASUS33)
    │
    ├── 4. check_compliance("MyCompany", "US", "UKSupplier", "GB", 25000, "USD", "Trade payment")
    │      → Decision: APPROVED, All checks passed
    │
    ├── 5. get_quote("USD", "GBP", 25000, "US", "GB", "SHA", "standard")
    │      → Total cost: $168 (0.67%)
    │      → Delivery: 2 business days
    │
    ├── 6. send_wire("USD", "GBP", 25000, ...)
    │      → UETR assigned, Payment initiated
    │
    └── 7. track_wire(uetr)
           → Status: In Progress, Estimated: 2 business days
```

## Quick Start

```bash
cd cross_border_payment_agent
pip install -r requirements.txt
python seed_knowledge.py

# Start an LLM backend
ollama serve  # or vllm serve / sglang

# Run the agent
python -m llm.agent_ollama
```

## Project Structure

```
cross_border_payment_agent/
├── server.py                  # MCP server with 20+ tools
├── rag_pipeline.py            # RAG engine (7 collections)
├── config.py                  # Settings
├── seed_knowledge.py          # Seed knowledge (15+ docs)
├── compare_agents.py          # Compare LLM backends
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py          # Base agent with production patterns
│   ├── agent_ollama.py        # Ollama
│   ├── agent_vllm.py          # vLLM
│   └── agent_sglang.py        # SGLang
└── tools/
    ├── __init__.py
    ├── fx_rates.py            # Exchange rates & conversion
    ├── swift_tracking.py      # SWIFT gpi tracking & initiation
    ├── correspondent_banks.py # Bank discovery & routing
    ├── sanctions_screening.py # OFAC/EU/UN screening
    ├── compliance.py          # Travel Rule, country risk checks
    ├── country_regulations.py # Capital controls, reporting
    ├── payment_quotes.py      # All-in cost quotes
    └── notifications.py       # Payment status notifications
```

## Knowledge Base (7 Collections)

| Collection | Content | Documents |
|------------|---------|-----------|
| `correspondent_banking` | Nostro/vostro, USD clearing, CLS | 2 |
| `swift_codes` | BIC format, MT messages, gpi tracking | 3 |
| `country_regulations` | US, EU, UK, JP, CN, IN, AE, NG, BR | 4 |
| `fee_schedules` | Wire fees, correspondent fees | 2 |
| `fx_trading_rules` | Spot/forward rates, spreads, markup | 2 |
| `compliance_requirements` | OFAC, FATF Travel Rule | 2 |
| `past_transactions` | Successful & delayed payment patterns | 2 |

## Key Features

| Feature | Description |
|---------|-------------|
| **FX Rate Comparison** | Online vs branch vs wire vs FX broker pricing |
| **SWIFT gpi Tracking** | End-to-end payment tracking with UETR |
| **Correspondent Discovery** | Optimal routing through correspondent chain |
| **Sanctions Screening** | OFAC SDN, EU, UN list screening with fuzzy matching |
| **Compliance Checks** | Travel Rule, country risk, amount thresholds |
| **Country Regulations** | Capital controls, reporting requirements, tax implications |
| **All-in Cost Quotes** | Transparent fee breakdown with OUR/BEN/SHA options |
| **Multi-currency** | 15+ currency pairs with cross-rate calculation |

## Notes

- FX rates are simulated — production uses Bloomberg, Reuters, or ECB feeds
- Sanctions lists are simplified — production uses full OFAC SDN, EU, UN lists
- SWIFT gpi tracking is simulated — production calls SWIFT API
- Correspondent routing is simplified — production considers real-time availability
- Compliance checks are rule-based — production integrates with compliance systems
