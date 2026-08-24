"""
CRM Tool — Salesforce-style CRM integration for lead and customer management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory CRM store ───────────────────────────────────────────
CRM_ACCOUNTS: dict[str, dict] = {}
CRM_ACTIVITIES: list[dict] = []


async def create_account(
    account_id: str,
    name: str,
    account_type: str,
    industry: str | None = None,
    revenue: float | None = None,
) -> dict[str, Any]:
    """Create a CRM account."""
    account = {
        "account_id": account_id,
        "name": name,
        "type": account_type,
        "industry": industry,
        "revenue": revenue,
        "created_at": datetime.utcnow().isoformat(),
        "contacts": [],
        "opportunities": [],
    }
    CRM_ACCOUNTS[account_id] = account
    return {"account_id": account_id, "message": f"Account {account_id} created."}


async def get_account(account_id: str) -> dict[str, Any]:
    """Get account details."""
    account = CRM_ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account {account_id} not found"}
    return account


async def update_account(account_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update an account."""
    account = CRM_ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account {account_id} not found"}
    account.update(updates)
    return {"account_id": account_id, "message": "Account updated."}


async def log_activity(
    who_id: str,
    what_id: str | None,
    activity_type: str,
    subject: str,
    description: str,
    due_date: str | None = None,
) -> dict[str, Any]:
    """Log a CRM activity."""
    activity = {
        "activity_id": f"ACT-{int(datetime.utcnow().timestamp())}",
        "who_id": who_id,
        "what_id": what_id,
        "type": activity_type,
        "subject": subject,
        "description": description,
        "due_date": due_date,
        "status": "completed",
        "created_at": datetime.utcnow().isoformat(),
    }
    CRM_ACTIVITIES.append(activity)
    return {"activity_id": activity["activity_id"], "message": "Activity logged."}


async def get_activities(
    who_id: str | None = None,
    what_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Get activities filtered by criteria."""
    results = CRM_ACTIVITIES[:]
    if who_id:
        results = [a for a in results if a["who_id"] == who_id]
    if what_id:
        results = [a for a in results if a.get("what_id") == what_id]
    results.sort(key=lambda x: x["created_at"], reverse=True)
    return {"total": len(results), "activities": results[:limit]}


async def create_opportunity(
    opportunity_id: str,
    account_id: str,
    name: str,
    amount: float,
    stage: str = "prospecting",
    close_date: str | None = None,
) -> dict[str, Any]:
    """Create a sales opportunity."""
    opportunity = {
        "opportunity_id": opportunity_id,
        "account_id": account_id,
        "name": name,
        "amount": amount,
        "stage": stage,
        "close_date": close_date,
        "created_at": datetime.utcnow().isoformat(),
    }
    account = CRM_ACCOUNTS.get(account_id)
    if account:
        account.setdefault("opportunities", []).append(opportunity)
    return {"opportunity_id": opportunity_id, "message": "Opportunity created."}


async def get_pipeline() -> dict[str, Any]:
    """Get sales pipeline summary."""
    all_opps = []
    for account in CRM_ACCOUNTS.values():
        all_opps.extend(account.get("opportunities", []))

    stages = {}
    for opp in all_opps:
        stage = opp.get("stage", "unknown")
        if stage not in stages:
            stages[stage] = {"count": 0, "total_amount": 0}
        stages[stage]["count"] += 1
        stages[stage]["total_amount"] += opp.get("amount", 0)

    return {
        "total_opportunities": len(all_opps),
        "total_value": sum(o.get("amount", 0) for o in all_opps),
        "by_stage": stages,
    }


async def search_accounts(
    account_type: str | None = None,
    industry: str | None = None,
) -> dict[str, Any]:
    """Search accounts."""
    results = list(CRM_ACCOUNTS.values())
    if account_type:
        results = [a for a in results if a.get("type") == account_type]
    if industry:
        results = [a for a in results if a.get("industry") == industry]
    return {"total": len(results), "accounts": results}
