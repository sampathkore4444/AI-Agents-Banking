"""
Human-in-the-loop approval workflow, DB-backed with SLA enforcement.

Every high-risk tool call becomes an `approval_requests` row with a decision
deadline (`decision_deadline` = requested_at + SLA). Officers (or an
integrating system) decide; overdue requests are auto-decided. Approvals are
recorded as audit entries and refused/replayed actions are idempotent via
`tool_call_log` so a retried decision never double-executes a side effect.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import db
from config import settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deadline(sla_seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=sla_seconds)).isoformat()


class ApprovalWorkflow:
    """Submit/decide lifecycle for high-risk KYC tool calls."""

    def __init__(self, officer_id: str | None = None, sla_seconds: int | None = None) -> None:
        self.officer_id = officer_id or settings.default_officer_id
        self.sla_seconds = sla_seconds if sla_seconds is not None else settings.approval_sla_seconds

    def submit(self, tool_name: str, arguments: dict, requested_by: str = "agent") -> dict:
        """Register a pending approval request; reuses an identical pending one."""
        db.init_db()
        args_json = db.json_dumps(arguments)
        with db.transaction() as conn:
            existing = conn.execute(
                "SELECT * FROM approval_requests WHERE tool_name = ? AND arguments = ? AND status = 'pending' ORDER BY requested_at DESC LIMIT 1",
                (tool_name, args_json),
            ).fetchone()
            if existing:
                return dict(existing)
            request_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
            requested_at = _now()
            conn.execute(
                "INSERT INTO approval_requests (request_id, tool_name, arguments, requested_by, status, requested_at, decision_deadline) "
                "VALUES (?, ?, ?, ?, 'pending', ?, ?)",
                (request_id, tool_name, args_json, requested_by, requested_at, _deadline(self.sla_seconds)),
            )
            db.log_action("approvals", "submit", {"request_id": request_id, "tool": tool_name, "sla_seconds": self.sla_seconds}, "ok", conn=conn)
        return self.get(request_id)

    def decide(
        self,
        request_id: str,
        decision: str,
        decided_by: str | None = None,
        notes: str = "",
        executor: Callable[[str, dict, str | None], dict] | None = None,
    ) -> dict:
        """Decide a request. On 'approved' runs the recorded tool via `executor`.

        executor(name, arguments, idempotency_key) runs the tool exactly once;
        pass `registry.invoke` from the calling layer.
        """
        db.init_db()
        decision = decision.lower()
        if decision not in ("approved", "approved_with_conditions", "rejected"):
            return {"error": f"decision must be approved / approved_with_conditions / rejected, got {decision}"}

        with db.transaction() as conn:
            row = conn.execute("SELECT * FROM approval_requests WHERE request_id = ?", (request_id,)).fetchone()
            if not row:
                return {"error": f"Approval request {request_id} not found"}
            if row["status"] != "pending":
                return {"error": f"Request already decided ({row['status']})", "request_id": request_id}

            arguments = json.loads(row["arguments"])
            decided_by = decided_by or self.officer_id
            conn.execute(
                "UPDATE approval_requests SET status = 'decided', decision = ?, decided_by = ?, decided_at = ?, notes = ? WHERE request_id = ?",
                (decision, decided_by, _now(), notes, request_id),
            )
            db.log_action(
                "approvals",
                "decide",
                {"request_id": request_id, "tool": row["tool_name"], "decision": decision, "decided_by": decided_by, "notes": notes, "sla_seconds": self.sla_seconds},
                "ok",
                conn=conn,
            )

        result: dict = {}
        ran = False
        if decision in ("approved", "approved_with_conditions"):
            if executor is None:
                result = {"executed": False, "message": "approved (no executor bound)"}
            else:
                ran = True
                idem = f"approval:{request_id}"
                raw = executor(row["tool_name"], arguments, idem)
                if isinstance(raw, dict) and "idempotent_replay" in raw:
                    result = {"replayed": True, "result": raw.get("result"), "message": f"{row['tool_name']} already executed (idempotent replay)"}
                else:
                    result = {"replayed": False, "result": raw}
        else:
            result = {"executed": False, "message": f"Rejected by {decided_by}"}

        return {
            "request_id": request_id,
            "tool": row["tool_name"],
            "decision": decision,
            "decided_by": decided_by,
            "decided_at": _now(),
            "executed": ran,
            **result,
        }

    def get(self, request_id: str) -> dict:
        db.init_db()
        conn = db._connect()
        try:
            row = conn.execute("SELECT * FROM approval_requests WHERE request_id = ?", (request_id,)).fetchone()
            if not row:
                return {"error": f"Approval request {request_id} not found"}
            return dict(row)
        finally:
            conn.close()

    def pending(self, limit: int = 50) -> list[dict]:
        db.init_db()
        conn = db._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM approval_requests WHERE status = 'pending' ORDER BY decision_deadline ASC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def expire_overdue(self, executor: Callable[[str, dict, str | None], dict] | None = None) -> list[dict]:
        """Auto-decide overdue requests (SLA breached) with an audit trail."""
        db.init_db()
        conn = db._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM approval_requests WHERE status = 'pending' AND decision_deadline < ?", (_now(),)
            ).fetchall()
        finally:
            conn.close()

        results = []
        for row in rows:
            decision = {"create_customer_profile": "approved", "open_account": "approved", "update_case": "approved_with_conditions"}.get(
                row["tool_name"], "approved"
            )
            summary = self.decide(row["request_id"], decision, decided_by="system/sla", notes="auto-decided past SLA", executor=executor)
            summary["sla_expired"] = True
            results.append(summary)
        for r in results:
            db.log_action("approvals", "sla_expire", {"request_id": r.get("request_id"), "decision": r.get("decision")}, "ok")
        return results


def build_approval_workflow(officer_id: str | None = None, sla_seconds: int | None = None) -> ApprovalWorkflow:
    return ApprovalWorkflow(officer_id=officer_id, sla_seconds=sla_seconds)