"""
Qualification Criteria Tool — Evaluate leads against qualification frameworks.
"""

from __future__ import annotations

from typing import Any


# ── Qualification frameworks ──────────────────────────────────────
FRAMEWORKS = {
    "BANT": {
        "name": "BANT",
        "criteria": {
            "budget": {"description": "Financial capacity to purchase", "checks": ["income", "credit_score", "existing_assets", "debt_to_income"]},
            "authority": {"description": "Decision-maker status", "checks": ["age", "employment_status", "account_ownership"]},
            "need": {"description": "Genuine banking need", "checks": ["life_stage", "current_products", "expressed_interest"]},
            "timeline": {"description": "When they need the product", "checks": ["urgency", "competing_offers", "stated_timeline"]},
        },
    },
    "CHAMP": {
        "name": "CHAMP",
        "criteria": {
            "challenges": {"description": "Problems they're facing", "checks": ["pain_points", "current_frustrations", "unmet_needs"]},
            "authority": {"description": "Decision-making power", "checks": ["account_authority", "joint_account", "business_owner"]},
            "money": {"description": "Financial qualification", "checks": ["minimum_balance", "income_threshold", "credit_requirement"]},
            "prioritization": {"description": "Urgency level", "checks": ["immediate", "30_days", "90_days", "exploring"]},
        },
    },
    "MEDDIC": {
        "name": "MEDDIC",
        "criteria": {
            "metrics": {"description": "Quantifiable benefits", "checks": ["fee_savings", "interest_earned", "convenience_value"]},
            "economic_buyer": {"description": "Budget controller", "checks": ["individual", "joint_holder", "business_owner"]},
            "decision_criteria": {"description": "What matters most", "checks": ["rate", "fees", "convenience", "brand"]},
            "decision_process": {"description": "How they decide", "checks": ["comparison", "advisor", "online_research"]},
            "identify_pain": {"description": "Core problem", "checks": ["high_fees", "poor_rates", "inconvenience"]},
            "champion": {"description": "Internal advocate", "checks": ["existing_customer", "employee_referral"]},
        },
    },
}


async def evaluate_lead(
    lead: dict,
    framework: str = "BANT",
) -> dict[str, Any]:
    """Evaluate a lead against a qualification framework."""
    if framework not in FRAMEWORKS:
        return {"error": f"Framework {framework} not found. Available: {list(FRAMEWORKS.keys())}"}

    fw = FRAMEWORKS[framework]
    demographics = lead.get("demographics", {})
    behavior = lead.get("behavior", {})

    results = {}
    score = 0

    if framework == "BANT":
        # Budget
        budget_score = 0
        if demographics.get("income", 0) >= 50000:
            budget_score += 25
        if demographics.get("credit_score", 0) >= 670:
            budget_score += 25
        results["budget"] = {"score": min(budget_score, 50), "max": 50, "qualified": budget_score >= 25}
        score += budget_score

        # Authority
        authority_score = 0
        if demographics.get("age", 0) >= 18:
            authority_score += 25
        results["authority"] = {"score": min(authority_score, 25), "max": 25, "qualified": authority_score >= 25}
        score += authority_score

        # Need
        need_score = 0
        if lead.get("product_interest"):
            need_score += 25
        if behavior.get("pages_visited", 0) >= 2:
            need_score += 15
        if behavior.get("calculator_used"):
            need_score += 10
        results["need"] = {"score": min(need_score, 50), "max": 50, "qualified": need_score >= 25}
        score += need_score

        # Timeline
        timeline_score = 20  # Base score
        if behavior.get("application_started"):
            timeline_score += 30
        results["timeline"] = {"score": min(timeline_score, 50), "max": 50, "qualified": timeline_score >= 20}
        score += timeline_score

    elif framework == "CHAMP":
        # Challenges
        challenges_score = 30  # Base from expressed interest
        results["challenges"] = {"score": challenges_score, "max": 40, "qualified": challenges_score >= 20}
        score += challenges_score

        # Authority
        authority_score = 25 if demographics.get("age", 0) >= 18 else 0
        results["authority"] = {"score": authority_score, "max": 25, "qualified": authority_score >= 25}
        score += authority_score

        # Money
        money_score = 0
        if demographics.get("income", 0) >= 50000:
            money_score += 20
        if demographics.get("credit_score", 0) >= 670:
            money_score += 15
        results["money"] = {"score": min(money_score, 35), "max": 35, "qualified": money_score >= 15}
        score += money_score

        # Prioritization
        priority_score = 10  # Base
        if behavior.get("application_started"):
            priority_score += 25
        elif behavior.get("pages_visited", 0) >= 3:
            priority_score += 15
        results["prioritization"] = {"score": min(priority_score, 35), "max": 35, "qualified": priority_score >= 10}
        score += priority_score

    # Determine qualification status
    qualified_count = sum(1 for v in results.values() if v.get("qualified"))
    total_criteria = len(results)
    qualification_rate = qualified_count / total_criteria if total_criteria > 0 else 0

    if qualification_rate >= 0.75:
        status = "fully_qualified"
    elif qualification_rate >= 0.5:
        status = "partially_qualified"
    else:
        status = "unqualified"

    return {
        "lead_id": lead.get("lead_id"),
        "framework": framework,
        "results": results,
        "total_score": score,
        "max_score": sum(v.get("max", 0) for v in results.values()),
        "qualification_rate": f"{qualification_rate*100:.0f}%",
        "status": status,
    }


async def get_qualification_checklist(
    product_interest: str,
) -> dict[str, Any]:
    """Get a qualification checklist for a specific product."""
    checklists = {
        "checking": {"required": ["age_18_plus", "valid_ssn", "us_resident"], "preferred": ["direct_deposit", "no_chexsystems_flags"]},
        "savings": {"required": ["age_18_plus", "valid_ssn", "us_resident"], "preferred": ["initial_deposit", "no_chexsystems_flags"]},
        "credit_card": {"required": ["age_18_plus", "credit_score_670_plus", "income_12k_plus", "no_bankruptcy_7yr"], "preferred": ["credit_score_720_plus", "low_utilization", "stable_employment"]},
        "mortgage": {"required": ["age_18_plus", "credit_score_620_plus", "income_40k_plus", "employment_2yr", "down_payment_3pct"], "preferred": ["credit_score_720_plus", "low_dti", "large_down_payment"]},
        "auto_loan": {"required": ["age_18_plus", "credit_score_660_plus", "income_25k_plus"], "preferred": ["credit_score_720_plus", "low_dti", "vehicle_selected"]},
        "investment": {"required": ["age_18_plus", "valid_ssn", "earned_income"], "preferred": ["financial_goals_defined", "risk_tolerance_assessed"]},
    }

    checklist = checklists.get(product_interest, {"required": [], "preferred": []})

    return {
        "product": product_interest,
        "checklist": checklist,
        "total_required": len(checklist["required"]),
        "total_preferred": len(checklist["preferred"]),
    }


async def get_frameworks() -> dict[str, Any]:
    """Get all available qualification frameworks."""
    return {
        "frameworks": [
            {"name": fw["name"], "criteria": list(fw["criteria"].keys()), "description": f"{fw['name']} qualification framework"}
            for fw in FRAMEWORKS.values()
        ]
    }
