"""
Sales Playbooks Tool — Retrieve and execute sales playbooks based on lead characteristics.
"""

from __future__ import annotations

from typing import Any


# ── Playbook definitions ──────────────────────────────────────────
PLAYBOOKS = {
    "mortgage_buyer": {
        "name": "Mortgage Buyer Playbook",
        "trigger": {"product_interest": "mortgage", "tier": ["hot", "warm"]},
        "steps": [
            {"step": 1, "action": "Confirm pre-qualification status", "template": "Are you pre-approved with another lender? We can match or beat their rate."},
            {"step": 2, "action": "Understand timeline", "template": "When are you looking to close on a home? This helps us prepare the right rate lock."},
            {"step": 3, "action": "Review financial profile", "template": "Let me quickly review your income and credit to find the best options for you."},
            {"step": 4, "action": "Present mortgage options", "template": "Based on your profile, here are the mortgage products that fit your needs..."},
            {"step": 5, "action": "Address objections", "template": "I understand your concern about rates. Let me show you how our total cost compares."},
            {"step": 6, "action": "Propose next step", "template": "Would you like to start a pre-approval application? It only takes 15 minutes."},
            {"step": 7, "action": "Schedule follow-up", "template": "Let's schedule a follow-up call to review your application and answer any questions."},
        ],
        "objection_handling": {
            "rates_too_high": "Our rates include no origination fees, so the total cost is competitive. Plus, we offer rate locks for 60 days.",
            "competitor_better": "We'd be happy to review their offer. Many of our customers find our total cost (fees + rate) is lower.",
            "not_ready": "No pressure! We can start a pre-approval that's valid for 90 days. You can shop with confidence.",
        },
    },
    "credit_card_shopper": {
        "name": "Credit Card Shopper Playbook",
        "trigger": {"product_interest": "credit_card", "tier": ["hot", "warm", "cool"]},
        "steps": [
            {"step": 1, "action": "Understand spending habits", "template": "What types of purchases do you make most? This helps me recommend the right rewards card."},
            {"step": 2, "action": "Identify current card", "template": "What card do you currently have? I can show you how our card compares."},
            {"step": 3, "action": "Present card benefits", "template": "Based on your spending, here's how much you'd earn with our card..."},
            {"step": 4, "action": "Address fee concerns", "template": "Our card has no annual fee, and the intro 0% APR lasts 15 months."},
            {"step": 5, "action": "Propose application", "template": "Would you like to apply? It takes just 3 minutes and there's no impact to your credit score for pre-qualification."},
        ],
        "objection_handling": {
            "have_good_card": "That's great! Let me show you how our rewards structure could earn you more on your specific spending.",
            "annual_fee": "Our cash back card has no annual fee. Even our travel card's fee is offset by the rewards.",
            "credit_concerns": "Pre-qualification doesn't affect your credit score. You only get a hard pull when you formally apply.",
        },
    },
    "savings_seeker": {
        "name": "Savings Account Seeker Playbook",
        "trigger": {"product_interest": "savings", "tier": ["hot", "warm"]},
        "steps": [
            {"step": 1, "action": "Understand savings goals", "template": "What are you saving for? Emergency fund, vacation, or long-term goals?"},
            {"step": 2, "action": "Compare current rate", "template": "What rate are you currently earning? I can show you the difference our APY makes."},
            {"step": 3, "action": "Present high-yield option", "template": "Our savings account earns 4.50% APY — that's 10x the national average."},
            {"step": 4, "action": "Show compound growth", "template": "On $10,000, you'd earn $450/year with us vs $46 at the national average."},
            {"step": 5, "action": "Propose account opening", "template": "Would you like to open an account today? It takes 5 minutes online."},
        ],
        "objection_handling": {
            "online_only": "We're FDIC insured just like traditional banks. You get the best rates because we don't have branch overhead.",
            "minimum_balance": "There's no minimum balance requirement. You can start with any amount.",
            "access_to_funds": "You can transfer to your checking account anytime. 6 free withdrawals per month, then $10 each.",
        },
    },
    "investment_curious": {
        "name": "Investment Curious Playbook",
        "trigger": {"product_interest": "investment", "tier": ["warm", "cool"]},
        "steps": [
            {"step": 1, "action": "Assess experience level", "template": "Have you invested before, or is this your first time? I'll tailor my recommendations accordingly."},
            {"step": 2, "action": "Understand goals", "template": "What's your investment goal? Retirement, building wealth, or saving for a specific目标?"},
            {"step": 3, "action": "Discuss risk tolerance", "template": "How would you feel if your investment dropped 10% in a month? This helps me recommend the right mix."},
            {"step": 4, "action": "Present IRA options", "template": "For retirement, a Roth IRA offers tax-free growth. You can contribute up to $7,000/year."},
            {"step": 5, "action": "Address concerns", "template": "I understand it can feel overwhelming. We have target-date funds that automatically adjust risk."},
            {"step": 6, "action": "Propose consultation", "template": "Would you like a free consultation with our wealth advisor? They can create a personalized plan."},
        ],
        "objection_handling": {
            "too_risky": "We have conservative options like bond funds that are lower risk. We'll find the right balance for you.",
            "too_complicated": "Our robo-advisor does the heavy lifting. You answer a few questions, and we build a diversified portfolio.",
            "not_enough_money": "You can start with as little as $100. Many of our clients started small and built from there.",
        },
    },
}


async def get_playbook(product_interest: str, tier: str) -> dict[str, Any]:
    """Get the appropriate playbook for a lead."""
    for playbook in PLAYBOOKS.values():
        trigger = playbook.get("trigger", {})
        if product_interest in trigger.get("product_interest", ""):
            if tier in trigger.get("tier", []):
                return playbook
    return {"message": "No specific playbook found. Use general qualification approach."}


async def get_all_playbooks() -> dict[str, Any]:
    """Get all available playbooks."""
    return {
        "playbooks": [
            {"name": pb["name"], "trigger": pb["trigger"], "steps_count": len(pb["steps"])}
            for pb in PLAYBOOKS.values()
        ]
    }


async def get_objection_handling(product_interest: str, objection: str) -> dict[str, Any]:
    """Get objection handling response for a specific product."""
    for playbook in PLAYBOOKS.values():
        trigger = playbook.get("trigger", {})
        if product_interest in trigger.get("product_interest", ""):
            objections = playbook.get("objection_handling", {})
            for key, response in objections.items():
                if key in objection.lower() or objection.lower() in key:
                    return {"response": response, "playbook": playbook["name"]}

    return {"response": "I understand your concern. Let me address that for you. What specific aspect would you like me to clarify?"}


async def get_conversation_starters(product_interest: str) -> dict[str, Any]:
    """Get conversation starters for a product."""
    starters = {
        "mortgage": ["What's driving your home search right now?", "Have you been pre-approved yet?", "What's your ideal timeline?"],
        "credit_card": ["What do you use your current card for most?", "Are you looking to earn rewards or save on interest?", "Do you travel internationally?"],
        "savings": ["What are your savings goals?", "What rate are you currently earning?", "Do you have an emergency fund?"],
        "investment": ["What's your investment experience level?", "Are you saving for retirement or another goal?", "How do you feel about risk?"],
        "auto_loan": ["Are you looking at new or used vehicles?", "Have you picked out a car yet?", "What monthly payment are you comfortable with?"],
    }

    return {"product": product_interest, "starters": starters.get(product_interest, ["How can I help you today?"])}
