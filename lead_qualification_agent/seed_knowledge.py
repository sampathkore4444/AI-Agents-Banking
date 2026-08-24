"""
Seed script: Populate ChromaDB with lead qualification knowledge base data.

Includes:
- Qualification criteria (BANT, MEDDIC, CHAMP)
- Sales playbooks (inbound, outbound, referral, digital)
- Lead scoring models (demographic, behavioral, firmographic)
- Conversion patterns (what converts, what doesn't)
- Product eligibility (who qualifies for what)
- Compliance rules (TCPA, DNC, consent)
- Competitor intelligence (market positioning)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  QUALIFICATION CRITERIA
# ══════════════════════════════════════════════════════════════════

QUALIFICATION_CRITERIA = [
    {
        "id": "qual_bant_001",
        "text": "BANT Qualification Framework: Budget — Does the lead have the financial capacity? Check: annual income, existing assets, debt-to-income ratio. Authority — Is the lead the decision-maker? Check: age, employment status, account ownership. Need — Does the lead have a genuine banking need? Check: life stage, current products, expressed interest. Timeline — When does the lead need the product? Check: urgency indicators, competing offers, stated timeline.",
        "metadata": {"framework": "BANT", "type": "qualification", "version": "2024-Q3"},
    },
    {
        "id": "qual_meddic_001",
        "text": "MEDDIC Qualification Framework for Banking: Metrics — What are the quantifiable benefits? (e.g., savings on fees, interest earned). Economic Buyer — Who controls the budget? (individual, joint account holder, business owner). Decision Criteria — What factors matter most? (rate, fees, convenience, brand). Decision Process — How do they decide? (comparison shopping, advisor referral, online research). Identify Pain — What problem are they solving? (high fees, poor rates, inconvenience). Champion — Who internally advocates for our bank? (existing customer, employee referral).",
        "metadata": {"framework": "MEDDIC", "type": "qualification", "version": "2024-Q3"},
    },
    {
        "id": "qual_champ_001",
        "text": "CHAMP Qualification Framework: Challenges — What challenges is the prospect facing? (high interest rates, limited credit options, poor customer service elsewhere). Authority — Do they have authority to open accounts? (age 18+, not restricted). Money — Can they afford the products? (minimum balance requirements, income thresholds). Prioritization — How urgent is their need? (immediate, 30 days, 90 days, just exploring).",
        "metadata": {"framework": "CHAMP", "type": "qualification", "version": "2024-Q3"},
    },
    {
        "id": "qual_tier_001",
        "text": "Lead Qualification Tiers: Tier 1 (Hot) — Score 80-100: High intent, clear need, budget confirmed, decision-maker, immediate timeline. Route to senior advisor. Tier 2 (Warm) — Score 60-79: Moderate intent, some qualification criteria met. Route to sales team. Tier 3 (Cool) — Score 40-59: Low intent, exploratory, needs nurturing. Route to marketing drip. Tier 4 (Cold) — Score 0-39: Minimal information, unqualified. Add to nurture database.",
        "metadata": {"framework": "tiering", "type": "qualification", "version": "2024-Q3"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  SALES PLAYBOOKS
# ══════════════════════════════════════════════════════════════════

SALES_PLAYBOOKS = [
    {
        "id": "play_inbound_001",
        "text": "Inbound Lead Playbook: Step 1: Acknowledge inquiry within 5 minutes (speed to lead). Step 2: Thank them for interest, confirm contact details. Step 3: Ask qualifying questions (BANT). Step 4: Identify primary product interest. Step 5: Check eligibility (credit score, income). Step 6: Present relevant product benefits. Step 7: Handle objections with empathy. Step 8: Propose next step (application, consultation, callback). Step 9: Send follow-up email with materials. Step 10: Schedule follow-up call within 48 hours.",
        "metadata": {"source": "sales_ops", "type": "inbound", "version": "2024-Q3"},
    },
    {
        "id": "play_outbound_001",
        "text": "Outbound Lead Playbook: Step 1: Research lead before calling (CRM, website activity). Step 2: Open with personalized value proposition. Step 3: Ask if now is a good time (respect their schedule). Step 4: Identify pain points with open-ended questions. Step 5: Qualify using BANT framework. Step 6: Present solution tailored to their needs. Step 7: Share social proof (testimonials, case studies). Step 8: Create urgency (limited-time offer, rate change). Step 9: Propose specific next step with date/time. Step 10: Log all interactions in CRM immediately.",
        "metadata": {"source": "sales_ops", "type": "outbound", "version": "2024-Q3"},
    },
    {
        "id": "play_referral_001",
        "text": "Referral Lead Playbook: Step 1: Acknowledge referral source (build trust immediately). Step 2: Explain referral benefits (both parties get $100). Step 3: Understand their current banking situation. Step 4: Identify why they're considering a change. Step 5: Qualify for specific products. Step 6: Offer exclusive referral rate/promotion. Step 7: Expedite application process (they're pre-qualified). Step 8: Keep referrer updated on status. Step 9: Process referral bonuses after account opening. Step 10: Request testimonial after positive experience.",
        "metadata": {"source": "sales_ops", "type": "referral", "version": "2024-Q3"},
    },
    {
        "id": "play_digital_001",
        "text": "Digital/Website Lead Playbook: Step 1: Trigger automated email within 2 minutes of form submission. Step 2: Score lead based on form data and website behavior. Step 3: If score > 80, route to sales immediately. Step 4: If score 60-80, send personalized email sequence. Step 5: If score < 60, add to nurture campaign. Step 6: Track engagement (email opens, clicks, page views). Step 7: Escalate to sales when engagement threshold met. Step 8: Offer live chat for high-intent visitors. Step 9: Retarget with relevant ads. Step 10: Measure conversion at each stage.",
        "metadata": {"source": "digital_marketing", "type": "digital", "version": "2024-Q3"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  LEAD SCORING MODELS
# ══════════════════════════════════════════════════════════════════

LEAD_SCORING_MODELS = [
    {
        "id": "score_demographic_001",
        "text": "Demographic Scoring: Age 25-45: +20 points (peak banking years). Age 45-65: +15 points (accumulation phase). Income $75K+: +20 points. Income $50-75K: +15 points. Income $25-50K: +10 points. Homeowner: +15 points. Employed full-time: +10 points. Recent life event (marriage, home purchase, baby): +20 points. Geographic location (high-growth market): +10 points.",
        "metadata": {"model": "demographic", "type": "scoring", "version": "2024-Q3"},
    },
    {
        "id": "score_behavioral_001",
        "text": "Behavioral Scoring: Visited product page: +10 points. Used rate calculator: +15 points. Downloaded brochure: +10 points. Started application: +25 points. Abandoned application: +5 points (still interested). Opened email: +5 points. Clicked email link: +10 points. Attended webinar: +15 points. Referred by existing customer: +20 points. Multiple touchpoints in 7 days: +10 points.",
        "metadata": {"model": "behavioral", "type": "scoring", "version": "2024-Q3"},
    },
    {
        "id": "score_firmographic_001",
        "text": "Firmographic Scoring (Business): Company revenue $1M+: +20 points. Company revenue $500K-$1M: +15 points. 10+ employees: +15 points. In growth industry (tech, healthcare): +10 points. Recently funded: +20 points. Current banking relationship: +10 points. Multiple accounts needed: +15 points. International operations: +10 points.",
        "metadata": {"model": "firmographic", "type": "scoring", "version": "2024-Q3"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CONVERSION PATTERNS
# ══════════════════════════════════════════════════════════════════

CONVERSION_PATTERNS = [
    {
        "id": "conv_high_intent_001",
        "text": "High-Intent Conversion Patterns: Leads who convert within 24 hours typically: Visited pricing page, Used calculator, Started application, Had prior relationship, Were referred. Average conversion rate: 35%. Key factors: Speed to lead (<5 min response), Personalized offer, Clear next step, Low friction application.",
        "metadata": {"pattern": "high_intent", "type": "conversion", "conversion_rate": 0.35},
    },
    {
        "id": "conv_nurture_001",
        "text": "Nurture Conversion Patterns: Leads who convert after nurture typically: Received 5-7 touches, Engaged with content, Attended webinar/event, Saw social proof, Had life change. Average conversion rate: 12%. Key factors: Consistent follow-up, Value-first content, Relationship building, Timing with life events.",
        "metadata": {"pattern": "nurture", "type": "conversion", "conversion_rate": 0.12},
    },
    {
        "id": "conv_referral_001",
        "text": "Referral Conversion Patterns: Referred leads convert at 3x the rate of non-referred. Average conversion rate: 28%. Key factors: Trust transfer from referrer, Social proof, Dual incentive ($100 each), Faster qualification, Higher lifetime value.",
        "metadata": {"pattern": "referral", "type": "conversion", "conversion_rate": 0.28},
    },
]

# ══════════════════════════════════════════════════════════════════
#  PRODUCT ELIGIBILITY
# ══════════════════════════════════════════════════════════════════

PRODUCT_ELIGIBILITY = [
    {
        "id": "elig_checking_001",
        "text": "Checking Account Eligibility: No credit score required. Age 18+ (or joint with parent). Valid SSN or ITIN. US resident. No ChexSystems negative marks. Easy qualification — most leads qualify.",
        "metadata": {"product": "checking", "qualification_difficulty": "easy"},
    },
    {
        "id": "elig_savings_001",
        "text": "Savings Account Eligibility: No credit score required. Age 18+. Valid SSN. US resident. No minimum balance for basic. No ChexSystems issues. Very easy qualification.",
        "metadata": {"product": "savings", "qualification_difficulty": "easy"},
    },
    {
        "id": "elig_credit_card_001",
        "text": "Credit Card Eligibility: Minimum credit score 670 (cash back) or 720 (travel rewards). DTI < 36%. No bankruptcies in 7 years. Income $12,000+ (basic) or $30,000+ (premium). Age 18+. US resident. Moderate qualification difficulty.",
        "metadata": {"product": "credit_card", "qualification_difficulty": "moderate"},
    },
    {
        "id": "elig_mortgage_001",
        "text": "Mortgage Eligibility: Minimum credit score 620. DTI < 43%. 2 years employment. 2 years tax returns. Down payment 3-20%. Property appraisal. Complex qualification — multiple documents required.",
        "metadata": {"product": "mortgage", "qualification_difficulty": "complex"},
    },
    {
        "id": "elig_auto_loan_001",
        "text": "Auto Loan Eligibility: Minimum credit score 660. DTI < 50%. Vehicle < 10 years old. Employment verification. Moderate qualification difficulty.",
        "metadata": {"product": "auto_loan", "qualification_difficulty": "moderate"},
    },
    {
        "id": "elig_investment_001",
        "text": "Investment Account Eligibility: No credit score required. Age 18+. Valid SSN. Earned income (for IRA). Minimum investment varies by product. Easy to moderate qualification.",
        "metadata": {"product": "investment", "qualification_difficulty": "easy"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE RULES
# ══════════════════════════════════════════════════════════════════

COMPLIANCE_RULES = [
    {
        "id": "comp_tcpa_001",
        "text": "TCPA Compliance for Lead Outreach: Do Not Call (DNC) registry must be checked before calling. Prior express written consent required for autodialed calls/texts. Calls allowed 8am-9pm local time. Must identify yourself and bank. Must provide opt-out mechanism. Penalties: $500-$1,500 per violation. Record consent for all leads.",
        "metadata": {"regulation": "TCPA", "type": "compliance", "jurisdiction": "US"},
    },
    {
        "id": "comp_dnc_001",
        "text": "Do Not Call (DNC) Compliance: Check National DNC Registry before any outbound calls. State DNC lists must also be checked. DNC registration is free at donotcall.gov. Penalties: $500 per call to DNC-listed number. Internal DNC list must be maintained and honored. Referrals are exempt if referral has business relationship.",
        "metadata": {"regulation": "DNC", "type": "compliance", "jurisdiction": "US"},
    },
    {
        "id": "comp_consent_001",
        "text": "Consent Requirements: Verbal consent: Record and timestamp. Written consent: Keep signed form or digital acknowledgment. Online consent: Checkbox must be un-checked by default (no pre-checking). Consent must be specific (not blanket). Consent can be withdrawn at any time. Maintain consent records for 5 years minimum.",
        "metadata": {"regulation": "consent", "type": "compliance", "jurisdiction": "US"},
    },
    {
        "id": "comp_fair_lending_001",
        "text": "Fair Lending in Lead Qualification: Cannot discriminate based on race, color, religion, national origin, sex, marital status, age, public assistance. Cannot use lead score to steer to higher-cost products. Same qualification criteria must apply to all leads in same category. Document all qualification decisions. Monitor for disparate impact in qualification outcomes.",
        "metadata": {"regulation": "ECOA", "type": "compliance", "jurisdiction": "US"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  COMPETITOR INTELLIGENCE
# ══════════════════════════════════════════════════════════════════

COMPETITOR_INTELLIGENCE = [
    {
        "id": "comp_chase_001",
        "text": "Competitor: Chase Bank — Strengths: Largest branch network, strong brand, Chase Sapphire brand loyalty. Weaknesses: Lower savings rates, higher fees, less personalized service. Our advantage: Higher APY (4.50% vs 0.01%), no-fee checking, digital-first experience. Counter: Emphasize rate difference and fee savings.",
        "metadata": {"competitor": "chase", "type": "competitive_intel"},
    },
    {
        "id": "comp_bofa_001",
        "text": "Competitor: Bank of America — Strengths: Merrill integration, Preferred Rewards program. Weaknesses: Complex fee structure, lower rates for non-preferred. Our advantage: Simpler products, transparent fees, competitive rates for all customers. Counter: Emphasize simplicity and transparency.",
        "metadata": {"competitor": "bank_of_america", "type": "competitive_intel"},
    },
    {
        "id": "comp_online_001",
        "text": "Competitor: Online-Only Banks (Ally, Marcus, Discover) — Strengths: High APY, low fees, digital-first. Weaknesses: No branches, limited product range, no relationship pricing. Our advantage: Full-service banking, relationship pricing, personal advisory. Counter: Emphasize comprehensive service and human touch.",
        "metadata": {"competitor": "online_banks", "type": "competitive_intel"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "qualification_criteria": QUALIFICATION_CRITERIA,
        "sales_playbooks": SALES_PLAYBOOKS,
        "lead_scoring_models": LEAD_SCORING_MODELS,
        "conversion_patterns": CONVERSION_PATTERNS,
        "product_eligibility": PRODUCT_ELIGIBILITY,
        "compliance_rules": COMPLIANCE_RULES,
        "competitor_intelligence": COMPETITOR_INTELLIGENCE,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  ✓ {collection_name}: {count} documents")

    print("\n✅ Lead Qualification Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
