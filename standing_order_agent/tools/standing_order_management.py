"""
Standing Order Management Tools — CRUD for recurring payments.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
_standing_orders: dict[str, dict[str, Any]] = {}


async def create_standing_order(
    account_id: str,
    customer_name: str,
    payee_name: str,
    payee_account_number: str,
    payee_routing: str,
    amount: float,
    frequency: str,
    start_date: str,
    end_date: str | None = None,
    payment_method: str = "ach_debit",
    description: str | None = None,
    max_amount: float | None = None,
    source_account_type: str = "checking",
) -> dict[str, Any]:
    """Create a new standing order."""
    so_id = f"SO-{uuid.uuid4().hex[:8].upper()}"

    # Validate frequency
    valid_frequencies = {"once", "daily", "weekly", "biweekly", "monthly", "quarterly", "semi-annual", "annual", "custom"}
    if frequency not in valid_frequencies:
        return {"error": f"Invalid frequency. Must be one of: {valid_frequencies}"}

    # Validate amount
    if amount <= 0:
        return {"error": "Amount must be positive"}
    if amount > 50000:
        return {"error": "Amount exceeds single payment limit of $50,000"}

    # Validate dates
    try:
        start = datetime.fromisoformat(start_date)
    except ValueError:
        return {"error": "Invalid start_date format. Use ISO 8601 (YYYY-MM-DD)"}

    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            if end <= start:
                return {"error": "end_date must be after start_date"}
        except ValueError:
            return {"error": "Invalid end_date format"}

    # Calculate next execution
    next_execution = _calculate_next_execution(start, frequency)

    so = {
        "standing_order_id": so_id,
        "account_id": account_id,
        "customer_name": customer_name,
        "payee_name": payee_name,
        "payee_account_number": payee_account_number,
        "payee_routing": payee_routing,
        "amount": amount,
        "frequency": frequency,
        "start_date": start_date,
        "end_date": end_date,
        "next_execution": next_execution.isoformat(),
        "payment_method": payment_method,
        "description": description or f"Standing order to {payee_name}",
        "max_amount": max_amount or amount,
        "source_account_type": source_account_type,
        "status": "active",
        "failure_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "history": [{"action": "created", "timestamp": datetime.utcnow().isoformat()}],
    }

    _standing_orders[so_id] = so

    return {
        "success": True,
        "standing_order_id": so_id,
        "payee": payee_name,
        "amount": amount,
        "frequency": frequency,
        "next_execution": next_execution.isoformat(),
        "status": "active",
    }


async def get_standing_order(standing_order_id: str) -> dict[str, Any]:
    """Get standing order details."""
    if standing_order_id not in _standing_orders:
        return {"error": f"Standing order {standing_order_id} not found"}
    return _standing_orders[standing_order_id]


async def update_standing_order(
    standing_order_id: str,
    amount: float | None = None,
    frequency: str | None = None,
    payee_name: str | None = None,
    payee_account_number: str | None = None,
    payee_routing: str | None = None,
    end_date: str | None = None,
    description: str | None = None,
    max_amount: float | None = None,
) -> dict[str, Any]:
    """Update an existing standing order."""
    if standing_order_id not in _standing_orders:
        return {"error": f"Standing order {standing_order_id} not found"}

    so = _standing_orders[standing_order_id]
    if so["status"] != "active":
        return {"error": f"Cannot modify standing order in '{so['status']}' status"}

    changes = []
    if amount is not None:
        if amount <= 0 or amount > 50000:
            return {"error": "Invalid amount"}
        old_amount = so["amount"]
        so["amount"] = amount
        so["max_amount"] = max_amount or amount
        changes.append(f"amount: ${old_amount} -> ${amount}")

    if frequency is not None:
        valid = {"once", "daily", "weekly", "biweekly", "monthly", "quarterly", "semi-annual", "annual", "custom"}
        if frequency not in valid:
            return {"error": f"Invalid frequency"}
        so["frequency"] = frequency
        changes.append(f"frequency: {frequency}")

    if payee_name is not None:
        so["payee_name"] = payee_name
        changes.append(f"payee: {payee_name}")
    if payee_account_number is not None:
        so["payee_account_number"] = payee_account_number
    if payee_routing is not None:
        so["payee_routing"] = payee_routing
    if end_date is not None:
        so["end_date"] = end_date
        changes.append(f"end_date: {end_date}")
    if description is not None:
        so["description"] = description

    # Recalculate next execution if frequency changed
    if frequency is not None:
        start = datetime.fromisoformat(so["start_date"])
        so["next_execution"] = _calculate_next_execution(start, frequency).isoformat()

    so["updated_at"] = datetime.utcnow().isoformat()
    so["history"].append({
        "action": "updated",
        "changes": changes,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {"success": True, "standing_order_id": standing_order_id, "changes": changes, "next_execution": so["next_execution"]}


async def cancel_standing_order(standing_order_id: str, reason: str = "customer_request") -> dict[str, Any]:
    """Cancel a standing order."""
    if standing_order_id not in _standing_orders:
        return {"error": f"Standing order {standing_order_id} not found"}

    so = _standing_orders[standing_order_id]
    if so["status"] == "cancelled":
        return {"error": "Standing order is already cancelled"}

    so["status"] = "cancelled"
    so["cancelled_at"] = datetime.utcnow().isoformat()
    so["cancel_reason"] = reason
    so["updated_at"] = datetime.utcnow().isoformat()
    so["history"].append({
        "action": "cancelled",
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {
        "success": True,
        "standing_order_id": standing_order_id,
        "status": "cancelled",
        "reason": reason,
    }


async def pause_standing_order(standing_order_id: str, reason: str = "customer_request") -> dict[str, Any]:
    """Pause a standing order temporarily."""
    if standing_order_id not in _standing_orders:
        return {"error": f"Standing order {standing_order_id} not found"}

    so = _standing_orders[standing_order_id]
    if so["status"] != "active":
        return {"error": f"Cannot pause standing order in '{so['status']}' status"}

    so["status"] = "paused"
    so["paused_at"] = datetime.utcnow().isoformat()
    so["pause_reason"] = reason
    so["updated_at"] = datetime.utcnow().isoformat()
    so["history"].append({"action": "paused", "reason": reason, "timestamp": datetime.utcnow().isoformat()})

    return {"success": True, "standing_order_id": standing_order_id, "status": "paused"}


async def resume_standing_order(standing_order_id: str) -> dict[str, Any]:
    """Resume a paused standing order."""
    if standing_order_id not in _standing_orders:
        return {"error": f"Standing order {standing_order_id} not found"}

    so = _standing_orders[standing_order_id]
    if so["status"] != "paused":
        return {"error": f"Cannot resume standing order in '{so['status']}' status"}

    so["status"] = "active"
    so["next_execution"] = _calculate_next_execution(datetime.utcnow(), so["frequency"]).isoformat()
    so["updated_at"] = datetime.utcnow().isoformat()
    so["history"].append({"action": "resumed", "timestamp": datetime.utcnow().isoformat()})

    return {"success": True, "standing_order_id": standing_order_id, "status": "active", "next_execution": so["next_execution"]}


async def list_standing_orders(
    account_id: str | None = None,
    status: str | None = None,
    payee_name: str | None = None,
) -> dict[str, Any]:
    """List standing orders with optional filters."""
    results = list(_standing_orders.values())

    if account_id:
        results = [so for so in results if so["account_id"] == account_id]
    if status:
        results = [so for so in results if so["status"] == status]
    if payee_name:
        results = [so for so in results if payee_name.lower() in so["payee_name"].lower()]

    return {
        "count": len(results),
        "standing_orders": results,
    }


async def get_upcoming_payments(account_id: str, days: int = 30) -> dict[str, Any]:
    """Get standing order payments due within N days."""
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days)

    upcoming = []
    for so in _standing_orders.values():
        if so["account_id"] != account_id or so["status"] != "active":
            continue
        next_exec = datetime.fromisoformat(so["next_execution"])
        if next_exec <= cutoff:
            upcoming.append({
                "standing_order_id": so["standing_order_id"],
                "payee_name": so["payee_name"],
                "amount": so["amount"],
                "next_execution": so["next_execution"],
                "days_until": (next_exec - now).days,
            })

    upcoming.sort(key=lambda x: x["next_execution"])
    total = sum(p["amount"] for p in upcoming)

    return {
        "account_id": account_id,
        "period_days": days,
        "count": len(upcoming),
        "total_amount": round(total, 2),
        "payments": upcoming,
    }


async def get_standing_order_stats(account_id: str | None = None) -> dict[str, Any]:
    """Get standing order statistics."""
    orders = list(_standing_orders.values())
    if account_id:
        orders = [so for so in orders if so["account_id"] == account_id]

    active = [so for so in orders if so["status"] == "active"]
    paused = [so for so in orders if so["status"] == "paused"]
    cancelled = [so for so in orders if so["status"] == "cancelled"]
    failed = [so for so in orders if so["status"] == "suspended"]

    total_monthly = sum(so["amount"] for so in active if so["frequency"] in {"monthly", "once"})
    total_weekly = sum(so["amount"] for so in active if so["frequency"] in {"weekly", "biweekly"})

    return {
        "total": len(orders),
        "active": len(active),
        "paused": len(paused),
        "cancelled": len(cancelled),
        "suspended": len(failed),
        "estimated_monthly_spend": round(total_monthly + (total_weekly * 4.33), 2),
        "by_frequency": _count_by_frequency(active),
    }


def _calculate_next_execution(from_date: datetime, frequency: str) -> datetime:
    """Calculate next execution date based on frequency."""
    match frequency:
        case "daily":
            return from_date + timedelta(days=1)
        case "weekly":
            return from_date + timedelta(weeks=1)
        case "biweekly":
            return from_date + timedelta(weeks=2)
        case "monthly":
            month = from_date.month + 1
            year = from_date.year
            if month > 12:
                month = 1
                year += 1
            return from_date.replace(year=year, month=month)
        case "quarterly":
            month = from_date.month + 3
            year = from_date.year
            while month > 12:
                month -= 12
                year += 1
            return from_date.replace(year=year, month=month)
        case "semi-annual":
            month = from_date.month + 6
            year = from_date.year
            while month > 12:
                month -= 12
                year += 1
            return from_date.replace(year=year, month=month)
        case "annual":
            return from_date.replace(year=from_date.year + 1)
        case _:
            return from_date + timedelta(days=30)


def _count_by_frequency(orders: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for so in orders:
        freq = so["frequency"]
        counts[freq] = counts.get(freq, 0) + 1
    return counts
