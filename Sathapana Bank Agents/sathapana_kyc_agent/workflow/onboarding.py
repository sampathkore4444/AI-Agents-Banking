"""
Onboarding saga (Saga pattern).

A customer's onboarding is a choreographed sequence of tool steps. Each step
is (a) persisted in `onboarding_steps` with a compact composite key, (b)
executed idempotently (`idempotency_key = "session:step"` so replays never
duplicate side effects), and (c) audited. On any step failure the session is
compensated (marked aborted + audit trail, pending approvals auto-rejected);
a session can always be resumed because already-executed steps are skipped.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Callable

import db
from config import settings
from tools import get_registry
from workflow.approvals import build_approval_workflow

APPROVAL_TOOLS = {"create_customer_profile", "open_account", "update_case"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OnboardingSaga:
    def __init__(self, registry=None, approvals=None) -> None:
        self.registry = registry or get_registry()
        self.approvals = approvals or build_approval_workflow(officer_id=settings.default_officer_id)

    # ── session lifecycle ─────────────────────────────────────────
    def start(self, scenario: str = "", customer_key: str = "") -> dict:
        db.init_db()
        session_id = f"OB-{uuid.uuid4().hex[:8].upper()}"
        created_at = _now()
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO onboarding_sessions (session_id, customer_key, scenario, status, created_at, updated_at) VALUES (?, ?, ?, 'new', ?, ?)",
                (session_id, customer_key, scenario, created_at, created_at),
            )
            db.log_action("onboarding", "start", {"session_id": session_id, "scenario": scenario}, "ok", conn=conn)
        return self.get(session_id)

    def get(self, session_id: str) -> dict:
        db.init_db()
        conn = db._connect()
        try:
            session = conn.execute("SELECT * FROM onboarding_sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not session:
                return {"error": f"Onboarding session {session_id} not found"}
            steps = conn.execute(
                "SELECT step, status, output, ts FROM onboarding_steps WHERE session_id = ? ORDER BY ts ASC", (session_id,)
            ).fetchall()
            result = dict(session)
            result["steps"] = [dict(s) for s in steps]
            return result
        finally:
            conn.close()

    # ── step execution ────────────────────────────────────────────
    def _execute_tool(self, tool: str, arguments: dict, idempotency_key: str) -> dict:
        if tool in APPROVAL_TOOLS:
            request = self.approvals.submit(tool, arguments, requested_by="saga")
            decision = self.approvals.decide(
                request["request_id"], "approved", decided_by=self.approvals.officer_id, notes="saga auto-approval", executor=self.registry.invoke
            )
            if "error" in decision:
                return decision
            if decision.get("replayed"):
                return {"replayed": True, "result": decision.get("result")}
            return decision.get("result", decision)
        return self.registry.invoke(tool, arguments, idempotency_key)

    def run(self, session_id: str, steps: list[tuple[str, dict]]) -> dict:
        """Execute ordered steps [(tool_name, arguments), ...] with compensation.

        Plain-step convenience wrapper over `run_functional`.
        """
        functional = [(f"step_{i:02d}_{tool}", (tool, arguments)) for i, (tool, arguments) in enumerate(steps)]
        return self.run_functional(session_id, functional)

    def run_functional(self, session_id: str, steps: list[tuple[str, dict | Callable]]) -> dict:
        """Execute ordered steps with compensation.

        Each entry is (step_name, builder) where builder maps previously
        computed step outputs (by step_name) to (tool_name, arguments). This
        lets generated ids (customer_id, account_id) flow between steps.
        """
        db.init_db()
        session = self.get(session_id)
        if "session_id" not in session:
            return session
        if session["status"] == "complete":
            return session

        outputs: dict[str, dict] = {}
        executed = {s["step"] for s in session["steps"] if s["status"] == "executed"}
        for s in session["steps"]:
            if s["status"] != "failed":
                try:
                    outputs[s["step"]] = json.loads(s["output"] or "{}")
                except Exception:  # noqa: BLE001
                    outputs[s["step"]] = {}

        for idx, (step_name, step_spec) in enumerate(steps):
            if step_name in executed:
                continue
            try:
                if callable(step_spec):
                    tool, arguments = step_spec(outputs)
                else:
                    tool, arguments = step_spec
                step_key = f"{idx:02d}_{step_name}"
                result = self._execute_tool(tool, arguments, f"{session_id}:{step_key}")
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(str(result["error"]))
                outputs[step_name] = result
                with db.transaction() as c:
                    c.execute(
                        "INSERT OR REPLACE INTO onboarding_steps (session_id, step, status, output, ts) VALUES (?, ?, 'executed', ?, ?)",
                        (session_id, step_name, db.json_dumps(result), _now()),
                    )
                    db.log_action("onboarding", "step_ok", {"session_id": session_id, "step": step_name, "tool": tool}, "ok", conn=c)
            except Exception as exc:  # noqa: BLE001 - saga compensation path
                return self.compensate(session_id, step_name, str(exc))

        with db.transaction() as conn:
            conn.execute(
                "UPDATE onboarding_sessions SET status = 'complete', current_step = NULL, error = NULL, updated_at = ? WHERE session_id = ?",
                (_now(), session_id),
            )
            db.log_action("onboarding", "complete", {"session_id": session_id}, "ok", conn=conn)
        return self.get(session_id)

    def compensate(self, session_id: str, failed_step: str, error: str) -> dict:
        """Roll back state visible to the outside: mark aborted, reject pending approvals."""
        with db.transaction() as conn:
            now = _now()
            conn.execute(
                "UPDATE onboarding_sessions SET status = 'aborted', current_step = ?, error = ?, updated_at = ? WHERE session_id = ?",
                (failed_step, error[:500], now, session_id),
            )
            conn.execute(
                "INSERT OR REPLACE INTO onboarding_steps (session_id, step, status, output, ts) VALUES (?, ?, 'failed', ?, ?)",
                (session_id, failed_step, db.json_dumps({"error": error}), now),
            )
            db.log_action("onboarding", "compensate", {"session_id": session_id, "failed_step": failed_step, "error": error[:500]}, "error", conn=conn)
        pending = self.approvals.pending(limit=100)
        for request in pending:
            self.approvals.decide(request["request_id"], "rejected", decided_by="system/saga", notes=f"session {session_id} compensated", executor=None)
        return self.get(session_id)

    def recent(self, limit: int = 20) -> list[dict]:
        db.init_db()
        conn = db._connect()
        try:
            rows = conn.execute("SELECT * FROM onboarding_sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def build_saga(registry=None, approvals=None) -> OnboardingSaga:
    return OnboardingSaga(registry=registry, approvals=approvals)