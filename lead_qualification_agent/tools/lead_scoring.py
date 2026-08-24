"""
Lead Scoring Tool — Score and tier leads based on demographic, behavioral, and intent signals.
"""

from __future__ import annotations

from typing import Any


# ── Scoring weights ───────────────────────────────────────────────
SCORING_WEIGHTS = {
    "demographic": 0.35,
    "behavioral": 0.35,
    "intent": 0.30,
}

TIER_THRESHOLDS = {"hot": 80, "warm": 60, "cool": 40, "cold": 0}


async def score_lead(lead: dict) -> dict[str, Any]:
    """Score a lead based on demographic, behavioral, and intent signals."""
    demographics = lead.get("demographics", {})
    behavior = lead.get("behavior", {})
    product_interest = lead.get("product_interest", "")
    source = lead.get("source", "")

    # Demographic score (0-100)
    demo_score = 0
    age = demographics.get("age", 0)
    income = demographics.get("income", 0)
    credit_score = demographics.get("credit_score", 0)
    homeowner = demographics.get("homeowner", False)

    if 25 <= age <= 45:
        demo_score += 25
    elif 45 < age <= 65:
        demo_score += 20
    elif 18 <= age < 25:
        demo_score += 10

    if income >= 100000:
        demo_score += 25
    elif income >= 75000:
        demo_score += 20
    elif income >= 50000:
        demo_score += 15
    elif income >= 25000:
        demo_score += 10

    if credit_score >= 750:
        demo_score += 20
    elif credit_score >= 700:
        demo_score += 15
    elif credit_score >= 650:
        demo_score += 10

    if homeowner:
        demo_score += 15

    # Behavioral score (0-100)
    beh_score = 0
    pages = behavior.get("pages_visited", 0)
    calc_used = behavior.get("calculator_used", False)
    app_started = behavior.get("application_started", False)

    if pages >= 5:
        beh_score += 25
    elif pages >= 3:
        beh_score += 15
    elif pages >= 1:
        beh_score += 5

    if calc_used:
        beh_score += 25

    if app_started:
        beh_score += 35

    # Base engagement
    beh_score += 10

    # Intent score (0-100)
    intent_score = 0
    if source == "referral":
        intent_score += 30
    elif source == "chat":
        intent_score += 25
    elif source == "webinar":
        intent_score += 20
    elif source == "website":
        intent_score += 15
    elif source == "outbound":
        intent_score += 10

    # Product interest alignment
    high_intent_products = ["mortgage", "auto_loan"]
    if product_interest in high_intent_products:
        intent_score += 25
    else:
        intent_score += 15

    # Weighted total
    demo_score = min(demo_score, 100)
    beh_score = min(beh_score, 100)
    intent_score = min(intent_score, 100)

    total_score = round(
        demo_score * SCORING_WEIGHTS["demographic"]
        + beh_score * SCORING_WEIGHTS["behavioral"]
        + intent_score * SCORING_WEIGHTS["intent"]
    )

    # Determine tier
    tier = "cold"
    for tier_name, threshold in TIER_THRESHOLDS.items():
        if total_score >= threshold:
            tier = tier_name
            break

    return {
        "lead_id": lead.get("lead_id"),
        "total_score": total_score,
        "tier": tier,
        "breakdown": {
            "demographic": {"score": demo_score, "weight": SCORING_WEIGHTS["demographic"], "contribution": round(demo_score * SCORING_WEIGHTS["demographic"])},
            "behavioral": {"score": beh_score, "weight": SCORING_WEIGHTS["behavioral"], "contribution": round(beh_score * SCORING_WEIGHTS["behavioral"])},
            "intent": {"score": intent_score, "weight": SCORING_WEIGHTS["intent"], "contribution": round(intent_score * SCORING_WEIGHTS["intent"])},
        },
        "factors": {
            "age": age,
            "income": income,
            "credit_score": credit_score,
            "homeowner": homeowner,
            "pages_visited": pages,
            "calculator_used": calc_used,
            "application_started": app_started,
            "source": source,
            "product_interest": product_interest,
        },
    }


async def score_leads_batch(leads: list[dict]) -> dict[str, Any]:
    """Score multiple leads at once."""
    results = []
    for lead in leads:
        score_result = await score_lead(lead)
        results.append(score_result)

    results.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "total_scored": len(results),
        "results": results,
        "tier_distribution": {
            "hot": sum(1 for r in results if r["tier"] == "hot"),
            "warm": sum(1 for r in results if r["tier"] == "warm"),
            "cool": sum(1 for r in results if r["tier"] == "cool"),
            "cold": sum(1 for r in results if r["tier"] == "cold"),
        },
        "avg_score": round(sum(r["total_score"] for r in results) / max(len(results), 1), 1),
    }


async def get_scoring_model() -> dict[str, Any]:
    """Get the current scoring model configuration."""
    return {
        "weights": SCORING_WEIGHTS,
        "tier_thresholds": TIER_THRESHOLDS,
        "rules": {
            "demographic": {
                "age_25_45": "+25 points",
                "age_45_65": "+20 points",
                "income_100k_plus": "+25 points",
                "income_75k_plus": "+20 points",
                "credit_750_plus": "+20 points",
                "homeowner": "+15 points",
            },
            "behavioral": {
                "pages_5_plus": "+25 points",
                "pages_3_plus": "+15 points",
                "calculator_used": "+25 points",
                "application_started": "+35 points",
            },
            "intent": {
                "referral_source": "+30 points",
                "chat_source": "+25 points",
                "webinar_source": "+20 points",
                "high_intent_product": "+25 points",
            },
        },
    }


async def update_scoring_weights(
    demographic: float | None = None,
    behavioral: float | None = None,
    intent: float | None = None,
) -> dict[str, Any]:
    """Update scoring weights (must sum to 1.0)."""
    if demographic is not None:
        SCORING_WEIGHTS["demographic"] = demographic
    if behavioral is not None:
        SCORING_WEIGHTS["behavioral"] = behavioral
    if intent is not None:
        SCORING_WEIGHTS["intent"] = intent

    total = sum(SCORING_WEIGHTS.values())
    valid = abs(total - 1.0) < 0.01

    return {
        "weights": SCORING_WEIGHTS,
        "total_weight": round(total, 2),
        "valid": valid,
        "message": "Scoring weights updated." if valid else f"Warning: weights sum to {total}, should be 1.0",
    }
