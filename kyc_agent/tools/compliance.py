"""
Compliance Case Management Tool — MCP tool stub.

In production this would call the bank's compliance/case management system.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory case store for demo purposes
_cases: dict[str, dict] = {}


async def create_compliance_case(
    customer_id: str,
    risk_level: str,
    summary: str,
    flags: list[str] | None = None,
    priority: str = "medium",
) -> dict:
    """
    Create a compliance review case for manual officer review.
    """
    logger.info("Creating compliance case for %s (risk=%s)", customer_id, risk_level)

    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    case = {
        "case_id": case_id,
        "customer_id": customer_id,
        "risk_level": risk_level,
        "summary": summary,
        "flags": flags or [],
        "priority": priority,
        "status": "open",
        "assigned_to": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _cases[case_id] = case
    logger.info("Compliance case created: %s", case_id)
    return case


async def get_compliance_case(case_id: str) -> dict:
    """Retrieve a compliance case by ID."""
    case = _cases.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}
    return case


async def update_compliance_case(
    case_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    decision: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update a compliance case status or assignment."""
    case = _cases.get(case_id)
    if not case:
        return {"error": f"Case {case_id} not found"}

    if status:
        case["status"] = status
    if assigned_to:
        case["assigned_to"] = assigned_to
    if decision:
        case["decision"] = decision
    if notes:
        case["notes"] = notes
    case["updated_at"] = datetime.utcnow().isoformat()

    logger.info("Compliance case %s updated: status=%s", case_id, status)
    return case
