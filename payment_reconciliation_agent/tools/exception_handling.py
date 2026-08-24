"""
Exception Handling Tool — MCP tool stub for reconciliation.

Manages unmatched items, discrepancies, and exception queues.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory exception store
_exceptions: dict[str, dict] = {}

# Seed sample exceptions
def _seed_exceptions():
    exceptions = [
        {
            "id": "EXC-001",
            "type": "unmatched_bank_entry",
            "severity": "high",
            "bank_entry_id": "BNK-007",
            "amount": 12000.00,
            "date": "2026-01-21",
            "description": "Check deposit with altered amount — possible fraud",
            "status": "open",
            "assigned_to": "analyst_001",
            "created_at": "2026-01-21T10:30:00",
            "aging_days": 3,
            "root_cause": None,
            "resolution": None,
        },
        {
            "id": "EXC-002",
            "type": "amount_discrepancy",
            "severity": "medium",
            "bank_entry_id": "BNK-005",
            "ledger_entry_id": "LED-005",
            "bank_amount": 3749.00,
            "ledger_amount": 3750.00,
            "discrepancy": 1.00,
            "date": "2026-01-19",
            "description": "Amount mismatch — $1.00 difference on ACH credit",
            "status": "open",
            "assigned_to": "analyst_002",
            "created_at": "2026-01-19T14:15:00",
            "aging_days": 5,
            "root_cause": None,
            "resolution": None,
        },
        {
            "id": "EXC-003",
            "type": "timing_difference",
            "severity": "low",
            "bank_entry_id": None,
            "ledger_entry_id": "LED-006",
            "amount": 5000.00,
            "date": "2026-01-20",
            "description": "Wire transfer booked in ledger but not yet settled in bank",
            "status": "monitoring",
            "assigned_to": "analyst_001",
            "created_at": "2026-01-20T09:00:00",
            "aging_days": 4,
            "expected_resolution_date": "2026-01-22",
            "root_cause": "timing",
            "resolution": "Pending bank settlement",
        },
    ]
    for e in exceptions:
        _exceptions[e["id"]] = e

_seed_exceptions()


async def create_exception(
    exception_type: str,
    severity: str,
    amount: float,
    date: str,
    description: str,
    bank_entry_id: str | None = None,
    ledger_entry_id: str | None = None,
    assigned_to: str | None = None,
) -> dict:
    """Create a new exception item."""
    exc_id = f"EXC-{uuid.uuid4().hex[:8].upper()}"

    exception = {
        "id": exc_id,
        "type": exception_type,
        "severity": severity,
        "bank_entry_id": bank_entry_id,
        "ledger_entry_id": ledger_entry_id,
        "amount": round(amount, 2),
        "date": date,
        "description": description,
        "status": "open",
        "assigned_to": assigned_to,
        "created_at": datetime.utcnow().isoformat(),
        "aging_days": 0,
        "root_cause": None,
        "resolution": None,
    }

    _exceptions[exc_id] = exception
    logger.info("Exception created: %s (type=%s, severity=%s)", exc_id, exception_type, severity)
    return exception


async def get_exception(exception_id: str) -> dict:
    """Get details of an exception item."""
    exc = _exceptions.get(exception_id)
    if not exc:
        return {"error": f"Exception {exception_id} not found"}
    return exc


async def get_exception_queue(
    status: str | None = None,
    severity: str | None = None,
    exception_type: str | None = None,
    assigned_to: str | None = None,
    limit: int = 50,
) -> dict:
    """Get exception queue with optional filters."""
    exceptions = list(_exceptions.values())

    if status:
        exceptions = [e for e in exceptions if e.get("status") == status]
    if severity:
        exceptions = [e for e in exceptions if e.get("severity") == severity]
    if exception_type:
        exceptions = [e for e in exceptions if e.get("type") == exception_type]
    if assigned_to:
        exceptions = [e for e in exceptions if e.get("assigned_to") == assigned_to]

    # Calculate aging
    for exc in exceptions:
        created = datetime.fromisoformat(exc.get("created_at", datetime.utcnow().isoformat()))
        exc["aging_days"] = (datetime.utcnow() - created).days

    exceptions.sort(key=lambda x: x.get("aging_days", 0), reverse=True)

    # Summary stats
    total = len(exceptions)
    by_severity = {}
    by_type = {}
    by_status = {}
    for e in exceptions:
        sev = e.get("severity", "unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        typ = e.get("type", "unknown")
        by_type[typ] = by_type.get(typ, 0) + 1
        stat = e.get("status", "unknown")
        by_status[stat] = by_status.get(stat, 0) + 1

    return {
        "total_exceptions": total,
        "exceptions": exceptions[:limit],
        "summary": {
            "by_severity": by_severity,
            "by_type": by_type,
            "by_status": by_status,
            "total_amount": round(sum(e.get("amount", 0) for e in exceptions), 2),
            "oldest_aging_days": max((e.get("aging_days", 0) for e in exceptions), default=0),
        },
    }


async def resolve_exception(
    exception_id: str,
    resolution: str,
    root_cause: str,
    adjusting_entry_id: str | None = None,
    notes: str | None = None,
) -> dict:
    """Resolve an exception item."""
    exc = _exceptions.get(exception_id)
    if not exc:
        return {"error": f"Exception {exception_id} not found"}

    exc["status"] = "resolved"
    exc["resolution"] = resolution
    exc["root_cause"] = root_cause
    exc["adjusting_entry_id"] = adjusting_entry_id
    exc["notes"] = notes
    exc["resolved_at"] = datetime.utcnow().isoformat()

    logger.info("Exception resolved: %s (root_cause=%s)", exception_id, root_cause)
    return exc


async def escalate_exception(
    exception_id: str,
    escalate_to: str,
    reason: str,
) -> dict:
    """Escalate an exception to a higher authority."""
    exc = _exceptions.get(exception_id)
    if not exc:
        return {"error": f"Exception {exception_id} not found"}

    exc["status"] = "escalated"
    exc["escalated_to"] = escalate_to
    exc["escalation_reason"] = reason
    exc["escalated_at"] = datetime.utcnow().isoformat()

    logger.info("Exception escalated: %s → %s", exception_id, escalate_to)
    return exc


async def get_exception_aging_report() -> dict:
    """Generate an aging report for all open exceptions."""
    open_exceptions = [e for e in _exceptions.values() if e.get("status") in ("open", "monitoring")]

    aging_buckets = {
        "0-3_days": {"count": 0, "amount": 0.0},
        "4-7_days": {"count": 0, "amount": 0.0},
        "8-14_days": {"count": 0, "amount": 0.0},
        "15-30_days": {"count": 0, "amount": 0.0},
        "31+_days": {"count": 0, "amount": 0.0},
    }

    for exc in open_exceptions:
        created = datetime.fromisoformat(exc.get("created_at", datetime.utcnow().isoformat()))
        aging = (datetime.utcnow() - created).days
        amount = exc.get("amount", 0)

        if aging <= 3:
            bucket = "0-3_days"
        elif aging <= 7:
            bucket = "4-7_days"
        elif aging <= 14:
            bucket = "8-14_days"
        elif aging <= 30:
            bucket = "15-30_days"
        else:
            bucket = "31+_days"

        aging_buckets[bucket]["count"] += 1
        aging_buckets[bucket]["amount"] = round(aging_buckets[bucket]["amount"] + amount, 2)

    return {
        "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_open_exceptions": len(open_exceptions),
        "total_open_amount": round(sum(e.get("amount", 0) for e in open_exceptions), 2),
        "aging_buckets": aging_buckets,
        "escalation_needed": [e for e in open_exceptions if e.get("aging_days", 0) > 7],
    }
