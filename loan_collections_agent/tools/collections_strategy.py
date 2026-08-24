"""
Collections Strategy Tool — MCP tool stub.

Analyzes debtor profiles and recommends optimal collection strategies
using embedding-based matching against successful past resolutions.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def recommend_strategy(
    account_id: str,
    borrower_name: str,
    delinquency_days: int,
    product_type: str,
    outstanding_balance: float,
    monthly_payment: float,
    has_collateral: bool,
    has_hardship: bool,
    previous_contact_outcome: str | None = None,
) -> dict:
    """
    Recommend the optimal collection strategy based on debtor profile.

    Uses rule-based logic (production would use ML embeddings to match
    against successful past resolution profiles).
    """
    logger.info("Recommending strategy for %s (%d days delinquent)", account_id, delinquency_days)

    # Determine collection stage
    if delinquency_days <= 30:
        stage = "early_stage"
        stage_description = "Early-Stage (1-30 days)"
    elif delinquency_days <= 90:
        stage = "mid_stage"
        stage_description = "Mid-Stage (31-90 days)"
    elif delinquency_days <= 180:
        stage = "late_stage"
        stage_description = "Late-Stage (91-180 days)"
    else:
        stage = "charge_off"
        stage_description = "Charge-Off / Recovery (180+ days)"

    # Build recommended actions
    actions = []
    contact_strategy = []
    compliance_notes = []

    if stage == "early_stage":
        actions = [
            "Send automated payment reminder (email/SMS)",
            "Personal phone call within 3 business days",
            "Offer self-service payment portal link",
            "Document contact attempt and borrower response",
        ]
        contact_strategy = [
            "Day 1: Automated email/SMS reminder",
            "Day 3: Personal phone call (empathetic tone)",
            "Day 7: Follow-up call + written notice",
            "Day 14: Discuss payment options",
            "Day 21: Formal past-due notice",
        ]

    elif stage == "mid_stage":
        actions = [
            "Weekly outreach (alternating phone/email)",
            "Evaluate hardship program eligibility",
            "Discuss deferment or modified payment plan",
            "Consider credit reporting (after 30 days delinquent)",
            "Begin documenting all outcomes for compliance",
        ]
        contact_strategy = [
            "Weekly calls (Mon/Wed/Fri rotation)",
            "Alternate with email updates",
            "Offer payment plan options (3-4 tiers)",
            "If hardship claimed: initiate hardship assessment",
            "If no response after 2 weeks: escalate to supervisor",
        ]

    elif stage == "late_stage":
        actions = [
            "Bi-weekly formal outreach with documentation",
            "Send formal demand letter",
            "Evaluate for workout options (modification, settlement)",
            "Assess collateral value for secured loans",
            "Begin skip tracing if contact is lost",
            "Initiate legal review for litigation",
        ]
        contact_strategy = [
            "Bi-weekly formal calls with recorded lines",
            "Written demand letter (certified mail)",
            "Offer settlement at 30-50% discount",
            "If no response: engage skip tracing service",
            "If collateral: assess repossession vs. workout",
        ]

    else:  # charge_off
        actions = [
            "Final internal recovery attempt (6-12 months)",
            "Evaluate for third-party collection referral",
            "Assess debt sale viability (5-20 cents on dollar)",
            "Consider litigation if statute of limitations permits",
            "Record charge-off for tax purposes",
        ]
        contact_strategy = [
            "Monthly outreach for internal recovery",
            "If no resolution in 90 days: refer to external agency",
            "If balance > $10,000: consider litigation",
            "Document all recovery efforts for tax write-off",
        ]

    # Product-specific adjustments
    product_adjustments = []
    if product_type == "mortgage":
        product_adjustments = [
            "Priority: Loss mitigation team review (required by regulation)",
            "Offer loan modification or forbearance before acceleration",
            "Dual tracking rules apply — cannot foreclose while modification under review",
            "Provide HUD-approved housing counseling referral",
        ]
        compliance_notes.append("Reg X (Regulation X) loss mitigation rules apply to mortgage servicing")
    elif product_type == "auto_loan":
        product_adjustments = [
            "Assess vehicle value vs. outstanding balance",
            "Consider voluntary surrender option",
            "If repossession: follow state-specific redemption laws",
            " GAP insurance may cover deficiency balance",
        ]
    elif product_type == "personal_loan":
        product_adjustments = [
            "Unsecured — no collateral to leverage",
            "Settlement more likely viable",
            "Consider statute of limitations (varies by state: 3-10 years)",
        ]
    elif product_type == "credit_card":
        product_adjustments = [
            "Unsecured — settlement primary recovery tool",
            "Can offer hardship programs (reduced APR, waive fees)",
            "Consider balance transfer to lower-rate product",
        ]

    # Hardship adjustments
    if has_hardship:
        actions.insert(0, "PRIORITY: Initiate hardship assessment immediately")
        actions.insert(1, "Request supporting documentation")
        compliance_notes.append("Hardship claims must be documented and evaluated within 5 business days")

    # Similar past resolution
    similar_cases = await _find_similar_resolutions(delinquency_days, product_type, outstanding_balance, has_hardship)

    strategy_score = _calculate_strategy_score(delinquency_days, outstanding_balance, has_collateral, has_hardship, previous_contact_outcome)

    return {
        "account_id": account_id,
        "borrower_name": borrower_name,
        "recommended_strategy": {
            "stage": stage,
            "stage_description": stage_description,
            "primary_approach": actions[0] if actions else "Standard outreach",
            "actions": actions,
            "contact_strategy": contact_strategy,
            "product_adjustments": product_adjustments,
            "compliance_notes": compliance_notes,
        },
        "strategy_score": strategy_score,
        "similar_resolution_cases": similar_cases,
        "escalation_needed": delinquency_days > 90 or (delinquency_days > 60 and not has_hardship),
        "recommended_timeline": {
            "next_action": "Within 2 business days",
            "review_date": f"{(datetime.utcnow().replace(day=min(datetime.utcnow().day + 14, 28))).strftime('%Y-%m-%d')}",
            "escalation_date": f"{(datetime.utcnow().replace(day=min(datetime.utcnow().day + 30, 28))).strftime('%Y-%m-%d')}",
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


async def _find_similar_resolutions(
    delinquency_days: int,
    product_type: str,
    balance: float,
    has_hardship: bool,
) -> list[dict]:
    """Find similar past resolution cases (simulated — production uses embeddings)."""
    cases = [
        {
            "case_id": "PAST-001",
            "scenario": "Mortgage forbearance for job loss",
            "delinquency_days": 45,
            "product_type": "mortgage",
            "resolution": "6-month forbearance + income-driven plan",
            "outcome": "success",
            "recovery_rate": 0.99,
            "similarity_score": 0.92,
        },
        {
            "case_id": "PAST-002",
            "scenario": "Auto loan settlement for relocation",
            "delinquency_days": 120,
            "product_type": "auto_loan",
            "resolution": "35% settlement with 12-month plan",
            "outcome": "success",
            "recovery_rate": 0.65,
            "similarity_score": 0.87,
        },
        {
            "case_id": "PAST-003",
            "scenario": "Personal loan workout for self-employed income dip",
            "delinquency_days": 75,
            "product_type": "personal_loan",
            "resolution": "Income-driven repayment with seasonal adjustment",
            "outcome": "success",
            "recovery_rate": 1.0,
            "similarity_score": 0.84,
        },
    ]

    # Filter and sort by relevance
    relevant = [c for c in cases if c["product_type"] == product_type or c["delinquency_days"] >= delinquency_days * 0.5]
    relevant.sort(key=lambda x: x["similarity_score"], reverse=True)
    return relevant[:3]


def _calculate_strategy_score(
    delinquency_days: int,
    balance: float,
    has_collateral: bool,
    has_hardship: bool,
    previous_outcome: str | None,
) -> dict:
    """Calculate a strategy effectiveness score."""
    # Recovery probability
    if delinquency_days <= 30:
        recovery_prob = 0.85
    elif delinquency_days <= 60:
        recovery_prob = 0.70
    elif delinquency_days <= 90:
        recovery_prob = 0.55
    elif delinquency_days <= 180:
        recovery_prob = 0.35
    else:
        recovery_prob = 0.15

    # Adjust for factors
    if has_collateral:
        recovery_prob = min(recovery_prob + 0.15, 1.0)
    if has_hardship:
        recovery_prob = min(recovery_prob + 0.10, 1.0)
    if previous_outcome == "promised_to_pay":
        recovery_prob = min(recovery_prob + 0.05, 1.0)
    elif previous_outcome == "refused_to_communicate":
        recovery_prob = max(recovery_prob - 0.20, 0.05)

    # Strategy urgency
    if delinquency_days > 120:
        urgency = "critical"
    elif delinquency_days > 60:
        urgency = "high"
    elif delinquency_days > 30:
        urgency = "medium"
    else:
        urgency = "low"

    return {
        "recovery_probability": round(recovery_prob, 2),
        "urgency": urgency,
        "estimated_recovery_amount": round(balance * recovery_prob, 2),
        "recommended_settlement_range": {
            "minimum_pct": max(30, 100 - int(delinquency_days * 0.5)),
            "maximum_pct": 100,
        },
    }
