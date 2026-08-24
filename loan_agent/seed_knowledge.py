"""
Seed script: Populate ChromaDB with loan application knowledge base data.

Includes:
- Loan regulations (TILA, ECOA, QM, HMDA)
- Product policies (conventional, FHA, auto, personal)
- Eligibility criteria (credit tiers, income, property)
- Underwriting guidelines (DTI, LTV, appraisal)
- Past loan decisions
- Fair lending guidelines (ECOA, adverse action)
- Credit scoring models (FICO, alternative scoring)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

LOAN_REGULATIONS = [
    {
        "id": "reg_tila_001",
        "text": "The Truth in Lending Act (TILA) requires lenders to disclose key terms and costs of credit to consumers. This includes APR, finance charges, amount financed, and total of payments. Lenders must provide a Loan Estimate within 3 business days of application and a Closing Disclosure at least 3 business days before closing.",
        "metadata": {"source": "CFPB", "section": "TILA/Regulation Z", "jurisdiction": "US", "type": "disclosure"},
    },
    {
        "id": "reg_ecoa_001",
        "text": "The Equal Credit Opportunity Act (ECOA) prohibits credit discrimination based on race, color, religion, national origin, sex, marital status, age, or receipt of public assistance. Lenders must notify applicants of action taken within 30 days. Adverse action notices must include specific reasons for denial.",
        "metadata": {"source": "CFPB", "section": "ECOA/Regulation B", "jurisdiction": "US", "type": "fair_lending"},
    },
    {
        "id": "reg_qm_001",
        "text": "Qualified Mortgage (QM) rules require lenders to make reasonable, good-faith determinations that borrowers have the ability to repay. QM loans generally cannot have: negative amortization, interest-only payments, balloon payments, or terms exceeding 30 years. The debt-to-income ratio must not exceed 43% for QM loans.",
        "metadata": {"source": "CFPB", "section": "QM Rule", "jurisdiction": "US", "type": "ability_to_repay"},
    },
    {
        "id": "reg_hmda_001",
        "text": "Home Mortgage Disclosure Act (HMDA) requires lenders to collect and report data about mortgage applications and originations. Data includes loan amount, interest rate, property type, ethnicity, race, sex, income, and action taken. This data is used to monitor fair lending practices.",
        "metadata": {"source": "CFPB", "section": "HMDA/Regulation C", "jurisdiction": "US", "type": "reporting"},
    },
    {
        "id": "reg_fair_lending_001",
        "text": "Fair lending laws prohibit discrimination in all aspects of a credit transaction. Pricing exceptions are permitted for: credit score differences, loan-to-value ratios, property type, loan amount, and geographic location. However, these exceptions must be applied consistently and documented.",
        "metadata": {"source": "OCC", "section": "Fair Lending", "jurisdiction": "US", "type": "pricing"},
    },
]

PRODUCT_POLICIES = [
    {
        "id": "pol_conventional_001",
        "text": "Conventional Mortgage — Requirements: 1. Minimum credit score: 620 (680+ preferred). 2. Maximum DTI: 45% (with compensating factors). 3. Down payment: 3% minimum for qualified buyers. 4. PMI required if LTV > 80%. 5. Employment: 2 years continuous employment. 6. Property: Primary residence, second home, or investment property.",
        "metadata": {"product": "conventional_mortgage", "version": "2024-Q3"},
    },
    {
        "id": "pol_fha_001",
        "text": "FHA Mortgage — Requirements: 1. Minimum credit score: 500 (10% down) or 580 (3.5% down). 2. Maximum DTI: 43% (up to 50% with compensating factors). 3. Mortgage insurance required for life of loan. 4. Property must meet FHA standards. 5. 2-year employment history required. 6. Non-occupant co-borrowers allowed.",
        "metadata": {"product": "fha_mortgage", "version": "2024-Q3"},
    },
    {
        "id": "pol_auto_loan_001",
        "text": "Auto Loan — Requirements: 1. Minimum credit score: 580 (660+ for best rates). 2. Maximum DTI: 50%. 3. Vehicle must be 10 years old or newer. 4. Maximum loan amount: $100,000. 5. Employment verification required. 6. GAP insurance recommended for loans with LTV > 90%.",
        "metadata": {"product": "auto_loan", "version": "2024-Q3"},
    },
    {
        "id": "pol_personal_loan_001",
        "text": "Personal Loan — Requirements: 1. Minimum credit score: 640. 2. Maximum DTI: 40%. 3. Maximum loan amount: $50,000. 4. No collateral required (unsecured). 5. Terms: 12-60 months. 6. Income verification: 2 years tax returns or 6 months bank statements.",
        "metadata": {"product": "personal_loan", "version": "2024-Q3"},
    },
]

ELIGIBILITY_CRITERIA = [
    {
        "id": "elig_credit_tiers_001",
        "text": "Credit Score Tiers for Loan Pricing: Tier 1 (750+): Best rates, automatic approval eligible, minimal documentation. Tier 2 (700-749): Competitive rates, standard documentation. Tier 3 (650-699): Above-market rates, additional documentation, manual review. Tier 4 (600-649): Subprime rates, full documentation, co-borrower recommended. Tier 5 (below 600): Decline or require significant down payment/co-borrower.",
        "metadata": {"topic": "credit_tiers", "version": "2024-Q3"},
    },
    {
        "id": "elig_income_001",
        "text": "Income Verification Requirements by Loan Type: Conventional: 2 years W-2s + recent paystub. Self-employed: 2 years tax returns + YTD P&L. Commission/Bonus: 2 years history of receipt. Rental Income: 2 years rental history + lease agreements. Retirement: Pension award letter + bank statements. All income must be stable, reliable, and likely to continue for 3+ years.",
        "metadata": {"topic": "income_requirements", "version": "2024-Q3"},
    },
    {
        "id": "elig_property_001",
        "text": "Property Eligibility: Primary residence: 1-4 units, condo, townhouse, SFR. Second home: 50+ miles from primary, no rental income. Investment property: 1-4 units, requires 15-25% down. Minimum property value: $50,000. Maximum property value: varies by program. Property must pass appraisal and meet lender standards.",
        "metadata": {"topic": "property_eligibility", "version": "2024-Q3"},
    },
]

UNDERWRITING_GUIDELINES = [
    {
        "id": "uw_dti_001",
        "text": "Debt-to-Income Ratio Guidelines: Front-end ratio (housing only): Maximum 28% for conventional, 31% for FHA. Back-end ratio (all debts): Maximum 36% preferred, 43% allowed with compensating factors, 50% maximum with strong compensating factors. Compensating factors include: high credit score (720+), significant cash reserves (6+ months), low LTV (70% or less), minimal payment shock, stable employment.",
        "metadata": {"topic": "dti_guidelines", "version": "2024-Q3"},
    },
    {
        "id": "uw_ltv_001",
        "text": "Loan-to-Value Ratio Guidelines: Conventional: 97% max (3% down). FHA: 96.5% max (3.5% down). VA: 100% (no down payment). PMI/MIP required above 80% LTV. Jumbo loans: typically 80-85% max LTV. Investment properties: 75-85% max LTV. Refinance: 95% max LTV for conventional, 97.75% for FHA.",
        "metadata": {"topic": "ltv_guidelines", "version": "2024-Q3"},
    },
]

PAST_LOAN_DECISIONS = [
    {
        "id": "case_approved_001",
        "text": "Approved: Conventional mortgage, $350,000, 30-year fixed. Borrower: credit score 742, DTI 31%, LTV 85%. W-2 income verified at $125,000/year, 5 years with same employer. No derogatory marks. PMI required (LTV > 80%). Rate: 6.25%. Approved by automated underwriting.",
        "metadata": {"decision": "approved", "product": "conventional", "risk": "low"},
    },
    {
        "id": "case_approved_002",
        "text": "Approved with conditions: FHA mortgage, $280,000, 30-year fixed. Borrower: credit score 648, DTI 38%, LTV 96.5%. Self-employed 3 years (tax returns verified). Rate: 7.0% + MIP. Conditions: 3 months reserves required, home inspection mandatory. Approved by manual underwriting.",
        "metadata": {"decision": "approved_with_conditions", "product": "fha", "risk": "medium"},
    },
    {
        "id": "case_declined_001",
        "text": "Declined: Personal loan, $50,000. Borrower: credit score 589, DTI 52%, recent late payments (2x in 12 months). Income unverifiable (self-employed < 2 years). No co-borrower. Reason: Exceeds DTI guidelines, insufficient credit history, income not stable. ECOA adverse action notice issued.",
        "metadata": {"decision": "declined", "product": "personal_loan", "risk": "high"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  NEW COLLECTIONS (3.2 Credit Scoring & Risk Assessment)
# ══════════════════════════════════════════════════════════════════

FAIR_LENDING_GUIDELINES = [
    {
        "id": "fair_lending_ecoa_001",
        "text": "ECOA Adverse Action Notice Requirements: When denying credit or offering less favorable terms, lenders must provide written notice within 30 days. The notice must include: 1) Specific reasons for the action (up to 4 reasons), 2) Name and address of the agency that provided the credit report, 3) Statement that the agency did not make the decision, 4) Right to obtain free credit report within 60 days, 5) Right to dispute inaccurate information. Reasons must be specific and accurate — vague reasons like 'credit profile' are not acceptable.",
        "metadata": {"source": "CFPB", "section": "ECOA/Reg B", "type": "adverse_action"},
    },
    {
        "id": "fair_lending_disparate_001",
        "text": "Disparate Impact Analysis: Lenders must ensure their credit policies do not disproportionately impact protected classes. Even neutral policies can violate fair lending if they have disparate impact. Mitigation requires: 1) Business necessity justification, 2) Less discriminatory alternative analysis, 3) Regular fair lending testing (regression analysis, matched-pair testing). Pricing exceptions based on credit score, LTV, and property type are permitted if applied consistently.",
        "metadata": {"source": "OCC", "section": "Fair Lending", "type": "disparate_impact"},
    },
    {
        "id": "fair_lending_overcharging_001",
        "text": "Pricing Fairness: Interest rates must be based on legitimate risk factors. Allowed risk-based pricing factors: credit score, LTV, loan amount, property type, occupancy status, geographic location, loan term. Prohibited factors: race, color, religion, national origin, sex, marital status, age, receipt of public assistance. All pricing exceptions must be documented and consistently applied across all applicants.",
        "metadata": {"source": "CFPB", "section": "Fair Lending Pricing", "type": "pricing"},
    },
    {
        "id": "fair_lending_examples_001",
        "text": "Fair Lending Violation Examples: 1) Charging higher rates to minority applicants with identical credit profiles. 2) Requiring additional documentation from certain ethnic groups. 3) Steering minority applicants to higher-cost products. 4) Different underwriting standards based on protected class. 5) Discouraging applications from certain neighborhoods (redlining). Penalties include fines, consent orders, and reputational damage.",
        "metadata": {"source": "DOJ", "section": "Fair Lending Enforcement", "type": "violations"},
    },
]

CREDIT_SCORING_MODELS = [
    {
        "id": "fico_factors_001",
        "text": "FICO Score Components: Payment History (35%): Most important factor. On-time payments build score; late payments, collections, bankruptcies hurt score. Amounts Owed (30%): Credit utilization ratio. Keep balances below 30% of credit limits. Length of Credit History (15%): Average age of accounts. Longer history is better. New Credit (10%): Recent hard inquiries and new accounts. Too many can hurt score. Credit Mix (10%): Variety of credit types (credit cards, auto loans, mortgages). Having a mix helps.",
        "metadata": {"source": "FICO", "model": "FICO 8", "type": "scoring_factors"},
    },
    {
        "id": "fico_ranges_001",
        "text": "FICO Score Ranges: Exceptional (800-850): Qualifies for best rates, minimal documentation. Very Good (740-799): Qualifies for excellent rates. Good (670-739): Above average, qualifies for most products. Fair (580-669): Below average, may qualify with conditions. Poor (300-579): Significant credit issues, likely declined. VantageScore uses similar ranges but different weights.",
        "metadata": {"source": "FICO", "ranges": "300-850", "type": "scoring_ranges"},
    },
    {
        "id": "alt_scoring_001",
        "text": "Alternative Credit Scoring: For consumers with thin credit files or no FICO score. Alternative data sources: rent payments, utility bills, phone payments, bank account cash flow, employment history. FICO XD and VantageScore 4.0 incorporate alternative data. UltraFICO considers checking/savings account behavior. Alternative scoring can increase scoreable population by ~50 million consumers. Must still comply with ECOA — cannot use prohibited factors.",
        "metadata": {"source": "CFPB", "type": "alternative_scoring"},
    },
    {
        "id": "scoring_best_practices_001",
        "text": "Credit Scoring Best Practices: 1) Use validated models with documented performance metrics. 2) Regularly backtest models against actual default rates. 3) Monitor for disparate impact across protected classes. 4) Maintain model documentation for regulatory examination. 5) Implement override tracking and monitoring. 6) Provide reason codes for all adverse decisions. 7) Review and update models at least annually. 8) Document all model changes and approvals.",
        "metadata": {"source": "OCC", "type": "model_governance"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "loan_regulations": LOAN_REGULATIONS,
        "product_policies": PRODUCT_POLICIES,
        "eligibility_criteria": ELIGIBILITY_CRITERIA,
        "underwriting_guidelines": UNDERWRITING_GUIDELINES,
        "past_loan_decisions": PAST_LOAN_DECISIONS,
        "fair_lending_guidelines": FAIR_LENDING_GUIDELINES,
        "credit_scoring_models": CREDIT_SCORING_MODELS,
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
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
