# Financial Statement Analysis Agent

A banking AI agent that parses, analyzes, and interprets financial statements for credit assessment, audit support, and investment due diligence using MCP tools, RAG, and embeddings.

## Overview

This agent implements **Section 10.3** of the banking AI use cases:
> *Parses and analyzes financial statements for credit assessment, audit support, or investment due diligence.*

### Capabilities

| Capability | Technique |
|---|---|
| **Financial Data Extraction** | MCP Tools — Parse and structure balance sheet, income statement, cash flow |
| **Ratio Analysis** | MCP Tools — 25+ ratios across liquidity, leverage, profitability, efficiency |
| **DuPont Decomposition** | MCP Tools — Break down ROE into 3 and 5 components |
| **Altman Z-Score** | MCP Tools — Bankruptcy prediction model |
| **Industry Benchmarks** | MCP Tools — Compare against 6 industry sectors |
| **Peer Comparison** | MCP Tools — Rank and compare against peer companies |
| **Trend Analysis** | Embeddings — Multi-period trend detection and CAGR |
| **Deterioration Detection** | Embeddings — Early warning signals for financial distress |
| **GAAP Compliance** | RAG — Accounting standards and compliance checks |
| **Executive Summaries** | MCP Tools — Automated credit/investment summaries |

## Architecture

```
financial_statement_agent/
├── server.py                              # MCP server with 30+ tools
├── rag_pipeline.py                        # RAG engine (7 collections)
├── config.py                              # Settings
├── seed_knowledge.py                      # 33 financial analysis documents
├── compare_agents.py                      # Compare Ollama/vLLM/SGLang
├── requirements.txt
├── README.md
├── BANKING_USE_CASES_FINANCIAL_STATEMENT_ARCHITECTURE.md
├── llm/
│   ├── base_agent.py                      # Guardrails, HITL, memory, streaming
│   ├── agent_ollama.py                    # Ollama
│   ├── agent_vllm.py                      # vLLM
│   └── agent_sglang.py                    # SGLang
└── tools/
    ├── financial_data_extraction.py       # Data parsing, company info, upload
    ├── ratio_analysis.py                  # 25+ ratios, DuPont, Z-Score
    ├── industry_benchmarks.py             # 6 sectors with quartile data
    ├── peer_comparison.py                 # Peer ranking and comparison
    ├── trend_analysis.py                  # Multi-period trends, deterioration
    ├── compliance_check.py                # GAAP compliance, audit readiness
    └── notifications.py                   # Alerts, executive summaries
```

## MCP Tools (30+)

### Financial Data Extraction
- `extract_data` — Extract structured financial data
- `company_info` — Get company information
- `companies` — List available companies
- `upload_stmt` — Upload a financial statement
- `validate_completeness` — Check statement completeness

### Ratio Analysis
- `liquidity_ratios` — Current, quick, cash ratios
- `leverage_ratios` — D/E, interest coverage, debt/EBITDA
- `profitability_ratios` — Margins, ROA, ROE
- `efficiency_ratios` — Turnover ratios, DSO, DPO, CCC
- `dupont_analysis` — ROE decomposition (3 and 5 component)
- `altman_zscore` — Bankruptcy prediction
- `full_analysis` — Comprehensive analysis across all categories

### Industry Benchmarks
- `benchmark` — Get benchmark data for an industry
- `benchmarks_list` — List all available benchmarks
- `compare_benchmark` — Compare single metric
- `full_benchmark` — Compare all ratios against industry

### Peer Comparison
- `peer_group` — Get peers in an industry
- `compare_to_peers` — Compare company against peers
- `peer_ranking` — Rank peers by metric
- `peer_stats` — Summary statistics for peer group

### Trend Analysis
- `trend` — Analyze single metric trend
- `multi_trend` — Multi-metric trend analysis
- `deterioration` — Detect financial deterioration signals

### Compliance
- `gaap_compliance` — Check GAAP compliance
- `ratio_health` — Check ratios against health thresholds
- `audit_readiness` — Audit readiness assessment

### Notifications & Reports
- `notify_analysis` — Analysis complete notification
- `notify_deterioration` — Deterioration alert
- `notify_benchmark` — Benchmark deviation alert
- `notify_compliance` — Compliance issue alert
- `executive_summary` — Generate executive summary
- `notifications_log` — Notification history

## Knowledge Base (7 Collections)

| Collection | Documents | Content |
|---|---|---|
| accounting_standards | 5 | GAAP, IFRS, revenue recognition, leases, impairment |
| analytical_frameworks | 6 | DuPont, Altman Z-Score, Piotroski F-Score, liquidity, solvency, profitability |
| industry_benchmarks | 6 | Technology, manufacturing, retail, financial, healthcare, energy |
| ratio_definitions | 5 | Liquidity, leverage, profitability, efficiency, valuation ratios |
| credit_analysis | 5 | Rating methodology, credit spreads, covenants, cash flow, earnings quality |
| statement_structures | 5 | Balance sheet, income statement, cash flow, equity, notes |
| regulatory_requirements | 4 | SEC filings, SOX, audit standards, Basel III |

## Sample Data

The agent includes 3 years of financial data for Acme Technologies Inc. (technology sector):
- **2021**: Revenue $1.2B, Net Income $162M, FCF $120M
- **2022**: Revenue $1.5B, Net Income $216M, FCF $180M
- **2023**: Revenue $1.8B, Net Income $275M, FCF $230M

## LLM Backends

| Backend | Model | Use Case |
|---|---|---|
| **Ollama** | llama3.1:8b | Development, local testing |
| **vLLM** | Llama-3.1-8B-Instruct | Production, batch analysis |
| **SGLang** | Llama-3.1-8B-Instruct | Structured output (ratio tables) |

## Compliance

- **GAAP** — Balance sheet equation, ASC 606/842/360 compliance
- **SOX** — Internal control assessment, certification requirements
- **SEC** — Filing requirements (10-K, 10-Q, 8-K)
- **Basel III** — Capital adequacy for bank analysis
