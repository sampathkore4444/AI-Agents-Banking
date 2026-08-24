"""
Transaction Monitoring Tool — Real-time transaction analysis and fraud scoring.
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timedelta
from typing import Any


# ── In-memory store (simulates transaction processing API) ─────────
TRANSACTION_DB: dict[str, dict] = {}
CUSTOMER_PROFILES: dict[str, dict] = {}


def _generate_txn_id() -> str:
    return f"TXN-{hashlib.md5(str(time.time()).encode()).hexdigest()[:10].upper()}"


def _generate_fraud_score(txn: dict, customer: dict | None) -> dict[str, Any]:
    """Calculate fraud score based on transaction features."""
    score = 0
    risk_factors: list[str] = []

    amount = txn.get("amount", 0)
    avg_amount = customer.get("avg_transaction_amount", 500) if customer else 500

    # Amount anomaly
    if amount > avg_amount * 3:
        score += 25
        risk_factors.append(f"Transaction amount ({amount:.2f}) is {amount/avg_amount:.1f}x average ({avg_amount:.2f})")
    elif amount > avg_amount * 2:
        score += 15
        risk_factors.append(f"Transaction amount ({amount:.2f}) is {amount/avg_amount:.1f}x average")

    # High-value transaction
    if amount > 10000:
        score += 20
        risk_factors.append("Transaction exceeds $10,000 (CTR threshold)")

    # Late-night transaction
    txn_hour = txn.get("hour", 12)
    if 2 <= txn_hour <= 5:
        score += 15
        risk_factors.append(f"Transaction at unusual time ({txn_hour}:00)")

    # New merchant
    if txn.get("is_new_merchant", False):
        score += 10
        risk_factors.append("First transaction with this merchant")

    # International transaction
    if txn.get("is_international", False):
        score += 15
        risk_factors.append(f"International transaction in {txn.get('country', 'unknown')}")

    # Card-not-present
    if txn.get("channel") == "card_not_present":
        score += 10
        risk_factors.append("Card-not-present transaction")

    # Multiple recent transactions
    recent_count = customer.get("transactions_last_hour", 0) if customer else 0
    if recent_count > 3:
        score += 20
        risk_factors.append(f"{recent_count} transactions in the last hour")

    # Device mismatch
    if txn.get("device_new", False):
        score += 15
        risk_factors.append("Transaction from new/unknown device")

    # Geo anomaly
    if txn.get("geo_mismatch", False):
        score += 25
        risk_factors.append("Geographic location mismatch (physically impossible travel)")

    # Clamp score
    score = min(score, 100)

    # Determine action
    if score >= 85:
        action = "block"
        risk_level = "critical"
    elif score >= 60:
        action = "review"
        risk_level = "high"
    elif score >= 40:
        action = "alert"
        risk_level = "medium"
    else:
        action = "allow"
        risk_level = "low"

    return {
        "score": score,
        "risk_level": risk_level,
        "action": action,
        "risk_factors": risk_factors,
        "model_version": "fraud-scorer-v2.1",
        "confidence": min(0.6 + score * 0.004, 0.99),
    }


async def analyze_transaction(
    transaction_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    merchant_id: str,
    merchant_category: str,
    channel: str,
    country: str,
    ip_address: str | None = None,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Analyze a transaction for fraud in real-time."""
    now = datetime.utcnow()

    txn = {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": currency,
        "merchant_id": merchant_id,
        "merchant_category": merchant_category,
        "channel": channel,
        "country": country,
        "ip_address": ip_address,
        "device_id": device_id,
        "timestamp": now.isoformat(),
        "hour": now.hour,
        "is_new_merchant": random.random() < 0.15,
        "is_international": country not in ("US", "CA"),
        "device_new": random.random() < 0.1,
        "geo_mismatch": random.random() < 0.08,
    }

    customer = CUSTOMER_PROFILES.get(customer_id, {
        "avg_transaction_amount": 500,
        "transactions_last_hour": 0,
        "normal_countries": ["US"],
        "normal_channels": ["card_present"],
    })

    fraud_result = _generate_fraud_score(txn, customer)

    # Store transaction
    TRANSACTION_DB[transaction_id] = {
        **txn,
        "fraud_score": fraud_result["score"],
        "risk_level": fraud_result["risk_level"],
        "action": fraud_result["action"],
        "status": "blocked" if fraud_result["action"] == "block" else "pending",
    }

    # Update customer profile
    if customer_id not in CUSTOMER_PROFILES:
        CUSTOMER_PROFILES[customer_id] = customer
    CUSTOMER_PROFILES[customer_id]["transactions_last_hour"] = customer.get("transactions_last_hour", 0) + 1

    return {
        "transaction_id": transaction_id,
        "analysis": fraud_result,
        "status": TRANSACTION_DB[transaction_id]["status"],
        "message": f"Transaction {'blocked' if fraud_result['action'] == 'block' else 'flagged for review' if fraud_result['action'] == 'review' else 'passed'} — Fraud score: {fraud_result['score']}/100",
    }


async def get_transaction(transaction_id: str) -> dict[str, Any]:
    """Get transaction details and fraud analysis."""
    txn = TRANSACTION_DB.get(transaction_id)
    if not txn:
        return {"error": f"Transaction {transaction_id} not found"}
    return txn


async def get_transaction_history(
    customer_id: str,
    hours: int = 24,
    limit: int = 50,
) -> dict[str, Any]:
    """Get recent transaction history for a customer."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    txns = [
        t for t in TRANSACTION_DB.values()
        if t["customer_id"] == customer_id and t["timestamp"] >= cutoff
    ]
    txns.sort(key=lambda x: x["timestamp"], reverse=True)
    return {
        "customer_id": customer_id,
        "time_range_hours": hours,
        "total_transactions": len(txns),
        "total_amount": sum(t["amount"] for t in txns),
        "flagged_count": sum(1 for t in txns if t.get("fraud_score", 0) >= 40),
        "transactions": txns[:limit],
    }


async def block_transaction(transaction_id: str, reason: str) -> dict[str, Any]:
    """Block a transaction."""
    txn = TRANSACTION_DB.get(transaction_id)
    if not txn:
        return {"error": f"Transaction {transaction_id} not found"}
    txn["status"] = "blocked"
    txn["block_reason"] = reason
    txn["blocked_at"] = datetime.utcnow().isoformat()
    return {"transaction_id": transaction_id, "status": "blocked", "reason": reason}


async def unblock_transaction(transaction_id: str, reason: str) -> dict[str, Any]:
    """Unblock a transaction."""
    txn = TRANSACTION_DB.get(transaction_id)
    if not txn:
        return {"error": f"Transaction {transaction_id} not found"}
    txn["status"] = "active"
    txn["unblock_reason"] = reason
    txn["unblocked_at"] = datetime.utcnow().isoformat()
    return {"transaction_id": transaction_id, "status": "active", "reason": reason}


async def get_fraud_stats(hours: int = 24) -> dict[str, Any]:
    """Get fraud statistics for a time period."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    txns = [t for t in TRANSACTION_DB.values() if t["timestamp"] >= cutoff]
    total = len(txns)
    flagged = sum(1 for t in txns if t.get("fraud_score", 0) >= 40)
    blocked = sum(1 for t in txns if t.get("status") == "blocked")
    return {
        "time_range_hours": hours,
        "total_transactions": total,
        "flagged_count": flagged,
        "blocked_count": blocked,
        "flag_rate": f"{(flagged/total*100):.1f}%" if total > 0 else "0%",
        "block_rate": f"{(blocked/total*100):.1f}%" if total > 0 else "0%",
        "total_amount": sum(t["amount"] for t in txns),
        "blocked_amount": sum(t["amount"] for t in txns if t.get("status") == "blocked"),
    }
