"""
Discrepancy Resolution Tool — MCP tool stub for reconciliation.

Investigates and resolves discrepancies between bank and ledger.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory discrepancy store
_discrepancies: dict[str, dict] = {}


async def identify_discrepancies(
    matched_pairs: list[dict],
    amount_tolerance_pct: float = 0.01,
) -> dict:
    """Analyze matched pairs to identify amount discrepancies."""
    logger.info("Identifying discrepancies in %d matched pairs", len(matched_pairs))

    discrepancies = []
    clean_matches = []

    for pair in matched_pairs:
        bank_amount = float(pair.get("bank_entry", {}).get("amount", 0))
        ledger_amount = float(pair.get("ledger_entry", {}).get("amount", 0))
        diff = abs(bank_amount - ledger_amount)
        diff_pct = diff / max(bank_amount, ledger_amount) if max(bank_amount, ledger_amount) > 0 else 0

        if diff > 0.01 and diff_pct > amount_tolerance_pct:
            disc_id = f"DISC-{uuid.uuid4().hex[:8].upper()}"
            discrepancy = {
                "id": disc_id,
                "type": "amount_mismatch",
                "bank_amount": bank_amount,
                "ledger_amount": ledger_amount,
                "difference": round(diff, 2),
                "difference_pct": round(diff_pct * 100, 2),
                "bank_entry": pair.get("bank_entry"),
                "ledger_entry": pair.get("ledger_entry"),
                "match_id": pair.get("match_id"),
                "status": "identified",
                "identified_at": datetime.utcnow().isoformat(),
            }
            discrepancies.append(discrepancy)
            _discrepancies[disc_id] = discrepancy
        else:
            clean_matches.append(pair)

    return {
        "total_analyzed": len(matched_pairs),
        "clean_matches": len(clean_matches),
        "discrepancies_found": len(discrepancies),
        "total_discrepancy_amount": round(sum(d["difference"] for d in discrepancies), 2),
        "discrepancies": discrepancies,
    }


async def investigate_discrepancy(discrepancy_id: str) -> dict:
    """Investigate a discrepancy and suggest possible causes."""
    disc = _discrepancies.get(discrepancy_id)
    if not disc:
        return {"error": f"Discrepancy {discrepancy_id} not found"}

    diff = disc.get("difference", 0)
    possible_causes = []

    # Common causes based on difference amount
    if diff < 1.00:
        possible_causes.extend([
            "Rounding difference",
            "Currency conversion rounding",
            "Bank fee deduction not recorded",
        ])
    elif diff < 10.00:
        possible_causes.extend([
            "Bank service charge",
            "ACH processing fee",
            "Interest earned/not earned",
            "Small FX conversion difference",
        ])
    elif diff < 100.00:
        possible_causes.extend([
            "Partial payment received",
            "Invoice amount adjusted",
            "Credit memo applied",
            "Tax or withholding difference",
        ])
    else:
        possible_causes.extend([
            "Data entry error",
            "Wrong amount recorded",
            "Duplicate or missing entry",
            "Fraudulent alteration",
            "Intercompany transaction mismatch",
        ])

    # Check if it's a common known pattern
    suggested_actions = [
        "Compare bank statement image to original check/invoice",
        "Verify with counterparty if payment amount matches",
        "Check for bank fees or deductions on statement",
        "Review journal entry supporting documentation",
        "Confirm FX rate used for international transactions",
    ]

    # Determine if write-off is appropriate
    write_off_eligible = diff <= 5.00
    write_off_threshold = 5.00

    return {
        "discrepancy_id": discrepancy_id,
        "difference": diff,
        "possible_causes": possible_causes,
        "suggested_actions": suggested_actions,
        "write_off_eligible": write_off_eligible,
        "write_off_threshold": write_off_threshold,
        "recommended_next_step": suggested_actions[0],
    }


async def resolve_amount_discrepancy(
    discrepancy_id: str,
    resolution_type: str,
    adjusting_amount: float | None = None,
    description: str | None = None,
    approved_by: str | None = None,
) -> dict:
    """
    Resolve an amount discrepancy.

    resolution_type: "adjust_ledger", "write_off", "bank_notification", "no_action"
    """
    disc = _discrepancies.get(discrepancy_id)
    if not disc:
        return {"error": f"Discrepancy {discrepancy_id} not found"}

    disc["status"] = "resolved"
    disc["resolution_type"] = resolution_type
    disc["adjusting_amount"] = adjusting_amount
    disc["resolution_description"] = description
    disc["approved_by"] = approved_by
    disc["resolved_at"] = datetime.utcnow().isoformat()

    # Generate adjusting entry if needed
    adjusting_entry = None
    if resolution_type == "adjust_ledger" and adjusting_amount:
        adjusting_entry = {
            "entry_id": f"ADJ-{uuid.uuid4().hex[:8].upper()}",
            "type": "adjustment",
            "amount": adjusting_amount,
            "description": description or f"Adjustment for {discrepancy_id}",
            "approved_by": approved_by,
        }
        disc["adjusting_entry"] = adjusting_entry
    elif resolution_type == "write_off":
        disc["write_off"] = {
            "amount": disc.get("difference", 0),
            "reason": description,
            "approved_by": approved_by,
            "tax_impact": "May be deductible as business loss",
        }

    logger.info("Discrepancy resolved: %s (type=%s)", discrepancy_id, resolution_type)
    return disc


async def get_discrepancy_report(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Generate a discrepancy report."""
    discrepancies = list(_discrepancies.values())

    if start_date:
        discrepancies = [d for d in discrepancies if d.get("identified_at", "") >= start_date]
    if end_date:
        discrepancies = [d for d in discrepancies if d.get("identified_at", "") <= end_date]

    total = len(discrepancies)
    resolved = len([d for d in discrepancies if d.get("status") == "resolved"])
    open_items = len([d for d in discrepancies if d.get("status") != "resolved"])

    total_amount = sum(d.get("difference", 0) for d in discrepancies)
    resolved_amount = sum(d.get("difference", 0) for d in discrepancies if d.get("status") == "resolved")

    by_resolution = {}
    for d in discrepancies:
        rt = d.get("resolution_type", "pending")
        by_resolution[rt] = by_resolution.get(rt, 0) + 1

    return {
        "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_discrepancies": total,
        "resolved": resolved,
        "open": open_items,
        "resolution_rate": round(resolved / max(total, 1) * 100, 1),
        "total_amount": round(total_amount, 2),
        "resolved_amount": round(resolved_amount, 2),
        "open_amount": round(total_amount - resolved_amount, 2),
        "by_resolution_type": by_resolution,
        "discrepancies": discrepancies,
    }
