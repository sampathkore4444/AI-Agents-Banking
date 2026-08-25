"""
Seed script: Populate ChromaDB with standing order & bill payment knowledge base data.

Includes:
- Standing order policies (creation, modification, cancellation rules)
- Biller directory (supported billers, categories, payment methods)
- Payment schedules (frequency rules, calendar handling, edge cases)
- Recurring payment rules (limits, validations, compliance)
- Compliance requirements (Reg E, NACHA, UDAAP)
- Customer billing knowledge (common scenarios, troubleshooting)
- Operational playbooks (failure handling, dispute resolution)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  STANDING ORDER POLICIES
# ══════════════════════════════════════════════════════════════════

STANDING_ORDER_POLICIES = [
    {
        "id": "so_policy_001",
        "text": "Standing Order Creation Policy: Customers may create standing orders (recurring payments) via online banking, mobile app, or branch. Requirements: 1) Valid source account with sufficient funds, 2) Verified payee/biller information, 3) Selection of payment frequency (daily, weekly, biweekly, monthly, quarterly, semi-annual, annual), 4) Start date and optional end date, 5) Payment amount (fixed or variable with cap), 6) Confirmation via two-factor authentication for amounts > $5,000. Maximum 50 active standing orders per account.",
        "metadata": {"source": "Payment Operations", "category": "policy", "type": "creation"},
    },
    {
        "id": "so_policy_002",
        "text": "Standing Order Modification Policy: Customers may modify active standing orders including: amount (within limits), frequency, start/end dates, payee details, and source account. Changes to amount > 20% of original require re-verification. Changes take effect on next scheduled payment unless made > 24 hours before next execution. Amount increases > $10,000 require dual approval. Payee changes require out-of-band verification for first payment to new payee.",
        "metadata": {"source": "Payment Operations", "category": "policy", "type": "modification"},
    },
    {
        "id": "so_policy_003",
        "text": "Standing Order Cancellation Policy: Customers may cancel standing orders at any time before the next scheduled execution. Cancellation requests received within 24 hours of next execution may still process. Full cancellation confirmation provided within 1 business day. Refund of most recent payment available within 60 days per Reg E. Bank-initiated cancellation may occur for: suspected fraud, regulatory requirements, account closure, or repeated payment failures.",
        "metadata": {"source": "Payment Operations", "category": "policy", "type": "cancellation"},
    },
    {
        "id": "so_policy_004",
        "text": "Standing Order Execution Policy: Standing orders execute according to the defined schedule. If the scheduled date falls on a weekend or holiday, the payment processes on the next business day. If the source account has insufficient funds: 1) First attempt: retry next business day, 2) Second attempt: retry after 3 business days, 3) Third attempt: suspend standing order and notify customer. Maximum 3 consecutive failures before suspension. Failed payments may incur overdraft or NSF fees per fee schedule.",
        "metadata": {"source": "Payment Operations", "category": "policy", "type": "execution"},
    },
    {
        "id": "so_policy_005",
        "text": "Standing Order Limits Policy: Per-account limits: Maximum 50 active standing orders, Maximum single payment $50,000, Maximum daily aggregate $100,000. Approval thresholds: < $10,000 auto-approved, $10,000-$25,000 requires manager review, > $25,000 requires senior manager approval. Wire transfers via standing order subject to additional OFAC screening. International standing orders require purpose of payment documentation.",
        "metadata": {"source": "Compliance", "category": "policy", "type": "limits"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  BILLER DIRECTORY
# ══════════════════════════════════════════════════════════════════

BILLER_DIRECTORY = [
    {
        "id": "biller_utility_001",
        "text": "Utility Billers: Electric companies (ConEd, Duke Energy, PG&E, FPL), Gas companies (National Grid, SoCalGas, CenterPoint), Water utilities, Sewer services. Payment methods: ACH debit preferred, some accept check-by-phone. Typical amount: $50-$300/month. Billing cycle: Monthly. Late payment grace period: 10-15 days. Auto-pay discount available from most utilities (typically $2-$5/month savings).",
        "metadata": {"source": "Biller Directory", "category": "utility", "type": "biller_info"},
    },
    {
        "id": "biller_mortgage_001",
        "text": "Mortgage Billers: Wells Fargo, Chase, Bank of America, US Bank, Quicken Loans, local credit unions. Payment methods: ACH debit from checking/savings. Payment amount: Fixed monthly (PITI). Escrow adjustments may change amount quarterly. Late fee: typically 4-5% of payment after 15-day grace period. Prepayment: Standing order must be updated if paying extra principal. Notice requirement: 10 business days for amount changes.",
        "metadata": {"source": "Biller Directory", "category": "mortgage", "type": "biller_info"},
    },
    {
        "id": "biller_insurance_001",
        "text": "Insurance Billers: Auto insurance (GEICO, State Farm, Progressive, Allstate), Homeowners insurance, Life insurance, Health insurance. Payment methods: ACH debit, credit card (some charge convenience fee). Billing: Monthly, quarterly, semi-annual, or annual. Multi-policy discount may require annual payment. Policy cancellation for non-payment: typically after 30 days past due. Agent contact information required for policy-specific questions.",
        "metadata": {"source": "Biller Directory", "category": "insurance", "type": "biller_info"},
    },
    {
        "id": "biller_subscription_001",
        "text": "Subscription Services: Streaming (Netflix, Hulu, Spotify, Disney+), Software (Microsoft 365, Adobe Creative Cloud), Gym memberships, Magazine subscriptions. Payment methods: Credit/debit card (ACH for some). Billing: Monthly or annual. Cancellation: Requires customer action, bank cannot cancel without customer authorization. Amount changes: Biller notifies customer 30 days before price increases. Card-on-file updates: Standing order may fail if card expires — customer must update.",
        "metadata": {"source": "Biller Directory", "category": "subscription", "type": "biller_info"},
    },
    {
        "id": "biller_loan_001",
        "text": "Loan Billers: Auto loans (Capital One, Ally, local credit unions), Personal loans, Student loans (federal: Nelnet, MOHELA; private: SoFi, Earnest), Business loans. Payment methods: ACH debit preferred. Federal student loans: Income-driven repayment plans may result in variable amounts. Forbearance/deferment: Standing order should be paused during approved periods. Auto-pay discount: Typically 0.25% interest rate reduction.",
        "metadata": {"source": "Biller Directory", "category": "loan", "type": "biller_info"},
    },
    {
        "id": "biller_telecom_001",
        "text": "Telecommunications Billers: Mobile carriers (Verizon, AT&T, T-Mobile), Internet providers (Comcast, Spectrum, AT&T Fiber), Landline phone services. Payment methods: ACH debit, credit/debit card. Billing: Monthly. Amount varies based on usage and plan changes. Equipment charges (router rental, phone lease) included. Early termination fees may apply. Bundled services: Single biller for multiple services.",
        "metadata": {"source": "Biller Directory", "category": "telecom", "type": "biller_info"},
    },
    {
        "id": "biller_govt_001",
        "text": "Government Billers: Property tax (county assessor), Vehicle registration (DMV), Business licenses, Federal tax (IRS — EFTPS), State tax. Payment methods: ACH debit, check. Property tax: Semi-annual or annual. Vehicle registration: Annual. IRS EFTPS: Required for business tax payments > $100K. Penalty for late payment: 0.5%/month on unpaid tax. Standing order must align with assessment calendar.",
        "metadata": {"source": "Biller Directory", "category": "government", "type": "biller_info"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  PAYMENT SCHEDULES
# ══════════════════════════════════════════════════════════════════

PAYMENT_SCHEDULES = [
    {
        "id": "schedule_daily_001",
        "text": "Daily Standing Order Rules: Daily payments execute every business day (Monday-Friday). Weekend/holiday handling: Payment deferred to next business day. Use cases: Rent payments on business day schedules, daily savings transfers. Limitations: Cannot execute on weekends, max 260 payments/year. Customer must specify: start date, end date (or indefinite), amount, source account.",
        "metadata": {"source": "Scheduling Engine", "category": "daily", "type": "schedule_rule"},
    },
    {
        "id": "schedule_weekly_001",
        "text": "Weekly Standing Order Rules: Payments execute on a specified day of the week (e.g., every Friday). Customer selects: day of week, amount, source account, start/end dates. Common patterns: Payroll alignment (Friday pay = Thursday transfer), rent due dates (1st of month). If selected day falls on holiday, payment defers to next business day. Annual frequency: 52 payments/year.",
        "metadata": {"source": "Scheduling Engine", "category": "weekly", "type": "schedule_rule"},
    },
    {
        "id": "schedule_monthly_001",
        "text": "Monthly Standing Order Rules: Most common frequency for bill payments. Customer selects: day of month (1-28) or last business day of month. Months with fewer days: If day 31 selected, payment on last day of shorter months. End-of-month option: Always pays on last business day regardless of month length. Common bill due dates: 1st (rent/mortgage), 15th (utilities), 25th (credit card). Annual frequency: 12 payments/year.",
        "metadata": {"source": "Scheduling Engine", "category": "monthly", "type": "schedule_rule"},
    },
    {
        "id": "schedule_quarterly_001",
        "text": "Quarterly Standing Order Rules: Payments execute every 3 months. Standard quarters: Jan/Apr/Jul/Oct or Feb/May/Aug/Nov or Mar/Jun/Sep/Dec. Customer selects: quarter start month, day of month, amount. Use cases: Insurance premiums, HOA dues, estimated tax payments, maintenance contracts. If day falls on weekend/holiday, defers to next business day. Annual frequency: 4 payments/year.",
        "metadata": {"source": "Scheduling Engine", "category": "quarterly", "type": "schedule_rule"},
    },
    {
        "id": "schedule_annual_001",
        "text": "Annual Standing Order Rules: Payments execute once per year on a specified date. Use cases: Annual insurance premiums, membership renewals, property tax, subscription renewals. Customer selects: month and day, amount, source account. Reminder: System sends reminder 7 days and 1 day before execution. If date falls on weekend/holiday, defers to next business day. Amount may change annually — customer must update before execution.",
        "metadata": {"source": "Scheduling Engine", "category": "annual", "type": "schedule_rule"},
    },
    {
        "id": "schedule_custom_001",
        "text": "Custom Standing Order Rules: For frequencies not covered by standard options. Examples: Biweekly (every 2 weeks), Semi-monthly (1st and 15th), Every 6 weeks, Specific days of week (Mon/Wed/Fri). System calculates next execution date based on custom interval. Customer provides: interval in days, start date, amount. System validates: minimum interval ≥ 1 day, maximum interval ≤ 365 days. Custom schedules require manual review for amounts > $10,000.",
        "metadata": {"source": "Scheduling Engine", "category": "custom", "type": "schedule_rule"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  RECURRING PAYMENT RULES
# ══════════════════════════════════════════════════════════════════

RECURRING_PAYMENT_RULES = [
    {
        "id": "rule_amount_001",
        "text": "Amount Validation Rules: Fixed amount standing orders: Must be > $0.01 and ≤ $50,000. Variable amount standing orders: Customer sets maximum cap; actual payment determined by biller. Amount changes: Increases > 20% of original require re-verification. Amount changes > $10,000 require dual approval. Daily aggregate limit: $100,000 across all standing orders on an account. Currency: Must match source account currency. Rounding: To nearest cent.",
        "metadata": {"source": "Payment Operations", "category": "validation", "type": "rule"},
    },
    {
        "id": "rule_account_001",
        "text": "Account Validation Rules: Source account must be: 1) Active and in good standing, 2) Have sufficient available balance (not including pending transactions), 3) Not restricted or frozen, 4) Eligible for ACH debits. Dual-signature accounts: Standing orders > $10,000 require both signatures. Joint accounts: Either account holder may create/modify standing orders. Business accounts: Standing orders require authorized signer approval. dormant accounts: Cannot create new standing orders.",
        "metadata": {"source": "Payment Operations", "category": "validation", "type": "rule"},
    },
    {
        "id": "rule_payee_001",
        "text": "Payee/Biller Validation Rules: New payee: First payment requires additional verification (amount cap, delayed execution, or out-of-band confirmation). Payee name matching: Fuzzy matching with ≥ 0.85 confidence for known billers. Payee changes: Existing standing order payee changes trigger notification to customer and 24-hour hold on first payment to new payee. International payees: Additional OFAC/sanctions screening required. Payee deactivation: Biller removal requires customer confirmation.",
        "metadata": {"source": "Payment Operations", "category": "validation", "type": "rule"},
    },
    {
        "id": "rule_timing_001",
        "text": "Timing and Execution Rules: Cut-off time: Standing orders submitted before 6:00 PM ET execute same business day. After cut-off: Next business day. Holiday calendar: Uses Federal Reserve holiday calendar. Weekend handling: Saturday/Sunday payments execute on Monday (or Tuesday if Monday is holiday). Execution window: Payments process between 2:00 AM and 6:00 AM ET. Customer notification: SMS/email sent 1 day before execution. Same-day cancellation: Must be before cut-off time.",
        "metadata": {"source": "Scheduling Engine", "category": "timing", "type": "rule"},
    },
    {
        "id": "rule_failure_001",
        "text": "Payment Failure Handling: Insufficient funds: 1) First failure: Retry next business day, 2) Second failure: Retry after 3 business days, 3) Third failure: Suspend standing order and notify customer. Invalid account: Immediate suspension, customer notification. Biller rejection: Customer notified, standing order suspended pending investigation. Network/system outage: Payment queued for next available processing window. Failed payment fees: NSF fee ($35) charged per failed attempt. Suspension notification: Email + SMS within 1 hour of suspension.",
        "metadata": {"source": "Payment Operations", "category": "failure", "type": "rule"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE REQUIREMENTS
# ══════════════════════════════════════════════════════════════════

COMPLIANCE_REQUIREMENTS = [
    {
        "id": "compliance_rege_001",
        "text": "Regulation E Compliance for Standing Orders: Standing orders initiated via electronic channels are covered by Reg E. Consumer rights: 1) Right to stop payment: Must be received at least 3 business days before scheduled transfer, 2) Error resolution: Bank must investigate within 10 business days, 3) Preauthorized transfers: Consumer may stop by notifying bank in writing. Bank obligations: 1) Provide confirmation of standing order setup, 2) Notify consumer of any changes to amount or payee, 3) Provide documentation of each transfer. Liability limits: $50 if reported within 2 business days, $500 within 60 days, unlimited after 60 days.",
        "metadata": {"source": "Compliance", "category": "regulation", "type": "compliance"},
    },
    {
        "id": "compliance_nacha_001",
        "text": "NACHA Rules for Recurring ACH: Originator obligations: 1) Obtain written or electronic authorization from receiver, 2) Retain authorization for 2 years after termination, 3) Provide stop-payment rights. Authorization requirements: Must be signed/mutually agreed, must identify account, must state frequency/amount (or method of determining), may authorize changes. Unauthorized return timeframe: R07 (authorization revoked) within 60 days of settlement. Dishonored return: RDFI must return within 2 business days of receipt._notification of changes: Originator notified within 2 business days.",
        "metadata": {"source": "Compliance", "category": "regulation", "type": "compliance"},
    },
    {
        "id": "compliance_udaap_001",
        "text": "UDAAP Compliance for Bill Payment: Standing order marketing and disclosures must be clear and not misleading. Prohibited practices: 1) Hidden fees for bill payment service, 2) Making it difficult to cancel standing orders, 3) Processing payments before scheduled date without consent, 4) Changing payment amounts without authorization. Best practices: 1) Clear fee disclosures upfront, 2) Easy-to-find cancel/modify options, 3) Advance notice of any changes, 4) Confirmation of all customer actions, 5) Accessible customer support for issues.",
        "metadata": {"source": "Compliance", "category": "regulation", "type": "compliance"},
    },
    {
        "id": "compliance_bsa_001",
        "text": "BSA/AML Considerations for Recurring Payments: Standing orders may be used for structuring. Monitoring: 1) Multiple standing orders to same payee just below CTR threshold, 2) Standing orders set up and immediately cancelled (test transactions), 3) Standing orders to high-risk jurisdictions. SAR filing: If recurring pattern appears suspicious, file SAR within 30 days. CTR aggregation: Standing order amounts aggregate with other cash transactions for CTR filing. Enhanced due diligence: International standing orders require additional documentation.",
        "metadata": {"source": "Compliance", "category": "regulation", "type": "compliance"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CUSTOMER BILLING KNOWLEDGE
# ══════════════════════════════════════════════════════════════════

CUSTOMER_BILLING_KNOWLEDGE = [
    {
        "id": "knowledge_rent_001",
        "text": "Rent Payment Scenario: Customer says 'Pay my rent on the 1st of every month.' System should: 1) Identify as monthly recurring payment, 2) Set frequency to monthly, day of month = 1, 3) Verify landlord/property management payee exists in biller directory or add new payee, 4) Set amount (fixed or variable), 5) Select source account, 6) Send confirmation. Edge cases: Month with 31st? → Pay on 1st. Leap year? → Feb 28 or 29 as applicable. Holiday on 1st? → Pay on next business day.",
        "metadata": {"source": "Customer Support", "category": "scenario", "type": "rent"},
    },
    {
        "id": "knowledge_utility_001",
        "text": "Utility Bill Scenario: Customer says 'Set up auto-pay for my electric bill.' System should: 1) Search biller directory for electric company, 2) If found: Link to existing biller profile, 3) If not found: Create new biller with customer-provided details, 4) Set frequency to monthly (utility billing cycle), 5) Amount: Variable with optional maximum cap, 6) Set source account, 7) Enable notifications for each payment. Note: Utility amounts may vary month to month — recommend variable amount with cap.",
        "metadata": {"source": "Customer Support", "category": "scenario", "type": "utility"},
    },
    {
        "id": "knowledge_subscription_001",
        "text": "Subscription Management Scenario: Customer says 'I want to track all my monthly subscriptions.' System should: 1) List all active standing orders categorized by type, 2) Highlight subscription payments (Netflix, Spotify, etc.), 3) Show total monthly subscription spend, 4) Identify any price increases in last 90 days, 5) Suggest consolidation or cancellation opportunities. Proactive insights: 'Your subscriptions total $187/month. Netflix increased from $15.49 to $17.99 last month.'",
        "metadata": {"source": "Customer Support", "category": "scenario", "type": "subscription"},
    },
    {
        "id": "knowledge_paycheck_001",
        "text": "Paycheck Transfer Scenario: Customer says 'Transfer $500 to my savings every time I get paid.' System should: 1) Identify as biweekly (most common payroll frequency), 2) Set frequency to biweekly or align with detected payroll deposits, 3) Set amount to $500 (fixed), 4) Source: checking account, Destination: savings account, 5) Timing: Day after typical payroll deposit (e.g., Friday if paid Thursday). Alternative: Set to 'daily' with amount matching detected payroll pattern.",
        "metadata": {"source": "Customer Support", "category": "scenario", "type": "savings"},
    },
    {
        "id": "knowledge_troubleshoot_001",
        "text": "Troubleshooting Standing Orders: Common issues and resolutions: 1) 'Payment didn't go through' → Check account balance, verify payee details, check for suspension due to failures, 2) 'Wrong amount charged' → Check if variable amount biller sent different amount, review cap setting, 3) 'Can't cancel' → Verify cancellation request is > 24 hours before next execution, check if customer has sufficient auth level, 4) 'Duplicate payment' → Check if standing order and manual payment overlap, review for processing timing issue, 5) 'Payment date changed' → Check holiday/weekend deferral rules.",
        "metadata": {"source": "Customer Support", "category": "troubleshooting", "type": "common_issues"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  OPERATIONAL PLAYBOOKS
# ══════════════════════════════════════════════════════════════════

OPERATIONAL_PLAYBOOKS = [
    {
        "id": "playbook_create_001",
        "text": "Standing Order Creation Playbook: Step 1: Customer provides payment details (payee, amount, frequency, start date). Step 2: Validate source account (active, sufficient funds, not restricted). Step 3: Verify payee/biller (search directory or create new). Step 4: Run compliance checks (OFAC, amount limits, velocity). Step 5: Calculate first execution date and present to customer. Step 6: Obtain customer confirmation and authentication. Step 7: Create standing order in system. Step 8: Send confirmation with standing order ID and schedule details. Step 9: Set up payment reminders (3 days, 1 day, day of). Step 10: Log all actions for audit trail.",
        "metadata": {"category": "creation", "type": "playbook", "steps": 10},
    },
    {
        "id": "playbook_modify_001",
        "text": "Standing Order Modification Playbook: Step 1: Customer identifies standing order to modify. Step 2: Present current standing order details. Step 3: Customer specifies changes (amount, frequency, dates, payee). Step 4: Validate changes against policy (amount limits, frequency rules). Step 5: If payee change: Trigger new payee verification flow. Step 6: Calculate effective date for changes. Step 7: If amount increase > 20%: Route to manager approval. Step 8: Obtain customer confirmation. Step 9: Apply changes and send confirmation. Step 10: Update audit trail with before/after values.",
        "metadata": {"category": "modification", "type": "playbook", "steps": 10},
    },
    {
        "id": "playbook_failure_001",
        "text": "Payment Failure Resolution Playbook: Step 1: Detect payment failure (insufficient funds, invalid account, biller rejection). Step 2: Log failure with error code and timestamp. Step 3: Determine failure type and retry eligibility. Step 4: If retryable: Schedule retry per failure policy (next business day → 3 days → suspension). Step 5: Send failure notification to customer with reason and next steps. Step 6: If third failure: Suspend standing order. Step 7: Send suspension notice with reactivation instructions. Step 8: If customer contacts support: Offer options (fund account, modify amount, cancel). Step 9: Track resolution and update standing order status. Step 10: Generate failure report for operations review.",
        "metadata": {"category": "failure", "type": "playbook", "steps": 10},
    },
    {
        "id": "playbook_dispute_001",
        "text": "Standing Order Dispute Playbook: Step 1: Customer disputes a standing order payment. Step 2: Identify disputed transaction and standing order. Step 3: Determine dispute type (unauthorized, incorrect amount, duplicate, timing). Step 4: If unauthorized: Initiate Reg E investigation (10 business days). Step 5: If amount dispute: Compare standing order terms with actual charge. Step 6: If duplicate: Check for system error or customer-initiated duplicate. Step 7: Provisional credit per Reg E if investigation > 10 business days. Step 8: Contact biller for additional information. Step 9: Complete investigation and document findings. Step 10: Resolve dispute and update standing order if needed.",
        "metadata": {"category": "dispute", "type": "playbook", "steps": 10},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "standing_order_policies": STANDING_ORDER_POLICIES,
        "biller_directory": BILLER_DIRECTORY,
        "payment_schedules": PAYMENT_SCHEDULES,
        "recurring_payment_rules": RECURRING_PAYMENT_RULES,
        "compliance_requirements": COMPLIANCE_REQUIREMENTS,
        "customer_billing_knowledge": CUSTOMER_BILLING_KNOWLEDGE,
        "operational_playbooks": OPERATIONAL_PLAYBOOKS,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  OK {collection_name}: {count} documents")

    print("\nStanding Order & Bill Payment Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
