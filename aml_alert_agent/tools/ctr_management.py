"""
CTR (Currency Transaction Report) Management — Filing, Aggregation, Exemptions.

Manages:
- Individual CTR filing for cash transactions ≥ $10,000
- Aggregation of multiple transactions
- Exemption management
- Filing tracking and deadlines
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

# ── In-memory store ───────────────────────────────────────────────
_CTRS: dict[str, dict] = {}
_CTR_EXEMPTIONS: list[dict] = []
_AGGREGATED_TXNS: list[dict] = []


async def file_ctr(
    customer_id: str,
    customer_name: str,
    customer_ssn_tin: str,
    customer_address: str,
    customer_occupation: str,
    transaction_date: str,
    total_amount: float,
    transaction_type: str,
    transaction_description: str,
    branch_id: str,
    employee_id: str,
    aggregation_applied: bool = False,
    aggregated_transactions: list[dict] | None = None,
) -> dict[str, Any]:
    """File a Currency Transaction Report."""
    if total_amount < settings_ctr_threshold():
        return {"error": "Amount below CTR threshold ($10,000)"}

    ctr_id = f"CTR-{hashlib.md5(f'{customer_id}{transaction_date}'.encode()).hexdigest()[:10].upper()}"

    ctr = {
        "ctr_id": ctr_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "customer_ssn_tin": customer_ssn_tin,
        "customer_address": customer_address,
        "customer_occupation": customer_occupation,
        "transaction_date": transaction_date,
        "total_amount": total_amount,
        "transaction_type": transaction_type,
        "transaction_description": transaction_description,
        "branch_id": branch_id,
        "employee_id": employee_id,
        "aggregation_applied": aggregation_applied,
        "aggregated_transactions": aggregated_transactions or [],
        "status": "filed",
        "filing_date": datetime.utcnow().isoformat(),
        "filing_deadline": (datetime.utcnow() + timedelta(days=15)).isoformat(),
        "confirmation_number": f"CTR-{hashlib.md5(ctr_id.encode()).hexdigest()[:8].upper()}",
        "retention_expires": (datetime.utcnow() + timedelta(days=5 * 365)).isoformat(),
    }

    _CTRS[ctr_id] = ctr
    return {
        "ctr_id": ctr_id,
        "status": "filed",
        "confirmation_number": ctr["confirmation_number"],
        "filing_date": ctr["filing_date"],
        "amount": total_amount,
    }


async def check_aggregation(
    customer_id: str,
    transactions: list[dict],
    aggregation_period_days: int = 15,
) -> dict[str, Any]:
    """Check if multiple transactions should be aggregated for CTR filing."""
    total_amount = sum(t.get("amount", 0) for t in transactions)
    cash_transactions = [t for t in transactions if t.get("transaction_type") in ("cash_deposit", "cash_withdrawal", "currency_exchange")]

    cash_total = sum(t.get("amount", 0) for t in cash_transactions)
    requires_ctr = cash_total >= 10000

    # Check for structuring patterns
    below_threshold = [t for t in cash_transactions if 8000 <= t.get("amount", 0) < 10000]
    structuring_suspected = len(below_threshold) >= 3

    return {
        "customer_id": customer_id,
        "aggregation_period_days": aggregation_period_days,
        "total_transactions": len(transactions),
        "cash_transactions": len(cash_transactions),
        "total_cash_amount": cash_total,
        "requires_ctr": requires_ctr,
        "structuring_suspected": structuring_suspected,
        "below_threshold_count": len(below_threshold),
        "recommendation": (
            "File aggregated CTR and SAR for suspected structuring"
            if structuring_suspected
            else "File aggregated CTR"
            if requires_ctr
            else "No CTR required"
        ),
    }


async def create_exemption(
    customer_id: str,
    customer_name: str,
    exemption_type: str,
    reason: str,
    approved_by: str,
) -> dict[str, Any]:
    """Create a CTR exemption for a customer."""
    exemption_id = f"EXEMPT-{hashlib.md5(f'{customer_id}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:8].upper()}"

    exemption = {
        "exemption_id": exemption_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "exemption_type": exemption_type,
        "reason": reason,
        "approved_by": approved_by,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
        "review_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
    }

    _CTR_EXEMPTIONS.append(exemption)
    return {
        "exemption_id": exemption_id,
        "status": "active",
        "customer_id": customer_id,
        "exemption_type": exemption_type,
    }


async def get_exemptions(customer_id: str | None = None) -> dict[str, Any]:
    """Get CTR exemptions."""
    if customer_id:
        filtered = [e for e in _CTR_EXEMPTIONS if e["customer_id"] == customer_id]
    else:
        filtered = _CTR_EXEMPTIONS

    return {
        "total_exemptions": len(filtered),
        "active_exemptions": len([e for e in filtered if e["status"] == "active"]),
        "exemptions": filtered,
    }


async def revoke_exemption(exemption_id: str, reason: str) -> dict[str, Any]:
    """Revoke a CTR exemption."""
    for e in _CTR_EXEMPTIONS:
        if e["exemption_id"] == exemption_id:
            e["status"] = "revoked"
            e["revoked_at"] = datetime.utcnow().isoformat()
            e["revocation_reason"] = reason
            return {"exemption_id": exemption_id, "status": "revoked", "reason": reason}
    return {"error": "Exemption not found"}


async def get_ctr_stats(days: int = 30) -> dict[str, Any]:
    """Get CTR filing statistics."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    all_ctrs = [c for c in _CTRS.values() if datetime.fromisoformat(c["filing_date"]) > cutoff]

    return {
        "period_days": days,
        "total_ctrs_filed": len(all_ctrs),
        "total_amount_reported": sum(c["total_amount"] for c in all_ctrs),
        "aggregated_ctrs": len([c for c in all_ctrs if c["aggregation_applied"]]),
        "active_exemptions": len([e for e in _CTR_EXEMPTIONS if e["status"] == "active"]),
    }


def settings_ctr_threshold() -> float:
    return 10000.0
