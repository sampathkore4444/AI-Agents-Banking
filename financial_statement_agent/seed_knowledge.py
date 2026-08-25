"""
Seed script: Populate ChromaDB with financial statement analysis knowledge base data.

Includes:
- Accounting standards (IFRS, GAAP)
- Analytical frameworks (DuPont, Altman Z-Score, Piotroski F-Score)
- Industry benchmarks (by sector)
- Ratio definitions and interpretation
- Credit analysis methodologies
- Financial statement structures
- Regulatory reporting requirements

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  ACCOUNTING STANDARDS
# ══════════════════════════════════════════════════════════════════

ACCOUNTING_STANDARDS = [
    {
        "id": "std_gaap_001",
        "text": "US GAAP (Generally Accepted Accounting Principles): Core principles for US financial reporting. Key standards: ASC 606 (Revenue Recognition — five-step model: identify contract, identify performance obligations, determine transaction price, allocate price, recognize revenue), ASC 360 (Property, Plant & Equipment — impairment testing, depreciation), ASC 820 (Fair Value Measurement — Level 1/2/3 hierarchy), ASC 842 (Leases — right-of-use assets and lease liabilities on balance sheet), ASC 740 (Income Taxes — deferred tax assets/liabilities). Financial statements required: Balance Sheet, Income Statement, Cash Flow Statement, Statement of Stockholders' Equity, Notes.",
        "metadata": {"source": "FASB", "category": "gaap", "type": "standard"},
    },
    {
        "id": "std_ifrs_001",
        "text": "IFRS (International Financial Reporting Standards): Global accounting standards issued by IASB. Key differences from GAAP: IFRS principles-based vs GAAP rules-based, IFRS prohibits LIFO inventory, IFRS allows revaluation of PP&E, IFRS IAS 16 vs GAAP ASC 360, IFRS IAS 38 (Intangibles — development costs capitalized if criteria met), IFRS 9 (Financial Instruments — expected credit loss model), IFRS 15 (Revenue Recognition — converged with ASC 606). Over 140 countries require or permit IFRS reporting.",
        "metadata": {"source": "IASB", "category": "ifrs", "type": "standard"},
    },
    {
        "id": "std_revenue_001",
        "text": "Revenue Recognition (ASC 606 / IFRS 15): Five-step model: 1) Identify the contract, 2) Identify performance obligations, 3) Determine transaction price (including variable consideration), 4) Allocate price to performance obligations, 5) Recognize revenue when/as obligations satisfied. Key concepts: Point-in-time vs over-time recognition, contract modifications, principal vs agent (gross vs net reporting), bill-and-hold arrangements, consignment. Industry impact: Software (subscription transition), Telecom (bundled arrangements), Construction (percentage-of-completion).",
        "metadata": {"source": "FASB/IASB", "category": "revenue", "type": "standard"},
    },
    {
        "id": "std_lease_001",
        "text": "Lease Accounting (ASC 842 / IFRS 16): Lessee accounting: Recognize right-of-use (ROU) asset and lease liability on balance sheet for all leases > 12 months. Key differences: IFRS 16 has single lessee model (all leases on balance sheet), ASC 842 distinguishes operating vs finance leases (different income statement treatment). Lease liability = PV of future lease payments. ROU asset = lease liability + initial direct costs + prepayments - incentives. Sale-and-leaseback transactions require specific treatment under both standards.",
        "metadata": {"source": "FASB/IASB", "category": "leases", "type": "standard"},
    },
    {
        "id": "std_impairment_001",
        "text": "Asset Impairment Testing: Goodwill: Annual impairment test under ASC 350 (two-step: fair value comparison, then implied goodwill calculation). Under ASC 360 (post-2017 update): One-step quantitative test. IAS 36: Annual impairment test, reversals allowed (except goodwill). Indefinite-lived intangibles: Annual fair value test. Long-lived assets (ASC 360): Trigger-based testing when events indicate potential impairment. Recoverability test: Undiscounted cash flows > carrying amount. Measurement: Fair value less cost to sell. Indicators: Significant decline in market value, adverse changes in business environment, sustained operating losses.",
        "metadata": {"source": "FASB/IASB", "category": "impairment", "type": "standard"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  ANALYTICAL FRAMEWORKS
# ══════════════════════════════════════════════════════════════════

ANALYTICAL_FRAMEWORKS = [
    {
        "id": "fw_dupont_001",
        "text": "DuPont Analysis Framework: Decomposes ROE into three (or five) components: ROE = Net Profit Margin × Asset Turnover × Equity Multiplier. Three-component: Profitability (Net Income/Revenue) × Efficiency (Revenue/Total Assets) × Leverage (Total Assets/Equity). Five-component: ROE = (Net Income/EBT) × (EBT/EBIT) × (EBIT/Revenue) × (Revenue/Assets) × (Assets/Equity) = Tax Burden × Interest Burden × Operating Margin × Asset Turnover × Financial Leverage. High ROE from leverage is riskier than from profitability. Useful for identifying drivers of return deterioration.",
        "metadata": {"source": "Analytical Framework", "category": "dupont", "type": "framework"},
    },
    {
        "id": "fw_altman_001",
        "text": "Altman Z-Score Model: Bankruptcy prediction model for publicly traded manufacturers: Z = 1.2(X1) + 1.4(X2) + 3.3(X3) + 0.6(X4) + 1.0(X5). Where: X1 = Working Capital/Total Assets, X2 = Retained Earnings/Total Assets, X3 = EBIT/Total Assets, X4 = Market Value of Equity/Book Value of Total Liabilities, X5 = Sales/Total Assets. Zones: Z > 3.0 = Safe, 1.8 < Z < 3.0 = Gray Zone, Z < 1.8 = Distress. Modified Z'-Score for private firms: Z' = 0.717(X1) + 0.847(X2) + 3.107(X3) + 0.420(X4) + 0.998(X5). Accuracy: ~90% within 1 year of bankruptcy.",
        "metadata": {"source": "Analytical Framework", "category": "altman", "type": "framework"},
    },
    {
        "id": "fw_piotroski_001",
        "text": "Piotroski F-Score (2000): 0-9 score measuring financial strength using 8 binary signals: 1) ROA > 0 (+1), 2) CFO > 0 (+1), 3) ROA improving (+1), 4) CFO > Net Income (+1, quality of earnings), 5) Long-term debt decreasing (+1), 6) Current ratio improving (+1), 7) No new shares issued (+1), 8) Gross margin improving (+1), 9) Asset turnover improving (+1). Score interpretation: 0-2 = Strong sell, 3-5 = Hold, 6-7 = Buy, 8-9 = Strong buy. Back-tested to produce 7.5% annual alpha in high book-to-market decile.",
        "metadata": {"source": "Analytical Framework", "category": "piotroski", "type": "framework"},
    },
    {
        "id": "fw_liquidity_001",
        "text": "Liquidity Analysis Framework: Short-term solvency assessment using: Current Ratio (Current Assets/Current Liabilities) — healthy > 1.5, warning < 1.0. Quick Ratio ((Cash + Receivables + Short-term Investments)/Current Liabilities) — healthy > 1.0, warning < 0.7. Cash Ratio (Cash + Cash Equivalents/Current Liabilities) — most conservative, healthy > 0.5. Operating Cash Flow Ratio (CFO/Current Liabilities) — measures ability to pay from operations. Net Working Capital = Current Assets - Current Liabilities. Cash Conversion Cycle = DIO + DSO - DPO (lower is better).",
        "metadata": {"source": "Analytical Framework", "category": "liquidity", "type": "framework"},
    },
    {
        "id": "fw_solvency_001",
        "text": "Solvency & Leverage Framework: Long-term debt capacity analysis: Debt-to-Equity (Total Debt/Total Equity) — varies by industry, manufacturing ~1.0, utilities ~1.5-2.0. Debt-to-Capital (Total Debt/(Total Debt+Equity)). Interest Coverage Ratio (EBIT/Interest Expense) — healthy > 3.0, danger < 1.5. Debt Service Coverage Ratio (NOI/Total Debt Service) — for real estate. Fixed Charge Coverage ((EBIT + Lease Payments)/(Interest + Lease Payments)). Debt-to-EBITDA — credit rating metric, investment grade typically < 3.0x. Net Debt = Total Debt - Cash & Equivalents.",
        "metadata": {"source": "Analytical Framework", "category": "solvency", "type": "framework"},
    },
    {
        "id": "fw_profitability_001",
        "text": "Profitability Analysis Framework: Margin analysis across the income statement: Gross Profit Margin (Gross Profit/Revenue) — measures production efficiency. Operating Profit Margin (Operating Income/Revenue) — core business profitability. Net Profit Margin (Net Income/Revenue) — bottom-line profitability. EBITDA Margin (EBITDA/Revenue) — cash earnings proxy. Return on Assets (Net Income/Total Assets) — asset utilization. Return on Equity (Net Income/Equity) — shareholder return. Return on Invested Capital (NOPAT/Invested Capital) — value creation above cost of capital. Economic Value Added (NOPAT - (Invested Capital × WACC)).",
        "metadata": {"source": "Analytical Framework", "category": "profitability", "type": "framework"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  INDUSTRY BENCHMARKS
# ══════════════════════════════════════════════════════════════════

INDUSTRY_BENCHMARKS = [
    {
        "id": "bench_tech_001",
        "text": "Technology Industry Benchmarks (NAICS 51): Median current ratio: 2.8, Median debt-to-equity: 0.4, Median gross margin: 55%, Median operating margin: 18%, Median net margin: 15%, Median ROA: 12%, Median ROE: 18%, Median interest coverage: 15.0x. Key metrics: R&D as % of revenue (8-15%), SBC as % of revenue (5-12%), Free cash flow margin (12-20%). Characteristics: High gross margins, low capex intensity, significant intangible assets, rapid revenue growth expected. Red flags: Declining gross margins, increasing SBC, negative FCF despite revenue growth.",
        "metadata": {"source": "Industry Benchmark", "category": "technology", "type": "benchmark"},
    },
    {
        "id": "bench_manufacturing_001",
        "text": "Manufacturing Industry Benchmarks (NAICS 31-33): Median current ratio: 1.8, Median debt-to-equity: 0.8, Median gross margin: 30%, Median operating margin: 8%, Median net margin: 5%, Median ROA: 6%, Median ROE: 12%, Median interest coverage: 5.0x. Key metrics: Inventory turnover (5-8x), PP&E as % of revenue (25-40%), Capex/Revenue (3-6%). Characteristics: Capital intensive, inventory management critical, cyclical demand patterns. Red flags: Declining inventory turnover, rising capex without revenue growth, increasing debt for maintenance capex.",
        "metadata": {"source": "Industry Benchmark", "category": "manufacturing", "type": "benchmark"},
    },
    {
        "id": "bench_retail_001",
        "text": "Retail Industry Benchmarks (NAICS 44-45): Median current ratio: 1.3, Median debt-to-equity: 1.2, Median gross margin: 35%, Median operating margin: 5%, Median net margin: 3%, Median ROA: 7%, Median ROE: 15%, Median interest coverage: 4.0x. Key metrics: Inventory turnover (4-6x), Same-store sales growth, Revenue per square foot. Characteristics: High inventory turnover critical, thin margins, seasonal patterns, lease obligations significant. Red flags: Declining same-store sales, rising inventory days, lease liabilities growing faster than revenue.",
        "metadata": {"source": "Industry Benchmark", "category": "retail", "type": "benchmark"},
    },
    {
        "id": "bench_financial_001",
        "text": "Financial Services Benchmarks (NAICS 52): Median current ratio: N/A (different capital structure), Debt-to-equity: Regulatory driven (Basel III), Net interest margin: 2.5-3.5%, Return on assets: 1.0-1.5%, Return on equity: 10-15%, Efficiency ratio: 55-65%, CET1 capital ratio: > 10.5%. Key metrics: Provision for loan losses/Total loans, Non-performing loans/Total loans (<2% healthy), Loan loss reserves/NPLs (>80%). Characteristics: Highly regulated, leverage constrained by capital requirements, interest rate sensitive. Red flags: Rising NPLs, declining net interest margin, increasing efficiency ratio.",
        "metadata": {"source": "Industry Benchmark", "category": "financial", "type": "benchmark"},
    },
    {
        "id": "bench_healthcare_001",
        "text": "Healthcare Industry Benchmarks (NAICS 62): Median current ratio: 1.6, Median debt-to-equity: 0.9, Median gross margin: 40%, Median operating margin: 10%, Median net margin: 7%, Median ROA: 6%, Median ROE: 13%, Median interest coverage: 4.5x. Key metrics: Days in A/R (45-60), Bad debt expense/Revenue (2-5%), Government payer mix. Characteristics: Regulatory complexity, reimbursement uncertainty, significant R&D for pharma, capital equipment intensive for hospitals. Red flags: Rising days in A/R, increasing bad debt, declining reimbursement rates.",
        "metadata": {"source": "Industry Benchmark", "category": "healthcare", "type": "benchmark"},
    },
    {
        "id": "bench_energy_001",
        "text": "Energy Industry Benchmarks (NAICS 21): Median current ratio: 1.4, Median debt-to-equity: 0.7, Median gross margin: 40%, Median operating margin: 15%, Median net margin: 8%, Median ROA: 5%, Median ROE: 10%, Median interest coverage: 6.0x. Key metrics: Reserve life index, Finding & development cost per BOE, Debt/EBITDA (<2.0x for investment grade). Characteristics: Commodity price driven, long asset life, significant capex, reserve-based lending. Red flags: Rising F&D cost, declining reserve life, high leverage in low commodity price environment.",
        "metadata": {"source": "Industry Benchmark", "category": "energy", "type": "benchmark"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  RATIO DEFINITIONS
# ══════════════════════════════════════════════════════════════════

RATIO_DEFINITIONS = [
    {
        "id": "ratio_liquidity_001",
        "text": "Liquidity Ratios: Current Ratio = Current Assets / Current Liabilities (measures short-term obligation coverage; healthy > 1.5, warning < 1.0). Quick Ratio = (Cash + Marketable Securities + Accounts Receivable) / Current Liabilities (excludes inventory; healthy > 1.0). Cash Ratio = (Cash + Cash Equivalents) / Current Liabilities (most conservative; healthy > 0.5). Working Capital = Current Assets - Current Liabilities. Operating Cash Flow Ratio = Cash from Operations / Current Liabilities. Net Trade Working Capital = (Current Assets - Cash) - (Current Liabilities - Short-term Debt).",
        "metadata": {"source": "Financial Analysis", "category": "liquidity", "type": "ratio"},
    },
    {
        "id": "ratio_leverage_001",
        "text": "Leverage Ratios: Debt-to-Equity = Total Liabilities / Total Equity (measures financial leverage; varies by industry). Debt-to-Capital = Total Debt / (Total Debt + Total Equity). Interest Coverage = EBIT / Interest Expense (measures ability to service debt; healthy > 3.0, danger < 1.5). Debt Service Coverage = Net Operating Income / Total Debt Service (for real estate). Debt-to-EBITDA = Total Debt / EBITDA (credit rating metric; IG < 3.0x). Fixed Charge Coverage = (EBIT + Lease Payments) / (Interest + Lease Payments). Net Debt = Total Debt - Cash & Equivalents.",
        "metadata": {"source": "Financial Analysis", "category": "leverage", "type": "ratio"},
    },
    {
        "id": "ratio_profitability_001",
        "text": "Profitability Ratios: Gross Margin = (Revenue - COGS) / Revenue (production efficiency). Operating Margin = Operating Income / Revenue (core business profitability). Net Margin = Net Income / Revenue (bottom-line profitability). EBITDA Margin = EBITDA / Revenue (cash earnings proxy). Return on Assets = Net Income / Total Assets (asset utilization). Return on Equity = Net Income / Shareholders' Equity (shareholder return). Return on Invested Capital = NOPAT / Invested Capital (value creation vs cost of capital). Economic Value Added = NOPAT - (Invested Capital × WACC).",
        "metadata": {"source": "Financial Analysis", "category": "profitability", "type": "ratio"},
    },
    {
        "id": "ratio_efficiency_001",
        "text": "Efficiency Ratios: Asset Turnover = Revenue / Total Assets (asset utilization). Inventory Turnover = COGS / Average Inventory (inventory management; higher is better). Days Inventory Outstanding = 365 / Inventory Turnover. Receivables Turnover = Revenue / Average Receivables. Days Sales Outstanding = 365 / Receivables Turnover (collection efficiency). Payables Turnover = COGS / Average Payables. Days Payable Outstanding = 365 / Payables Turnover. Cash Conversion Cycle = DIO + DSO - DPO (lower is better). Fixed Asset Turnover = Revenue / Net PP&E.",
        "metadata": {"source": "Financial Analysis", "category": "efficiency", "type": "ratio"},
    },
    {
        "id": "ratio_valuation_001",
        "text": "Valuation Ratios: Price-to-Earnings (P/E) = Market Price per Share / EPS (earnings multiple). Price-to-Book (P/B) = Market Price per Share / Book Value per Share. Price-to-Sales (P/S) = Market Cap / Revenue. EV/EBITDA = Enterprise Value / EBITDA (enterprise-level valuation). EV/Revenue = Enterprise Value / Revenue. Price-to-Cash Flow = Market Price per Share / Operating Cash Flow per Share. Dividend Yield = Annual Dividends per Share / Market Price per Share. PEG Ratio = P/E / Expected EPS Growth Rate (growth-adjusted PE).",
        "metadata": {"source": "Financial Analysis", "category": "valuation", "type": "ratio"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CREDIT ANALYSIS
# ══════════════════════════════════════════════════════════════════

CREDIT_ANALYSIS = [
    {
        "id": "credit_rating_001",
        "text": "Credit Rating Methodology (S&P / Moody's): Key financial metrics for investment grade: Debt/EBITDA < 3.0x, FFO/Debt > 30%, EBITDA Interest Coverage > 5.0x, Funds from Operations/Total Debt > 20%. Rating categories: AAA (highest quality), AA, A, BBB (lowest investment grade), BB, B, CCC, CC, C, D (default). Key qualitative factors: Industry position, business diversification, management quality, financial policy (M&A appetite, share buybacks), competitive landscape. Rating transition matrices show annual migration rates between categories.",
        "metadata": {"source": "Credit Analysis", "category": "rating", "type": "analysis"},
    },
    {
        "id": "credit_spread_001",
        "text": "Credit Spread Analysis: Spread = Corporate Bond Yield - Treasury Yield of same maturity. Spreads reflect default risk premium. Historical averages: Investment grade 100-200 bps, High yield 300-600 bps. Spread widening signals increasing credit risk. Spread compression signals improving credit quality or risk appetite. Key drivers: Default probability, Loss given default, Risk-free rate, Liquidity premium, Market risk sentiment. Expected loss = Probability of Default × Loss Given Default. Credit spread ≈ Expected loss + Risk premium + Liquidity premium.",
        "metadata": {"source": "Credit Analysis", "category": "spread", "type": "analysis"},
    },
    {
        "id": "credit_covenants_001",
        "text": "Financial Covenants: Common negative covenants: Maximum Debt/EBITDA, Minimum Interest Coverage, Minimum Net Worth, Maximum Capital Expenditures, Limitations on dividends/distributions, Change of control provisions. Financial maintenance covenants tested quarterly: Leverage ratio, Coverage ratio, Working capital minimum. Incurrence-based covenants: Triggered by specific events (M&A, new debt). Covenant breach consequences: Technical default, Acceleration of debt, Penalty rates, Restricted operations. Springing crevants: Only tested when revolver is drawn.",
        "metadata": {"source": "Credit Analysis", "category": "covenants", "type": "analysis"},
    },
    {
        "id": "credit_cashflow_001",
        "text": "Cash Flow Analysis for Credit: Free Cash Flow = CFO - CapEx. Adjusted FCF = FCF - Working Capital Changes - One-time items. Debt Service Coverage = CFO / (Interest + Mandatory Principal Payments). Free Cash Flow Yield = FCF / Market Cap. Cash flow adequacy: CFO/Revenue > 10% for most industries. Cash conversion: Net Income → CFO quality (CFO/NI > 1.0 indicates earnings quality). CapEx analysis: Maintenance CapEx vs Growth CapEx. Sustained negative FCF requires external financing (debt or equity).",
        "metadata": {"source": "Credit Analysis", "category": "cashflow", "type": "analysis"},
    },
    {
        "id": "credit_earnings_001",
        "text": "Earnings Quality Assessment: Quality indicators: 1) CFO > Net Income (cash backs earnings), 2) Accruals ratio low (Net Income - CFO)/Total Assets, 3) Non-recurring items separated, 4) Revenue recognition policy conservative, 5) No significant related party transactions, 6) Auditor opinion unqualified. Red flags: Growing gap between Net Income and CFO, Frequent non-recurring gains masking operating losses, Aggressive revenue recognition (bill-and-hold, channel stuffing), Rising accounts receivable relative to revenue, Increasing deferred revenue decline.",
        "metadata": {"source": "Credit Analysis", "category": "earnings_quality", "type": "analysis"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  FINANCIAL STATEMENT STRUCTURES
# ══════════════════════════════════════════════════════════════════

STATEMENT_STRUCTURES = [
    {
        "id": "stmt_balance_001",
        "text": "Balance Sheet Structure: Assets: Current Assets (Cash & Equivalents, Accounts Receivable, Inventory, Prepaid Expenses, Other Current Assets), Non-Current Assets (PP&E net, Operating Lease ROU Assets, Goodwill, Intangible Assets, Deferred Tax Assets, Other Non-Current Assets). Liabilities: Current Liabilities (Accounts Payable, Accrued Liabilities, Current Portion of Long-term Debt, Operating Lease Current Liabilities, Deferred Revenue, Other Current Liabilities), Non-Current Liabilities (Long-term Debt, Operating Lease Non-current Liabilities, Deferred Tax Liabilities, Pension Obligations, Other Non-Current Liabilities). Equity: Common Stock, APIC, Retained Earnings, Treasury Stock, AOCI.",
        "metadata": {"source": "Financial Reporting", "category": "balance_sheet", "type": "structure"},
    },
    {
        "id": "stmt_income_001",
        "text": "Income Statement Structure: Revenue (Net Revenue = Gross Revenue - Returns - Allowances - Discounts), Cost of Revenue (COGS), Gross Profit, Operating Expenses (Selling, General & Administrative; Research & Development; Depreciation & Amortization; Restructuring Charges; Impairment Charges), Operating Income (EBIT), Non-Operating Items (Interest Income, Interest Expense, Other Income/Expense), Pre-Tax Income (EBT), Income Tax Expense, Net Income, Earnings Per Share (Basic & Diluted). Non-GAAP metrics commonly reported: Adjusted EBITDA, Adjusted Net Income, Free Cash Flow.",
        "metadata": {"source": "Financial Reporting", "category": "income_statement", "type": "structure"},
    },
    {
        "id": "stmt_cashflow_001",
        "text": "Cash Flow Statement Structure: Operating Activities (Net Income adjusted for non-cash items: D&A, stock comp, deferred taxes, changes in working capital: AR, inventory, AP, accrued liabilities). Investing Activities (Capital expenditures, Acquisitions, Purchases/sales of investments, Asset dispositions). Financing Activities (Debt issuance/repayment, Equity issuance/buybacks, Dividends paid). Net Change in Cash = CFO + CFI + CFF. Reconciliation: Beginning Cash + Net Change = Ending Cash. Free Cash Flow = CFO - CapEx. Cash flow from operations is most critical for credit analysis.",
        "metadata": {"source": "Financial Reporting", "category": "cash_flow", "type": "structure"},
    },
    {
        "id": "stmt_equity_001",
        "text": "Statement of Stockholders' Equity: Components: Common Stock (par value × shares issued), Additional Paid-in Capital (APIC — excess over par), Retained Earnings (cumulative net income - dividends), Treasury Stock (cost of repurchased shares, contra-equity), Accumulated Other Comprehensive Income (AOCI — unrealized gains/losses on hedges, foreign currency translation, pension adjustments). Key transactions: Share issuances, Share repurchases (buybacks), Dividends (cash and stock), Stock-based compensation, Other comprehensive income items.",
        "metadata": {"source": "Financial Reporting", "category": "equity", "type": "structure"},
    },
    {
        "id": "stmt_notes_001",
        "text": "Financial Statement Notes (Key Disclosures): Summary of Significant Accounting Policies (revenue recognition, inventory method, depreciation, lease classification). Segment Reporting (ASC 280 / IFRS 8 — revenue and profit by segment). Contingencies and Commitments (litigation, guarantees, purchase obligations). Related Party Transactions. Subsequent Events. Fair Value Measurements (Level 1/2/3 hierarchy). Debt Schedule (maturity, interest rates, covenants). Pension and Post-retirement Benefits. Income Tax disclosures (effective rate reconciliation, deferred tax components).",
        "metadata": {"source": "Financial Reporting", "category": "notes", "type": "structure"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  REGULATORY REQUIREMENTS
# ══════════════════════════════════════════════════════════════════

REGULATORY_REQUIREMENTS = [
    {
        "id": "reg_sec_001",
        "text": "SEC Filing Requirements: Public companies must file: 10-K (Annual Report — audited financials, MD&A, risk factors), 10-Q (Quarterly Report — unaudited financials), 8-K (Current Report — material events within 4 business days), Proxy Statement (executive compensation, board elections). XBRL tagging required for all financial statements. SOX Section 302: CEO/CFO certification of financial statements. SOX Section 404: Internal control over financial reporting (ICFR) assessment. Accelerated filers: >$75M public float. Large accelerated filers: >$700M public float.",
        "metadata": {"source": "SEC", "category": "sec", "type": "regulatory"},
    },
    {
        "id": "reg_sox_001",
        "text": "Sarbanes-Oxley Act (SOX) Key Sections: Section 302: CEO/CFO must certify accuracy of financial statements and effectiveness of internal controls. Section 404(a): Management assessment of ICFR effectiveness (required for accelerated filers). Section 404(b): External auditor attestation of ICFR (required for large accelerated filers). Section 906: Criminal penalties for false certification (up to $5M fine, 20 years imprisonment). Section 409: Real-time disclosure of material changes in financial condition. Key for financial statement analysis: SOX compliance indicates stronger internal controls and financial reporting quality.",
        "metadata": {"source": "SEC", "category": "sox", "type": "regulatory"},
    },
    {
        "id": "reg_audit_001",
        "text": "Audit Standards and Requirements: PCAOB Standards: AS 2201 (ICFR audit), AS 3101 ( auditor's report). Key audit matters (KAM) required in auditor report for large accelerated filers. Going concern assessment: AS 2415 — must evaluate if substantial doubt exists about entity's ability to continue as going concern for 1 year from financial statement issuance. Materiality: Typically 3-5% of pre-tax income or 0.5-1% of revenue for planning materiality. Audit adjustments: Corrected misstatements vs uncorrected (must evaluate aggregate effect). Emphasis of matter paragraphs highlight specific disclosures.",
        "metadata": {"source": "PCAOB", "category": "audit", "type": "regulatory"},
    },
    {
        "id": "reg Basel_001",
        "text": "Basel III / Capital Requirements (for bank analysis): Common Equity Tier 1 (CET1) ratio: Minimum 4.5% of RWA. Tier 1 Capital ratio: Minimum 6.0% of RWA. Total Capital ratio: Minimum 8.0% of RWA. Capital conservation buffer: 2.5%. Countercyclical buffer: 0-2.5%. Leverage ratio: Tier 1 capital / Total exposure > 3%. Liquidity Coverage Ratio (LCR): High-quality liquid assets / Net cash outflows > 100%. Net Stable Funding Ratio (NSFR): Available stable funding / Required stable funding > 100%. For analyzing bank financial statements: Focus on capital ratios, asset quality (NPLs), and profitability (NIM).",
        "metadata": {"source": "BIS", "category": "basel", "type": "regulatory"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "accounting_standards": ACCOUNTING_STANDARDS,
        "analytical_frameworks": ANALYTICAL_FRAMEWORKS,
        "industry_benchmarks": INDUSTRY_BENCHMARKS,
        "ratio_definitions": RATIO_DEFINITIONS,
        "credit_analysis": CREDIT_ANALYSIS,
        "statement_structures": STATEMENT_STRUCTURES,
        "regulatory_requirements": REGULATORY_REQUIREMENTS,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  OK {collection_name}: {count} documents")

    print("\nFinancial Statement Analysis Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
