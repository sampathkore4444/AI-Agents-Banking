"""
Seed script: Populate ChromaDB with loan collections knowledge base data.

Includes:
- FDCPA regulations (Fair Debt Collection Practices Act)
- Collection strategies (early, mid, late-stage, recovery)
- Negotiation frameworks (payment plans, settlements, hardship)
- Compliance guidelines (communication restrictions, disclosure requirements)
- Past resolution cases (successful outcomes, patterns)
- Hardship programs (forbearance, modification, deferment)
- Communication templates (letters, calls, emails)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

FDCPA_REGULATIONS = [
    {
        "id": "fdcpa_001",
        "text": "Fair Debt Collection Practices Act (FDCPA) — Overview: The FDCPA (15 U.S.C. § 1692) governs third-party debt collectors. It prohibits harassment, false or misleading representations, and unfair practices. Applies to collectors acting on behalf of creditors to collect debts primarily for personal, family, or household purposes. Does NOT apply to original creditors collecting their own debts.",
        "metadata": {"source": "CFPB", "section": "15 U.S.C. § 1692", "type": "overview"},
    },
    {
        "id": "fdcpa_002",
        "text": "FDCPA Communication Restrictions: Debt collectors may NOT contact consumers: (1) Before 8:00 AM or after 9:00 PM local time, (2) At work if told employer disapproves, (3) After receiving written cease-and-desist letter (except to confirm cessation or notify of specific action), (4) Through postcard or envelope showing it's from a debt collector. Max 3 attempts per day. Must honor request to communicate only through attorney.",
        "metadata": {"source": "CFPB", "section": "15 U.S.C. § 1692c", "type": "communication_restrictions"},
    },
    {
        "id": "fdcpa_003",
        "text": "FDCPA Validation Notice Requirements: Within 5 days of initial communication, collector must send written notice containing: (1) Amount of debt, (2) Name of creditor, (3) Statement that consumer has 30 days to dispute debt, (4) Statement that if debt is disputed within 30 days, collector will provide verification, (5) Statement that upon request, collector will provide name/address of original creditor. Failure to provide validation notice bars collection until provided.",
        "metadata": {"source": "CFPB", "section": "15 U.S.C. § 1692g", "type": "validation_notice"},
    },
    {
        "id": "fdcpa_004",
        "text": "FDCPA Prohibited Conduct: Debt collectors may NOT: (1) Use threats of violence or criminal means, (2) Use obscene or profane language, (3) Call repeatedly to harass, (4) Publish lists of consumers who refuse to pay, (5) Misrepresent the amount owed, (6) Threaten to take legal action not intended or not legally possible, (7) Fail to identify themselves as debt collectors on first communication, (8) Misrepresent as attorney or government official.",
        "metadata": {"source": "CFPB", "section": "15 U.S.C. § 1692d-1692e", "type": "prohibited_conduct"},
    },
    {
        "id": "fdcpa_005",
        "text": "FDCPA Cease and Desist: Consumers have the right to send a written cease-and-desist letter requesting the collector to stop all communication. Once received, collector may only: (1) Confirm cessation of communication, (2) Notify consumer that specific action will be taken (e.g., lawsuit), (3) Notify that collector is terminating its attempt to collect. The debt still exists — collector can still report to credit bureaus and pursue legal action.",
        "metadata": {"source": "CFPB", "section": "15 U.S.C. § 1692c(c)", "type": "cease_desist"},
    },
    {
        "id": "fdcpa_006",
        "text": "FDCPA Dispute Rights: If consumer disputes debt (in writing within 30 days of validation notice) or requests original creditor name, collector must: (1) Cease all collection activity, (2) Obtain verification of debt, (3) Mail verification to consumer. Collector may resume collection only after providing verification. Verification should include: amount owed, name of creditor, and copies of relevant documents.",
        "metadata": {"source": "CFPB", "section": "15 U.S.C. § 1692g(b)", "type": "dispute_rights"},
    },
    {
        "id": "fdcpa_007",
        "text": "FDCPA Penalties and Enforcement: Consumers may sue collectors within 1 year of violation. Statutory damages up to $1,000 per lawsuit (or actual damages if greater). Actual damages for emotional distress, lost wages, etc. Attorney's fees and court costs recoverable. Class action suits possible. CFPB and FTC enforcement. State attorneys general may also enforce. Collectors may face regulatory fines and consent orders.",
        "metadata": {"source": "CFPB", "section": "15 U.S.C. § 1692k", "type": "penalties"},
    },
]

COLLECTION_STRATEGIES = [
    {
        "id": "strategy_001",
        "text": "Early-Stage Collections (1-30 days past due): Focus on reminder and engagement, not pressure. Contact strategy: Day 1 — automated payment reminder (email/SMS). Day 3 — personal phone call, empathetic tone. Day 7 — second call + written notice. Day 14 — third call, discuss options. Day 21 — formal past-due notice. Day 28 — escalation warning. Goal: Understand reason for delinquency and restore account to current status.",
        "metadata": {"strategy": "early_stage", "delinquency_days": "1-30", "type": "proactive"},
    },
    {
        "id": "strategy_002",
        "text": "Mid-Stage Collections (31-90 days past due): Increased urgency but maintain professionalism. Focus on payment arrangement and hardship identification. Contact strategy: Weekly calls, alternating phone/email. Discuss deferment, forbearance, or modified payment plan. Evaluate for hardship program eligibility. Begin documenting all contact attempts and outcomes. Consider credit reporting (after 30 days delinquent). Offer settlement at reduced amount if account shows risk indicators.",
        "metadata": {"strategy": "mid_stage", "delinquency_days": "31-90", "type": "negotiation"},
    },
    {
        "id": "strategy_003",
        "text": "Late-Stage Collections (91-180 days past due): Formal escalation and recovery focus. Contact strategy: Bi-weekly calls with documentation. Send formal demand letter. Evaluate for workout options (loan modification, settlement). Consider account for charge-off preparation. Assess collateral value (secured loans). Engage skip tracing if contact is lost. Begin legal review for litigation. Compliance becomes critical — document everything.",
        "metadata": {"strategy": "late_stage", "delinquency_days": "91-180", "type": "escalation"},
    },
    {
        "id": "strategy_004",
        "text": "Charge-Off and Recovery (180+ days past due): Account is typically charged off at 180 days. Options: (1) Internal recovery — continue collection efforts for 6-12 months, (2) Third-party collection — assign to external agency (typically 25-50% commission), (3) Debt sale — sell debt to debt buyer (typically 5-20 cents on dollar), (4) Legal action — file lawsuit if statute of limitations permits, (5) Write-off — record as bad debt loss for tax purposes. Credit report shows charge-off for 7 years from original delinquency date.",
        "metadata": {"strategy": "charge_off", "delinquency_days": "180+", "type": "recovery"},
    },
    {
        "id": "strategy_005",
        "text": "Best Contact Strategy by Debtor Profile: Young professionals (22-35): Prefer digital communication (email, SMS, app notifications). Respond better to self-service payment portals. Avoid aggressive language. Respond to financial education content. Families with mortgage: Prioritize phone calls during evening hours. Understand housing stability concerns. Offer mortgage-specific forbearance programs. Approach with empathy — fear of losing home. Self-employed/irregular income: Flexible payment schedules (bi-weekly, custom dates). Income-driven repayment plans. Seasonal payment adjustments. Document income volatility.",
        "metadata": {"strategy": "segmentation", "type": "personalization"},
    },
]

NEGOTIATION_FRAMEWORKS = [
    {
        "id": "negotiation_001",
        "text": "Payment Plan Structuring: Key principles: (1) Always start by listening — understand the borrower's situation before proposing solutions, (2) Offer 3-4 options ranging from minimum to optimal payment, (3) Include a 'commitment payment' that's affordable and sustainable, (4) Build in review dates (90-day check-ins), (5) Document all agreements in writing, (6) Allow grace periods for first 1-2 payments of new plan. Common structures: Standard (equal payments over 6-12 months), Graduated (increasing payments as income recovers), Seasonal (adjusted for irregular income), Interest-only (temporary reduced payments).",
        "metadata": {"framework": "payment_plan", "type": "negotiation"},
    },
    {
        "id": "negotiation_002",
        "text": "Settlement Negotiation Guidelines: Settlement authority tiers: Front-line collector: up to 20% discount. Supervisor: up to 40% discount. Manager: up to 50% discount. VP/C-suite: up to 70% discount (rare). Settlement factors: Account age, amount owed, borrower financial situation, litigation risk, bankruptcy risk, recovery probability. Always get settlement in writing before accepting payment. Settlement must include: (1) Payment terms, (2) What happens to remaining balance, (3) Credit reporting language, (4) Release of liability. Note: Forgiven debt over $600 is taxable (IRS Form 1099-C).",
        "metadata": {"framework": "settlement", "type": "negotiation"},
    },
    {
        "id": "negotiation_003",
        "text": "Hardship Assessment Framework: When a borrower claims hardship, assess: (1) Documentation — Request supporting documents (medical bills, termination letter, divorce decree), (2) Duration — Is this temporary or permanent? (3) Income impact — What percentage of income is affected? (4) Other obligations — Are they paying other debts? (5) Willingness to pay — Is the borrower engaged and cooperative? Hardship categories: Medical (illness, injury, disability), Employment (job loss, reduced hours), Family (divorce, death of spouse, dependent care), Natural disaster, Military deployment. Response options: Forbearance (3-12 months), Loan modification (permanent rate/term change), Deferment (0% interest period), Reduced payment plan, Hardship withdrawal from retirement (with guidance).",
        "metadata": {"framework": "hardship", "type": "assessment"},
    },
    {
        "id": "negotiation_004",
        "text": "De-escalation Techniques: Key phrases and approaches: 'I understand this is a difficult situation. Let's work together to find a solution.' 'What would make this payment manageable for you?' 'I want to help you keep your account in good standing.' Avoid: 'You need to pay right now.' 'If you don't pay, we'll take legal action.' 'You should have planned better.' Active listening: Repeat back what the borrower says. Acknowledge their feelings. Don't interrupt. Take notes during the call. Offer to call back at a better time. Silence is okay — let them talk.",
        "metadata": {"framework": "deescalation", "type": "communication"},
    },
]

COMPLIANCE_GUIDELINES = [
    {
        "id": "compliance_001",
        "text": "TCPA Compliance for Collections: Telephone Consumer Protection Act (TCPA) restricts: (1) Automated calls/texts without prior express consent, (2) Calls to numbers on the Do Not Call registry, (3) Calls before 8 AM or after 9 PM local time, (4) Calls to cell phones using autodialed or prerecorded messages without consent. Exceptions: (1) Calls with prior express consent, (2) Calls to landlines with artificial/prerecorded messages (with consent), (3) Emergency calls. Penalties: $500 per violation, $1,500 per willful violation. Always check DNC registry before calling. Obtain and document consent for automated communications.",
        "metadata": {"source": "FCC", "regulation": "TCPA", "type": "communication_compliance"},
    },
    {
        "id": "compliance_002",
        "text": "State-Specific Collections Laws: Many states have stricter laws than FDCPA: California (Rosenthal Act): Covers original creditors, 3-year statute of limitations, requires license. New York: Requires license, 6-year statute of limitations, specific notice requirements. Texas: 4-year statute of limitations, caps on attorney fees. Florida: Requires license, 5-year statute of limitations. Key considerations: (1) Always apply the more restrictive law (federal or state), (2) Maintain state-specific compliance checklists, (3) Train collectors on applicable state laws, (4) Update procedures when laws change.",
        "metadata": {"source": "State regulators", "type": "state_compliance"},
    },
    {
        "id": "compliance_003",
        "text": "Fair Credit Reporting Act (FCRA) for Collections: When reporting to credit bureaus: (1) Must report accurate information — no knowingly false data, (2) Must investigate disputes within 30 days, (3) Must notify consumer within 30 days of reporting, (4) Must update/delete information that is incomplete or inaccurate, (5) Cannot report account as 'disputed' without consumer's request, (6) Must include date of first delinquency in reporting, (7) Negative information must be removed after 7 years (10 years for bankruptcy). Dispute handling: Forward dispute to original creditor within 5 days. Cease collection activity during investigation. Provide results to consumer. Correct any inaccuracies.",
        "metadata": {"source": "CFPB", "regulation": "FCRA", "type": "credit_reporting"},
    },
    {
        "id": "compliance_004",
        "text": "UDAAP Compliance: Unfair, Deceptive, or Abusive Acts or Practices: Unfair: Causes substantial injury, not reasonably avoidable, not outweighed by benefits. Deceptive: Misleading representation, omission, or practice that affects consumer decision. Abusive: Takes unreasonable advantage of consumer's lack of understanding, inability to protect themselves, or reasonable reliance on collector. Examples of violations: (1) Misrepresenting amount owed, (2) Threatening legal action not intended, (3) Calling employer about debt, (4) Failing to disclose debt is time-barred, (5) Misleading about credit consequences. Best practices: Train staff on UDAAP regularly, document all interactions, implement mystery shopping, maintain complaint tracking system.",
        "metadata": {"source": "CFPB", "regulation": "UDAAP", "type": "unfair_practices"},
    },
]

PAST_RESOLUTION_CASES = [
    {
        "id": "case_001",
        "text": "Successful Resolution — Mortgage Delinquency (62 days past due): Borrower profile: Married couple, 2 kids, combined income $95,000. Husband lost job due to layoff. 30-year fixed mortgage, $2,200/month payment, $180,000 remaining balance. Approach: Empathetic outreach, identified root cause (job loss), enrolled in 6-month forbearance program, reduced payment to interest-only ($950/month) during forbaince. Outcome: Husband found new job within 4 months. Returned to full payments. Total recovered: $178,500 (99.2% recovery). Key success factor: Early identification + flexible hardship program.",
        "metadata": {"resolution": "forbearance", "product": "mortgage", "outcome": "success", "recovery_rate": 0.992},
    },
    {
        "id": "case_002",
        "text": "Successful Resolution — Auto Loan Settlement (120 days past due): Borrower profile: Single, age 28, income $52,000. Auto loan $22,000 remaining, $485/month payment. Job relocation caused 3-month gap in income. Approach: Mid-stage strategy — weekly outreach, explored trade-in options, eventually negotiated 35% settlement ($14,300) with 12-month payment plan. Borrower paid $1,192/month for 12 months. Outcome: Full settlement amount paid. Account closed. Recovery: $14,300 (65% of original balance). Key success factor: Flexibility in settlement terms + structured payment plan.",
        "metadata": {"resolution": "settlement", "product": "auto_loan", "outcome": "success", "recovery_rate": 0.65},
    },
    {
        "id": "case_003",
        "text": "Successful Resolution — Personal Loan Workout (75 days past due): Borrower profile: Self-employed graphic designer, age 35, variable income averaging $68,000. Personal loan $15,000, $350/month. Seasonal income dip caused missed payments. Approach: Income-driven repayment plan — reduced to $150/month during slow season (Nov-Feb), $500/month during busy season (Mar-Oct). Added 6 months to term. Total additional interest: $890. Outcome: Borrower completed modified plan, returned to standard payments. Full recovery: $15,890 (100% + interest). Key success factor: Understanding income volatility + flexible scheduling.",
        "metadata": {"resolution": "modification", "product": "personal_loan", "outcome": "success", "recovery_rate": 1.0},
    },
    {
        "id": "case_004",
        "text": "Failed Resolution — Credit Card Charge-Off (180+ days): Borrower profile: Age 42, income $45,000. Credit card debt $8,500, minimum payment $170. Multiple competing debts, DTI over 60%. Approach: Early-stage failed — borrower ignored calls. Mid-stage — partial engagement, promised to pay but never followed through. Late-stage — skip tracing found new address, sent demand letter. No response. Outcome: Account charged off at 180 days. Sold to debt buyer for $1,275 (15 cents on dollar). Credit score impact: -150 points. Lesson: Earlier intervention and more aggressive hardship screening may have improved outcome.",
        "metadata": {"resolution": "charge_off", "product": "credit_card", "outcome": "failure", "recovery_rate": 0.15},
    },
]

HARDSHIP_PROGRAMS = [
    {
        "id": "hardship_001",
        "text": "Forbearance Program: Definition: Temporary reduction or suspension of loan payments. Duration: 3-12 months (extendable to 18 months in exceptional circumstances). Eligibility: (1) Documented hardship, (2) Account was current or less than 60 days delinquent at hardship onset, (3) Willingness to resume payments, (4) Hardship is expected to be temporary. Options: Full forbearance (no payments), Partial forbearance (reduced payments), Interest-only payments. After forbearance: (1) Catch-up plan (lump sum or added to end of loan), (2) Loan modification to extend term, (3) Resume standard payments. Credit reporting: Account should be reported as 'in forbearance' — not delinquent.",
        "metadata": {"program": "forbearance", "type": "temporary_relief"},
    },
    {
        "id": "hardship_002",
        "text": "Loan Modification Program: Definition: Permanent change to loan terms. Available for: Mortgages (most common), auto loans (rare), personal loans (case-by-case). Common modifications: (1) Interest rate reduction, (2) Term extension (e.g., 30 to 40 years), (3) Principal forbearance (deferred balance), (4) Principal reduction (rare, requires investor approval). Requirements: (1) Hardship documentation, (2) Financial assessment (income, expenses, assets), (3) Trial payment period (3 months), (4) Investor approval. Credit impact: May show as 'modified' on credit report. Less negative than charge-off. Tax implications: Principal forgiveness may be taxable (consult tax advisor).",
        "metadata": {"program": "modification", "type": "permanent_relief"},
    },
    {
        "id": "hardship_003",
        "text": "Deferment Program: Definition: Temporary pause on principal payments (interest continues to accrue or is subsidized). Common for: Student loans (most common), private loans (limited availability). Eligibility: (1) Enrolled in school half-time, (2) Active military service, (3) Economic hardship, (4) Unemployment. Duration: Varies by program — typically 6-36 months. Interest treatment: Subsidized loans — government pays interest during deferment. Unsubsidized loans — interest accrues and capitalizes. Credit reporting: Should show as 'in deferment' — not delinquent. Key difference from forbearance: Deferment may not accrue interest (subsidized).",
        "metadata": {"program": "deferment", "type": "temporary_relief"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "fdcpa_regulations": FDCPA_REGULATIONS,
        "collection_strategies": COLLECTION_STRATEGIES,
        "negotiation_frameworks": NEGOTIATION_FRAMEWORKS,
        "compliance_guidelines": COMPLIANCE_GUIDELINES,
        "past_resolution_cases": PAST_RESOLUTION_CASES,
        "hardship_programs": HARDSHIP_PROGRAMS,
        "communication_templates": [],  # Templates are in the notification tool
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        if documents:
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
