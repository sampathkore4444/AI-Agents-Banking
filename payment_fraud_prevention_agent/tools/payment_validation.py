"""
Payment Validation — Real-time payment fraud scoring and decision.

Validates outgoing payments across all channels:
- Wire transfers (domestic/international)
- ACH debits/credits
- Check deposits/clearing
- Real-time payments (RTP, FedNow, Zelle)
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta
from typing import Any

from config import settings


# ── In-memory store ───────────────────────────────────────────────
_PAYMENTS: dict[str, dict] = {}
_PAYMENT_HISTORY: dict[str, list[dict]] = {}
_ALERTS: dict[str, dict] = {}


async def validate_payment(
    payment_id: str,
    payer_account_id: str,
    payer_name: str,
    payee_name: str,
    payee_account_id: str | None,
    payee_bank_routing: str,
    amount: float,
    currency: str,
    payment_type: str,
    channel: str,
    originator_ip: str | None = None,
    device_id: str | None = None,
    description: str | None = None,
    purpose_of_payment: str | None = None,
    is_international: bool = False,
    beneficiary_country: str | None = None,
) -> dict[str, Any]:
    """Validate a payment in real-time for fraud indicators."""
    risk_score = 0.0
    red_flags: list[str] = []
    risk_factors: list[dict] = []

    # --- Amount threshold checks by payment type ---
    thresholds = {
        "wire": (settings.wire_threshold_review, settings.wire_threshold_block),
        "ach": (settings.ach_threshold_review, settings.ach_threshold_block),
        "check": (settings.check_threshold_review, settings.check_threshold_block),
        "rtp": (settings.rtp_threshold_review, settings.rtp_threshold_block),
        "fednow": (settings.rtp_threshold_review, settings.rtp_threshold_block),
        "zelle": (5000, 10000),
    }
    review_t, block_t = thresholds.get(payment_type, (10000, 50000))

    if amount >= block_t:
        red_flags.append("AMOUNT_EXCEEDS_BLOCK_THRESHOLD")
        risk_score += 40.0
        risk_factors.append({"factor": "amount_threshold", "severity": "critical", "detail": f"${amount:,.2f} exceeds ${block_t:,.2f} block threshold for {payment_type}"})
    elif amount >= review_t:
        red_flags.append("AMOUNT_EXCEEDS_REVIEW_THRESHOLD")
        risk_score += 20.0
        risk_factors.append({"factor": "amount_threshold", "severity": "high", "detail": f"${amount:,.2f} exceeds ${review_t:,.2f} review threshold for {payment_type}"})

    # --- Velocity check ---
    recent = _get_recent_payments(payer_account_id, hours=24)
    wire_count = sum(1 for p in recent if p.get("payment_type") == "wire")
    total_wire_amount = sum(p.get("amount", 0) for p in recent if p.get("payment_type") == "wire")

    if payment_type == "wire":
        if wire_count >= settings.velocity_limit_daily_wires:
            red_flags.append("WIRE_VELOCITY_EXCEEDED")
            risk_score += 35.0
            risk_factors.append({"factor": "wire_velocity", "severity": "high", "detail": f"{wire_count} wires in 24h (limit: {settings.velocity_limit_daily_wires})"})
        if total_wire_amount + amount > settings.velocity_limit_daily_wire_amount:
            red_flags.append("WIRE_AMOUNT_VELOCITY_EXCEEDED")
            risk_score += 30.0
            risk_factors.append({"factor": "wire_amount_velocity", "severity": "high", "detail": f"Daily wire total ${total_wire_amount + amount:,.2f} exceeds ${settings.velocity_limit_daily_wire_amount:,.2f}"})

    # --- New beneficiary check ---
    if payee_account_id:
        history = _PAYMENT_HISTORY.get(payer_account_id, [])
        known_beneficiaries = set(p.get("payee_account_id") for p in history if p.get("payee_account_id"))
        if payee_account_id not in known_beneficiaries:
            red_flags.append("NEW_BENEFICIARY")
            risk_score += 15.0
            risk_factors.append({"factor": "new_beneficiary", "severity": "medium", "detail": f"First payment to beneficiary {payee_account_id}"})

    # --- Beneficiary name mismatch ---
    if payee_name and payer_name:
        from difflib import SequenceMatcher
        name_sim = SequenceMatcher(None, payee_name.lower(), payer_name.lower()).ratio()
        if name_sim > 0.8 and payee_account_id != payer_account_id:
            red_flags.append("BENEFICIARY_NAME_SIMILAR_TO_PAYER")
            risk_score += 10.0
            risk_factors.append({"factor": "name_similarity", "severity": "low", "detail": f"Payee name similar to payer (score: {name_sim:.2f})"})

    # --- International payment ---
    if is_international:
        risk_score += 10.0
        risk_factors.append({"factor": "international", "severity": "medium", "detail": "International payment requires enhanced screening"})

    # --- High-risk country ---
    if beneficiary_country and beneficiary_country in settings.high_risk_countries:
        red_flags.append(f"HIGH_RISK_BENEFICIARY_COUNTRY_{beneficiary_country}")
        risk_score += 30.0
        risk_factors.append({"factor": "high_risk_country", "severity": "critical", "detail": f"Beneficiary country {beneficiary_country} is high-risk"})

    # --- Round number check ---
    if amount >= 5000 and amount % 1000 == 0:
        red_flags.append("ROUND_NUMBER")
        risk_score += 5.0
        risk_factors.append({"factor": "round_number", "severity": "low", "detail": "Round number amount"})

    # --- Unusual time check ---
    now = datetime.utcnow()
    if 0 <= now.hour <= 5:
        red_flags.append("UNUSUAL_TIME")
        risk_score += 10.0
        risk_factors.append({"factor": "unusual_time", "severity": "medium", "detail": f"Payment initiated at {now.strftime('%H:%M')} UTC"})

    # --- ACH payroll check ---
    if payment_type == "ach" and description and "payroll" in description.lower():
        recent_ach = [p for p in recent if p.get("payment_type") == "ach" and "payroll" in (p.get("description") or "").lower()]
        if len(recent_ach) > 0:
            red_flags.append("ACH_PAYROLL_DUPLICATE")
            risk_score += 25.0
            risk_factors.append({"factor": "ach_payroll_duplicate", "severity": "high", "detail": "Duplicate ACH payroll payment detected"})

    # --- RTP new recipient ---
    if payment_type in ("rtp", "fednow", "zelle") and payee_account_id:
        history = _PAYMENT_HISTORY.get(payer_account_id, [])
        known_rtp = set(p.get("payee_account_id") for p in history if p.get("payment_type") in ("rtp", "fednow", "zelle"))
        if payee_account_id not in known_rtp:
            red_flags.append("RTP_NEW_RECIPIENT")
            risk_score += 15.0
            risk_factors.append({"factor": "rtp_new_recipient", "severity": "medium", "detail": "First RTP to this recipient"})

    # Cap score at 100
    risk_score = min(risk_score, 100.0)

    # Determine decision
    if risk_score >= settings.fraud_score_threshold_block:
        decision = "block"
        alert_level = "critical"
    elif risk_score >= settings.fraud_score_threshold_review:
        decision = "review"
        alert_level = "high"
    elif risk_score >= settings.fraud_score_threshold_alert:
        decision = "alert"
        alert_level = "medium"
    else:
        decision = "allow"
        alert_level = "low"

    # Store payment
    payment = {
        "payment_id": payment_id,
        "payer_account_id": payer_account_id,
        "payer_name": payer_name,
        "payee_name": payee_name,
        "payee_account_id": payee_account_id,
        "payee_bank_routing": payee_bank_routing,
        "amount": amount,
        "currency": currency,
        "payment_type": payment_type,
        "channel": channel,
        "is_international": is_international,
        "beneficiary_country": beneficiary_country,
        "description": description,
        "purpose_of_payment": purpose_of_payment,
        "risk_score": risk_score,
        "decision": decision,
        "alert_level": alert_level,
        "red_flags": red_flags,
        "risk_factors": risk_factors,
        "timestamp": datetime.utcnow().isoformat(),
        "status": decision,
    }
    _PAYMENTS[payment_id] = payment

    if payer_account_id not in _PAYMENT_HISTORY:
        _PAYMENT_HISTORY[payer_account_id] = []
    _PAYMENT_HISTORY[payer_account_id].append(payment)

    # Create alert if needed
    if risk_score >= settings.fraud_score_threshold_alert:
        alert_id = f"PF-ALERT-{hashlib.md5(payment_id.encode()).hexdigest()[:8].upper()}"
        alert = {
            "alert_id": alert_id,
            "payment_id": payment_id,
            "payer_account_id": payer_account_id,
            "risk_score": risk_score,
            "decision": decision,
            "alert_level": alert_level,
            "red_flags": red_flags,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "open",
        }
        _ALERTS[alert_id] = alert
        return {
            "status": "alert_generated",
            "alert_id": alert_id,
            "payment_id": payment_id,
            "decision": decision,
            "risk_score": round(risk_score, 2),
            "alert_level": alert_level,
            "red_flags": red_flags,
            "risk_factors": risk_factors,
            "requires_sar": risk_score >= 80 and amount >= settings.wire_threshold_sar,
        }

    return {
        "status": "validated",
        "payment_id": payment_id,
        "decision": decision,
        "risk_score": round(risk_score, 2),
        "alert_level": alert_level,
        "red_flags": red_flags,
        "risk_factors": risk_factors,
        "requires_sar": False,
    }


async def get_payment(payment_id: str) -> dict[str, Any]:
    """Get payment details and fraud analysis."""
    payment = _PAYMENTS.get(payment_id)
    if not payment:
        return {"error": "Payment not found"}
    return payment


async def get_payment_history(account_id: str, days: int = 90, limit: int = 100) -> dict[str, Any]:
    """Get payment history for fraud analysis."""
    history = _PAYMENT_HISTORY.get(account_id, [])
    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = [p for p in history if datetime.fromisoformat(p["timestamp"]) > cutoff]
    return {"account_id": account_id, "total": len(filtered), "payments": filtered[:limit]}


async def block_payment(payment_id: str, reason: str) -> dict[str, Any]:
    """Block a suspicious payment."""
    payment = _PAYMENTS.get(payment_id)
    if not payment:
        return {"error": "Payment not found"}
    payment["status"] = "blocked"
    payment["block_reason"] = reason
    payment["blocked_at"] = datetime.utcnow().isoformat()
    return {"status": "blocked", "payment_id": payment_id, "reason": reason}


async def approve_payment(payment_id: str, approved_by: str, notes: str | None = None) -> dict[str, Any]:
    """Approve a payment that was held for review."""
    payment = _PAYMENTS.get(payment_id)
    if not payment:
        return {"error": "Payment not found"}
    payment["status"] = "approved"
    payment["approved_by"] = approved_by
    payment["approved_at"] = datetime.utcnow().isoformat()
    payment["approval_notes"] = notes
    return {"status": "approved", "payment_id": payment_id, "approved_by": approved_by}


async def get_fraud_alerts(status: str = "open", limit: int = 50) -> dict[str, Any]:
    """Get payment fraud alerts filtered by status."""
    filtered = [a for a in _ALERTS.values() if status == "all" or a["status"] == status]
    return {"status": status, "total": len(filtered), "alerts": filtered[:limit]}


async def get_payment_stats(days: int = 30) -> dict[str, Any]:
    """Get payment fraud monitoring statistics."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    all_payments = [p for p in _PAYMENTS.values() if datetime.fromisoformat(p["timestamp"]) > cutoff]
    all_alerts = [a for a in _ALERTS.values() if datetime.fromisoformat(a["timestamp"]) > cutoff]

    by_type: dict[str, int] = {}
    by_decision: dict[str, int] = {}
    for p in all_payments:
        by_type[p["payment_type"]] = by_type.get(p["payment_type"], 0) + 1
        by_decision[p["decision"]] = by_decision.get(p["decision"], 0) + 1

    return {
        "period_days": days,
        "total_payments": len(all_payments),
        "total_alerts": len(all_alerts),
        "by_type": by_type,
        "by_decision": by_decision,
        "blocked": by_decision.get("block", 0),
        "review": by_decision.get("review", 0),
        "total_amount": sum(p.get("amount", 0) for p in all_payments),
    }


def _get_recent_payments(account_id: str, hours: int = 24) -> list[dict]:
    history = _PAYMENT_HISTORY.get(account_id, [])
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    return [p for p in history if datetime.fromisoformat(p["timestamp"]) > cutoff]
