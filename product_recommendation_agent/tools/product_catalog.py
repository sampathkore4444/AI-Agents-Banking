"""
Product Catalog Tool — Manage and query banking product catalog.
"""

from __future__ import annotations

from typing import Any


# ── In-memory product catalog ─────────────────────────────────────
PRODUCT_DB: dict[str, dict] = {
    "PROD-SAV-001": {
        "product_id": "PROD-SAV-001",
        "name": "High-Yield Savings Account",
        "category": "deposit",
        "subcategory": "savings",
        "description": "Earn 4.50% APY on balances up to $250,000. No minimum balance. No monthly fee.",
        "apy": 4.50,
        "min_balance": 0,
        "monthly_fee": 0,
        "features": ["FDIC insured", "Online banking", "Mobile app", "Auto-transfers"],
        "target_segments": ["all", "students", "young_professionals"],
        "status": "active",
    },
    "PROD-CHK-001": {
        "product_id": "PROD-CHK-001",
        "name": "Premium Checking Account",
        "category": "deposit",
        "subcategory": "checking",
        "description": "$0 monthly fee with direct deposit. Free debit card. 55,000+ ATM network.",
        "apy": 0.10,
        "min_balance": 0,
        "monthly_fee": 0,
        "features": ["Free debit card", "Mobile deposit", "Bill pay", "Overdraft protection"],
        "target_segments": ["all"],
        "status": "active",
    },
    "PROD-CC-001": {
        "product_id": "PROD-CC-001",
        "name": "Cash Back Rewards Credit Card",
        "category": "credit",
        "subcategory": "credit_card",
        "description": "2% cash back on all purchases. 3% on dining/entertainment. No annual fee. 0% intro APR 15 months.",
        "rewards_rate": 0.02,
        "annual_fee": 0,
        "intro_apr_months": 15,
        "regular_apr": 16.99,
        "features": ["2% cash back", "No annual fee", "Free FICO score", "Contactless"],
        "target_segments": ["all", "young_professionals"],
        "status": "active",
    },
    "PROD-CC-002": {
        "product_id": "PROD-CC-002",
        "name": "Travel Rewards Credit Card",
        "category": "credit",
        "subcategory": "credit_card",
        "description": "3x points on travel and dining. $95 annual fee (waived first year). 60,000 bonus points.",
        "rewards_rate": 0.03,
        "annual_fee": 95,
        "intro_apr_months": 0,
        "regular_apr": 19.99,
        "features": ["3x travel/dining", "No foreign fees", "Lounge access", "Global Entry credit"],
        "target_segments": ["affluent", "young_professionals"],
        "status": "active",
    },
    "PROD-MTG-001": {
        "product_id": "PROD-MTG-001",
        "name": "30-Year Fixed Mortgage",
        "category": "lending",
        "subcategory": "mortgage",
        "description": "Competitive fixed rate. 3% down payment. Pre-approval in 24 hours. No origination fee.",
        "min_credit_score": 620,
        "min_down_payment_pct": 3,
        "term_months": 360,
        "features": ["Fast pre-approval", "Digital application", "Rate lock", "No origination fee"],
        "target_segments": ["homebuyers", "families"],
        "status": "active",
    },
    "PROD-AUTO-001": {
        "product_id": "PROD-AUTO-001",
        "name": "Auto Loan",
        "category": "lending",
        "subcategory": "auto_loan",
        "description": "New and used vehicle financing. Rates from 4.99% APR. Terms 36-72 months.",
        "min_credit_score": 660,
        "min_loan": 5000,
        "max_loan": 100000,
        "features": ["Pre-approval", "Dealer network", "Refinancing", "GAP insurance"],
        "target_segments": ["all", "families"],
        "status": "active",
    },
    "PROD-PER-001": {
        "product_id": "PROD-PER-001",
        "name": "Personal Loan",
        "category": "lending",
        "subcategory": "personal_loan",
        "description": "Unsecured loan $2,000-$50,000. Fixed rates from 6.99% APR. Same-day funding.",
        "min_credit_score": 640,
        "min_loan": 2000,
        "max_loan": 50000,
        "features": ["No collateral", "Same-day funding", "No prepayment penalty"],
        "target_segments": ["all"],
        "status": "active",
    },
    "PROD-CD-001": {
        "product_id": "PROD-CD-001",
        "name": "Certificate of Deposit",
        "category": "deposit",
        "subcategory": "cd",
        "description": "Fixed rates from 4.75% APY for 12 months. Minimum deposit $1,000. FDIC insured.",
        "apy": 4.75,
        "min_deposit": 1000,
        "term_months": 12,
        "features": ["Guaranteed returns", "FDIC insured", "Auto-renewal"],
        "target_segments": ["conservative_savers", "retirees"],
        "status": "active",
    },
    "PROD-IRA-001": {
        "product_id": "PROD-IRA-001",
        "name": "Traditional IRA",
        "category": "investment",
        "subcategory": "ira",
        "description": "Tax-deductible contributions up to $7,000/year. Tax-deferred growth.",
        "annual_limit": 7000,
        "features": ["Tax deduction", "Tax-deferred growth", "Wide investment options"],
        "target_segments": ["young_professionals", "families"],
        "status": "active",
    },
    "PROD-ROTH-001": {
        "product_id": "PROD-ROTH-001",
        "name": "Roth IRA",
        "category": "investment",
        "subcategory": "roth_ira",
        "description": "After-tax contributions. Tax-free growth and withdrawals in retirement.",
        "annual_limit": 7000,
        "features": ["Tax-free growth", "No RMDs", "Flexible withdrawals"],
        "target_segments": ["young_professionals", "students"],
        "status": "active",
    },
    "PROD-HELOC-001": {
        "product_id": "PROD-HELOC-001",
        "name": "Home Equity Line of Credit",
        "category": "lending",
        "subcategory": "heloc",
        "description": "Borrow against home equity. Credit line $25,000-$500,000. Variable rate.",
        "min_credit_score": 680,
        "min_line": 25000,
        "max_line": 500000,
        "features": ["Interest-only payments", "No annual fee", "Flexible draws"],
        "target_segments": ["homeowners", "families"],
        "status": "active",
    },
    "PROD-STU-001": {
        "product_id": "PROD-STU-001",
        "name": "Private Student Loan",
        "category": "lending",
        "subcategory": "student_loan",
        "description": "Refinance or supplement federal student loans. Fixed rates from 5.49% APR.",
        "min_credit_score": 650,
        "min_loan": 5000,
        "max_loan": 300000,
        "features": ["Deferment options", "No origination fee", "Flexible terms"],
        "target_segments": ["students", "young_professionals"],
        "status": "active",
    },
}


async def search_products(
    category: str | None = None,
    subcategory: str | None = None,
    target_segment: str | None = None,
    min_credit_score: int | None = None,
    max_annual_fee: float | None = None,
    features: list[str] | None = None,
) -> dict[str, Any]:
    """Search products by criteria."""
    results = list(PRODUCT_DB.values())

    if category:
        results = [p for p in results if p["category"] == category]
    if subcategory:
        results = [p for p in results if p.get("subcategory") == subcategory]
    if target_segment:
        results = [p for p in results if target_segment in p.get("target_segments", [])]
    if min_credit_score is not None:
        results = [p for p in results if p.get("min_credit_score", 0) <= min_credit_score]
    if max_annual_fee is not None:
        results = [p for p in results if p.get("annual_fee", 0) <= max_annual_fee]
    if features:
        results = [p for p in results if all(f.lower() in [feat.lower() for feat in p.get("features", [])] for f in features)]

    return {
        "total_products": len(results),
        "filters_applied": {"category": category, "subcategory": subcategory, "target_segment": target_segment, "min_credit_score": min_credit_score},
        "products": results,
    }


async def get_product(product_id: str) -> dict[str, Any]:
    """Get product details."""
    product = PRODUCT_DB.get(product_id)
    if not product:
        return {"error": f"Product {product_id} not found"}
    return product


async def compare_products(product_ids: list[str]) -> dict[str, Any]:
    """Compare multiple products side by side."""
    products = [PRODUCT_DB.get(pid) for pid in product_ids]
    products = [p for p in products if p is not None]

    if not products:
        return {"error": "No valid products found"}

    # Find common attributes
    all_features = set()
    for p in products:
        all_features.update(p.get("features", []))

    return {
        "products": products,
        "comparison_features": sorted(all_features),
        "price_comparison": [
            {"product_id": p["product_id"], "name": p["name"], "monthly_fee": p.get("monthly_fee", 0), "annual_fee": p.get("annual_fee", 0)}
            for p in products
        ],
    }


async def get_product_recommendations(
    product_id: str,
    limit: int = 5,
) -> dict[str, Any]:
    """Get related product recommendations."""
    product = PRODUCT_DB.get(product_id)
    if not product:
        return {"error": f"Product {product_id} not found"}

    category = product.get("category", "")
    segment = product.get("target_segments", ["all"])[0]

    recommendations = []
    for pid, p in PRODUCT_DB.items():
        if pid == product_id:
            continue
        score = 0
        # Same category bonus
        if p.get("category") == category:
            score += 30
        # Same segment bonus
        if segment in p.get("target_segments", []):
            score += 20
        # Cross-sell potential (different category)
        if p.get("category") != category:
            score += 10
        recommendations.append({"product_id": pid, "name": p["name"], "category": p["category"], "relevance_score": score})

    recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {
        "source_product": product["name"],
        "recommendations": recommendations[:limit],
    }


async def add_product(
    product_id: str,
    name: str,
    category: str,
    subcategory: str,
    description: str,
    features: list[str],
    target_segments: list[str],
    **kwargs: Any,
) -> dict[str, Any]:
    """Add a new product to the catalog."""
    product = {
        "product_id": product_id,
        "name": name,
        "category": category,
        "subcategory": subcategory,
        "description": description,
        "features": features,
        "target_segments": target_segments,
        "status": "active",
        **kwargs,
    }
    PRODUCT_DB[product_id] = product

    return {
        "product_id": product_id,
        "name": name,
        "message": f"Product {product_id} added to catalog.",
    }


async def update_product(product_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update a product in the catalog."""
    product = PRODUCT_DB.get(product_id)
    if not product:
        return {"error": f"Product {product_id} not found"}

    product.update(updates)
    return {"product_id": product_id, "message": f"Product {product_id} updated."}


async def deactivate_product(product_id: str, reason: str) -> dict[str, Any]:
    """Deactivate a product."""
    product = PRODUCT_DB.get(product_id)
    if not product:
        return {"error": f"Product {product_id} not found"}

    product["status"] = "inactive"
    product["deactivation_reason"] = reason
    return {"product_id": product_id, "status": "inactive", "message": f"Product {product_id} deactivated."}
