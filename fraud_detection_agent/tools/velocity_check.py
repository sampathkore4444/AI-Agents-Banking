"""
Velocity Check Tool — Transaction velocity monitoring and rate limiting.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


# ── In-memory velocity store ──────────────────────────────────────
VELOCITY_DB: dict[str, list[dict]] = {}
VELOCITY_LIMITS = {
    "hourly_transactions": 5,
    "daily_transactions": 20,
    "weekly_transactions": 50,
    "hourly_amount": 5000.0,
    "daily_amount": 50000.0,
    "weekly_amount": 150000.0,
}


async def check_velocity(
    customer_id: str,
    amount: float,
    transaction_id: str,
) -> dict[str, Any]:
    """Check transaction velocity against limits."""
    now = datetime.utcnow()

    if customer_id not in VELOCITY_DB:
        VELOCITY_DB[customer_id] = []

    # Clean old entries
    VELOCITY_DB[customer_id] = [
        t for t in VELOCITY_DB[customer_id]
        if (now - datetime.fromisoformat(t["timestamp"])).total_seconds() < 7 * 86400
    ]

    # Count transactions in time windows
    hourly = [t for t in VELOCITY_DB[customer_id] if (now - datetime.fromisoformat(t["timestamp"])).total_seconds() < 3600]
    daily = [t for t in VELOCITY_DB[customer_id] if (now - datetime.fromisoformat(t["timestamp"])).total_seconds() < 86400]
    weekly = VELOCITY_DB[customer_id]

    hourly_count = len(hourly)
    daily_count = len(daily)
    weekly_count = len(weekly)

    hourly_amount = sum(t["amount"] for t in hourly)
    daily_amount = sum(t["amount"] for t in daily)
    weekly_amount = sum(t["amount"] for t in weekly)

    # Check limits
    violations: list[dict] = []
    risk_score = 0

    if hourly_count >= VELOCITY_LIMITS["hourly_transactions"]:
        violations.append({"type": "hourly_count", "current": hourly_count, "limit": VELOCITY_LIMITS["hourly_transactions"], "severity": "high"})
        risk_score += 30

    if daily_count >= VELOCITY_LIMITS["daily_transactions"]:
        violations.append({"type": "daily_count", "current": daily_count, "limit": VELOCITY_LIMITS["daily_transactions"], "severity": "critical"})
        risk_score += 40

    if weekly_count >= VELOCITY_LIMITS["weekly_transactions"]:
        violations.append({"type": "weekly_count", "current": weekly_count, "limit": VELOCITY_LIMITS["weekly_transactions"], "severity": "critical"})
        risk_score += 50

    if hourly_amount + amount > VELOCITY_LIMITS["hourly_amount"]:
        violations.append({"type": "hourly_amount", "current": hourly_amount + amount, "limit": VELOCITY_LIMITS["hourly_amount"], "severity": "high"})
        risk_score += 25

    if daily_amount + amount > VELOCITY_LIMITS["daily_amount"]:
        violations.append({"type": "daily_amount", "current": daily_amount + amount, "limit": VELOCITY_LIMITS["daily_amount"], "severity": "critical"})
        risk_score += 35

    if weekly_amount + amount > VELOCITY_LIMITS["weekly_amount"]:
        violations.append({"type": "weekly_amount", "current": weekly_amount + amount, "limit": VELOCITY_LIMITS["weekly_amount"], "severity": "critical"})
        risk_score += 45

    risk_score = min(risk_score, 100)

    # Determine action
    if any(v["severity"] == "critical" for v in violations):
        action = "block"
    elif any(v["severity"] == "high" for v in violations):
        action = "review"
    elif risk_score > 20:
        action = "alert"
    else:
        action = "allow"

    # Record this transaction
    VELOCITY_DB[customer_id].append({
        "transaction_id": transaction_id,
        "amount": amount,
        "timestamp": now.isoformat(),
    })

    return {
        "customer_id": customer_id,
        "transaction_id": transaction_id,
        "velocity_check": {
            "hourly_count": hourly_count + 1,
            "daily_count": daily_count + 1,
            "weekly_count": weekly_count + 1,
            "hourly_amount": round(hourly_amount + amount, 2),
            "daily_amount": round(daily_amount + amount, 2),
            "weekly_amount": round(weekly_amount + amount, 2),
        },
        "limits": VELOCITY_LIMITS,
        "violations": violations,
        "risk_score": risk_score,
        "action": action,
        "message": f"Velocity check {'PASSED' if action == 'allow' else 'FAILED'} — {len(violations)} violation(s) detected",
    }


async def get_velocity_summary(customer_id: str) -> dict[str, Any]:
    """Get velocity summary for a customer."""
    now = datetime.utcnow()
    txns = VELOCITY_DB.get(customer_id, [])

    hourly = [t for t in txns if (now - datetime.fromisoformat(t["timestamp"])).total_seconds() < 3600]
    daily = [t for t in txns if (now - datetime.fromisoformat(t["timestamp"])).total_seconds() < 86400]
    weekly = txns

    return {
        "customer_id": customer_id,
        "hourly": {"count": len(hourly), "amount": round(sum(t["amount"] for t in hourly), 2), "limit_count": VELOCITY_LIMITS["hourly_transactions"], "limit_amount": VELOCITY_LIMITS["hourly_amount"]},
        "daily": {"count": len(daily), "amount": round(sum(t["amount"] for t in daily), 2), "limit_count": VELOCITY_LIMITS["daily_transactions"], "limit_amount": VELOCITY_LIMITS["daily_amount"]},
        "weekly": {"count": len(weekly), "amount": round(sum(t["amount"] for t in weekly), 2), "limit_count": VELOCITY_LIMITS["weekly_transactions"], "limit_amount": VELOCITY_LIMITS["weekly_amount"]},
    }


async def update_velocity_limits(
    hourly_transactions: int | None = None,
    daily_transactions: int | None = None,
    weekly_transactions: int | None = None,
    hourly_amount: float | None = None,
    daily_amount: float | None = None,
    weekly_amount: float | None = None,
) -> dict[str, Any]:
    """Update velocity limits."""
    if hourly_transactions is not None:
        VELOCITY_LIMITS["hourly_transactions"] = hourly_transactions
    if daily_transactions is not None:
        VELOCITY_LIMITS["daily_transactions"] = daily_transactions
    if weekly_transactions is not None:
        VELOCITY_LIMITS["weekly_transactions"] = weekly_transactions
    if hourly_amount is not None:
        VELOCITY_LIMITS["hourly_amount"] = hourly_amount
    if daily_amount is not None:
        VELOCITY_LIMITS["daily_amount"] = daily_amount
    if weekly_amount is not None:
        VELOCITY_LIMITS["weekly_amount"] = weekly_amount

    return {"limits": VELOCITY_LIMITS, "message": "Velocity limits updated successfully"}
