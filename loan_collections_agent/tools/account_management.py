"""
Account Management Tool — MCP tool stub for collections.

Manages delinquent account lookups, borrower profiles, and account status.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory account store (simulates core banking system)
_accounts: dict[str, dict] = {}

# Seed some sample delinquent accounts
def _seed_accounts():
    accounts = [
        {
            "account_id": "ACCT-10001",
            "borrower_id": "BR-20001",
            "borrower_name": "Sarah Johnson",
            "product_type": "mortgage",
            "original_balance": 250000.00,
            "current_balance": 185000.00,
            "monthly_payment": 1850.00,
            "interest_rate": 5.75,
            "delinquency_days": 45,
            "delinquency_status": "31-60_days",
            "last_payment_date": (datetime.utcnow() - timedelta(days=45)).strftime("%Y-%m-%d"),
            "last_payment_amount": 1850.00,
            "collection_stage": "mid_stage",
            "assigned_collector": "COL-001",
            "account_opened": "2019-03-15",
            "collateral": {"type": "real_estate", "value": 320000.00, "address": "123 Main St, Austin, TX"},
            "contact_attempts": 3,
            "last_contact_date": (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "hardship_flag": False,
            "payment_plan_active": False,
        },
        {
            "account_id": "ACCT-10002",
            "borrower_id": "BR-20002",
            "borrower_name": "Michael Chen",
            "product_type": "auto_loan",
            "original_balance": 32000.00,
            "current_balance": 18500.00,
            "monthly_payment": 520.00,
            "interest_rate": 6.25,
            "delinquency_days": 75,
            "delinquency_status": "61-90_days",
            "last_payment_date": (datetime.utcnow() - timedelta(days=75)).strftime("%Y-%m-%d"),
            "last_payment_amount": 520.00,
            "collection_stage": "mid_stage",
            "assigned_collector": "COL-002",
            "account_opened": "2021-06-10",
            "collateral": {"type": "vehicle", "value": 14000.00, "year": 2021, "make": "Honda", "model": "Civic"},
            "contact_attempts": 6,
            "last_contact_date": (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "hardship_flag": True,
            "hardship_type": "medical",
            "payment_plan_active": False,
        },
        {
            "account_id": "ACCT-10003",
            "borrower_id": "BR-20003",
            "borrower_name": "Emily Rodriguez",
            "product_type": "personal_loan",
            "original_balance": 15000.00,
            "current_balance": 11200.00,
            "monthly_payment": 350.00,
            "interest_rate": 9.50,
            "delinquency_days": 120,
            "delinquency_status": "91-180_days",
            "last_payment_date": (datetime.utcnow() - timedelta(days=120)).strftime("%Y-%m-%d"),
            "last_payment_amount": 350.00,
            "collection_stage": "late_stage",
            "assigned_collector": "COL-003",
            "account_opened": "2022-01-20",
            "collateral": None,
            "contact_attempts": 12,
            "last_contact_date": (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "hardship_flag": True,
            "hardship_type": "employment",
            "payment_plan_active": True,
            "payment_plan": {"monthly_amount": 200.00, "months_completed": 2, "total_months": 12},
        },
    ]
    for acc in accounts:
        _accounts[acc["account_id"]] = acc

_seed_accounts()


async def lookup_account(account_id: str) -> dict:
    """Look up a delinquent account by ID."""
    logger.info("Looking up account: %s", account_id)
    account = _accounts.get(account_id)
    if not account:
        return {"error": f"Account {account_id} not found"}
    return account


async def lookup_account_by_borrower(borrower_id: str) -> dict | list[dict]:
    """Look up accounts by borrower ID."""
    logger.info("Looking up accounts for borrower: %s", borrower_id)
    results = [a for a in _accounts.values() if a["borrower_id"] == borrower_id]
    if not results:
        return {"error": f"No accounts found for borrower {borrower_id}"}
    return results if len(results) > 1 else results[0]


async def get_portfolio_summary(collector_id: str | None = None) -> dict:
    """Get summary of delinquent portfolio."""
    logger.info("Getting portfolio summary (collector=%s)", collector_id)

    accounts = list(_accounts.values())
    if collector_id:
        accounts = [a for a in accounts if a.get("assigned_collector") == collector_id]

    total_balance = sum(a["current_balance"] for a in accounts)
    total_delinquent = len(accounts)
    by_stage = {}
    by_product = {}
    for a in accounts:
        stage = a.get("collection_stage", "unknown")
        by_stage[stage] = by_stage.get(stage, 0) + 1
        product = a.get("product_type", "unknown")
        by_product[product] = by_product.get(product, 0) + 1

    return {
        "total_delinquent_accounts": total_delinquent,
        "total_delinquent_balance": round(total_balance, 2),
        "average_delinquency_days": round(sum(a["delinquency_days"] for a in accounts) / max(total_delinquent, 1), 1),
        "by_stage": by_stage,
        "by_product": by_product,
        "accounts": [{"account_id": a["account_id"], "borrower_name": a["borrower_name"], "balance": a["current_balance"], "days_past_due": a["delinquency_days"], "stage": a["collection_stage"]} for a in accounts],
    }


async def update_account_status(
    account_id: str,
    delinquency_status: str | None = None,
    collection_stage: str | None = None,
    assigned_collector: str | None = None,
    hardship_flag: bool | None = None,
    hardship_type: str | None = None,
    payment_plan_active: bool | None = None,
    notes: str | None = None,
) -> dict:
    """Update a delinquent account's status."""
    account = _accounts.get(account_id)
    if not account:
        return {"error": f"Account {account_id} not found"}

    if delinquency_status:
        account["delinquency_status"] = delinquency_status
    if collection_stage:
        account["collection_stage"] = collection_stage
    if assigned_collector:
        account["assigned_collector"] = assigned_collector
    if hardship_flag is not None:
        account["hardship_flag"] = hardship_flag
    if hardship_type:
        account["hardship_type"] = hardship_type
    if payment_plan_active is not None:
        account["payment_plan_active"] = payment_plan_active
    if notes:
        account["notes"] = notes

    account["last_updated"] = datetime.utcnow().isoformat()
    logger.info("Account %s updated", account_id)
    return account
