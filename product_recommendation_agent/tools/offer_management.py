"""
Offer Management Tool — Create, manage, and track promotional offers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory offer store ─────────────────────────────────────────
OFFER_DB: dict[str, dict] = {
    "OFF-001": {
        "offer_id": "OFF-001",
        "name": "Q3 Savings Bonus",
        "type": "apy_bonus",
        "product_id": "PROD-SAV-001",
        "description": "Earn an extra 0.50% APY on high-yield savings accounts",
        "bonus_apy": 0.50,
        "min_deposit": 1000,
        "duration_months": 12,
        "start_date": "2026-07-01",
        "end_date": "2026-09-30",
        "target_segments": ["all"],
        "status": "active",
        "redemptions": 1250,
        "max_redemptions": 5000,
    },
    "OFF-002": {
        "offer_id": "OFF-002",
        "name": "Summer Travel Promo",
        "type": "bonus_points",
        "product_id": "PROD-CC-002",
        "description": "Earn 60,000 bonus points on Travel Rewards card",
        "bonus_points": 60000,
        "spend_requirement": 4000,
        "spend_period_months": 3,
        "start_date": "2026-06-01",
        "end_date": "2026-08-31",
        "target_segments": ["affluent", "young_professionals"],
        "status": "active",
        "redemptions": 850,
        "max_redemptions": 3000,
    },
    "OFF-003": {
        "offer_id": "OFF-003",
        "name": "Homebuying Season Credit",
        "type": "closing_cost_credit",
        "product_id": "PROD-MTG-001",
        "description": "$500 closing cost credit on new mortgage applications",
        "credit_amount": 500,
        "min_loan": 200000,
        "start_date": "2026-07-01",
        "end_date": "2026-10-31",
        "target_segments": ["homebuyers", "families"],
        "status": "active",
        "redemptions": 320,
        "max_redemptions": 1000,
    },
    "OFF-004": {
        "offer_id": "OFF-004",
        "name": "Auto Loan Rate Special",
        "type": "rate_reduction",
        "product_id": "PROD-AUTO-001",
        "description": "0.25% rate reduction on new and used auto loans",
        "rate_reduction": 0.25,
        "min_loan": 15000,
        "start_date": "2026-07-01",
        "end_date": "2026-09-15",
        "target_segments": ["all", "families"],
        "status": "active",
        "redemptions": 580,
        "max_redemptions": 2000,
    },
    "OFF-005": {
        "offer_id": "OFF-005",
        "name": "Referral Program",
        "type": "referral_bonus",
        "product_id": None,
        "description": "Earn $100 for each friend who opens checking with direct deposit",
        "referral_bonus": 100,
        "friend_bonus": 100,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "target_segments": ["all"],
        "status": "active",
        "redemptions": 2100,
        "max_redemptions": None,
    },
}


async def get_active_offers(
    product_id: str | None = None,
    target_segment: str | None = None,
    offer_type: str | None = None,
) -> dict[str, Any]:
    """Get all active promotional offers."""
    offers = [o for o in OFFER_DB.values() if o["status"] == "active"]

    if product_id:
        offers = [o for o in offers if o.get("product_id") == product_id]
    if target_segment:
        offers = [o for o in offers if target_segment in o.get("target_segments", []) or "all" in o.get("target_segments", [])]
    if offer_type:
        offers = [o for o in offers if o.get("type") == offer_type]

    return {
        "total_active": len(offers),
        "offers": offers,
    }


async def get_offer(offer_id: str) -> dict[str, Any]:
    """Get offer details."""
    offer = OFFER_DB.get(offer_id)
    if not offer:
        return {"error": f"Offer {offer_id} not found"}
    return offer


async def create_offer(
    offer_id: str,
    name: str,
    offer_type: str,
    product_id: str | None,
    description: str,
    target_segments: list[str],
    start_date: str,
    end_date: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a new promotional offer."""
    offer = {
        "offer_id": offer_id,
        "name": name,
        "type": offer_type,
        "product_id": product_id,
        "description": description,
        "target_segments": target_segments,
        "start_date": start_date,
        "end_date": end_date,
        "status": "active",
        "redemptions": 0,
        "max_redemptions": kwargs.get("max_redemptions"),
        **kwargs,
    }
    OFFER_DB[offer_id] = offer

    return {
        "offer_id": offer_id,
        "name": name,
        "message": f"Offer {offer_id} created successfully.",
    }


async def update_offer(offer_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update an offer."""
    offer = OFFER_DB.get(offer_id)
    if not offer:
        return {"error": f"Offer {offer_id} not found"}

    offer.update(updates)
    return {"offer_id": offer_id, "message": f"Offer {offer_id} updated."}


async def deactivate_offer(offer_id: str, reason: str) -> dict[str, Any]:
    """Deactivate an offer."""
    offer = OFFER_DB.get(offer_id)
    if not offer:
        return {"error": f"Offer {offer_id} not found"}

    offer["status"] = "inactive"
    offer["deactivation_reason"] = reason
    return {"offer_id": offer_id, "status": "inactive", "message": f"Offer {offer_id} deactivated."}


async def redeem_offer(offer_id: str, customer_id: str) -> dict[str, Any]:
    """Record offer redemption."""
    offer = OFFER_DB.get(offer_id)
    if not offer:
        return {"error": f"Offer {offer_id} not found"}

    if offer["status"] != "active":
        return {"error": f"Offer {offer_id} is not active"}

    max_redemptions = offer.get("max_redemptions")
    if max_redemptions and offer["redemptions"] >= max_redemptions:
        return {"error": f"Offer {offer_id} has reached maximum redemptions"}

    offer["redemptions"] += 1

    return {
        "offer_id": offer_id,
        "customer_id": customer_id,
        "redemptions_total": offer["redemptions"],
        "message": f"Offer {offer_id} redeemed for customer {customer_id}.",
    }


async def get_offer_analytics(offer_id: str | None = None) -> dict[str, Any]:
    """Get offer performance analytics."""
    offers = list(OFFER_DB.values()) if not offer_id else [OFFER_DB.get(offer_id)]

    if offer_id and offer_id not in OFFER_DB:
        return {"error": f"Offer {offer_id} not found"}

    total_redemptions = sum(o.get("redemptions", 0) for o in offers)
    active_offers = sum(1 for o in offers if o.get("status") == "active")

    return {
        "total_offers": len(offers),
        "active_offers": active_offers,
        "total_redemptions": total_redemptions,
        "avg_redemptions_per_offer": round(total_redemptions / len(offers), 1) if offers else 0,
        "offers": [
            {
                "offer_id": o["offer_id"],
                "name": o["name"],
                "redemptions": o.get("redemptions", 0),
                "max_redemptions": o.get("max_redemptions"),
                "utilization_rate": f"{(o.get('redemptions', 0) / o.get('max_redemptions', 1) * 100):.1f}%" if o.get("max_redemptions") else "N/A",
            }
            for o in offers
        ],
    }


async def get_personalized_offers(customer_id: str) -> dict[str, Any]:
    """Get offers personalized for a specific customer."""
    from tools.customer_360 import CUSTOMER_DB
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    segment = customer.get("segment", "all")
    products_held = customer.get("existing_products", [])

    personalized = []
    for offer in OFFER_DB.values():
        if offer["status"] != "active":
            continue
        # Check segment match
        if segment not in offer.get("target_segments", []) and "all" not in offer.get("target_segments", []):
            continue
        # Check product relevance
        product_id = offer.get("product_id")
        if product_id and product_id not in products_held:
            continue  # Skip offers for products they already have (unless cross-sell)

        personalized.append(offer)

    return {
        "customer_id": customer_id,
        "segment": segment,
        "personalized_offers": personalized,
    }
