"""
Seed script: Populate ChromaDB with product recommendation knowledge base data.

Includes:
- Product catalog (savings, checking, credit cards, loans, insurance, investments)
- Eligibility criteria (credit score, income, age, residency requirements)
- Cross-sell rules (product affinity, lifecycle triggers, bundling)
- Promotional offers (current campaigns, seasonal promotions, targeted offers)
- Customer segments (life stages, behavioral, value-based)
- Fee schedules (account fees, transaction fees, penalty fees)
- Competitor products (benchmarking, feature comparison)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  PRODUCT CATALOG
# ══════════════════════════════════════════════════════════════════

PRODUCT_CATALOG = [
    {
        "id": "prod_savings_001",
        "text": "High-Yield Savings Account — Earn 4.50% APY on balances up to $250,000. No minimum balance requirement. No monthly maintenance fee. FDIC insured up to $250,000. Free online and mobile banking. Automatic savings transfers available. 6 free withdrawals per month (Reg D). Ideal for emergency funds and short-term savings goals.",
        "metadata": {"product": "savings", "category": "deposit", "apy": 4.50, "min_balance": 0, "fee": 0, "target_segment": "all"},
    },
    {
        "id": "prod_checking_001",
        "text": "Premium Checking Account — $0 monthly fee with direct deposit ($500+). Free debit card. Free ATM network (55,000+ locations). Mobile check deposit. Online bill pay. Overdraft protection available. Earns 0.10% APY on balances over $10,000. Includes free checks. Ideal for everyday banking.",
        "metadata": {"product": "checking", "category": "deposit", "apy": 0.10, "min_balance": 0, "fee": 0, "target_segment": "all"},
    },
    {
        "id": "prod_credit_card_001",
        "text": "Cash Back Rewards Credit Card — Earn 2% cash back on all purchases, 3% on dining and entertainment, 1% on everything else. No annual fee. 0% introductory APR for 15 months on purchases and balance transfers. Free FICO score monthly. Contactless payment. Mobile wallet compatible. Credit limit $500-$10,000 based on creditworthiness.",
        "metadata": {"product": "credit_card", "category": "credit", "rewards_rate": 0.02, "annual_fee": 0, "intro_apr": 0.0, "target_segment": "all"},
    },
    {
        "id": "prod_credit_card_002",
        "text": "Travel Rewards Credit Card — Earn 3x points on travel and dining, 2x on all other purchases. $95 annual fee (waived first year). 60,000 bonus points after $3,000 spend in first 3 months. No foreign transaction fees. Priority boarding benefits. Global Entry/TSA PreCheck credit. Airport lounge access. Credit limit $2,000-$25,000.",
        "metadata": {"product": "credit_card", "category": "credit", "rewards_rate": 0.03, "annual_fee": 95, "intro_apr": None, "target_segment": "affluent"},
    },
    {
        "id": "prod_mortgage_001",
        "text": "30-Year Fixed Rate Mortgage — Competitive fixed rate for 30 years. Loan amounts $50,000-$2,000,000. Down payment as low as 3%. PMI required if LTV > 80%. Rate lock for 60 days. Digital application with pre-approval in 24 hours. No origination fee for qualified buyers. Ideal for first-time homebuyers.",
        "metadata": {"product": "mortgage", "category": "lending", "term_months": 360, "min_credit_score": 620, "target_segment": "homebuyers"},
    },
    {
        "id": "prod_auto_loan_001",
        "text": "Auto Loan — New and used vehicle financing. Terms 36-72 months. Rates starting at 4.99% APR. No down payment required for qualified buyers. Pre-approval in minutes. Refinancing available. GAP insurance optional. Pre-approved dealer network. Ideal for vehicle purchases.",
        "metadata": {"product": "auto_loan", "category": "lending", "min_credit_score": 660, "target_segment": "auto_buyers"},
    },
    {
        "id": "prod_personal_loan_001",
        "text": "Personal Loan — Unsecured loan from $2,000-$50,000. Fixed rates from 6.99% APR. Terms 24-60 months. No collateral required. Same-day funding available. No prepayment penalty. Ideal for debt consolidation, home improvement, or major purchases.",
        "metadata": {"product": "personal_loan", "category": "lending", "min_credit_score": 640, "target_segment": "all"},
    },
    {
        "id": "prod_cd_001",
        "text": "Certificate of Deposit (CD) — Fixed rates from 4.75% APY for 12 months, 4.50% for 24 months, 4.25% for 36 months. Minimum deposit $1,000. FDIC insured. Early withdrawal penalty applies. Automatic renewal option. Ideal for long-term savings with guaranteed returns.",
        "metadata": {"product": "cd", "category": "deposit", "apy": 4.75, "min_deposit": 1000, "target_segment": "conservative_savers"},
    },
    {
        "id": "prod_ira_001",
        "text": "Traditional IRA — Tax-deductible contributions (up to $7,000/year, $8,000 if 50+). Tax-deferred growth. Taxable withdrawals in retirement. Wide range of investment options (stocks, bonds, mutual funds, ETFs). No account maintenance fee. Required Minimum Distributions starting at age 73. Ideal for retirement planning.",
        "metadata": {"product": "ira", "category": "investment", "annual_limit": 7000, "target_segment": "retirement_planners"},
    },
    {
        "id": "prod_roth_ira_001",
        "text": "Roth IRA — After-tax contributions (up to $7,000/year). Tax-free growth and withdrawals in retirement. No Required Minimum Distributions. Withdraw contributions anytime penalty-free. Wide investment options. Income limits apply ($161,000 single, $240,000 married). Ideal for younger investors expecting higher future tax rates.",
        "metadata": {"product": "roth_ira", "category": "investment", "annual_limit": 7000, "target_segment": "young_professionals"},
    },
    {
        "id": "prod_home_equity_001",
        "text": "Home Equity Line of Credit (HELOC) — Borrow against home equity. Credit line $25,000-$500,000. Variable rate (Prime + 0.50%). 10-year draw period, 20-year repayment. Interest-only payments during draw. No annual fee. No prepayment penalty. Ideal for home improvements or large expenses.",
        "metadata": {"product": "heloc", "category": "lending", "min_credit_score": 680, "target_segment": "homeowners"},
    },
    {
        "id": "prod_student_loan_001",
        "text": "Private Student Loan — Refinance or supplement federal student loans. Fixed rates from 5.49% APR. Variable rates from 4.99% APR. Loan amounts $5,000-$300,000. Terms 5-20 years. Deferment options available. No origination fee. Ideal for graduate students and parents.",
        "metadata": {"product": "student_loan", "category": "lending", "min_credit_score": 650, "target_segment": "students"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  ELIGIBILITY CRITERIA
# ══════════════════════════════════════════════════════════════════

ELIGIBILITY_CRITERIA = [
    {
        "id": "elig_savings_001",
        "text": "Savings Account Eligibility: No minimum credit score required. Must be 18+ years old (or joint account with parent). Valid SSN or ITIN. US resident or citizen. No ChexSystems negative marks within last 12 months. One account per Social Security number.",
        "metadata": {"product": "savings", "requirements": ["age_18", "valid_ssn", "us_resident"]},
    },
    {
        "id": "elig_credit_card_001",
        "text": "Credit Card Eligibility — Cash Back: Minimum credit score 670. Debt-to-income ratio below 36%. No bankruptcies in last 7 years. No recent charge-offs. Must be 18+ years old. US resident. Annual income $12,000+ (or $15,000+ with co-signer).",
        "metadata": {"product": "credit_card", "requirements": ["credit_score_670", "dti_below_36", "age_18", "income_12000"]},
    },
    {
        "id": "elig_credit_card_002",
        "text": "Credit Card Eligibility — Travel Rewards: Minimum credit score 720. Debt-to-income ratio below 30%. No derogatory marks in last 5 years. Annual income $30,000+. Must be 18+ years old. US resident. No recent credit card applications (less than 3 in 12 months).",
        "metadata": {"product": "credit_card_premium", "requirements": ["credit_score_720", "dti_below_30", "age_18", "income_30000"]},
    },
    {
        "id": "elig_mortgage_001",
        "text": "Mortgage Eligibility: Minimum credit score 620 (680+ for best rates). Debt-to-income ratio below 43%. Down payment 3-20%. 2 years employment history. 2 years tax returns. Property appraisal required. PMI required if down payment < 20%. First-time homebuyer programs available.",
        "metadata": {"product": "mortgage", "requirements": ["credit_score_620", "dti_below_43", "employment_2yr", "down_payment_3pct"]},
    },
    {
        "id": "elig_auto_loan_001",
        "text": "Auto Loan Eligibility: Minimum credit score 660 (700+ for best rates). Debt-to-income ratio below 50%. Vehicle must be 10 years old or newer. Maximum loan amount $100,000. Employment verification required. GAP insurance recommended for LTV > 90%.",
        "metadata": {"product": "auto_loan", "requirements": ["credit_score_660", "dti_below_50", "vehicle_age_10yr"]},
    },
    {
        "id": "elig_personal_loan_001",
        "text": "Personal Loan Eligibility: Minimum credit score 640. Debt-to-income ratio below 40%. No bankruptcies in last 7 years. 2 years income history. Maximum loan amount $50,000. No collateral required (unsecured). Terms 24-60 months.",
        "metadata": {"product": "personal_loan", "requirements": ["credit_score_640", "dti_below_40", "income_2yr"]},
    },
    {
        "id": "elig_ira_001",
        "text": "IRA Eligibility: Traditional IRA — Anyone with earned income can contribute (no income limit). Roth IRA — Single filers: MAGI below $161,000 (full contribution) or $161,000-$176,000 (reduced). Married filing jointly: MAGI below $240,000 (full) or $240,000-$255,000 (reduced). Must be 18+ to open.",
        "metadata": {"product": "ira", "requirements": ["earned_income", "age_18", "income_limit_roth"]},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CROSS-SELL RULES
# ══════════════════════════════════════════════════════════════════

CROSS_SELL_RULES = [
    {
        "id": "xsel_checking_savings_001",
        "text": "Checking → Savings Cross-Sell: Customers with checking accounts but no savings account have a 35% conversion rate when offered a high-yield savings account. Best timing: within 90 days of account opening. Offer: 0.25% APY bonus for first 6 months. Channel: in-app notification + email. Success rate: 35%.",
        "metadata": {"trigger": "has_checking_no_savings", "offer_type": "apy_bonus", "timing": "90_days"},
    },
    {
        "id": "xsel_debit_credit_001",
        "text": "Debit Card → Credit Card Cross-Sell: Customers using debit card 20+ times/month who have no credit card are prime candidates for cash back credit card. Credit score 670+ required. Best timing: after 6 months of active debit use. Offer: 0% intro APR for 15 months + $200 cash back bonus. Success rate: 28%.",
        "metadata": {"trigger": "active_debit_no_credit", "offer_type": "intro_apr_bonus", "timing": "6_months"},
    },
    {
        "id": "xsel_savings_investment_001",
        "text": "Savings → Investment Cross-Sell: Customers with savings > $10,000 for 6+ months are candidates for CD or IRA products. Credit score not required. Best timing: when CD rates are competitive. Offer: 0.50% APY bonus on first CD + free financial consultation. Success rate: 22%.",
        "metadata": {"trigger": "high_savings_balance", "offer_type": "cd_bonus", "timing": "6_months"},
    },
    {
        "id": "xsel_auto_insurance_001",
        "text": "Auto Loan → Insurance Cross-Sell: Customers with active auto loan are prime candidates for auto insurance. Best timing: within 30 days of loan origination. Offer: bundled discount (auto loan + insurance = 0.25% rate reduction on loan). Success rate: 40%.",
        "metadata": {"trigger": "has_auto_loan", "offer_type": "bundled_discount", "timing": "30_days"},
    },
    {
        "id": "xsel_mortgage_heloc_001",
        "text": "Mortgage → HELOC Cross-Sell: Homeowners with 20%+ equity after 2+ years are candidates for HELOC. Credit score 680+ required. Best timing: after home value appreciation. Offer: no annual fee for first year. Success rate: 18%.",
        "metadata": {"trigger": "mortgage_2yr_equity", "offer_type": "fee_waiver", "timing": "24_months"},
    },
    {
        "id": "xsel_student_refi_001",
        "text": "Student Loan → Refinance Cross-Sell: Customers with federal student loans and credit score 700+ are candidates for private refinancing. Best timing: when rates are competitive. Offer: 0.50% rate reduction + $200 cash back. Success rate: 15%.",
        "metadata": {"trigger": "has_student_loan_high_credit", "offer_type": "rate_reduction", "timing": "rate_dependent"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  PROMOTIONAL OFFERS
# ══════════════════════════════════════════════════════════════════

PROMOTIONAL_OFFERS = [
    {
        "id": "promo_savings_bonus_001",
        "text": "Q3 Savings Bonus: Earn an extra 0.50% APY on high-yield savings accounts opened before September 30, 2026. Minimum deposit $1,000. Bonus maintained for 12 months. Available to new and existing customers who open a new savings account. Limit one bonus per household.",
        "metadata": {"promo": "savings_bonus", "end_date": "2026-09-30", "min_deposit": 1000, "bonus_apy": 0.50},
    },
    {
        "id": "promo_credit_card_001",
        "text": "Summer Travel Promo: Earn 60,000 bonus points on Travel Rewards card (instead of standard 40,000). Must spend $4,000 in first 3 months. Offer valid through August 31, 2026. First-year annual fee waived. Free Global Entry credit ($100 value).",
        "metadata": {"promo": "travel_card_bonus", "end_date": "2026-08-31", "bonus_points": 60000, "spend_requirement": 4000},
    },
    {
        "id": "promo_mortgage_001",
        "text": "Homebuying Season Promo: $500 closing cost credit on new mortgage applications submitted before October 31, 2026. Minimum loan amount $200,000. Available for purchase transactions only. Cannot be combined with other offers.",
        "metadata": {"promo": "mortgage_credit", "end_date": "2026-10-31", "credit_amount": 500, "min_loan": 200000},
    },
    {
        "id": "promo_auto_loan_001",
        "text": "Auto Loan Rate Special: 0.25% rate reduction on new and used auto loans originated before September 15, 2026. Available for terms 48-72 months. Minimum loan amount $15,000. Refinancing also eligible.",
        "metadata": {"promo": "auto_rate_reduction", "end_date": "2026-09-15", "rate_reduction": 0.25, "min_loan": 15000},
    },
    {
        "id": "promo_referral_001",
        "text": "Referral Program: Earn $100 for each friend who opens a checking account and sets up direct deposit. Referred friend also earns $100. No limit on referrals. Bonus credited within 60 days of qualifying activity. Active through December 31, 2026.",
        "metadata": {"promo": "referral", "end_date": "2026-12-31", "referral_bonus": 100, "friend_bonus": 100},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CUSTOMER SEGMENTS
# ══════════════════════════════════════════════════════════════════

CUSTOMER_SEGMENTS = [
    {
        "id": "seg_student_001",
        "text": "Student Segment: Age 18-24, enrolled in college/university. Low income ($0-$25,000). No credit history or thin file. Needs: basic checking, student credit card, student loan refinancing. Best products: student checking (no fees), secured credit card, student loan. Channel: mobile-first, social media. Lifecycle stage: entry-level banking.",
        "metadata": {"segment": "students", "age_range": "18-24", "income_range": "0-25000", "lifecycle": "entry"},
    },
    {
        "id": "seg_young_professional_001",
        "text": "Young Professional Segment: Age 25-35, employed, income $40,000-$80,000. Building credit (score 650-740). Starting to save and invest. Needs: premium checking, cash back credit card, Roth IRA, auto loan. Best products: cash back card, high-yield savings, Roth IRA. Channel: mobile + digital. Lifecycle stage: growth.",
        "metadata": {"segment": "young_professionals", "age_range": "25-35", "income_range": "40000-80000", "lifecycle": "growth"},
    },
    {
        "id": "seg_family_001",
        "text": "Family Segment: Age 30-50, married with children. Income $80,000-$150,000. Established credit (score 700+). Homeownership likely. Needs: family checking, mortgage, auto loans, college savings, life insurance. Best products: premium checking, 529 plan, home equity, bundled insurance. Channel: branch + digital. Lifecycle stage: accumulation.",
        "metadata": {"segment": "families", "age_range": "30-50", "income_range": "80000-150000", "lifecycle": "accumulation"},
    },
    {
        "id": "seg_affluent_001",
        "text": "Affluent Segment: Age 35-65, high income ($150,000+). Excellent credit (score 750+). Multiple existing products. High net worth. Needs: wealth management, premium credit card, investment accounts, estate planning. Best products: travel rewards card, brokerage account, private banking, trust services. Channel: dedicated advisor + digital. Lifecycle stage: preservation.",
        "metadata": {"segment": "affluent", "age_range": "35-65", "income_range": "150000+", "lifecycle": "preservation"},
    },
    {
        "id": "seg_retiree_001",
        "text": "Retiree Segment: Age 65+, retired. Fixed income ($30,000-$80,000 from pensions/SS/withdrawals). Excellent credit history. Low debt. Needs: income-focused investments, estate planning, long-term care, Medicare supplement. Best products: CD ladder, bond portfolio, trust services, health savings. Channel: branch + phone. Lifecycle stage: distribution.",
        "metadata": {"segment": "retirees", "age_range": "65+", "income_range": "30000-80000", "lifecycle": "distribution"},
    },
    {
        "id": "seg_small_business_001",
        "text": "Small Business Segment: Business owners with revenue $100K-$5M. Needs: business checking, business credit card, commercial loans, merchant services, payroll. Best products: business checking, business rewards card, SBA loans, merchant processing. Channel: relationship manager + digital. Lifecycle stage: business_growth.",
        "metadata": {"segment": "small_business", "revenue_range": "100000-5000000", "lifecycle": "business_growth"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  FEE SCHEDULES
# ══════════════════════════════════════════════════════════════════

FEE_SCHEDULES = [
    {
        "id": "fee_checking_001",
        "text": "Checking Account Fees: Monthly maintenance: $0 with direct deposit ($500+), otherwise $12/month. Out-of-network ATM: $3.00 per transaction. Overdraft: $35 per occurrence (3 per day max). Returned item: $35. Wire transfer (domestic): $25. Wire transfer (international): $45. Stop payment: $35. Cashier's check: $10. Paper statement: $3/month.",
        "metadata": {"product": "checking", "fee_type": "schedule"},
    },
    {
        "id": "fee_savings_001",
        "text": "Savings Account Fees: Monthly maintenance: $0 (no minimum balance). Excess withdrawals (beyond 6/month): $10 per transaction. Overdraft from savings: $10 per transfer. Wire transfer (domestic): $25. Wire transfer (international): $45. Account closure within 90 days: $25.",
        "metadata": {"product": "savings", "fee_type": "schedule"},
    },
    {
        "id": "fee_credit_card_001",
        "text": "Credit Card Fees — Cash Back: Annual fee: $0. Late payment: Up to $41. Returned payment: Up to $41. Balance transfer: 3% (min $5). Cash advance: 5% (min $10). Foreign transaction: 3%. Expedited payment: $15. Additional card: $0. Credit limit increase: $0.",
        "metadata": {"product": "credit_card", "fee_type": "schedule"},
    },
    {
        "id": "fee_mortgage_001",
        "text": "Mortgage Fees: Origination: $0 for qualified buyers. Application: $500 (refundable at closing). Appraisal: $400-$600. Title search: $300-$500. Recording fee: $100-$250. Flood certification: $20. Credit report: $30. Prepayment penalty: None. Late payment: 4% of payment amount.",
        "metadata": {"product": "mortgage", "fee_type": "schedule"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  COMPETITOR PRODUCTS
# ══════════════════════════════════════════════════════════════════

COMPETITOR_PRODUCTS = [
    {
        "id": "comp_savings_001",
        "text": "Competitor Benchmark — Savings: Industry average savings APY: 0.46% (national average). Top online banks: 4.50-5.00% APY. Our rate: 4.50% APY. Positioning: Competitive with top online banks. Advantage: No minimum balance, FDIC insured, full-service banking. Disadvantage: No physical branches for walk-in service.",
        "metadata": {"category": "savings", "benchmark_type": "apy"},
    },
    {
        "id": "comp_credit_card_001",
        "text": "Competitor Benchmark — Credit Cards: Cash back cards: 1.5-2% on all purchases (industry standard). Our card: 2% all purchases, 3% dining/entertainment. No annual fee. Positioning: Above-average rewards rate. Advantage: Higher category rewards, no annual fee. Disadvantage: No sign-up bonus category flexibility.",
        "metadata": {"category": "credit_card", "benchmark_type": "rewards"},
    },
    {
        "id": "comp_mortgage_001",
        "text": "Competitor Benchmark — Mortgage: Industry average 30-year fixed: 6.5-7.0% APR. Our rate: Competitive (within 0.125% of best available). Positioning: Digital-first experience with fast closing. Advantage: Pre-approval in 24 hours, $500 credit. Disadvantage: Fewer branch locations for in-person service.",
        "metadata": {"category": "mortgage", "benchmark_type": "rate"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "product_catalog": PRODUCT_CATALOG,
        "eligibility_criteria": ELIGIBILITY_CRITERIA,
        "cross_sell_rules": CROSS_SELL_RULES,
        "promotional_offers": PROMOTIONAL_OFFERS,
        "customer_segments": CUSTOMER_SEGMENTS,
        "fee_schedules": FEE_SCHEDULES,
        "competitor_products": COMPETITOR_PRODUCTS,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  ✓ {collection_name}: {count} documents")

    print("\n✅ Product Recommendation Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
