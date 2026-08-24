"""
Payment Gateway Tool — MCP tool stub.

Processes payments for collections accounts.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def process_payment(
    account_id: str,
    amount: float,
    payment_method: str,
    payment_type: str = "regular",
    plan_id: str | None = None,
) -> dict:
    """
    Process a payment for a collections account.

    payment_method: "card", "ach", "wire", "check", "cash"
    payment_type: "regular", "catch_up", "settlement", "partial"
    """
    logger.info("Processing payment: account=%s, amount=$%.2f, method=%s", account_id, amount, payment_method)

    payment_id = f"PMT-{uuid.uuid4().hex[:8].upper()}"

    result = {
        "payment_id": payment_id,
        "account_id": account_id,
        "amount": round(amount, 2),
        "payment_method": payment_method,
        "payment_type": payment_type,
        "plan_id": plan_id,
        "status": "processed",
        "processed_at": datetime.utcnow().isoformat(),
        "confirmation_number": f"CONF-{uuid.uuid4().hex[:12].upper()}",
        "receipt_available": True,
    }

    # Payment type specific handling
    if payment_type == "settlement":
        result["settlement_applied"] = True
        result["settlement_note"] = "Settlement payment processed. Remaining balance will be adjusted per settlement agreement."
    elif payment_type == "catch_up":
        result["catch_up_applied"] = True
        result["catch_up_note"] = "Catch-up payment applied to bring account current."
    elif payment_type == "partial":
        result["partial_payment"] = True
        result["partial_note"] = "Partial payment received. Remaining balance will be carried forward."

    logger.info("Payment processed: %s", payment_id)
    return result


async def setup_autopay(
    account_id: str,
    plan_id: str,
    payment_method: str,
    payment_day: int = 1,
    amount: float | None = None,
) -> dict:
    """Set up automatic payments for a collections account."""
    logger.info("Setting up autopay: account=%s, plan=%s", account_id, plan_id)

    autopay_id = f"AP-{uuid.uuid4().hex[:8].upper()}"

    return {
        "autopay_id": autopay_id,
        "account_id": account_id,
        "plan_id": plan_id,
        "payment_method": payment_method,
        "payment_day": payment_day,
        "amount": amount,
        "status": "active",
        "next_payment_date": f"Next month, day {payment_day}",
        "started_at": datetime.utcnow().isoformat(),
    }


async def get_payment_history(account_id: str, limit: int = 10) -> dict:
    """Get payment history for a collections account."""
    # Simulated payment history
    history = [
        {
            "payment_id": f"PMT-{uuid.uuid4().hex[:6].upper()}",
            "date": (datetime.utcnow()).strftime("%Y-%m-%d"),
            "amount": 500.00,
            "method": "ach",
            "type": "regular",
            "status": "processed",
        },
    ]

    return {
        "account_id": account_id,
        "payments": history[:limit],
        "total_payments": len(history),
        "total_paid": sum(p["amount"] for p in history),
    }
