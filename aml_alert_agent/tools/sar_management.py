"""
SAR (Suspicious Activity Report) Management — Creation, Filing, Tracking.

Manages the full SAR lifecycle:
- SAR creation with narrative generation
- Filing via FinCEN BSA E-Filing
- Continuing activity SARs (90-day cycle)
- SAR amendments and withdrawals
- Retention tracking (5 years)
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

# ── In-memory store ───────────────────────────────────────────────
_SARS: dict[str, dict] = {}


async def create_sar(
    customer_id: str,
    customer_name: str,
    customer_ssn_tin: str,
    customer_dob: str,
    customer_address: str,
    suspicious_activity_type: str,
    activity_description: str,
    first_activity_date: str,
    last_activity_date: str,
    amount_involved: float,
    related_account_numbers: list[str] | None = None,
    related_transactions: list[str] | None = None,
    disposition: str = "file_sar",
    filing_type: str = "initial",
    original_sar_id: str | None = None,
) -> dict[str, Any]:
    """Create a SAR with narrative."""
    sar_id = f"SAR-{hashlib.md5(f'{customer_id}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:10].upper()}"

    # Generate narrative
    narrative = _generate_narrative(
        customer_name, customer_ssn_tin, customer_dob, customer_address,
        suspicious_activity_type, activity_description,
        first_activity_date, last_activity_date, amount_involved,
    )

    sar = {
        "sar_id": sar_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "customer_ssn_tin": customer_ssn_tin,
        "customer_dob": customer_dob,
        "customer_address": customer_address,
        "suspicious_activity_type": suspicious_activity_type,
        "activity_description": activity_description,
        "first_activity_date": first_activity_date,
        "last_activity_date": last_activity_date,
        "amount_involved": amount_involved,
        "related_account_numbers": related_account_numbers or [],
        "related_transactions": related_transactions or [],
        "disposition": disposition,
        "narrative": narrative,
        "filing_type": filing_type,
        "original_sar_id": original_sar_id,
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "filing_deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "filing_date": None,
        "fincen_confirmation_number": None,
        "next_continuing_date": None,
        "retention_expires": None,
    }

    _SARS[sar_id] = sar
    return {
        "sar_id": sar_id,
        "status": "draft",
        "filing_deadline": sar["filing_deadline"],
        "narrative_preview": narrative[:500],
    }


async def update_sar(
    sar_id: str,
    activity_description: str | None = None,
    amount_involved: float | None = None,
    related_transactions: list[str] | None = None,
    disposition: str | None = None,
) -> dict[str, Any]:
    """Update SAR details."""
    sar = _SARS.get(sar_id)
    if not sar:
        return {"error": "SAR not found"}

    if activity_description:
        sar["activity_description"] = activity_description
    if amount_involved is not None:
        sar["amount_involved"] = amount_involved
    if related_transactions:
        sar["related_transactions"].extend(related_transactions)
    if disposition:
        sar["disposition"] = disposition

    sar["updated_at"] = datetime.utcnow().isoformat()
    return {"sar_id": sar_id, "status": "updated", "current_status": sar["status"]}


async def file_sar(sar_id: str) -> dict[str, Any]:
    """File SAR electronically via BSA E-Filing (simulated)."""
    sar = _SARS.get(sar_id)
    if not sar:
        return {"error": "SAR not found"}

    if sar["status"] == "filed":
        return {"error": "SAR already filed", "filing_date": sar["filing_date"]}

    # Simulate filing
    confirmation = f"BSA-{hashlib.md5(sar_id.encode()).hexdigest()[:8].upper()}"
    sar["status"] = "filed"
    sar["filing_date"] = datetime.utcnow().isoformat()
    sar["fincen_confirmation_number"] = confirmation
    sar["retention_expires"] = (datetime.utcnow() + timedelta(days=5 * 365)).isoformat()

    # Set first continuing SAR date (90 days)
    sar["next_continuing_date"] = (datetime.utcnow() + timedelta(days=90)).isoformat()

    return {
        "sar_id": sar_id,
        "status": "filed",
        "filing_date": sar["filing_date"],
        "fincen_confirmation_number": confirmation,
        "retention_expires": sar["retention_expires"],
        "next_continuing_date": sar["next_continuing_date"],
        "message": "SAR filed successfully. File continuing activity SAR every 90 days.",
    }


async def create_continuing_sar(original_sar_id: str, activity_update: str) -> dict[str, Any]:
    """Create a continuing activity SAR."""
    original = _SARS.get(original_sar_id)
    if not original:
        return {"error": "Original SAR not found"}

    return await create_sar(
        customer_id=original["customer_id"],
        customer_name=original["customer_name"],
        customer_ssn_tin=original["customer_ssn_tin"],
        customer_dob=original["customer_dob"],
        customer_address=original["customer_address"],
        suspicious_activity_type=original["suspicious_activity_type"],
        activity_description=activity_update,
        first_activity_date=original["first_activity_date"],
        last_activity_date=datetime.utcnow().strftime("%Y-%m-%d"),
        amount_involved=original["amount_involved"],
        related_account_numbers=original["related_account_numbers"],
        related_transactions=original["related_transactions"],
        disposition=original["disposition"],
        filing_type="continuing",
        original_sar_id=original_sar_id,
    )


async def get_sar(sar_id: str) -> dict[str, Any]:
    """Get SAR details."""
    sar = _SARS.get(sar_id)
    if not sar:
        return {"error": "SAR not found"}
    return sar


async def get_sars_by_status(status: str = "all", limit: int = 50) -> dict[str, Any]:
    """Get SARs filtered by status."""
    filtered = [s for s in _SARS.values() if status == "all" or s["status"] == status]
    return {
        "status_filter": status,
        "total": len(filtered),
        "sars": filtered[:limit],
    }


async def get_sar_stats() -> dict[str, Any]:
    """Get SAR filing statistics."""
    all_sars = list(_SARS.values())
    by_status: dict[str, int] = {}
    for s in all_sars:
        status = s["status"]
        by_status[status] = by_status.get(status, 0) + 1

    total_amount = sum(s.get("amount_involved", 0) for s in all_sars)
    overdue = [
        s for s in all_sars
        if s["status"] == "draft"
        and datetime.fromisoformat(s["filing_deadline"]) < datetime.utcnow()
    ]

    return {
        "total_sars": len(all_sars),
        "by_status": by_status,
        "total_amount_involved": total_amount,
        "overdue_filings": len(overdue),
        "draft_sars": by_status.get("draft", 0),
        "filed_sars": by_status.get("filed", 0),
    }


def _generate_narrative(
    name: str, ssn: str, dob: str, address: str,
    activity_type: str, description: str,
    first_date: str, last_date: str, amount: float,
) -> str:
    """Generate a SAR narrative in FinCEN format."""
    return (
        f"NARRATIVE\n\n"
        f"SUSPECT INFORMATION:\n"
        f"Name: {name}\n"
        f"SSN/TIN: {ssn}\n"
        f"Date of Birth: {dob}\n"
        f"Address: {address}\n\n"
        f"SUSPICIOUS ACTIVITY:\n"
        f"Type: {activity_type}\n"
        f"Amount Involved: ${amount:,.2f}\n"
        f"Activity Period: {first_date} to {last_date}\n\n"
        f"DESCRIPTION OF ACTIVITY:\n"
        f"{description}\n\n"
        f"INVESTIGATION FINDINGS:\n"
        f"This SAR was filed based on the suspicious activity identified during "
        f"transaction monitoring and/or customer due diligence. The activity "
        f"pattern is consistent with {activity_type.lower()} typologies as "
        f"defined in BSA/AML guidelines.\n\n"
        f"SUPPORTING DOCUMENTATION:\n"
        f"Transaction records, account statements, and internal investigation "
        f"notes are maintained in the case file and available upon request.\n\n"
        f"DISPOSITION:\n"
        f"Law enforcement referral may be warranted given the nature and scale "
        f"of the suspicious activity."
    )
