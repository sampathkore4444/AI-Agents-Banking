"""
Transaction Monitoring — AML Red Flag Detection.

Monitors transactions for:
- Structuring (multiple just-below-$10,000 transactions)
- Rapid movement of funds
- Unusual patterns (velocity, amounts, geography)
- High-risk merchant/category flags
- Threshold analysis
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timedelta
from typing import Any

from config import settings


# ── In-memory store ───────────────────────────────────────────────
_TRANSACTIONS: dict[str, dict] = {}
_CUSTOMER_HISTORY: dict[str, list[dict]] = {}
_ALERTS: dict[str, dict] = {}


async def monitor_transaction(
    transaction_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    transaction_type: str,
    channel: str,
    country: str,
    counterparty_name: str | None = None,
    counterparty_country: str | None = None,
    account_id: str | None = None,
) -> dict[str, Any]:
    """Monitor a transaction for AML red flags."""
    risk_score = 0.0
    red_flags: list[str] = []

    # --- Threshold checks ---
    if amount >= settings.ctr_threshold_amount:
        red_flags.append("CTR_THRESHOLD_EXCEEDED")
        risk_score += 25.0

    if settings.structuring_threshold_amount - 1000 <= amount < settings.structuring_threshold_amount:
        red_flags.append("POTENTIAL_STRUCTURING")
        risk_score += 35.0

    # --- Check recent transaction history for structuring ---
    if account_id or customer_id:
        recent = _get_recent_transactions(customer_id, hours=settings.structuring_window_hours)
        below_threshold_count = sum(
            1 for t in recent
            if settings.structuring_threshold_amount - 1000 <= t.get("amount", 0) < settings.structuring_threshold_amount
        )
        if below_threshold_count >= settings.structuring_max_transactions:
            red_flags.append("STRUCTURING_PATTERN_DETECTED")
            risk_score += 50.0

        # Rapid movement check
        if len(recent) > 5:
            total_out = sum(t.get("amount", 0) for t in recent if t.get("transaction_type") in ("wire", "ach", "internal_transfer"))
            if total_out > amount * 10:
                red_flags.append("RAPID_FUND_MOVEMENT")
                risk_score += 30.0

    # --- Country risk ---
    high_risk_countries = {"IR", "KP", "SY", "CU", "VE", "MM", "AF", "IQ", "LY", "SO", "SD", "YE", "SS"}
    if country in high_risk_countries:
        red_flags.append(f"HIGH_RISK_COUNTRY_{country}")
        risk_score += 25.0
    if counterparty_country and counterparty_country in high_risk_countries:
        red_flags.append(f"COUNTERPARTY_HIGH_RISK_COUNTRY_{counterparty_country}")
        risk_score += 20.0

    # --- Amount anomaly ---
    avg_amount = _get_avg_amount(customer_id)
    if avg_amount > 0 and amount > avg_amount * 5:
        red_flags.append("AMOUNT_ANOMALY")
        risk_score += 15.0

    # --- Round number check ---
    if amount >= 5000 and amount % 1000 == 0:
        red_flags.append("ROUND_NUMBER")
        risk_score += 10.0

    # --- Round to 0-100 ---
    risk_score = min(risk_score, 100.0)

    # Determine alert level
    if risk_score >= 80:
        alert_level = "critical"
    elif risk_score >= 60:
        alert_level = "high"
    elif risk_score >= 40:
        alert_level = "medium"
    else:
        alert_level = "low"

    # Store transaction
    txn = {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": currency,
        "transaction_type": transaction_type,
        "channel": channel,
        "country": country,
        "counterparty_name": counterparty_name,
        "counterparty_country": counterparty_country,
        "account_id": account_id,
        "risk_score": risk_score,
        "red_flags": red_flags,
        "alert_level": alert_level,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _TRANSACTIONS[transaction_id] = txn

    if customer_id not in _CUSTOMER_HISTORY:
        _CUSTOMER_HISTORY[customer_id] = []
    _CUSTOMER_HISTORY[customer_id].append(txn)

    # Create alert if needed
    if risk_score >= 40:
        alert_id = f"ALERT-{hashlib.md5(transaction_id.encode()).hexdigest()[:8].upper()}"
        alert = {
            "alert_id": alert_id,
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "risk_score": risk_score,
            "red_flags": red_flags,
            "alert_level": alert_level,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "open",
        }
        _ALERTS[alert_id] = alert
        return {
            "status": "alert_generated",
            "alert_id": alert_id,
            "transaction_id": transaction_id,
            "risk_score": round(risk_score, 2),
            "alert_level": alert_level,
            "red_flags": red_flags,
            "requires_sar_filing": risk_score >= 80,
            "requires_ctr_filing": amount >= settings.ctr_threshold_amount,
        }

    return {
        "status": "cleared",
        "transaction_id": transaction_id,
        "risk_score": round(risk_score, 2),
        "alert_level": alert_level,
        "red_flags": red_flags,
        "requires_sar_filing": False,
        "requires_ctr_filing": amount >= settings.ctr_threshold_amount,
    }


async def get_transaction(transaction_id: str) -> dict[str, Any]:
    """Get transaction details and AML analysis."""
    txn = _TRANSACTIONS.get(transaction_id)
    if not txn:
        return {"error": "Transaction not found"}
    return txn


async def get_transaction_history(customer_id: str, days: int = 90, limit: int = 100) -> dict[str, Any]:
    """Get transaction history for AML analysis."""
    history = _CUSTOMER_HISTORY.get(customer_id, [])
    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = [
        t for t in history
        if datetime.fromisoformat(t["timestamp"]) > cutoff
    ]
    return {
        "customer_id": customer_id,
        "total_transactions": len(filtered),
        "transactions": filtered[:limit],
    }


async def block_transaction(transaction_id: str, reason: str) -> dict[str, Any]:
    """Block a suspicious transaction."""
    txn = _TRANSACTIONS.get(transaction_id)
    if not txn:
        return {"error": "Transaction not found"}
    txn["status"] = "blocked"
    txn["block_reason"] = reason
    txn["blocked_at"] = datetime.utcnow().isoformat()
    return {
        "status": "blocked",
        "transaction_id": transaction_id,
        "reason": reason,
    }


async def get_structuring_analysis(customer_id: str) -> dict[str, Any]:
    """Analyze a customer's transaction patterns for structuring."""
    history = _CUSTOMER_HISTORY.get(customer_id, [])
    if not history:
        return {"customer_id": customer_id, "structuring_risk": "low", "patterns": []}

    patterns: list[str] = []
    risk_score = 0.0

    # Count transactions just below $10,000
    below_threshold = [
        t for t in history
        if settings.structuring_threshold_amount - 1000 <= t.get("amount", 0) < settings.structuring_threshold_amount
    ]
    if len(below_threshold) >= settings.structuring_max_transactions:
        patterns.append(f"{len(below_threshold)} transactions just below $10,000 threshold")
        risk_score += 40.0

    # Round number analysis
    round_txns = [t for t in history if t.get("amount", 0) >= 5000 and t.get("amount", 0) % 1000 == 0]
    if len(round_txns) > len(history) * 0.5:
        patterns.append(f"{len(round_txns)} of {len(history)} transactions are round numbers")
        risk_score += 20.0

    # Multi-party deposits
    unique_parties = set()
    for t in history:
        if t.get("counterparty_name"):
            unique_parties.add(t["counterparty_name"])
    if len(unique_parties) > 3:
        patterns.append(f"Multiple counterparty parties ({len(unique_parties)} unique)")
        risk_score += 15.0

    risk_score = min(risk_score, 100.0)
    if risk_score >= 70:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "customer_id": customer_id,
        "structuring_risk": risk_level,
        "risk_score": round(risk_score, 2),
        "patterns": patterns,
        "below_threshold_count": len(below_threshold),
        "total_transactions": len(history),
        "recommendation": "SAR filing recommended" if risk_score >= 70 else "Enhanced monitoring" if risk_score >= 50 else "Standard monitoring",
    }


async def get_aml_alerts(status: str = "open", limit: int = 50) -> dict[str, Any]:
    """Get AML alerts filtered by status."""
    filtered = [a for a in _ALERTS.values() if status == "all" or a["status"] == status]
    return {"status": status, "total": len(filtered), "alerts": filtered[:limit]}


async def get_aml_stats(days: int = 30) -> dict[str, Any]:
    """Get AML monitoring statistics."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    all_txns = [
        t for t in _TRANSACTIONS.values()
        if datetime.fromisoformat(t["timestamp"]) > cutoff
    ]
    all_alerts = [
        a for a in _ALERTS.values()
        if datetime.fromisoformat(a["timestamp"]) > cutoff
    ]

    high_risk = [t for t in all_txns if t.get("risk_score", 0) >= 60]
    critical = [a for a in all_alerts if a["alert_level"] == "critical"]

    return {
        "period_days": days,
        "total_transactions_monitored": len(all_txns),
        "total_alerts": len(all_alerts),
        "critical_alerts": len(critical),
        "high_risk_transactions": len(high_risk),
        "sar_recommended": len([t for t in all_txns if t.get("requires_sar_filing")]),
        "ctr_required": len([t for t in all_txns if t.get("requires_ctr_filing")]),
    }


# ── Helpers ───────────────────────────────────────────────────────

def _get_recent_transactions(customer_id: str, hours: int = 24) -> list[dict]:
    history = _CUSTOMER_HISTORY.get(customer_id, [])
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    return [t for t in history if datetime.fromisoformat(t["timestamp"]) > cutoff]


def _get_avg_amount(customer_id: str) -> float:
    history = _CUSTOMER_HISTORY.get(customer_id, [])
    if not history:
        return 0.0
    return sum(t.get("amount", 0) for t in history) / len(history)
