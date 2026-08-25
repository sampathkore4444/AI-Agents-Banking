# Financial Statement Analysis Agent — Architecture

## 1. Overview

The Financial Statement Analysis Agent parses, analyzes, and interprets financial statements to support credit assessment, audit procedures, and investment due diligence.

### 1.1 Business Objectives
- Automate financial statement analysis for credit decisions
- Provide consistent, auditable ratio calculations
- Detect early signs of financial deterioration
- Benchmark companies against industry peers
- Generate executive summaries for investment committees

### 1.2 Key Metrics
- Analysis accuracy: > 95% for ratio calculations
- Processing time: < 30 seconds per company
- Deterioration detection rate: > 80% (1 year advance warning)
- Audit readiness: 100% GAAP compliance check coverage

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  Credit Analyst  │  Portfolio Manager  │  Auditor  │  Risk      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                     MCP SERVER LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Financial Statement Analysis Agent (server.py)         │    │
│  │  ├── 30+ MCP Tools                                      │    │
│  │  ├── Guardrails Engine                                  │    │
│  │  ├── Human-in-the-Loop                                  │    │
│  │  └── Memory (analysis context)                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                     TOOL LAYER                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Financial    │ │ Ratio        │ │ Industry     │            │
│  │ Data Extract │ │ Analysis     │ │ Benchmarks   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Peer         │ │ Trend        │ │ Compliance   │            │
│  │ Comparison   │ │ Analysis     │ │ Check        │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐                                              │
│  │ Notifications│                                              │
│  │ & Reports    │                                              │
│  └──────────────┘                                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                     DATA LAYER                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RAG Pipeline (ChromaDB)                                 │  │
│  │  ├── accounting_standards (5 docs)                       │  │
│  │  ├── analytical_frameworks (6 docs)                      │  │
│  │  ├── industry_benchmarks (6 docs)                        │  │
│  │  ├── ratio_definitions (5 docs)                          │  │
│  │  ├── credit_analysis (5 docs)                            │  │
│  │  ├── statement_structures (5 docs)                       │  │
│  │  └── regulatory_requirements (4 docs)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Embeddings (SentenceTransformer)                        │  │
│  │  ├── Financial metric vectors (128-dim)                  │  │
│  │  ├── Industry peer vectors (128-dim)                     │  │
│  │  └── Deterioration pattern vectors (128-dim)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Design

### 3.1 Financial Data Extraction
- **Statement parsing**: Balance sheet, income statement, cash flow statement
- **Data validation**: Completeness checks, cross-statement consistency
- **Upload support**: Manual data entry or structured JSON upload
- **Multi-period storage**: Track 3-5 years of historical data

### 3.2 Ratio Analysis Engine
- **Liquidity**: Current ratio, quick ratio, cash ratio, working capital
- **Leverage**: D/E, debt-to-capital, interest coverage, debt/EBITDA, fixed charge coverage
- **Profitability**: Gross/operating/net/EBITDA margins, ROA, ROE, ROIC
- **Efficiency**: Asset turnover, inventory turnover, DSO, DPO, cash conversion cycle
- **Credit**: Altman Z-Score (1.2-1.8 distress zone), Piotroski F-Score (0-9)
- **Valuation**: P/E, EV/EBITDA, P/B, P/S (when market data available)

### 3.3 DuPont Decomposition
- **3-component**: ROE = Net Margin × Asset Turnover × Equity Multiplier
- **5-component**: ROE = Tax Burden × Interest Burden × Operating Margin × Asset Turnover × Leverage
- **Driver identification**: Pinpoint whether returns are driven by profitability, efficiency, or leverage

### 3.4 Industry Benchmarking
- **6 sectors**: Technology, Manufacturing, Retail, Financial Services, Healthcare, Energy
- **Quartile data**: P25, Median, P75 for each metric
- **Lower-is-better handling**: Correct interpretation for D/E, DSO, DIO
- **Deviation alerts**: Flag metrics >25% from industry median

### 3.5 Peer Comparison
- **Peer groups**: 5-6 companies per industry
- **Ranking**: Rank by any metric within peer group
- **Summary statistics**: Mean, median, min, max for peer group
- **Relative positioning**: Percentile rank within peer group

### 3.6 Trend & Deterioration Analysis
- **Multi-period trends**: CAGR, period-over-period changes, volatility
- **Deterioration signals**: Revenue decline, margin compression, rising leverage, declining CFO, earnings quality
- **Risk level assessment**: Low/Medium/High based on signal count and severity
- **Early warning**: Detect distress 1-2 years before potential default

### 3.7 Compliance Checking
- **GAAP compliance**: Balance sheet equation, ASC 606/842/360 consistency
- **Ratio health**: Threshold-based alerts for critical ratios
- **Audit readiness**: Completeness checks, multi-period consistency, materiality assessment

---

## 4. Data Model

### 4.1 Financial Statement
```json
{
  "statement_id": "STMT-XXXXXXXX",
  "company_id": "ACME-001",
  "period": "2023",
  "period_type": "annual",
  "balance_sheet": {
    "total_current_assets": 850000000,
    "total_assets": 2400000000,
    "total_liabilities": 850000000,
    "total_equity": 1550000000
  },
  "income_statement": {
    "revenue": 1800000000,
    "gross_profit": 1080000000,
    "operating_income": 360000000,
    "net_income": 275200000,
    "ebitda": 450000000
  },
  "cash_flow_statement": {
    "cash_from_operations": 380000000,
    "capital_expenditures": -150000000,
    "free_cash_flow": 230000000
  }
}
```

### 4.2 Ratio Analysis Output
```json
{
  "liquidity": {"current_ratio": 2.74, "quick_ratio": 1.61},
  "leverage": {"debt_to_equity": 0.55, "interest_coverage": 20.0},
  "profitability": {"net_margin_pct": 15.3, "roe_pct": 17.8},
  "dupont": {"roe_three_component": 17.75, "drivers": ["Strong profit margins"]},
  "altman_zscore": {"z_score": 3.85, "zone": "safe"},
  "overall_health": {"health_rating": "strong", "score": 8}
}
```

### 4.3 Benchmark Comparison
```json
{
  "industry": "Technology",
  "metric": "gross_margin_pct",
  "company_value": 60.0,
  "benchmark_median": 55.0,
  "percentile_label": "above median (50th-75th)",
  "comparison": "above_average"
}
```

---

## 5. Analysis Frameworks

### 5.1 Altman Z-Score
| Zone | Z-Score Range | Interpretation |
|---|---|---|
| Safe | Z > 3.0 | Low bankruptcy probability |
| Gray | 1.8 < Z < 3.0 | Uncertain — requires monitoring |
| Distress | Z < 1.8 | High bankruptcy risk |

### 5.2 DuPont 5-Component
```
ROE = (NI/EBT) × (EBT/EBIT) × (EBIT/Rev) × (Rev/Assets) × (Assets/Equity)
     = Tax     × Interest    × Operating   × Asset        × Financial
       Burden    Burden        Margin        Turnover       Leverage
```

### 5.3 Deterioration Detection Signals
| Signal | Threshold | Severity |
|---|---|---|
| Revenue decline | > 10% YoY | High |
| Margin compression | > 3pp decline | Medium |
| Rising leverage | D/E increase > 25% | Medium |
| Z-Score < 1.8 | Distress zone | Critical |
| Negative FCF | 2+ consecutive periods | High |
| Earnings quality | CFO < 70% of NI | Medium |

---

## 6. Security & Compliance

### 6.1 Data Protection
- Financial data encrypted at rest and in transit
- Access restricted to authorized analysts
- Audit trail for all analysis activities
- Retention per regulatory requirements (7 years)

### 6.2 Analytical Standards
- All ratio calculations auditable and reproducible
- Assumptions clearly documented
- Materiality thresholds applied consistently
- Industry benchmarks sourced from reliable databases

---

## 7. Integration Points

| System | Protocol | Purpose |
|---|---|---|
| SEC EDGAR | REST API | Fetch public company filings (10-K, 10-Q) |
| Bloomberg/Reuters | REST API | Market data, peer comparison |
| Internal Credit System | REST API | Feed analysis into credit decisions |
| Audit Management | REST API | Support audit procedures |
| Risk Dashboard | REST API | Display analysis results |
| Email/Slack | REST API | Send alerts and reports |
