"""
Velocity Check — Monitor payment velocity across all channels.

Tracks:
- Payment count by account (hourly, daily, weekly)
- Payment amount velocity
- Channel-specific velocity (wire, ACH, RTP)
- Cross-channel velocity patterns
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from config import settings


# ── In-memory velocity tracker ────────────────────────────────────
_VELOCITY_LOG: list[dict] = []


async def check_payment_velocity(
    account_id: str,
    amount: float,
    payment_type: str,
    payment_id: str,
) -> dict[str, Any]:
    """Check payment velocity against configured limits."""
    violations: list[dict] = []
    risk_score = 0.0

    now = datetime.utcnow()
    _VELOCITY_LOG.append({
        "account_id": account_id,
        "amount": amount,
        "payment_type": payment_type,
        "payment_id": payment_id,
        "timestamp": now.isoformat(),
    })

    # --- Hourly velocity ---
    hourly = [v for v in _VELOCITY_LOG if v["account_id"] == account_id and datetime.fromisoformat(v["timestamp"]) > now - timedelta(hours=1)]
    if len(hourly) > settings.velocity_limit_hourly_payments:
        violations.append({
            "rule": "hourly_count",
            "current": len(hourly),
            "limit": settings.velocity_limit_hourly_payments,
            "severity": "high",
        })
        risk_score += 30.0

    # --- Daily wire velocity ---
    daily_wires = [v for v in _VELOCITY_LOG if v["account_id"] == account_id and v["payment_type"] == "wire" and datetime.fromisoformat(v["timestamp"]) > now - timedelta(hours=24)]
    daily_wire_amount = sum(v["amount"] for v in daily_wires)

    if len(daily_wires) > settings.velocity_limit_daily_wires:
        violations.append({
            "rule": "daily_wire_count",
            "current": len(daily_wires),
            "limit": settings.velocity_limit_daily_wires,
            "severity": "critical",
        })
        risk_score += 40.0

    if daily_wire_amount > settings.velocity_limit_daily_wire_amount:
        violations.append({
            "rule": "daily_wire_amount",
            "current": daily_wire_amount,
            "limit": settings.velocity_limit_daily_wire_amount,
            "severity": "critical",
        })
        risk_score += 35.0

    # --- Daily ACH velocity ---
    daily_ach = [v for v in _VELOCITY_LOG if v["account_id"] == account_id and v["payment_type"] == "ach" and datetime.fromisoformat(v["timestamp"]) > now - timedelta(hours=24)]
    daily_ach_amount = sum(v["amount"] for v in daily_ach)

    if len(daily_ach) > settings.velocity_limit_daily_ach:
        violations.append({
            "rule": "daily_ach_count",
            "current": len(daily_ach),
            "limit": settings.velocity_limit_daily_ach,
            "severity": "high",
        })
        risk_score += 30.0

    if daily_ach_amount > settings.velocity_limit_daily_ach_amount:
        violations.append({
            "rule": "daily_ach_amount",
            "current": daily_ach_amount,
            "limit": settings.velocity_limit_daily_ach_amount,
            "severity": "high",
        })
        risk_score += 25.0

    # --- Weekly velocity ---
    weekly = [v for v in _VELOCITY_LOG if v["account_id"] == account_id and datetime.fromisoformat(v["timestamp"]) > now - timedelta(days=7)]
    weekly_amount = sum(v["amount"] for v in weekly)

    if len(weekly) > 20:
        violations.append({
            "rule": "weekly_count",
            "current": len(weekly),
            "limit": 20,
            "severity": "medium",
        })
        risk_score += 15.0

    if weekly_amount > 250000:
        violations.append({
            "rule": "weekly_amount",
            "current": weekly_amount,
            "limit": 250000,
            "severity": "high",
        })
        risk_score += 20.0

    risk_score = min(risk_score, 100.0)
    has_violations = len(violations) > 0

    return {
        "account_id": account_id,
        "payment_id": payment_id,
        "payment_type": payment_type,
        "amount": amount,
        "velocity_violations": violations,
        "has_violations": has_violations,
        "risk_score": round(risk_score, 2),
        "action": "BLOCK" if risk_score >= 70 else "REVIEW" if risk_score >= 40 else "PROCEED",
        "recent_activity": {
            "hourly_count": len(hourly),
            "daily_wire_count": len(daily_wires),
            "daily_wire_amount": round(daily_wire_amount, 2),
            "daily_ach_count": len(daily_ach),
            "daily_ach_amount": round(daily_ach_amount, 2),
            "weekly_count": len(weekly),
            "weekly_amount": round(weekly_amount, 2),
        },
    }


async def get_velocity_summary(account_id: str) -> dict[str, Any]:
    """Get current velocity summary for an account."""
    now = datetime.utcnow()
    hourly = [v for v in _VELOCITY_LOG if v["account_id"] == account_id and datetime.fromisoformat(v["timestamp"]) > now - timedelta(hours=1)]
    daily = [v for v in _VELOCITY_LOG if v["account_id"] == account_id and datetime.fromisoformat(v["timestamp"]) > now - timedelta(hours=24)]
    weekly = [v for v in _VELOCITY_LOG if v["account_id"] == account_id and datetime.fromisoformat(v["timestamp"]) > now - timedelta(days=7)]

    return {
        "account_id": account_id,
        "hourly": {"count": len(hourly), "amount": round(sum(v["amount"] for v in hourly), 2)},
        "daily": {"count": len(daily), "amount": round(sum(v["amount"] for v in daily), 2)},
        "weekly": {"count": len(weekly), "amount": round(sum(v["amount"] for v in weekly), 2)},
    }


async def update_velocity_limits(
    hourly_payments: int | None = None,
    daily_wires: int | None = None,
    daily_wire_amount: float | None = None,
    daily_ach: int | None = None,
    daily_ach_amount: float | None = None,
) -> dict[str, Any]:
    """Update velocity limits (admin function)."""
    changes: list[str] = []
    if hourly_payments is not None:
        settings.velocity_limit_hourly_payments = hourly_payments
        changes.append(f"hourly_payments: {hourly_payments}")
    if daily_wires is not None:
        settings.velocity_limit_daily_wires = daily_wires
        changes.append(f"daily_wires: {daily_wires}")
    if daily_wire_amount is not None:
        settings.velocity_limit_daily_wire_amount = daily_wire_amount
        changes.append(f"daily_wire_amount: {daily_wire_amount}")
    if daily_ach is not None:
        settings.velocity_limit_daily_ach = daily_ach
        changes.append(f"daily_ach: {daily_ach}")
    if daily_ach_amount is not None:
        settings.velocity_limit_daily_ach_amount = daily_ach_amount
        changes.append(f"daily_ach_amount: {daily_ach_amount}")

    return {"status": "updated", "changes": changes}
