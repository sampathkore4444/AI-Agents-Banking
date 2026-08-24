"""
SWIFT gpi Tracking Tool — MCP tool stub for cross-border payments.

Handles SWIFT gpi payment tracking, status updates, and delivery confirmation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory transaction store
_transactions: dict[str, dict] = {}


async def track_payment(uetr: str) -> dict:
    """
    Track a cross-border payment using SWIFT gpi UETR.

    UETR: Unique End-to-End Transaction Reference (UUID v4 format).
    """
    logger.info("Tracking payment: UETR=%s", uetr)

    # Simulate tracking based on UETR hash
    import hashlib
    h = int(hashlib.md5(uetr.encode()).hexdigest()[:8], 16)
    status_code = h % 5

    statuses = [
        {"code": "ACSP", "label": "Accepted Settlement Complete", "description": "Payment has been credited to beneficiary account", "is_final": True},
        {"code": "ACCP", "label": "Accepted Customer Payment Performed", "description": "Payment instruction received and processed", "is_final": False},
        {"code": "ACTC", "label": "Accepted Settlement Completed Instructed", "description": "Payment is being processed by intermediary", "is_final": False},
        {"code": "ACWC", "label": "Accepted With Conditions", "description": "Payment accepted but may need additional information", "is_final": False},
        {"code": "RJCT", "label": "Rejected", "description": "Payment was rejected — check reason code", "is_final": True},
    ]

    status = statuses[status_code]

    # Simulate correspondent chain
    chain_length = (h % 3) + 2
    banks_in_chain = ["JPMorgan Chase NY", "Barclays London", "Deutsche Bank Frankfurt", "HSBC Hong Kong", "Citibank Tokyo"]
    correspondent_chain = []
    for i in range(chain_length):
        bank = banks_in_chain[i % len(banks_in_chain)]
        correspondent_chain.append({
            "bank": bank,
            "bic": f"BK{i+1}US33",
            "status": "processed" if i < chain_length - 1 else status["label"],
            "timestamp": f"2026-01-{15+i:02d}T{(10+i):02d}:30:00Z",
        })

    # Look up stored transaction or create tracking record
    stored = _transactions.get(uetr)

    result = {
        "uetr": uetr,
        "status": status["code"],
        "status_label": status["label"],
        "description": status["description"],
        "is_final": status["is_final"],
        "correspondent_chain": correspondent_chain,
        "initiation_date": "2026-01-15",
        "expected_delivery": "2026-01-17" if not status["is_final"] else "2026-01-16",
        "tracked_at": datetime.utcnow().isoformat(),
    }

    if stored:
        result["amount"] = stored.get("amount")
        result["currency"] = stored.get("currency")
        result["originator"] = stored.get("originator")
        result["beneficiary"] = stored.get("beneficiary")

    return result


async def initiate_payment(
    source_currency: str,
    target_currency: str,
    amount: float,
    originator_name: str,
    originator_account: str,
    beneficiary_name: str,
    beneficiary_account: str,
    beneficiary_bank_bic: str,
    purpose: str,
    charges_type: str = "SHA",
    originator_address: str | None = None,
    beneficiary_address: str | None = None,
) -> dict:
    """Initiate a cross-border payment and generate UETR."""
    logger.info("Initiating payment: %s %s → %s (%s)", amount, source_currency, target_currency, beneficiary_name)

    uetr = str(uuid.uuid4())

    payment = {
        "uetr": uetr,
        "payment_type": "MT103",
        "source_currency": source_currency.upper(),
        "target_currency": target_currency.upper(),
        "amount": round(amount, 2),
        "originator": {
            "name": originator_name,
            "account": originator_account,
            "address": originator_address,
        },
        "beneficiary": {
            "name": beneficiary_name,
            "account": beneficiary_account,
            "address": beneficiary_address,
        },
        "beneficiary_bank_bic": beneficiary_bank_bic,
        "purpose": purpose,
        "charges_type": charges_type,
        "status": "initiated",
        "created_at": datetime.utcnow().isoformat(),
    }

    _transactions[uetr] = payment

    return {
        "uetr": uetr,
        "status": "initiated",
        "message": "Payment instruction received. SWIFT gpi UETR assigned.",
        "payment_details": payment,
    }


async def get_transaction_history(
    originator_account: str | None = None,
    limit: int = 10,
) -> dict:
    """Get recent cross-border transaction history."""
    txns = list(_transactions.values())

    if originator_account:
        txns = [t for t in txns if t.get("originator", {}).get("account") == originator_account]

    txns.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "total_transactions": len(txns),
        "transactions": txns[:limit],
    }
