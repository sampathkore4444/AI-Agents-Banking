"""
Case Management Tool — Fraud case lifecycle management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
CASE_DB: dict[str, dict] = {}


async def create_case(
    customer_id: str,
    case_type: str,
    description: str,
    priority: str = "medium",
    related_transactions: list[str] | None = None,
    related_cards: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new fraud case."""
    case_id = f"CASE-{int(datetime.utcnow().timestamp()) % 10**6:06d}"

    case = {
        "case_id": case_id,
        "customer_id": customer_id,
        "case_type": case_type,
        "description": description,
        "priority": priority,
        "status": "open",
        "stage": "investigation",
        "related_transactions": related_transactions or [],
        "related_cards": related_cards or [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "assigned_to": None,
        "resolution": None,
        "timeline": [
            {"event": "case_created", "timestamp": datetime.utcnow().isoformat(), "details": f"Case created: {description}"}
        ],
    }

    CASE_DB[case_id] = case

    return {
        "case_id": case_id,
        "status": "open",
        "priority": priority,
        "message": f"Fraud case {case_id} created successfully.",
    }


async def update_case(
    case_id: str,
    status: str | None = None,
    stage: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Update a fraud case."""
    case = CASE_DB.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    if status:
        case["status"] = status
    if stage:
        case["stage"] = stage
    if priority:
        case["priority"] = priority
    if assigned_to:
        case["assigned_to"] = assigned_to

    case["updated_at"] = datetime.utcnow().isoformat()

    if notes:
        case["timeline"].append({
            "event": "note_added",
            "timestamp": datetime.utcnow().isoformat(),
            "details": notes,
        })

    return {
        "case_id": case_id,
        "status": case["status"],
        "stage": case["stage"],
        "message": f"Case {case_id} updated.",
    }


async def resolve_case(
    case_id: str,
    resolution: str,
    outcome: str,
    amount_lost: float = 0,
    amount_recovered: float = 0,
    notes: str | None = None,
) -> dict[str, Any]:
    """Resolve a fraud case."""
    case = CASE_DB.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    case["status"] = "closed"
    case["stage"] = "resolved"
    case["resolution"] = {
        "resolution": resolution,
        "outcome": outcome,
        "amount_lost": amount_lost,
        "amount_recovered": amount_recovered,
        "net_loss": amount_lost - amount_recovered,
        "resolved_at": datetime.utcnow().isoformat(),
        "notes": notes,
    }
    case["updated_at"] = datetime.utcnow().isoformat()
    case["timeline"].append({
        "event": "case_resolved",
        "timestamp": datetime.utcnow().isoformat(),
        "details": f"Resolution: {resolution}. Outcome: {outcome}. Loss: ${amount_lost:.2f}, Recovered: ${amount_recovered:.2f}",
    })

    return {
        "case_id": case_id,
        "status": "closed",
        "resolution": case["resolution"],
        "message": f"Case {case_id} resolved. {outcome}.",
    }


async def get_case(case_id: str) -> dict[str, Any]:
    """Get case details."""
    case = CASE_DB.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}
    return case


async def get_cases_by_customer(customer_id: str) -> dict[str, Any]:
    """Get all cases for a customer."""
    cases = [c for c in CASE_DB.values() if c["customer_id"] == customer_id]
    cases.sort(key=lambda x: x["created_at"], reverse=True)
    return {
        "customer_id": customer_id,
        "total_cases": len(cases),
        "open_cases": sum(1 for c in cases if c["status"] == "open"),
        "closed_cases": sum(1 for c in cases if c["status"] == "closed"),
        "total_loss": sum(c.get("resolution", {}).get("amount_lost", 0) for c in cases),
        "total_recovered": sum(c.get("resolution", {}).get("amount_recovered", 0) for c in cases),
        "cases": cases,
    }


async def get_open_cases(priority: str | None = None) -> dict[str, Any]:
    """Get all open cases, optionally filtered by priority."""
    cases = [c for c in CASE_DB.values() if c["status"] == "open"]
    if priority:
        cases = [c for c in cases if c["priority"] == priority]
    cases.sort(key=lambda x: x["created_at"])
    return {
        "total_open": len(cases),
        "critical": sum(1 for c in cases if c["priority"] == "critical"),
        "high": sum(1 for c in cases if c["priority"] == "high"),
        "medium": sum(1 for c in cases if c["priority"] == "medium"),
        "low": sum(1 for c in cases if c["priority"] == "low"),
        "cases": cases,
    }


async def add_evidence(
    case_id: str,
    evidence_type: str,
    description: str,
    data: dict | None = None,
) -> dict[str, Any]:
    """Add evidence to a case."""
    case = CASE_DB.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    if "evidence" not in case:
        case["evidence"] = []

    evidence = {
        "evidence_id": f"EV-{len(case['evidence']) + 1}",
        "type": evidence_type,
        "description": description,
        "data": data,
        "added_at": datetime.utcnow().isoformat(),
    }
    case["evidence"].append(evidence)
    case["updated_at"] = datetime.utcnow().isoformat()

    case["timeline"].append({
        "event": "evidence_added",
        "timestamp": datetime.utcnow().isoformat(),
        "details": f"Evidence added: {evidence_type} - {description}",
    })

    return {
        "case_id": case_id,
        "evidence_id": evidence["evidence_id"],
        "message": f"Evidence {evidence['evidence_id']} added to case {case_id}.",
    }


async def escalate_case(
    case_id: str,
    escalation_reason: str,
    escalate_to: str = "senior_investigator",
) -> dict[str, Any]:
    """Escalate a case to higher authority."""
    case = CASE_DB.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    case["priority"] = "critical"
    case["assigned_to"] = escalate_to
    case["updated_at"] = datetime.utcnow().isoformat()

    case["timeline"].append({
        "event": "escalated",
        "timestamp": datetime.utcnow().isoformat(),
        "details": f"Escalated to {escalate_to}: {escalation_reason}",
    })

    return {
        "case_id": case_id,
        "escalated_to": escalate_to,
        "reason": escalation_reason,
        "message": f"Case {case_id} escalated to {escalate_to}.",
    }


async def get_case_stats() -> dict[str, Any]:
    """Get overall case statistics."""
    cases = list(CASE_DB.values())
    total = len(cases)
    open_cases = [c for c in cases if c["status"] == "open"]
    closed_cases = [c for c in cases if c["status"] == "closed"]

    total_loss = sum(c.get("resolution", {}).get("amount_lost", 0) for c in closed_cases)
    total_recovered = sum(c.get("resolution", {}).get("amount_recovered", 0) for c in closed_cases)

    return {
        "total_cases": total,
        "open_cases": len(open_cases),
        "closed_cases": len(closed_cases),
        "critical_open": sum(1 for c in open_cases if c["priority"] == "critical"),
        "total_loss": total_loss,
        "total_recovered": total_recovered,
        "recovery_rate": f"{(total_recovered/total_loss*100):.1f}%" if total_loss > 0 else "N/A",
    }
