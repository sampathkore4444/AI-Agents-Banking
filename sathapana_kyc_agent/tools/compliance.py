"""
Compliance Case Management Tool — MCP tool stub with SQLite persistence.

In production this calls the bank's compliance/case management system.
Cases flagged as suspicious can be marked for STR reporting to CAMFIU.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_compliance_case(
    customer_id: str,
    risk_level: str,
    summary: str,
    flags: list[str] | None = None,
    priority: str = "medium",
    file_str_to_camfiu: bool = False,
) -> dict:
    """Create a compliance review case for manual officer review."""
    db.init_db()
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    flags = flags or []
    created_at = _now()
    conn = db._connect()
    try:
        conn.execute(
            "INSERT INTO compliance_cases (case_id, customer_id, risk_level, summary, flags, priority, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (case_id, customer_id, risk_level, summary, json.dumps(flags), priority, "open", created_at, created_at),
        )
        conn.commit()
        db.log_action("compliance", "create_compliance_case", {"case_id": case_id, "risk_level": risk_level, "str_to_camfiu": file_str_to_camfiu})
    finally:
        conn.close()

    case = get_compliance_case(case_id)
    if file_str_to_camfiu:
        case["str_filed_camfiu"] = _file_str_to_camfiu(case_id, summary, flags)
    return case


def _file_str_to_camfiu(case_id: str, summary: str, flags: list[str]) -> dict:
    """Simulated filing of a Suspicious Transaction Report to CAMFIU."""
    db.log_action("compliance", "file_str_camfiu", {"case_id": case_id, "flags": flags}, "ok")
    return {
        "str_reference": f"STR-{uuid.uuid4().hex[:10].upper()}",
        "authority": "Cambodia Financial Intelligence Unit (CAMFIU)",
        "submitted_at": _now(),
        "summary": summary,
    }


def get_compliance_case(case_id: str) -> dict:
    """Retrieve a compliance case by ID."""
    db.init_db()
    conn = db._connect()
    try:
        row = conn.execute("SELECT * FROM compliance_cases WHERE case_id = ?", (case_id,)).fetchone()
        return dict(row) if row else {"error": f"Case {case_id} not found"}
    finally:
        conn.close()


def update_compliance_case(
    case_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    decision: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update a compliance case: status, assignment, decision, notes."""
    db.init_db()
    conn = db._connect()
    try:
        row = conn.execute("SELECT * FROM compliance_cases WHERE case_id = ?", (case_id,)).fetchone()
        if not row:
            return {"error": f"Case {case_id} not found"}
        current = dict(row)
        new_status = status or current["status"]
        conn.execute(
            "UPDATE compliance_cases SET status = ?, assigned_to = ?, decision = ?, notes = ?, updated_at = ? WHERE case_id = ?",
            (
                new_status,
                assigned_to or current["assigned_to"],
                decision or current["decision"],
                notes or current["notes"],
                _now(),
                case_id,
            ),
        )
        conn.commit()
        db.log_action("compliance", "update_compliance_case", {"case_id": case_id, "status": new_status, "decision": decision})
    finally:
        conn.close()
    return get_compliance_case(case_id)