"""
Recommendation Engine Tool — ML-based product recommendations.
"""

from __future__ import annotations

from typing import Any

from tools.customer_360 import CUSTOMER_DB
from tools.product_catalog import PRODUCT_DB


# ── Cross-sell rules ──────────────────────────────────────────────
CROSS_SELL_RULES: dict[str, list[dict[str, Any]]] = {
    "has_checking_no_savings": {
        "trigger": "has_checking_no_savings",
        "condition": lambda p: "PROD-CHK-001" in p and "PROD-SAV-001" not in p,
        "recommend": ["PROD-SAV-001"],
        "offer": "0.25% APY bonus for 6 months",
        "conversion_rate": 0.35,
    },
    "active_debit_no_credit": {
        "trigger": "active_debit_no_credit",
        "condition": lambda p: "PROD-CHK-001" in p and not any("PROD-CC" in pid for pid in p),
        "recommend": ["PROD-CC-001"],
        "offer": "0% intro APR 15 months + $200 cash back",
        "conversion_rate": 0.28,
    },
    "high_savings_no_investment": {
        "trigger": "high_savings_no_investment",
        "condition": lambda p: "PROD-SAV-001" in p and "PROD-CD-001" not in p and "PROD-IRA-001" not in p,
        "recommend": ["PROD-CD-001", "PROD-IRA-001"],
        "offer": "0.50% APY bonus on first CD",
        "conversion_rate": 0.22,
    },
    "has_auto_loan_no_insurance": {
        "trigger": "has_auto_loan_no_insurance",
        "condition": lambda p: "PROD-AUTO-001" in p,
        "recommend": ["PROD-CC-001"],
        "offer": "Bundled discount (auto loan + insurance = 0.25% rate reduction)",
        "conversion_rate": 0.40,
    },
    "mortgage_owner_no_heloc": {
        "trigger": "mortgage_owner_no_heloc",
        "condition": lambda p: "PROD-MTG-001" in p and "PROD-HELOC-001" not in p,
        "recommend": ["PROD-HELOC-001"],
        "offer": "No annual fee for first year",
        "conversion_rate": 0.18,
    },
    "student_loan_high_credit": {
        "trigger": "student_loan_high_credit",
        "condition": lambda p: "PROD-STU-001" in p,
        "recommend": ["PROD-PER-001"],
        "offer": "0.50% rate reduction + $200 cash back",
        "conversion_rate": 0.15,
    },
}


async def generate_recommendations(
    customer_id: str,
    max_recommendations: int = 10,
    strategy: str = "balanced",
) -> dict[str, Any]:
    """Generate personalized product recommendations."""
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    products_held = customer.get("existing_products", [])
    credit_score = customer.get("credit_score", 0)
    income = customer.get("income", 0)
    segment = customer.get("segment", "all")
    age = customer.get("age", 0)

    recommendations = []

    # 1. Cross-sell: Products from different categories
    held_categories = set()
    for pid in products_held:
        product = PRODUCT_DB.get(pid)
        if product:
            held_categories.add(product.get("category", ""))

    for pid, product in PRODUCT_DB.items():
        if pid in products_held:
            continue
        score = 0
        reasons = []

        # Credit score eligibility
        min_credit = product.get("min_credit_score", 0)
        if min_credit > 0 and credit_score < min_credit:
            continue  # Not eligible

        # Income eligibility
        min_income = product.get("min_income", 0)
        if min_income > 0 and income < min_income:
            continue  # Not eligible

        # Category diversity (different from held products)
        if product.get("category") not in held_categories:
            score += 20
            reasons.append("new_category")

        # Segment match
        if segment in product.get("target_segments", []):
            score += 15
            reasons.append("segment_match")

        # Age-based fit
        if product.get("subcategory") in ("roth_ira",) and age < 40:
            score += 10
            reasons.append("age_fit_roth")
        if product.get("subcategory") in ("cd",) and age > 50:
            score += 10
            reasons.append("age_fit_cd")
        if product.get("subcategory") in ("student_loan",) and age < 30:
            score += 8
            reasons.append("age_fit_student")

        # Credit score sweet spot
        if min_credit > 0:
            credit_buffer = credit_score - min_credit
            if 0 < credit_buffer < 50:
                score += 5
                reasons.append("credit_sweet_spot")

        # Product popularity (simulated)
        score += 5
        reasons.append("base_popularity")

        if score > 0:
            recommendations.append({
                "product_id": pid,
                "name": product["name"],
                "category": product["category"],
                "relevance_score": score,
                "reasons": reasons,
            })

    # 2. Cross-sell triggers
    for rule_name, rule in CROSS_SELL_RULES.items():
        try:
            if rule["condition"](products_held):
                for pid in rule["recommend"]:
                    if pid not in [r["product_id"] for r in recommendations] and pid not in products_held:
                        product = PRODUCT_DB.get(pid)
                        if product:
                            recommendations.append({
                                "product_id": pid,
                                "name": product["name"],
                                "category": product["category"],
                                "relevance_score": 40,  # High score for cross-sell
                                "reasons": ["cross_sell_trigger", rule_name],
                                "offer": rule["offer"],
                            })
        except Exception:
            pass

    # Sort by relevance
    recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {
        "customer_id": customer_id,
        "customer_segment": segment,
        "products_held": len(products_held),
        "recommendations": recommendations[:max_recommendations],
        "strategy": strategy,
    }


async def get_recommendation_explanation(
    customer_id: str,
    product_id: str,
) -> dict[str, Any]:
    """Get detailed explanation for a recommendation."""
    customer = CUSTOMER_DB.get(customer_id)
    product = PRODUCT_DB.get(product_id)

    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    if not product:
        return {"error": f"Product {product_id} not found"}

    products_held = customer.get("existing_products", [])
    credit_score = customer.get("credit_score", 0)
    income = customer.get("income", 0)
    segment = customer.get("segment", "all")
    age = customer.get("age", 0)

    explanations = []

    # Eligibility check
    min_credit = product.get("min_credit_score", 0)
    if min_credit > 0 and credit_score < min_credit:
        return {"error": "Not eligible", "reason": f"Credit score {credit_score} below minimum {min_credit}"}

    # Why recommended
    if segment in product.get("target_segments", []):
        explanations.append(f"Matches your customer segment ({segment})")

    held_categories = set()
    for pid in products_held:
        p = PRODUCT_DB.get(pid)
        if p:
            held_categories.add(p.get("category", ""))
    if product.get("category") not in held_categories:
        explanations.append("Diversifies your product portfolio with a new category")

    if product.get("subcategory") in ("roth_ira",) and age < 40:
        explanations.append("Roth IRA is ideal for your age — tax-free growth over decades")
    if product.get("subcategory") in ("cd",) and age > 50:
        explanations.append("CD provides guaranteed returns as you approach retirement")

    # Benefits
    if product.get("apy"):
        explanations.append(f"Earn {product['apy']}% APY — higher than national average")
    if product.get("rewards_rate"):
        explanations.append(f"Earn {product['rewards_rate']*100:.0f}% cash back on all purchases")
    if product.get("intro_apr_months"):
        explanations.append(f"Enjoy 0% intro APR for {product['intro_apr_months']} months")

    return {
        "customer_id": customer_id,
        "product_id": product_id,
        "product_name": product["name"],
        "explanations": explanations,
        "eligibility": "eligible",
    }


async def get_upsell_opportunities(customer_id: str) -> dict[str, Any]:
    """Identify upsell opportunities for existing products."""
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    products_held = customer.get("existing_products", [])
    credit_score = customer.get("credit_score", 0)
    income = customer.get("income", 0)

    upsells = []

    # Checking → Premium checking
    if "PROD-CHK-001" in products_held and income > 100000:
        upsells.append({
            "current_product": "Premium Checking",
            "upsell_product": "Premium Checking with Interest",
            "reason": "High income qualifies for interest-bearing checking",
            "benefit": "Earn 0.10% APY on balances over $10,000",
        })

    # Cash back card → Travel card
    if "PROD-CC-001" in products_held and credit_score > 720 and income > 50000:
        upsells.append({
            "current_product": "Cash Back Rewards Card",
            "upsell_product": "Travel Rewards Card",
            "reason": "Excellent credit and income qualify for premium travel card",
            "benefit": "3x points on travel and dining, lounge access, no foreign fees",
        })

    # Savings → High-yield savings
    if "PROD-SAV-001" in products_held and customer.get("total_deposits", 0) > 50000:
        upsells.append({
            "current_product": "Standard Savings",
            "upsell_product": "High-Yield Savings",
            "reason": "Large savings balance earns more with high-yield account",
            "benefit": "4.50% APY vs national average 0.46%",
        })

    return {
        "customer_id": customer_id,
        "upsell_opportunities": upsells,
    }


async def get_win_back_recommendations(customer_id: str) -> dict[str, Any]:
    """Generate win-back recommendations for at-risk customers."""
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    # At-risk indicators (simulated)
    last_transaction = customer.get("last_transaction", "")
    account_age = customer.get("account_age_days", 0)

    recommendations = []

    # Low activity → Offer engagement incentive
    recommendations.append({
        "type": "engagement",
        "offer": "$50 bonus for setting up automatic savings transfer",
        "channel": "email",
        "timing": "immediate",
    })

    # Competing products → Rate match
    if customer.get("total_deposits", 0) > 10000:
        recommendations.append({
            "type": "rate_match",
            "offer": "0.50% APY bonus for 12 months on savings",
            "channel": "phone",
            "timing": "within_7_days",
        })

    return {
        "customer_id": customer_id,
        "win_back_recommendations": recommendations,
    }
