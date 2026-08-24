# Credit Risk Monitoring Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for credit risk monitoring in banking, powered by **RAG** for risk knowledge retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                  CREDIT RISK MONITORING AGENT                             │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  Risk     │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Analyst  │    │  (ReAct     │◀───│  ├── search_risk_knowledge      │ │
│  │  Query    │◀───│   Agent)    │    │  ├── get_portfolio              │ │
│  │           │    │             │    │  ├── run_early_warning          │ │
│  │           │    │  Options:   │    │  ├── analyze_financials         │ │
│  │           │    │  • Ollama   │    │  ├── get_market                 │ │
│  │           │    │  • vLLM     │    │  ├── get_rating                 │ │
│  │           │    │  • SGLang   │    │  ├── assess_risk                │ │
│  └──────────┘    └──────┬──────┘    │  ├── create_alert               │ │
│                         │           │  ├── daily_report                │ │
│                         ▼           │  └── calculate_el                │ │
│                  ┌──────────────┐   └──────────────────────────────────┘ │
│                  │  RAG Engine  │                                         │
│                  │  (ChromaDB)  │    ┌──────────────────────────────────┐ │
│                  │              │    │       External APIs              │ │
│                  │  • Risk      │    │  ┌──────────┐ ┌───────────┐    │ │
│                  │    Policies  │    │  │ Credit   │ │ Market    │    │ │
│                  │  • Basel     │    │  │ Bureau   │ │ Data API  │    │ │
│                  │  • Review    │    │  └──────────┘ └───────────┘    │ │
│                  │    Procedures│    │  ┌──────────┐ ┌───────────┐    │ │
│                  │  • Default   │    │  │ Rating   │ │ Portfolio │    │ │
│                  │    Patterns  │    │  │ Agency   │ │ System    │    │ │
│                  │  • Watchlist │    │  └──────────┘ └───────────┘    │ │
│                  │  • Capital   │    └──────────────────────────────────┘ │
│                  └──────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed (20 Tools)

### Portfolio Monitoring
| Tool | Description |
|------|-------------|
| `get_portfolio` | Portfolio summary with PD, LGD, expected loss |
| `get_exposure` | Borrower-specific exposure details |
| `check_portfolio_concentration` | Concentration limits check |

### Early Warning System
| Tool | Description |
|------|-------------|
| `run_early_warning` | Scan portfolio for deteriorating signals |
| `check_borrower` | Early warning signals for specific borrower |
| `get_watchlist_borrowers` | Current watchlist with severity levels |

### Financial Analysis
| Tool | Description |
|------|-------------|
| `analyze_financials` | Ratio analysis, Altman Z-Score, credit health |

### Market Data
| Tool | Description |
|------|-------------|
| `get_market` | Credit spreads, yields, VIX, recession probability |
| `get_sector` | Sector-specific default rates and risk outlook |
| `get_pd_curve` | Term structure of default probability |

### Rating Agency
| Tool | Description |
|------|-------------|
| `get_rating` | Current ratings from Moody's, S&P, Fitch |
| `check_rating` | Rating transition probability |

### Alert Management
| Tool | Description |
|------|-------------|
| `create_alert` | Generate risk alert with auto-escalation |
| `acknowledge` | Acknowledge alert with analyst notes |
| `get_alerts` | Active alerts filtered by severity |
| `daily_report` | Daily risk summary report |

### Risk Assessment
| Tool | Description |
|------|-------------|
| `assess_risk` | Comprehensive risk assessment (financial + market + rating) |
| `calculate_el` | Expected Loss = PD × LGD × EAD |

### Knowledge Search
| Tool | Description |
|------|-------------|
| `search_risk_knowledge` | RAG search over risk policies and Basel requirements |

## Risk Monitoring Flows

### Daily Monitoring Flow
```
Morning: "Show me today's risk summary"
    │
    ├── 1. daily_report(portfolio_id)
    │
    ├── 2. run_early_warning(portfolio_id)
    │
    ├── 3. get_alerts(severity_filter="critical")
    │
    └── 4. Summarize key actions required
```

### Borrower Deep-Dive Flow
```
"Analyze borrower BORR-0187"
    │
    ├── 1. get_exposure("BORR-0187")
    │
    ├── 2. analyze_financials("BORR-0187")
    │   → Ratios, Z-Score, credit health
    │
    ├── 3. get_rating("BORR-0187")
    │   → Current rating, outlook
    │
    ├── 4. check_borrower("BORR-0187")
    │   → Early warning signals
    │
    ├── 5. get_pd_curve("BORR-0187")
    │   → Default probability term structure
    │
    ├── 6. assess_risk("BORR-0187")
    │   → Comprehensive risk score
    │
    ├── 7. search_risk_knowledge("watchlist criteria for covenant breach")
    │   → Retrieval from RAG
    │
    └── 8. Provide risk assessment with recommendation
```

### Portfolio Stress Test Flow
```
"What's the impact of a 200bps rate increase?"
    │
    ├── 1. get_portfolio()
    │   → Current exposure and metrics
    │
    ├── 2. get_market()
    │   → Current spreads and yields
    │
    ├── 3. get_sector("commercial_real_estate")
    │   → Sector vulnerability
    │
    ├── 4. For top 10 borrowers:
    │   ├── assess_risk(borrower_id)
    │   └── calculate_el(exposure, pd, lgd)
    │
    └── 5. Aggregate stress impact
```

## Quick Start

```bash
cd credit_risk_agent
pip install -r requirements.txt
python seed_knowledge.py

# Start an LLM backend
ollama serve

# Run the agent
python -m llm.agent_ollama
```

## Project Structure

```
credit_risk_agent/
├── server.py              # MCP server (20 tools)
├── rag_pipeline.py        # RAG engine (6 collections)
├── config.py              # Settings with risk thresholds
├── seed_knowledge.py      # 30+ risk documents
├── compare_agents.py
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py
│   ├── agent_ollama.py
│   ├── agent_vllm.py
│   └── agent_sglang.py
└── tools/
    ├── __init__.py
    ├── portfolio_monitor.py    # Portfolio exposure, concentration
    ├── early_warning.py        # Deterioration detection, watchlist
    ├── financial_analysis.py   # Ratios, Z-Score, credit health
    ├── market_data.py          # Spreads, yields, sector risk, PD curves
    ├── rating_agency.py        # Moody's, S&P, Fitch ratings
    ├── risk_assessment.py      # Comprehensive risk scoring, EL calculation
    └── alerts.py               # Alert generation, escalation, daily reports
```

## Knowledge Base (6 Collections)

| Collection | Content | Documents |
|------------|---------|-----------|
| `risk_policies` | Risk appetite, review policy, classification, concentration | 5 |
| `basel_requirements` | CET1, RWA, stress testing, leverage ratio | 4 |
| `credit_review_procedures` | Annual review, watchlist review, CECL provisioning | 3 |
| `default_patterns` | Leading indicators, timelines, sector patterns, recovery rates | 4 |
| `watchlist_criteria` | Placement criteria, escalation rules | 2 |
| `regulatory_capital_rules` | Capital adequacy, planning process | 2 |

## Risk Metrics Explained

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **PD** | Probability of Default | <2.5% target |
| **LGD** | Loss Given Default | 35-60% typical |
| **EAD** | Exposure at Default | Facility amount |
| **EL** | Expected Loss (PD × LGD × EAD) | Monitored daily |
| **Z-Score** | Altman bankruptcy predictor | >2.99 safe, <1.81 distress |
| **RAROC** | Risk-Adjusted Return on Capital | >15% target |

## Production Patterns

Same as other agents — see `llm/base_agent.py`:

| Pattern | Class |
|---------|-------|
| Intent Routing | `IntentRouter` |
| Guardrails | `Guardrails` |
| Human-in-the-Loop | `HumanApprovalManager` |
| Memory Management | `ConversationMemory` |
| Error Handling | `ErrorHandler` |
| Observability | `AgentTracer` |

## Notes

- Tool stubs return deterministic results — swap for real Bloomberg, Moody's, S&P APIs
- Financial analysis uses simulated data — integrate with actual financial statement feeds
- Z-Score calculation uses simplified formula — production uses full Altman model
- Early warning signals are rule-based — production uses ML models (XGBoost, survival analysis)
- Default probability curves are simplified — production uses credit models (Merton, KMV)
