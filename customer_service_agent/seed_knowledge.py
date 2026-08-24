"""
Seed script: Populate ChromaDB with customer service knowledge base data.

Collections:
- banking_faq: Common banking questions and answers
- product_information: Account types, features, eligibility
- fee_schedules: Account fees, transaction fees, penalty fees
- dispute_policies: Dispute process, timelines, requirements
- complaint_history: Past complaint resolutions and precedents
- regulatory_guidelines: Consumer protection, fair lending, privacy
- resolution_playbooks: Step-by-step resolution guides

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

BANKING_FAQ = [
    {"id": "faq_001", "text": "How do I check my account balance? You can check your balance through: 1) Our mobile app (Accounts tab), 2) Online banking (Dashboard), 3) ATM (insert card and select Balance), 4) Call our automated line at 1-800-XXX-XXXX, 5) Visit any branch. Balances are updated in real-time for most transactions.", "metadata": {"topic": "account_balance", "source": "FAQ"}},
    {"id": "faq_002", "text": "How do I stop a payment? To stop a pending payment: 1) Log into online banking, 2) Go to Payments > Pending Payments, 3) Select the payment to stop, 4) Click 'Stop Payment'. For checks, call us at 1-800-XXX-XXXX at least 3 business days before the check clears. A stop payment fee of $30 may apply.", "metadata": {"topic": "stop_payment", "source": "FAQ"}},
    {"id": "faq_003", "text": "How do I dispute a transaction? To dispute a transaction: 1) Log into online banking, 2) Go to the transaction in your history, 3) Click 'Dispute This Transaction', 4) Follow the prompts to provide details. You can also call us at 1-800-XXX-XXXX or visit a branch. Disputes are typically resolved within 10-30 business days.", "metadata": {"topic": "dispute", "source": "FAQ"}},
    {"id": "faq_004", "text": "How do I reset my online banking password? To reset your password: 1) Go to the login page, 2) Click 'Forgot Password', 3) Enter your username and email, 4) Check your email for a reset link, 5) Create a new password (must include uppercase, lowercase, number, and special character). If you're locked out, call 1-800-XXX-XXXX for assistance.", "metadata": {"topic": "password_reset", "source": "FAQ"}},
    {"id": "faq_005", "text": "What are your branch hours? Most branches are open: Monday-Friday 9:00 AM - 5:00 PM, Saturday 9:00 AM - 1:00 PM, Sunday Closed. Drive-through hours may vary. Use our branch locator at bank.com/locations for specific hours and holiday schedules.", "metadata": {"topic": "branch_hours", "source": "FAQ"}},
    {"id": "faq_006", "text": "How do I set up direct deposit? To set up direct deposit: 1) Get a direct deposit form from your employer, 2) Provide your routing number (found on your checks or in online banking), 3) Provide your account number, 4) Choose checking or savings account. Setup typically takes 1-2 pay cycles.", "metadata": {"topic": "direct_deposit", "source": "FAQ"}},
    {"id": "faq_007", "text": "How do I order new checks? To order checks: 1) Log into online banking, 2) Go to Account Services > Order Checks, 3) Select your account and check style, 4) Confirm your shipping address. You can also call us or visit a branch. Standard delivery is free; expedited shipping has a fee.", "metadata": {"topic": "order_checks", "source": "FAQ"}},
    {"id": "faq_008", "text": "What should I do if my card is lost or stolen? If your card is lost or stolen: 1) Immediately lock your card in the mobile app (Card Controls > Lock Card), 2) Call us at 1-800-XXX-XXXX (available 24/7), 3) We'll issue a replacement card within 3-5 business days, 4) Review your recent transactions for unauthorized charges. You're not liable for unauthorized charges reported within 60 days.", "metadata": {"topic": "lost_card", "source": "FAQ"}},
]

PRODUCT_INFORMATION = [
    {"id": "prod_001", "text": "Personal Checking Account: No monthly fee with $500+ average daily balance or $500+ in direct deposits. Free debit card, free online banking, free bill pay. ATM fee refunds up to $15/month at other banks. Overdraft protection available. Minimum opening deposit: $25.", "metadata": {"product": "personal_checking", "source": "Products"}},
    {"id": "prod_002", "text": "Premium Checking Account: $25/month fee (waived with $5,000+ average daily balance). All Personal Checking features plus: free checks, free wire transfers, free money orders, ATM fee refunds up to $25/month, dedicated relationship manager, preferred loan rates.", "metadata": {"product": "premium_checking", "source": "Products"}},
    {"id": "prod_003", "text": "Savings Account: 0.50% APY (0.05% for balances under $1,000). No monthly fee with $300+ average daily balance. Free transfers to linked accounts. 6 withdrawals per month free (excess withdrawal fee: $10). FDIC insured up to $250,000.", "metadata": {"product": "savings_account", "source": "Products"}},
    {"id": "prod_004", "text": "High-Yield Savings Account: 4.25% APY for balances $10,000+. 2.50% APY for balances $1,000-$9,999. No monthly fee. No minimum balance requirement. 6 withdrawals per month free. FDIC insured up to $250,000. Online only — no branch access.", "metadata": {"product": "high_yield_savings", "source": "Products"}},
    {"id": "prod_005", "text": "Money Market Account: 3.75% APY for balances $25,000+. $15/month fee (waived with $25,000+ balance). Free checks and debit card. 6 withdrawals per month free. FDIC insured up to $250,000. Best for customers with larger balances seeking higher returns with check-writing privileges.", "metadata": {"product": "money_market", "source": "Products"}},
    {"id": "prod_006", "text": "Credit Card — Rewards: Earn 2% cash back on all purchases, 3% on dining and travel. No annual fee. 0% intro APR for 15 months on purchases and balance transfers. After intro: 16.99%-24.99% variable APR. Free FICO score. Purchase protection and extended warranty.", "metadata": {"product": "rewards_credit_card", "source": "Products"}},
    {"id": "prod_007", "text": "Credit Card — Secured: Build or rebuild credit. $200 minimum deposit (becomes your credit limit). 1% cash back on all purchases. 22.99% APR. No annual fee. Reports to all 3 credit bureaus. Automatic reviews for upgrade to unsecured card after 12 months of responsible use.", "metadata": {"product": "secured_credit_card", "source": "Products"}},
]

FEE_SCHEDULES = [
    {"id": "fee_001", "text": "Account Fees: Personal Checking: $12/month (waived with $500+ balance). Premium Checking: $25/month (waived with $5,000+ balance). Savings: $5/month (waived with $300+ balance). Money Market: $15/month (waived with $25,000+ balance). Overdraft fee: $35 per occurrence (max 3 per day).", "metadata": {"topic": "account_fees", "source": "Fee Schedule"}},
    {"id": "fee_002", "text": "Transaction Fees: ATM (other bank): $3 per transaction (refunded for Premium). ATM (international): $5 per transaction + 1% of amount. Wire transfer (domestic): $25 outgoing, $0 incoming. Wire transfer (international): $45 outgoing, $15 incoming. Stop payment: $30 per request. Cashier's check: $10.", "metadata": {"topic": "transaction_fees", "source": "Fee Schedule"}},
    {"id": "fee_003", "text": "Penalty Fees: Overdraft: $35 per item (max 3/day = $105). Returned item: $30 per item. Late payment (credit card): Up to $40. Excess savings withdrawal: $10 per transaction. Account closure within 90 days: $25. Dormant account (no activity 12 months): $10/month after 24 months.", "metadata": {"topic": "penalty_fees", "source": "Fee Schedule"}},
]

DISPUTE_POLICIES = [
    {"id": "disp_001", "text": "Dispute Process Overview: 1) Customer contacts us within 60 days of transaction date. 2) We investigate within 10 business days (45 for new accounts). 3) Provisional credit issued for disputes over $50 within 10 business days. 4) Final resolution within 45-90 days. 5) Customer notified of outcome in writing. Unauthorized transactions: Report within 60 days for zero liability.", "metadata": {"topic": "dispute_process", "source": "Dispute Policy"}},
    {"id": "disp_002", "text": "Dispute Types and Timelines: Unauthorized transaction: 10 business days investigation, provisional credit, 45 days final resolution. Duplicate charge: 10 business days, no provisional credit needed. Incorrect amount: 10 business days. Product not received: 10 business days, may contact merchant. Billing error: 10 business days. All disputes: 90 day maximum resolution.", "metadata": {"topic": "dispute_timelines", "source": "Dispute Policy"}},
    {"id": "disp_003", "text": "Dispute Documentation Requirements: Customer must provide: 1) Transaction details (date, amount, merchant). 2) Description of the issue. 3) Any supporting documents (receipts, correspondence). 4) Contact information for merchant (if available). We may request additional documentation during investigation. Provisional credit may be reversed if dispute is not valid.", "metadata": {"topic": "dispute_docs", "source": "Dispute Policy"}},
]

COMPLAINT_HISTORY = [
    {"id": "comp_001", "text": "Complaint Resolution: Billing Error — Customer charged twice for same purchase. Resolution: Verified duplicate charge with merchant, issued credit within 3 business days. Customer satisfied. Prevention: Updated merchant verification system. Category: billing. Priority: medium. Resolution time: 3 days.", "metadata": {"category": "billing", "source": "Complaint History", "outcome": "resolved"}},
    {"id": "comp_002", "text": "Complaint Resolution: App Crash — Mobile banking app crashing on login for multiple customers. Resolution: Identified bug in latest update, pushed hotfix within 24 hours. Issued service credit to affected customers. Category: technology. Priority: high. Resolution time: 1 day.", "metadata": {"category": "technology", "source": "Complaint History", "outcome": "resolved"}},
    {"id": "comp_003", "text": "Complaint Resolution: Hidden Fee — Customer charged $35 overdraft fee they didn't expect. Resolution: Reviewed account history, determined fee was legitimate per account agreement. Provided detailed explanation of overdraft policy. Offered to enroll customer in overdraft protection (free). Category: fees. Priority: medium. Resolution time: 2 days.", "metadata": {"category": "fees", "source": "Complaint History", "outcome": "resolved"}},
    {"id": "comp_004", "text": "Complaint Resolution: Long Wait Times — Customer waited 45 minutes on phone. Resolution: Apologized, offered callback option, provided direct line for future calls. Implemented callback system to reduce wait times. Category: service_quality. Priority: low. Resolution time: 1 day.", "metadata": {"category": "service_quality", "source": "Complaint History", "outcome": "resolved"}},
]

REGULATORY_GUIDELINES = [
    {"id": "reg_001", "text": "Fair Credit Billing Act (FCBA): Customers have the right to dispute billing errors within 60 days of the statement date. The bank must acknowledge the dispute within 30 days and resolve within 2 billing cycles (max 90 days). During investigation, the customer does not have to pay the disputed amount. Finance charges on disputed amounts are suspended.", "metadata": {"source": "FCBA", "type": "consumer_protection"}},
    {"id": "reg_002", "text": "Electronic Fund Transfer Act (EFTA): For unauthorized electronic transfers, customer liability is limited to $50 if reported within 2 business days, $500 if reported within 60 days, and unlimited after 60 days. Bank must investigate within 10 business days (45 for new accounts). Provisional credit required for investigations exceeding 10 days.", "metadata": {"source": "EFTA", "type": "consumer_protection"}},
    {"id": "reg_003", "text": "Truth in Savings Act (TISA): Banks must disclose all fees, APY, and terms before account opening. Fee schedules must be provided at account opening and upon request. Changes to fees require 30 days notice (60 days for savings). Customers have the right to close accounts without penalty (except within 90 days of opening).", "metadata": {"source": "TISA", "type": "consumer_protection"}},
    {"id": "reg_004", "text": "Gramm-Leach-Bliley Act (GLBA): Banks must protect customer financial information. Privacy notice must be provided at account opening and annually. Customers have the right to opt out of information sharing with non-affiliated third parties. Data security measures must be implemented and maintained.", "metadata": {"source": "GLBA", "type": "privacy"}},
]

RESOLUTION_PLAYBOOKS = [
    {"id": "play_001", "text": "Dispute Resolution Playbook: Step 1: Acknowledge customer concern empathetically. Step 2: Gather transaction details (date, amount, merchant). Step 3: Check if within dispute window (60 days). Step 4: File dispute in system. Step 5: Explain timeline (10-45 days). Step 6: Set expectations for provisional credit if applicable. Step 7: Provide dispute ID for tracking. Step 8: Follow up within 48 hours.", "metadata": {"scenario": "dispute", "source": "Playbook"}},
    {"id": "play_002", "text": "Complaint Resolution Playbook: Step 1: Listen actively and acknowledge the complaint. Step 2: Apologize for the inconvenience. Step 3: Gather all relevant details. Step 4: Categorize the complaint. Step 5: Offer immediate solution if possible. Step 6: Escalate if needed. Step 7: Document everything. Step 8: Follow up within 24 hours. Step 9: Send satisfaction survey after resolution.", "metadata": {"scenario": "complaint", "source": "Playbook"}},
    {"id": "play_003", "text": "Lost/Stolen Card Playbook: Step 1: Immediately lock the card in mobile app. Step 2: Confirm customer identity (3 security questions). Step 3: Review last 24 hours of transactions for unauthorized charges. Step 4: If unauthorized charges found, file fraud dispute. Step 5: Order replacement card (3-5 business days). Step 6: Update any recurring payments linked to the card. Step 7: Send confirmation with new card details.", "metadata": {"scenario": "lost_card", "source": "Playbook"}},
]


def seed() -> None:
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "banking_faq": BANKING_FAQ,
        "product_information": PRODUCT_INFORMATION,
        "fee_schedules": FEE_SCHEDULES,
        "dispute_policies": DISPUTE_POLICIES,
        "complaint_history": COMPLAINT_HISTORY,
        "regulatory_guidelines": REGULATORY_GUIDELINES,
        "resolution_playbooks": RESOLUTION_PLAYBOOKS,
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
