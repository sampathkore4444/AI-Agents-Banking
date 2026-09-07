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
from config import settings
from integrations import get_providers
from integrations.camfiu import build_str_record


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_compliance_case(
    customer_id: str,
    risk_level: str,
    summary: str,
    flags: list[str] | None = None,
    priority: str = "medium",
    file_str_to_camfiu: bool = False,
    customer_pii: dict | None = None,
) -> dict:
    """Create a compliance review case for manual officer review.

    customer_pii (optional) supplies the identity for STR filing when the
    applicant was declined before a customer row existed.
    """
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
        case["str_filed_camfiu"] = _file_str_to_camfiu(case_id, summary, flags, customer=customer_pii)
    return case


def _file_str_to_camfiu(case_id: str, summary: str, flags: list[str], customer: dict | None = None) -> dict:
    """Build + validate an STR and transmit it to CAMFIU via the configured provider.

    Returns the STR reference and validation summary, or a validation_error
    listing missing mandatory fields (nothing is filed when invalid).
    """
    if customer is None:
        customer = db_customer_pii(case_id)
    record, info = build_str_record(
        {"case_id": case_id, "summary": summary, "flags": flags, "risk_level": "high", "bank_name": "Sathapana Bank PLC"},
        customer,
        agent_id="sathapana-kyc-agent",
    )
    if record is None:
        db.log_action("compliance", "file_str_camfiu_rejected", info, status="error")
        return info

    result = get_providers().camfiu.file(record)
    db.log_action("compliance", "file_str_camfiu", {"case_id": case_id, "str_reference": result.get("str_reference"), "flags": flags, "validation": "passed"}, "ok")
    result.setdefault("validation", "passed")
    return result


def db_customer_pii(case_id: str) -> dict | None:
    """Resolve the customer PII tied to a compliance case (for STR narrative)."""
    from tools import core_banking

    conn = db._connect()
    try:
        row = conn.execute("SELECT customer_id FROM compliance_cases WHERE case_id = ?", (case_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return core_banking.get_customer_pii(row["customer_id"])


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