"""
Seed script: Populate ChromaDB with credit risk knowledge base data.

Collections:
- risk_policies: Internal risk management policies
- basel_requirements: Basel III/IV capital requirements
- credit_review_procedures: Review processes and workflows
- default_patterns: Historical default indicators and patterns
- watchlist_criteria: Watchlist placement and escalation rules
- regulatory_capital_rules: Capital adequacy requirements

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

RISK_POLICIES = [
    {"id": "rp_001", "text": "Credit Risk Appetite Statement: The bank maintains a moderate credit risk appetite. Target portfolio PD: <2.5%. Maximum single-name exposure: 5% of total capital. Minimum coverage ratio: 120%. Stress loss tolerance: <15% of Tier 1 capital. Risk-adjusted return target: >15% RAROC.", "metadata": {"topic": "risk_appetite", "source": "Risk Policy"}},
    {"id": "rp_002", "text": "Credit Review Policy: All commercial loans >$1M require annual review. Loans >$10M require semi-annual review. Watchlist loans require quarterly review. Criticized loans require monthly review. Reviews must include updated financials, site visits, and management assessment.", "metadata": {"topic": "credit_review", "source": "Risk Policy"}},
    {"id": "rp_003", "text": "Classification Policy: Pass: No concerns identified. Special Mention: Potential weakness requiring attention. Substandard: Well-defined weakness in capacity to repay. Doubtful: High probability of loss. Loss: Uncollectible. Classified loans require specific provisioning per FFIEC guidelines.", "metadata": {"topic": "classification", "source": "Risk Policy"}},
    {"id": "rp_004", "text": "Concentration Risk Policy: Single borrower limit: 10% of total capital. Single industry limit: 25% of total capital. Geographic concentration limit: 40% of total capital within single metro. Real estate concentration: Must perform quarterly stress test if >300% of Tier 1.", "metadata": {"topic": "concentration", "source": "Risk Policy"}},
    {"id": "rp_005", "text": "Watchlist Policy: Borrowers placed on watchlist when: 1) Payment >30 days past due, 2) Covenant breach (actual or anticipated), 3) Adverse rating action, 4) Material adverse change in financial condition, 5) Negative media exposure. Watchlist reviewed monthly by Credit Risk Committee.", "metadata": {"topic": "watchlist", "source": "Risk Policy"}},
]

BASEL_REQUIREMENTS = [
    {"id": "b_001", "text": "Basel III Capital Requirements: Minimum CET1 ratio: 4.5%. Minimum Tier 1 ratio: 6.0%. Minimum Total Capital ratio: 8.0%. Capital conservation buffer: 2.5%. Countercyclical buffer: 0-2.5% (varies by jurisdiction). G-SIB surcharge: 1-3.5% (for systemically important banks).", "metadata": {"topic": "capital_requirements", "source": "Basel III"}},
    {"id": "b_002", "text": "Risk-Weighted Assets (RWA) Calculation: Corporate exposures: 100% risk weight (standardized). Residential mortgages: 35-50% risk weight. sovereign exposures: 0-100% depending on rating. Off-balance sheet items: Credit conversion factor applied. Market risk: Using FRTB framework.", "metadata": {"topic": "rwa", "source": "Basel III"}},
    {"id": "b_003", "text": "Stress Testing Requirements: Annual DFAST stress test required for large banks. Scenarios: Severely Adverse, Adverse, Baseline. Must project losses over 9-quarter horizon. Capital planning must survive severely adverse scenario. Results disclosed in regulatory filings. CCAR: qualitative assessment of risk governance.", "metadata": {"topic": "stress_testing", "source": "Basel III"}},
    {"id": "b_004", "text": "Leverage Ratio: Minimum leverage ratio: 3% (Tier 1 capital / total exposure). Supplementary leverage ratio (SLR): 5% for G-SIBs. Includes off-balance sheet exposures. Backstop to risk-weighted capital requirements. Cannot be circumvented through risk-weight optimization.", "metadata": {"topic": "leverage_ratio", "source": "Basel III"}},
]

CREDIT_REVIEW_PROCEDURES = [
    {"id": "cr_001", "text": "Annual Credit Review Process: Step 1: Request updated financial statements (3 years + interim). Step 2: Analyze financial ratios and trends. Step 3: Update credit scorecard/rating. Step 4: Review collateral values. Step 5: Assess management quality. Step 6: Determine watchlist status. Step 7: Write review memo. Step 8: Present to Credit Committee. Turnaround: 15 business days.", "metadata": {"process": "annual_review", "source": "Credit Review"}},
    {"id": "cr_002", "text": "Watchlist Review Process: Monthly review includes: 1) Payment status update, 2) Financial performance vs plan, 3) Collateral value reassessment, 4) Recovery prospect analysis, 5) Escalation/reclassification recommendation. Quarterly: Full financial analysis update. Escalation path: Analyst → Manager → Committee → Board (if loss expected).", "metadata": {"process": "watchlist_review", "source": "Credit Review"}},
    {"id": "cr_003", "text": "Provisioning Methodology (CECL): Current Expected Credit Loss (CECL) replaces incurred loss model. Calculate lifetime expected loss at origination. Update quarterly based on: historical loss rates, current conditions, reasonable and supportable forecasts. Segmented by: portfolio, risk rating, vintage, geography. Qualitative adjustments for qualitative factors.", "metadata": {"process": "provisioning", "source": "CECL"}},
]

DEFAULT_PATTERNS = [
    {"id": "dp_001", "text": "Leading Indicators of Default: 1) Revenue decline >10% YoY, 2) EBITDA margin compression >300bps, 3) Leverage increase >1.0x in 12 months, 4) Interest coverage <2.0x, 5) Working capital deterioration, 6) Management changes (CFO departure), 7) Covenant breach or waiver request, 8) Industry downturn, 9) Loss of major customer, 10) Litigation or regulatory action.", "metadata": {"topic": "leading_indicators", "source": "Default Patterns"}},
    {"id": "dp_002", "text": "Default Timeline Patterns: Average time from first warning signal to default: 18-24 months. Most common sequence: Deterioration → Covenant breach → Waiver → Credit downgrade → Payment default. Early intervention (before covenant breach) reduces loss by 30-40%. Banks that engage early recover 15-20% more than those that delay.", "metadata": {"topic": "default_timeline", "source": "Default Patterns"}},
    {"id": "dp_003", "text": "Sector-Specific Default Patterns: Commercial Real Estate: Default follows vacancy rate increase (12-18 month lag). Energy: Default follows commodity price decline (6-12 month lag). Retail: Default follows traffic decline (3-6 month lag). Technology: Default follows funding market tightening (6-9 month lag). Healthcare: Default follows reimbursement rate changes (12-24 month lag).", "metadata": {"topic": "sector_patterns", "source": "Default Patterns"}},
    {"id": "dp_004", "text": "Recovery Rate Patterns: Senior Secured: 60-80% recovery rate. Senior Unsecured: 40-60% recovery rate. Subordinated: 20-40% recovery rate. Equity: 0-20% recovery rate. Recovery rates decline during recessions (avg 15-20% lower). Industry matters: Healthcare highest recovery, Real Estate lowest during downturns.", "metadata": {"topic": "recovery_rates", "source": "Default Patterns"}},
]

WATCHLIST_CRITERIA = [
    {"id": "wc_001", "text": "Watchlist Placement Criteria: Automatic placement: Payment >30 days past due, Covenant breach (any), Bankruptcy filing, Receivership. Discretionary placement: Rating downgrade, Adverse media, Industry stress, Management concerns, Collateral value decline >15%, Revenue decline >15%. Review cycle: Monthly for all watchlist items.", "metadata": {"topic": "placement", "source": "Watchlist Policy"}},
    {"id": "wc_002", "text": "Watchlist Escalation Rules: 30 days on watchlist: Analyst escalation to manager. 60 days: Manager escalation to committee. 90 days: Committee escalation to senior management. 120 days: Board notification required. Critical severity: Immediate escalation regardless of time. Payment default: Automatic reclassification.", "metadata": {"topic": "escalation", "source": "Watchlist Policy"}},
]

REGULATORY_CAPITAL_RULES = [
    {"id": "rc_001", "text": "Capital Adequacy Framework: CET1 Capital: Common equity, retained earnings, AOCI. Additional Tier 1: Non-cumulative perpetual preferred stock. Tier 2: Subordinated debt (5+ years), loan loss reserves. Deductions: Goodwill, intangibles, deferred tax assets >15% of CET1. Total capital ratio must exceed 10.5% (8% + 2.5% buffer).", "metadata": {"topic": "capital_adequacy", "source": "Regulatory Capital"}},
    {"id": "rc_002", "text": "Capital Planning Process: Annual capital plan submitted to regulators. Includes: Projected capital ratios over 9-quarter horizon, Capital actions (dividends, buybacks, issuances), Stress test results, Risk appetite alignment. Regulatory review: Qualitative (CCAR) + Quantitative (DFAST). Non-objection required before capital distributions.", "metadata": {"topic": "capital_planning", "source": "Regulatory Capital"}},
]


def seed() -> None:
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "risk_policies": RISK_POLICIES,
        "basel_requirements": BASEL_REQUIREMENTS,
        "credit_review_procedures": CREDIT_REVIEW_PROCEDURES,
        "default_patterns": DEFAULT_PATTERNS,
        "watchlist_criteria": WATCHLIST_CRITERIA,
        "regulatory_capital_rules": REGULATORY_CAPITAL_RULES,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  ✓ {collection_name}: {count} documents")

    print("\n✅ Knowledge base seeded successfully!")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
