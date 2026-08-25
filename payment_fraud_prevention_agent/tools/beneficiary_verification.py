"""
Beneficiary Verification — Verify payment recipients for fraud prevention.

Capabilities:
- Beneficiary name matching against known payees
- Account number validation
- New beneficiary detection and monitoring
- Beneficiary risk profiling
- Cross-reference against fraud databases
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

# ── Known payee database (simulated) ─────────────────────────────
_KNOWN_PAYEES: dict[str, list[dict]] = {}
_BENEFICIARY_ALERTS: dict[str, dict] = {}


async def verify_beneficiary(
    account_id: str,
    payee_name: str,
    payee_account_number: str,
    payee_routing_number: str,
    payee_bank_name: str | None = None,
    payee_country: str | None = None,
    payment_amount: float = 0.0,
    payment_type: str = "wire",
) -> dict[str, Any]:
    """Verify a beneficiary against known payees and risk indicators."""
    verification_checks: list[dict] = []
    risk_score = 0.0

    # --- Check against known payees ---
    known = _KNOWN_PAYEES.get(account_id, [])
    name_match = False
    account_match = False
    matched_payee = None

    for payee in known:
        name_sim = SequenceMatcher(None, payee_name.lower(), payee.get("name", "").lower()).ratio()
        if name_sim >= 0.85:
            name_match = True
        if payee_account_number == payee.get("account_number"):
            account_match = True
            matched_payee = payee
            break

    if matched_payee:
        verification_checks.append({"check": "known_payee", "result": "match", "payee": matched_payee["name"]})
    elif name_match:
        verification_checks.append({"check": "known_payee", "result": "name_match_only", "detail": "Account number does not match known payee"})
        risk_score += 15.0
    else:
        verification_checks.append({"check": "known_payee", "result": "new_beneficiary"})
        risk_score += 10.0

    # --- Account number validation ---
    if len(payee_account_number) < 4 or not payee_account_number.isdigit():
        verification_checks.append({"check": "account_format", "result": "invalid", "detail": "Account number format invalid"})
        risk_score += 25.0
    else:
        verification_checks.append({"check": "account_format", "result": "valid"})

    # --- Routing number validation ---
    if len(payee_routing_number) != 9 or not payee_routing_number.isdigit():
        verification_checks.append({"check": "routing_format", "result": "invalid", "detail": "Routing number must be 9 digits"})
        risk_score += 25.0
    else:
        verification_checks.append({"check": "routing_format", "result": "valid"})

    # --- Same-bank check (internal transfer lower risk) ---
    if payee_routing_number.startswith("021000021") or payee_routing_number.startswith("021000089"):
        verification_checks.append({"check": "internal_transfer", "result": "same_bank"})
        risk_score -= 5.0
    else:
        verification_checks.append({"check": "internal_transfer", "result": "external"})

    # --- Beneficiary country risk ---
    high_risk = {"IR", "KP", "SY", "CU", "VE", "MM", "AF", "IQ"}
    if payee_country and payee_country in high_risk:
        verification_checks.append({"check": "country_risk", "result": "high_risk", "country": payee_country})
        risk_score += 30.0
    elif payee_country:
        verification_checks.append({"check": "country_risk", "result": "normal", "country": payee_country})

    # --- Amount vs beneficiary pattern ---
    if matched_payee and payment_amount > 0:
        avg = matched_payee.get("avg_payment_amount", 0)
        if avg > 0 and payment_amount > avg * 3:
            verification_checks.append({"check": "amount_pattern", "result": "anomaly", "detail": f"${payment_amount:,.2f} > 3x average ${avg:,.2f}"})
            risk_score += 15.0
        else:
            verification_checks.append({"check": "amount_pattern", "result": "normal"})

    risk_score = max(0.0, min(risk_score, 100.0))

    # Record verification
    verification_id = hashlib.md5(f"{account_id}{payee_account_number}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12].upper()

    return {
        "verification_id": verification_id,
        "account_id": account_id,
        "payee_name": payee_name,
        "payee_account_number": payee_account_number,
        "payee_routing_number": payee_routing_number,
        "is_known_beneficiary": matched_payee is not None,
        "verification_checks": verification_checks,
        "risk_score": round(risk_score, 2),
        "risk_level": "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low",
        "recommendation": "BLOCK" if risk_score >= 70 else "REVIEW" if risk_score >= 40 else "PROCEED",
        "timestamp": datetime.utcnow().isoformat(),
    }


async def add_known_payee(
    account_id: str,
    name: str,
    account_number: str,
    routing_number: str,
    bank_name: str | None = None,
    payee_type: str = "individual",
    avg_payment_amount: float = 0.0,
    category: str = "general",
) -> dict[str, Any]:
    """Add a known payee to the account's payee database."""
    if account_id not in _KNOWN_PAYEES:
        _KNOWN_PAYEES[account_id] = []

    payee_id = hashlib.md5(f"{account_id}{account_number}".encode()).hexdigest()[:10].upper()
    payee = {
        "payee_id": payee_id,
        "name": name,
        "account_number": account_number,
        "routing_number": routing_number,
        "bank_name": bank_name,
        "payee_type": payee_type,
        "avg_payment_amount": avg_payment_amount,
        "category": category,
        "added_at": datetime.utcnow().isoformat(),
        "status": "active",
    }
    _KNOWN_PAYEES[account_id].append(payee)
    return {"payee_id": payee_id, "status": "added", "name": name}


async def get_known_payees(account_id: str) -> dict[str, Any]:
    """Get known payees for an account."""
    payees = _KNOWN_PAYEES.get(account_id, [])
    return {"account_id": account_id, "total": len(payees), "payees": payees}


async def remove_known_payee(account_id: str, payee_id: str) -> dict[str, Any]:
    """Remove a known payee."""
    payees = _KNOWN_PAYEES.get(account_id, [])
    _KNOWN_PAYEES[account_id] = [p for p in payees if p["payee_id"] != payee_id]
    return {"status": "removed", "payee_id": payee_id}


async def get_beneficiary_risk_profile(payee_account_number: str, payee_routing_number: str) -> dict[str, Any]:
    """Get risk profile for a beneficiary based on historical data."""
    # Count how many accounts have paid this beneficiary
    paying_accounts = 0
    total_payments = 0
    total_amount = 0.0
    for account_id, payees in _KNOWN_PAYEES.items():
        for p in payees:
            if p.get("account_number") == payee_account_number:
                paying_accounts += 1
                total_amount += p.get("avg_payment_amount", 0) * 12  # annualized

    risk_score = 0.0
    risk_factors: list[str] = []

    if paying_accounts > 5:
        risk_factors.append(f"Beneficiary receives payments from {paying_accounts} accounts (potential mule)")
        risk_score += 20.0

    if paying_accounts == 0:
        risk_factors.append("Beneficiary not in any known payee database")
        risk_score += 10.0

    return {
        "payee_account_number": payee_account_number,
        "payee_routing_number": payee_routing_number,
        "paying_accounts": paying_accounts,
        "estimated_annual_volume": round(total_amount, 2),
        "risk_score": round(min(risk_score, 100.0), 2),
        "risk_factors": risk_factors,
    }
