"""
Biller Directory Tools — Search, verify, and manage billers.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from rapidfuzz import fuzz


# ── In-memory biller database ────────────────────────────────────
_billers: dict[str, dict[str, Any]] = {
    "BLR-CONED": {
        "biller_id": "BLR-CONED",
        "name": "Con Edison",
        "category": "utility",
        "sub_category": "electric",
        "payment_methods": ["ach_debit"],
        "typical_amount_min": 50,
        "typical_amount_max": 400,
        "billing_cycle": "monthly",
        "grace_period_days": 15,
        "auto_pay_discount": 2.50,
        "accepts_variable_amount": True,
        "supported_accounts": ["checking", "savings"],
        "verification_required": False,
        "status": "active",
    },
    "BLR-WF-MORT": {
        "biller_id": "BLR-WF-MORT",
        "name": "Wells Fargo Mortgage",
        "category": "mortgage",
        "sub_category": "home_loan",
        "payment_methods": ["ach_debit"],
        "typical_amount_min": 500,
        "typical_amount_max": 5000,
        "billing_cycle": "monthly",
        "grace_period_days": 15,
        "auto_pay_discount": 0.25,
        "auto_pay_discount_type": "interest_rate",
        "accepts_variable_amount": True,
        "supported_accounts": ["checking", "savings"],
        "verification_required": True,
        "status": "active",
    },
    "BLR-NETFLIX": {
        "biller_id": "BLR-NETFLIX",
        "name": "Netflix",
        "category": "subscription",
        "sub_category": "streaming",
        "payment_methods": ["credit_card", "debit_card"],
        "typical_amount_min": 6.99,
        "typical_amount_max": 22.99,
        "billing_cycle": "monthly",
        "grace_period_days": 0,
        "auto_pay_discount": 0,
        "accepts_variable_amount": True,
        "supported_accounts": ["credit_card", "debit_card"],
        "verification_required": False,
        "status": "active",
    },
    "BLR-GEICO": {
        "biller_id": "BLR-GEICO",
        "name": "GEICO Auto Insurance",
        "category": "insurance",
        "sub_category": "auto",
        "payment_methods": ["ach_debit", "credit_card", "debit_card"],
        "typical_amount_min": 80,
        "typical_amount_max": 300,
        "billing_cycle": "monthly",
        "grace_period_days": 10,
        "auto_pay_discount": 5.00,
        "accepts_variable_amount": True,
        "supported_accounts": ["checking", "savings", "credit_card", "debit_card"],
        "verification_required": True,
        "status": "active",
    },
    "BLR-VERIZON": {
        "biller_id": "BLR-VERIZON",
        "name": "Verizon Wireless",
        "category": "telecom",
        "sub_category": "mobile",
        "payment_methods": ["ach_debit", "credit_card", "debit_card"],
        "typical_amount_min": 35,
        "typical_amount_max": 250,
        "billing_cycle": "monthly",
        "grace_period_days": 10,
        "auto_pay_discount": 10.00,
        "accepts_variable_amount": True,
        "supported_accounts": ["checking", "savings", "credit_card", "debit_card"],
        "verification_required": False,
        "status": "active",
    },
    "BLR-IRS-EFTPS": {
        "biller_id": "BLR-IRS-EFTPS",
        "name": "IRS Federal Tax (EFTPS)",
        "category": "government",
        "sub_category": "federal_tax",
        "payment_methods": ["ach_debit"],
        "typical_amount_min": 100,
        "typical_amount_max": 100000,
        "billing_cycle": "quarterly",
        "grace_period_days": 0,
        "auto_pay_discount": 0,
        "accepts_variable_amount": True,
        "supported_accounts": ["checking", "savings"],
        "verification_required": True,
        "status": "active",
    },
    "BLR-NELNET": {
        "biller_id": "BLR-NELNET",
        "name": "Nelnet Student Loans",
        "category": "loan",
        "sub_category": "student_loan",
        "payment_methods": ["ach_debit"],
        "typical_amount_min": 50,
        "typical_amount_max": 2000,
        "billing_cycle": "monthly",
        "grace_period_days": 15,
        "auto_pay_discount": 0.25,
        "auto_pay_discount_type": "interest_rate",
        "accepts_variable_amount": True,
        "supported_accounts": ["checking", "savings"],
        "verification_required": True,
        "status": "active",
    },
    "BLR-SPOTIFY": {
        "biller_id": "BLR-SPOTIFY",
        "name": "Spotify",
        "category": "subscription",
        "sub_category": "streaming",
        "payment_methods": ["credit_card", "debit_card"],
        "typical_amount_min": 10.99,
        "typical_amount_max": 16.99,
        "billing_cycle": "monthly",
        "grace_period_days": 0,
        "auto_pay_discount": 0,
        "accepts_variable_amount": True,
        "supported_accounts": ["credit_card", "debit_card"],
        "verification_required": False,
        "status": "active",
    },
}


async def search_billers(
    query: str,
    category: str | None = None,
    payment_method: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search billers by name or category."""
    results = []
    for biller in _billers.values():
        if biller["status"] != "active":
            continue
        if category and biller["category"] != category:
            continue
        if payment_method and payment_method not in biller["payment_methods"]:
            continue

        # Fuzzy match on name
        score = fuzz.partial_ratio(query.lower(), biller["name"].lower())
        if score >= 60:
            results.append({**biller, "match_score": score})

    results.sort(key=lambda b: b["match_score"], reverse=True)
    return {"count": len(results[:limit]), "billers": results[:limit]}


async def get_biller(biller_id: str) -> dict[str, Any]:
    """Get biller details by ID."""
    if biller_id not in _billers:
        return {"error": f"Biller {biller_id} not found"}
    return _billers[biller_id]


async def verify_biller(
    biller_id: str,
    account_number: str | None = None,
    customer_name: str | None = None,
) -> dict[str, Any]:
    """Verify a biller for a specific customer account."""
    if biller_id not in _billers:
        return {"error": f"Biller {biller_id} not found"}

    biller = _billers[biller_id]
    verification_steps = []

    if biller.get("verification_required"):
        verification_steps.append("Account number verification with biller")
        if account_number:
            verification_steps.append(f"Account {account_number[-4:].rjust(len(account_number), '*')} verified")
        if customer_name:
            verification_steps.append(f"Name match: {customer_name} on file")

    return {
        "biller_id": biller_id,
        "name": biller["name"],
        "verification_required": biller.get("verification_required", False),
        "verification_steps": verification_steps,
        "verified": True if not biller.get("verification_required") else bool(account_number),
        "payment_methods": biller["payment_methods"],
        "typical_amount_range": f"${biller['typical_amount_min']}-${biller['typical_amount_max']}",
    }


async def add_biller(
    name: str,
    category: str,
    sub_category: str | None = None,
    payment_methods: list[str] | None = None,
    typical_amount_min: float = 0,
    typical_amount_max: float = 10000,
    billing_cycle: str = "monthly",
    grace_period_days: int = 15,
) -> dict[str, Any]:
    """Add a new biller to the directory."""
    biller_id = f"BLR-{uuid.uuid4().hex[:6].upper()}"

    biller = {
        "biller_id": biller_id,
        "name": name,
        "category": category,
        "sub_category": sub_category or category,
        "payment_methods": payment_methods or ["ach_debit"],
        "typical_amount_min": typical_amount_min,
        "typical_amount_max": typical_amount_max,
        "billing_cycle": billing_cycle,
        "grace_period_days": grace_period_days,
        "auto_pay_discount": 0,
        "accepts_variable_amount": True,
        "supported_accounts": ["checking", "savings"],
        "verification_required": True,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
    }

    _billers[biller_id] = biller
    return {"success": True, "biller_id": biller_id, "name": name}


async def list_billers_by_category(category: str) -> dict[str, Any]:
    """List all billers in a category."""
    results = [b for b in _billers.values() if b["category"] == category and b["status"] == "active"]
    return {"category": category, "count": len(results), "billers": results}


async def get_biller_categories() -> dict[str, Any]:
    """Get all biller categories with counts."""
    categories: dict[str, int] = {}
    for b in _billers.values():
        if b["status"] == "active":
            cat = b["category"]
            categories[cat] = categories.get(cat, 0) + 1
    return {"categories": categories, "total_billers": len([b for b in _billers.values() if b["status"] == "active"])}
