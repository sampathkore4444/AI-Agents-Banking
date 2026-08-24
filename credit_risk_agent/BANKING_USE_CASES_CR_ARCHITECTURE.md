# Credit Risk Monitoring Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Credit Risk Monitoring Agent that uses **RAG** for risk knowledge retrieval and **MCP** for tool orchestration across portfolio monitoring, early warning, financial analysis, market data, and alert management.

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                  CREDIT RISK MONITORING AGENT                             │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  Risk     │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Analyst  │    │  (ReAct     │◀───│  ├── search_risk_knowledge      │ │
│  │  Dashboard│◀───│   Agent)    │    │  ├── get_portfolio              │ │
│  │           │    │             │    │  ├── run_early_warning          │ │
│  │  • Alert  │    │  Options:   │    │  ├── analyze_financials         │ │
│  │    Inbox  │    │  • Ollama   │    │  ├── get_market                 │ │
│  │  • Watch  │    │  • vLLM     │    │  ├── get_rating                 │ │
│  │    List   │    │  • SGLang   │    │  ├── assess_risk                │ │
│  │  • Reports│    │             │    │  ├── create_alert               │ │
│  └──────────┘    └──────┬──────┘    │  ├── daily_report                │ │
│                         │           │  └── calculate_el                │ │
│                         ▼           └──────────────────────────────────┘ │
│                  ┌──────────────┐                                         │
│                  │  RAG Engine  │    ┌──────────────────────────────────┐ │
│                  │  (ChromaDB)  │    │       External APIs              │ │
│                  │              │    │  ┌──────────┐ ┌───────────┐    │ │
│                  │  • Risk      │    │  │ Credit   │ │ Bloomberg  │    │ │
│                  │    Policies  │    │  │ Bureau   │ │ Reuters    │    │ │
│                  │  • Basel     │    │  └──────────┘ └───────────┘    │ │
│                  │  • Review    │    │  ┌──────────┐ ┌───────────┐    │ │
│                  │    Procedures│    │  │ Moody's  │ │ Portfolio  │    │ │
│                  │  • Default   │    │  │ S&P      │ │ Management │    │ │
│                  │    Patterns  │    │  │ Fitch    │ │ System     │    │ │
│                  │  • Watchlist │    │  └──────────┘ └───────────┘    │ │
│                  │  • Capital   │    └──────────────────────────────────┘ │
│                  └──────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Flows

### Flow 1: Daily Risk Monitoring

```
RISK ANALYST               AGENT (LLM + RAG + MCP)           SYSTEMS
───────────               ──────────────────────              ───────

  │  "Show me today's     │                                │
  │   risk summary"       │                                │
  │──────────────────────▶│                                │
  │                       │  1. MCP: daily_report()         │
  │                       │──────┐                         │
  │                       │      │  Alert API              │
  │                       │◀─────┘                         │
  │                       │     → 350 borrowers            │
  │                       │     → 12 on watchlist          │
  │                       │     → EL: $3.25M               │
  │                       │                                │
  │                       │  2. MCP: run_early_warning()   │
  │                       │──────┐                         │
  │                       │      │  Portfolio API           │
  │                       │◀─────┘                         │
  │                       │     → 5 new alerts             │
  │                       │     → 2 critical               │
  │                       │                                │
  │                       │  3. MCP: get_alerts("critical")│
  │                       │──────┐                         │
  │                       │◀─────┘                         │
  │                       │     → BORR-0187: covenant      │
  │                       │       breach                   │
  │                       │     → BORR-0042: payment       │
  │                       │       delinquency              │
  │                       │                                │
  │  "Today's summary:    │                                │
  │   • 350 borrowers     │                                │
  │   • 12 on watchlist   │                                │
  │   • 2 critical alerts │                                │
  │   • BORR-0187 needs   │                                │
  │     immediate review  │                                │
  │   • EL: $3.25M"       │                                │
  │◀──────────────────────│                                │
```

### Flow 2: Borrower Deep-Dive

```
RISK ANALYST               AGENT (LLM + RAG + MCP)           SYSTEMS
───────────               ──────────────────────              ───────

  │  "Analyze borrower    │                                │
  │   BORR-0187"          │                                │
  │──────────────────────▶│                                │
  │                       │  1. MCP: get_exposure()         │
  │                       │──────┐                         │
  │                       │      │  Portfolio API           │
  │                       │◀─────┘                         │
  │                       │     → $5.2M total exposure     │
  │                       │                                │
  │                       │  2. MCP: analyze_financials()  │
  │                       │──────┐                         │
  │                       │      │  Financial API           │
  │                       │◀─────┘                         │
  │                       │     → Leverage: 4.5x (critical)│
  │                       │     → Interest cov: 1.8x       │
  │                       │     → Z-Score: 1.45 (distress) │
  │                       │                                │
  │                       │  3. MCP: get_rating()          │
  │                       │──────┐                         │
  │                       │      │  Rating Agency API       │
  │                       │◀─────┘                         │
  │                       │     → BBB- (negative outlook)  │
  │                       │                                │
  │                       │  4. MCP: check_borrower()      │
  │                       │──────┐                         │
  │                       │◀─────┘                         │
  │                       │     → covenant_breach (critical)│
  │                       │     → leverage_increase (high) │
  │                       │                                │
  │                       │  5. MCP: get_pd_curve()        │
  │                       │──────┐                         │
  │                       │◀─────┘                         │
  │                       │     → 1yr PD: 3.2%             │
  │                       │     → 5yr survival: 85%        │
  │                       │                                │
  │                       │  6. RAG: watchlist criteria    │
  │                       │──────┐                         │
  │                       │      │  Query Vector DB        │
  │                       │◀─────┘                         │
  │                       │     → Escalation rules         │
  │                       │                                │
  │  "BORR-0187 Analysis: │                                │
  │   Risk: HIGH          │                                │
  │   Leverage: 4.5x      │                                │
  │   Z-Score: 1.45       │                                │
  │   Rating: BBB- ↓      │                                │
  │   Signals: covenant   │                                │
  │     breach, leverage  │                                │
  │   PD 1yr: 3.2%        │                                │
  │   Recommendation:     │                                │
  │   Immediate senior    │                                │
  │   review required"    │                                │
  │◀──────────────────────│                                │
```

### Flow 3: Alert Escalation

```
AGENT                       RISK ANALYST                  SYSTEMS
──────                       ───────────                  ───────

  │  Early warning scan      │                            │
  │  detects critical alert  │                            │
  │                          │                            │
  │  1. MCP: create_alert()  │                            │
  │     severity: critical   │                            │
  │     escalation: true     │                            │
  │──────┐                   │                            │
  │      │                   │                            │
  │◀─────┘                   │                            │
  │  → ALT-X1Y2Z3W4          │                            │
  │                          │                            │
  │  2. RAG: search_risk_    │                            │
  │     knowledge("covenant  │                            │
  │     breach procedure")   │                            │
  │──────┐                   │                            │
  │      │                   │                            │
  │◀─────┘                   │                            │
  │  → Escalation rules      │                            │
  │  → Resolution steps      │                            │
  │                          │                            │
  │  3. Email notification   │                            │
  │     to senior analyst    │───────────────────────────▶│
  │                          │  Email/Slack               │
  │                          │                            │
  │  4. Wait for             │                            │
  │     acknowledgment       │                            │
  │                          │                            │
  │                          │  "I'll review              │
  │                          │   BORR-0187"               │
  │◀─────────────────────────│                            │
  │                          │                            │
  │  5. MCP: acknowledge()   │                            │
  │──────┐                   │                            │
  │      │                   │                            │
  │◀─────┘                   │                            │
  │  → Alert acknowledged    │                            │
```

---

## MCP Tool Definitions

### Portfolio Monitoring

```jsonc
{
  "name": "get_portfolio",
  "description": "Get overall portfolio summary with PD, LGD, expected loss",
  "inputSchema": {
    "type": "object",
    "properties": {
      "portfolio_id": { "type": "string" }
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "total_exposure": { "type": "number" },
      "num_borrowers": { "type": "integer" },
      "average_pd": { "type": "number" },
      "expected_loss": { "type": "number" },
      "concentration_top10_pct": { "type": "number" }
    }
  }
}
```

### Early Warning System

```jsonc
{
  "name": "run_early_warning",
  "description": "Scan portfolio for deteriorating credit signals",
  "inputSchema": {
    "type": "object",
    "properties": {
      "portfolio_id": { "type": "string" }
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "borrowers_scanned": { "type": "integer" },
      "alerts_generated": { "type": "integer" },
      "critical_count": { "type": "integer" },
      "alerts": { "type": "array" }
    }
  }
}
```

### Financial Analysis

```jsonc
{
  "name": "analyze_financials",
  "description": "Analyze financial statements: ratios, Z-Score, credit health",
  "inputSchema": {
    "type": "object",
    "properties": {
      "borrower_id": { "type": "string" }
    },
    "required": ["borrower_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "financials": { "type": "object" },
      "ratios": { "type": "object" },
      "altman_z_score": { "type": "object" },
      "credit_health": { "type": "string" }
    }
  }
}
```

### Risk Assessment

```jsonc
{
  "name": "assess_risk",
  "description": "Comprehensive risk assessment combining all data sources",
  "inputSchema": {
    "type": "object",
    "properties": {
      "borrower_id": { "type": "string" }
    },
    "required": ["borrower_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "risk_scores": { "type": "object" },
      "risk_rating": { "type": "string" },
      "recommendation": { "type": "string" },
      "stress_test": { "type": "object" }
    }
  }
}
```

---

## Vector Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR DB COLLECTIONS                        │
│                                                                 │
│  Collection: risk_policies                                      │
│  ───────────────────────                                        │
│  │  "Credit Risk Appetite: Target PD <2.5%..."            │    │
│  │  Metadata: {topic: "risk_appetite"}                     │    │
│                                                                 │
│  Collection: basel_requirements                                 │
│  ──────────────────────────                                     │
│  │  "Basel III: CET1 4.5%, Tier 1 6.0%..."              │    │
│  │  Metadata: {topic: "capital_requirements"}              │    │
│                                                                 │
│  Collection: credit_review_procedures                           │
│  ──────────────────────────────                                 │
│  │  "Annual Review: All loans >$1M require..."           │    │
│  │  Metadata: {process: "annual_review"}                   │    │
│                                                                 │
│  Collection: default_patterns                                   │
│  ────────────────────────                                       │
│  │  "Leading Indicators: Revenue decline >10%..."        │    │
│  │  Metadata: {topic: "leading_indicators"}               │    │
│                                                                 │
│  Collection: watchlist_criteria                                 │
│  ────────────────────────                                       │
│  │  "Watchlist Placement: Payment >30 days..."           │    │
│  │  Metadata: {topic: "placement"}                         │    │
│                                                                 │
│  Collection: regulatory_capital_rules                           │
│  ──────────────────────────────                                 │
│  │  "Capital Adequacy: CET1 + Retained Earnings..."     │    │
│  │  Metadata: {topic: "capital_adequacy"}                  │    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Portfolio Monitoring** | Real-time scan | Daily early warning scans catch deterioration early |
| **Financial Analysis** | Multi-ratio + Z-Score | Comprehensive view; Z-Score provides quick health check |
| **Risk Assessment** | Weighted composite | Financial (40%) + Market (30%) + Rating (30%) balanced view |
| **Alert Escalation** | Severity-based | Critical alerts immediately escalate; low alerts batch |
| **EL Calculation** | PD × LGD × EAD | Industry standard; auditable and regulatory compliant |
| **Watchlist** | Automatic + Discretionary | Automation catches objective triggers; analyst judgment for subjective |
| **Knowledge Retrieval** | RAG over policies | Always current risk policies; no retraining needed |
| **Stress Testing** | Scenario-based | Regulatory requirement; tests portfolio resilience |

---

## Risk Workflow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    CREDIT RISK MONITORING WORKFLOW               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  DAILY: Portfolio Scan                                   │   │
│  │  → Early warning scan                                    │   │
│  │  → Generate alerts                                       │   │
│  │  → Update watchlist                                      │   │
│  │  → Daily report                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  WEEKLY: Borrower Reviews                                │   │
│  │  → Deep-dive on flagged borrowers                        │   │
│  │  → Financial statement analysis                          │   │
│  │  → Rating monitoring                                     │   │
│  │  → Watchlist updates                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MONTHLY: Committee Review                               │   │
│  │  → Watchlist review                                      │   │
│  │  → Provisioning updates                                  │   │
│  │  → Classification changes                                │   │
│  │  → Policy adjustments                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  QUARTERLY: Regulatory Reporting                         │   │
│  │  → Stress test results                                   │   │
│  │  → Capital adequacy assessment                           │   │
│  │  → Portfolio quality metrics                             │   │
│  │  → Board reporting                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

*Architecture designed for Credit Risk Monitoring Agent (Section 6.1) — August 2026*
