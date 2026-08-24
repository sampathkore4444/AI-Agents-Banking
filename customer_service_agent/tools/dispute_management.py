"""
Dispute Resolution Tool — MCP tool stub.

Guides customers through dispute process, files disputes,
and tracks resolution status.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_disputes: dict[str, dict] = {}

DISPUTE_CATEGORIES = {
    "unauthorized_transaction": "Unauthorized or fraudulent transaction",
    "duplicate_charge": "Merchant charged twice",
    "incorrect_amount": "Transaction amount incorrect",
    "product_not_received": "Product or service not received",
    "product_defective": "Product defective or not as described",
    "billing_error": "Billing statement error",
    "subscription_cancelled": "Charge after cancellation",
    "atm_error": "ATM dispensed wrong amount or failed to dispense",
}


async def file_dispute(
    customer_id: str,
    account_number: str,
    transaction_date: str,
    transaction_amount: float,
    dispute_type: str,
    description: str,
    merchant_name: str | None = None,
) -> dict:
    """File a new dispute for an unauthorized or incorrect transaction."""
    logger.info("Filing dispute for customer %s: %s ($%.2f)", customer_id, dispute_type, transaction_amount)

    dispute_id = f"DISP-{uuid.uuid4().hex[:8].upper()}"

    # Determine priority based on amount and type
    if dispute_type == "unauthorized_transaction" or transaction_amount > 500:
        priority = "high"
        sla_days = 10
    elif transaction_amount > 100:
        priority = "medium"
        sla_days = 15
    else:
        priority = "low"
        sla_days = 30

    dispute = {
        "dispute_id": dispute_id,
        "customer_id": customer_id,
        "account_number": account_number,
        "transaction_date": transaction_date,
        "transaction_amount": transaction_amount,
        "dispute_type": dispute_type,
        "dispute_category": DISPUTE_CATEGORIES.get(dispute_type, "Other"),
        "description": description,
        "merchant_name": merchant_name,
        "status": "submitted",
        "priority": priority,
        "sla_days": sla_days,
        "expected_resolution": (datetime.utcnow() + timedelta(days=sla_days)).strftime("%Y-%m-%d"),
        "provisional_credit": transaction_amount > 500,  # Large amounts get provisional credit
        "created_at": datetime.utcnow().isoformat(),
    }
    _disputes[dispute_id] = dispute
    logger.info("Dispute filed: %s (priority: %s, SLA: %d days)", dispute_id, priority, sla_days)
    return dispute


async def get_dispute_status(dispute_id: str) -> dict:
    """Get current status of a dispute."""
    dispute = _disputes.get(dispute_id)
    if not dispute:
        return {"error": f"Dispute {dispute_id} not found"}
    return dispute


async def update_dispute(
    dispute_id: str,
    status: str | None = None,
    notes: str | None = None,
    resolution: str | None = None,
) -> dict:
    """Update dispute status or add notes."""
    dispute = _disputes.get(dispute_id)
    if not dispute:
        return {"error": f"Dispute {dispute_id} not found"}
    if status:
        dispute["status"] = status
    if notes:
        dispute["notes"] = notes
    if resolution:
        dispute["resolution"] = resolution
        dispute["resolved_at"] = datetime.utcnow().isoformat()
    dispute["updated_at"] = datetime.utcnow().isoformat()
    return dispute


async def get_dispute_types() -> dict:
    """Get available dispute types and their descriptions."""
    return {"categories": [{"type": k, "description": v} for k, v in DISPUTE_CATEGORIES.items()]}
