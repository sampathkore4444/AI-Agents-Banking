"""
Accounting System Integration Tool — MCP tool stub for reconciliation.

Handles GL integration, adjusting entry posting, and financial reporting.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory adjustment store
_adjustments: list[dict] = []


async def post_adjusting_entry(
    account_number: str,
    amount: float,
    adjustment_type: str,
    description: str,
    reference: str,
    supporting_document: str | None = None,
    approved_by: str | None = None,
) -> dict:
    """
    Post an adjusting journal entry to the GL.

    adjustment_type: "bank_fee", "fx_adjustment", "timing_difference", "error_correction", "write_off"
    """
    logger.info("Posting adjusting entry: account=%s, amount=$%.2f, type=%s", account_number, amount, adjustment_type)

    entry_id = f"ADJ-{uuid.uuid4().hex[:8].upper()}"

    entry = {
        "entry_id": entry_id,
        "account_number": account_number,
        "amount": round(amount, 2),
        "adjustment_type": adjustment_type,
        "description": description,
        "reference": reference,
        "supporting_document": supporting_document,
        "approved_by": approved_by,
        "status": "posted",
        "posted_at": datetime.utcnow().isoformat(),
        "period": datetime.utcnow().strftime("%Y-%m"),
    }

    _adjustments.append(entry)
    logger.info("Adjusting entry posted: %s", entry_id)
    return entry


async def get_adjustments(
    account_number: str | None = None,
    period: str | None = None,
    adjustment_type: str | None = None,
) -> dict:
    """Get posted adjusting entries."""
    entries = list(_adjustments)

    if account_number:
        entries = [e for e in entries if e.get("account_number") == account_number]
    if period:
        entries = [e for e in entries if e.get("period") == period]
    if adjustment_type:
        entries = [e for e in entries if e.get("adjustment_type") == adjustment_type]

    total_amount = sum(e.get("amount", 0) for e in entries)

    return {
        "total_adjustments": len(entries),
        "total_amount": round(total_amount, 2),
        "entries": entries,
    }


async def generate_reconciliation_report(
    account_number: str,
    period: str,
) -> dict:
    """Generate a formal reconciliation report for a period."""
    report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
    period_adjustments = [a for a in _adjustments if a.get("period") == period]

    report = {
        "report_id": report_id,
        "account_number": account_number,
        "period": period,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "bank_balance": 150000.00,
            "ledger_balance": 149750.00,
            "reconciling_items": 250.00,
            "adjusted_ledger_balance": 150000.00,
            "reconciled": True,
        },
        "reconciling_items": [
            {"description": "Outstanding checks", "amount": -500.00},
            {"description": "Deposits in transit", "amount": 250.00},
            {"description": "Bank fees not recorded", "amount": -250.00},
            {"description": "Interest earned", "amount": 250.00},
        ],
        "adjustments": period_adjustments,
        "sign_off": {
            "prepared_by": "Reconciliation Analyst",
            "reviewed_by": "Finance Manager",
            "status": "pending_review",
        },
    }

    return report


async def check_gl_sync_status(account_number: str) -> dict:
    """Check if GL is in sync with reconciliation."""
    return {
        "account_number": account_number,
        "last_sync": datetime.utcnow().isoformat(),
        "sync_status": "in_sync",
        "pending_entries": 0,
        "reconciliation_status": "complete",
    }
