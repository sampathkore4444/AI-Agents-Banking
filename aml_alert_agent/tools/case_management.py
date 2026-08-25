"""
AML Case Management — Investigation Workflow.

Manages the full case lifecycle:
- Case creation from alerts
- Investigation tracking
- Evidence collection
- Escalation to compliance/law enforcement
- Resolution and SAR filing
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

# ── In-memory store ───────────────────────────────────────────────
_CASES: dict[str, dict] = {}
_CASE_EVIDENCE: dict[str, list[dict]] = {}


async def create_case(
    customer_id: str,
    customer_name: str,
    case_type: str,
    description: str,
    priority: str = "medium",
    related_alerts: list[str] | None = None,
    related_transactions: list[str] | None = None,
    related_accounts: list[str] | None = None,
    risk_score: float = 0.0,
) -> dict[str, Any]:
    """Create an AML investigation case."""
    case_id = f"AML-{hashlib.md5(f'{customer_id}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:10].upper()}"

    case = {
        "case_id": case_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "case_type": case_type,
        "description": description,
        "priority": priority,
        "risk_score": risk_score,
        "related_alerts": related_alerts or [],
        "related_transactions": related_transactions or [],
        "related_accounts": related_accounts or [],
        "status": "open",
        "stage": "triage",
        "assigned_to": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "sla_deadline": (datetime.utcnow() + timedelta(days=_get_sla_days(priority))).isoformat(),
        "investigation_notes": [],
        "resolution": None,
        "sar_id": None,
    }

    _CASES[case_id] = case
    _CASE_EVIDENCE[case_id] = []

    return {
        "case_id": case_id,
        "status": "open",
        "priority": priority,
        "sla_deadline": case["sla_deadline"],
        "requires_sar_filing": case_type in ("structuring", "layering", "trade_based_ml", "shell_company", "terrorist_financing"),
    }


async def update_case(
    case_id: str,
    status: str | None = None,
    stage: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Update a case."""
    case = _CASES.get(case_id)
    if not case:
        return {"error": "Case not found"}

    if status:
        case["status"] = status
    if stage:
        case["stage"] = stage
    if priority:
        case["priority"] = priority
    if assigned_to:
        case["assigned_to"] = assigned_to
    if notes:
        case["investigation_notes"].append({
            "note": notes,
            "timestamp": datetime.utcnow().isoformat(),
            "author": assigned_to or "system",
        })

    case["updated_at"] = datetime.utcnow().isoformat()
    return {"case_id": case_id, "status": case["status"], "stage": case["stage"]}


async def add_evidence(
    case_id: str,
    evidence_type: str,
    description: str,
    data: dict | None = None,
) -> dict[str, Any]:
    """Add evidence to a case."""
    if case_id not in _CASES:
        return {"error": "Case not found"}

    evidence_id = f"EVD-{hashlib.md5(f'{case_id}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:8].upper()}"
    evidence = {
        "evidence_id": evidence_id,
        "case_id": case_id,
        "evidence_type": evidence_type,
        "description": description,
        "data": data or {},
        "added_at": datetime.utcnow().isoformat(),
        "added_by": "system",
    }

    _CASE_EVIDENCE[case_id].append(evidence)
    return {"evidence_id": evidence_id, "case_id": case_id, "type": evidence_type}


async def escalate_case(
    case_id: str,
    escalation_reason: str,
    escalate_to: str = "senior_compliance_officer",
    escalate_to_law_enforcement: bool = False,
) -> dict[str, Any]:
    """Escalate a case."""
    case = _CASES.get(case_id)
    if not case:
        return {"error": "Case not found"}

    case["stage"] = "escalated"
    case["assigned_to"] = escalate_to
    case["updated_at"] = datetime.utcnow().isoformat()
    case["investigation_notes"].append({
        "note": f"Escalated to {escalate_to}: {escalation_reason}" + (" (law enforcement referral)" if escalate_to_law_enforcement else ""),
        "timestamp": datetime.utcnow().isoformat(),
        "author": "system",
    })

    return {
        "case_id": case_id,
        "escalated_to": escalate_to,
        "law_enforcement_referral": escalate_to_law_enforcement,
        "reason": escalation_reason,
    }


async def resolve_case(
    case_id: str,
    resolution: str,
    outcome: str,
    sar_id: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Resolve an AML case."""
    case = _CASES.get(case_id)
    if not case:
        return {"error": "Case not found"}

    case["status"] = "resolved"
    case["stage"] = "closed"
    case["resolution"] = {
        "resolution_type": resolution,
        "outcome": outcome,
        "sar_id": sar_id,
        "resolved_at": datetime.utcnow().isoformat(),
    }
    case["sar_id"] = sar_id
    case["updated_at"] = datetime.utcnow().isoformat()

    if notes:
        case["investigation_notes"].append({
            "note": notes,
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
        })

    return {
        "case_id": case_id,
        "status": "resolved",
        "resolution": resolution,
        "outcome": outcome,
        "sar_id": sar_id,
    }


async def get_case(case_id: str) -> dict[str, Any]:
    """Get case details."""
    case = _CASES.get(case_id)
    if not case:
        return {"error": "Case not found"}
    evidence = _CASE_EVIDENCE.get(case_id, [])
    return {**case, "evidence": evidence, "evidence_count": len(evidence)}


async def get_cases_by_customer(customer_id: str) -> dict[str, Any]:
    """Get all cases for a customer."""
    cases = [c for c in _CASES.values() if c["customer_id"] == customer_id]
    return {"customer_id": customer_id, "total": len(cases), "cases": cases}


async def get_open_cases(priority: str | None = None) -> dict[str, Any]:
    """Get all open cases."""
    cases = [c for c in _CASES.values() if c["status"] == "open"]
    if priority:
        cases = [c for c in cases if c["priority"] == priority]

    # Sort by SLA deadline
    cases.sort(key=lambda c: c.get("sla_deadline", ""))
    return {"total": len(cases), "cases": cases}


async def get_escalated_cases() -> dict[str, Any]:
    """Get all escalated cases."""
    cases = [c for c in _CASES.values() if c["stage"] == "escalated"]
    return {"total": len(cases), "cases": cases}


async def get_case_stats() -> dict[str, Any]:
    """Get case statistics."""
    all_cases = list(_CASES.values())
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for c in all_cases:
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
        by_type[c["case_type"]] = by_type.get(c["case_type"], 0) + 1

    overdue = [
        c for c in all_cases
        if c["status"] == "open" and datetime.fromisoformat(c["sla_deadline"]) < datetime.utcnow()
    ]

    return {
        "total_cases": len(all_cases),
        "by_status": by_status,
        "by_type": by_type,
        "overdue_cases": len(overdue),
        "cases_with_sar": len([c for c in all_cases if c.get("sar_id")]),
    }


def _get_sla_days(priority: str) -> int:
    sla_map = {"critical": 3, "high": 7, "medium": 30, "low": 60}
    return sla_map.get(priority, 30)
