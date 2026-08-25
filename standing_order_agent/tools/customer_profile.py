"""
Customer Profile Tools — Customer billing information and payment history.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory customer database ───────────────────────────────────
_customers: dict[str, dict[str, Any]] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "+1-555-0101",
        "accounts": [
            {"account_id": "ACC-CHK-001", "type": "checking", "balance": 15000.00, "status": "active"},
            {"account_id": "ACC-SAV-001", "type": "savings", "balance": 45000.00, "status": "active"},
        ],
        "standing_orders": 5,
        "monthly_recurring_total": 2850.00,
        "biller_categories": ["mortgage", "utility", "insurance", "subscription"],
        "preferred_payment_method": "ach_debit",
        "customer_since": "2018-03-15",
        "risk_profile": "low",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Sarah Johnson",
        "email": "sarah.j@email.com",
        "phone": "+1-555-0102",
        "accounts": [
            {"account_id": "ACC-CHK-002", "type": "checking", "balance": 8500.00, "status": "active"},
            {"account_id": "ACC-CC-001", "type": "credit_card", "balance": -3200.00, "status": "active"},
        ],
        "standing_orders": 8,
        "monthly_recurring_total": 1850.00,
        "biller_categories": ["utility", "telecom", "subscription", "loan"],
        "preferred_payment_method": "ach_debit",
        "customer_since": "2020-07-22",
        "risk_profile": "low",
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Michael Chen",
        "email": "m.chen@business.com",
        "phone": "+1-555-0103",
        "accounts": [
            {"account_id": "ACC-BUS-001", "type": "business_checking", "balance": 125000.00, "status": "active"},
            {"account_id": "ACC-SAV-002", "type": "business_savings", "balance": 350000.00, "status": "active"},
        ],
        "standing_orders": 12,
        "monthly_recurring_total": 18500.00,
        "biller_categories": ["government", "utility", "insurance", "loan"],
        "preferred_payment_method": "ach_debit",
        "customer_since": "2015-01-10",
        "risk_profile": "medium",
    },
}


async def get_customer_profile(customer_id: str) -> dict[str, Any]:
    """Get full customer profile."""
    if customer_id not in _customers:
        return {"error": f"Customer {customer_id} not found"}
    return _customers[customer_id]


async def get_customer_accounts(customer_id: str) -> dict[str, Any]:
    """Get accounts for a customer."""
    if customer_id not in _customers:
        return {"error": f"Customer {customer_id} not found"}

    customer = _customers[customer_id]
    return {
        "customer_id": customer_id,
        "name": customer["name"],
        "accounts": customer["accounts"],
    }


async def search_customers(
    query: str | None = None,
    min_balance: float | None = None,
    has_standing_orders: bool | None = None,
) -> dict[str, Any]:
    """Search customers."""
    results = list(_customers.values())

    if query:
        results = [c for c in results if query.lower() in c["name"].lower() or query.lower() in c.get("email", "").lower()]
    if min_balance is not None:
        results = [
            c for c in results
            if any(a["balance"] >= min_balance for a in c["accounts"])
        ]
    if has_standing_orders is not None:
        if has_standing_orders:
            results = [c for c in results if c["standing_orders"] > 0]
        else:
            results = [c for c in results if c["standing_orders"] == 0]

    return {"count": len(results), "customers": results}


async def get_billing_summary(customer_id: str) -> dict[str, Any]:
    """Get billing summary for a customer."""
    if customer_id not in _customers:
        return {"error": f"Customer {customer_id} not found"}

    customer = _customers[customer_id]
    return {
        "customer_id": customer_id,
        "name": customer["name"],
        "standing_order_count": customer["standing_orders"],
        "monthly_recurring_total": customer["monthly_recurring_total"],
        "annual_recurring_estimate": customer["monthly_recurring_total"] * 12,
        "biller_categories": customer["biller_categories"],
        "accounts": [
            {"account_id": a["account_id"], "type": a["type"], "balance": a["balance"]}
            for a in customer["accounts"]
        ],
    }


async def get_account_balance(account_id: str) -> dict[str, Any]:
    """Get account balance for payment validation."""
    for customer in _customers.values():
        for account in customer["accounts"]:
            if account["account_id"] == account_id:
                return {
                    "account_id": account_id,
                    "balance": account["balance"],
                    "status": account["status"],
                    "type": account["type"],
                }
    return {"error": f"Account {account_id} not found"}
