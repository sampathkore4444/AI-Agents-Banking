"""
Shared SQLite access for the Sathapana KYC agent.

Schema: audit_log (hash-chained, tamper-evident), customers (PII encrypted at
rest), accounts, compliance_cases, approval_requests (HITL workflow),
tool_call_log (idempotency), onboarding_sessions/steps (saga).

All writes go through `transaction()` (BEGIN IMMEDIATE) so a step commits
atomically with its audit entry.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from config import settings
from security import crypto

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    agent       TEXT NOT NULL,
    action      TEXT NOT NULL,
    detail      TEXT,
    status      TEXT NOT NULL DEFAULT 'ok',
    prev_hash   TEXT NOT NULL DEFAULT '',
    entry_hash  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT PRIMARY KEY,
    full_name     TEXT NOT NULL,
    customer_type TEXT NOT NULL DEFAULT 'individual',
    dob           TEXT,
    nationality   TEXT,
    currency      TEXT NOT NULL DEFAULT 'USD',
    kyc_result    TEXT NOT NULL,
    risk_rating   TEXT NOT NULL,
    kyc_case_id   TEXT,
    pii_encrypted TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id   TEXT PRIMARY KEY,
    customer_id  TEXT NOT NULL,
    currency     TEXT NOT NULL,
    account_type TEXT NOT NULL,
    status       TEXT NOT NULL,
    bakong_id    TEXT,
    opened_at    TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS compliance_cases (
    case_id     TEXT PRIMARY KEY,
    customer_id TEXT,
    risk_level  TEXT NOT NULL,
    summary     TEXT NOT NULL,
    flags       TEXT,
    priority    TEXT NOT NULL DEFAULT 'medium',
    status      TEXT NOT NULL DEFAULT 'open',
    assigned_to TEXT,
    decision    TEXT,
    notes       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approval_requests (
    request_id      TEXT PRIMARY KEY,
    tool_name       TEXT NOT NULL,
    arguments       TEXT NOT NULL,
    requested_by    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    requested_at    TEXT NOT NULL,
    decision_deadline TEXT NOT NULL,
    decided_by      TEXT,
    decided_at      TEXT,
    decision        TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS tool_call_log (
    key         TEXT PRIMARY KEY,
    tool_name   TEXT NOT NULL,
    arguments   TEXT NOT NULL,
    result      TEXT NOT NULL,
    ts          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS onboarding_sessions (
    session_id   TEXT PRIMARY KEY,
    customer_key TEXT NOT NULL,
    scenario     TEXT,
    status       TEXT NOT NULL DEFAULT 'new',
    current_step TEXT,
    error        TEXT,
    result       TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS onboarding_steps (
    session_id TEXT NOT NULL,
    step       TEXT NOT NULL,
    status     TEXT NOT NULL,
    output     TEXT,
    ts         TEXT NOT NULL,
    PRIMARY KEY (session_id, step)
);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after the original schema (idempotent)."""
    migrations = [
        ("audit_log", "prev_hash", "TEXT NOT NULL DEFAULT ''"),
        ("audit_log", "entry_hash", "TEXT NOT NULL DEFAULT ''"),
        ("customers", "pii_encrypted", "TEXT"),
    ]
    for table, column, decl in migrations:
        cols = {c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def init_db() -> None:
    """Create/migrate tables. Called once at startup."""
    conn = _connect()
    try:
        conn.executescript(_SCHEMA)
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    """Idempotent create/migrate before schema-dependent reads/writes."""
    init_db()


# ── transactions ───────────────────────────────────────────────────
@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """SQLite transaction (BEGIN IMMEDIATE) with commit/rollback."""
    _ensure_db()
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Audit trail (hash-chained) ─────────────────────────────────────
def json_dumps(obj) -> str:
    return json.dumps(obj or {}, ensure_ascii=False, default=str)


def _entry_payload(ts: str, agent: str, action: str, detail: str, status: str) -> str:
    return f"{ts}|{agent}|{action}|{detail}|{status}"


def log_action(agent: str, action: str, detail: dict | None = None, status: str = "ok", conn: sqlite3.Connection | None = None) -> None:
    """Append a tamper-evident entry to the audit log (PII redacted).

    Pass `conn` when already inside a `db.transaction()` block to avoid
    nested transactions.
    """
    detail_json = json_dumps(crypto.redact_pii(detail))
    ts = utcnow()

    def _write(c: sqlite3.Connection) -> None:
        last = c.execute("SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
        prev_hash = last["entry_hash"] if last else ""
        payload = _entry_payload(ts, agent, action, detail_json, status)
        entry_hash = crypto.chain_hash(prev_hash, payload)
        c.execute(
            "INSERT INTO audit_log (ts, agent, action, detail, status, prev_hash, entry_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, agent, action, detail_json, status, prev_hash, entry_hash),
        )

    if conn is not None:
        _write(conn)
        return
    with transaction() as txn:
        _write(txn)


def last_audit_entries(limit: int = 20) -> list[dict]:
    _ensure_db()
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def verify_audit_chain() -> dict:
    """Walk the audit log and verify the hash chain (tamper detection).

    Returns {'ok', 'rows_checked', 'first_bad_id', 'legacy_rows'}.
    """
    _ensure_db()
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id ASC").fetchall()
    finally:
        conn.close()

    prev_hash = ""
    legacy = 0
    for row in rows:
        entry = dict(row)
        if not entry["entry_hash"]:
            legacy += 1
            continue
        payload = _entry_payload(entry["ts"], entry["agent"], entry["action"], entry["detail"] or "", entry["status"])
        computed = crypto.chain_hash(prev_hash, payload)
        if computed != entry["entry_hash"] or entry["prev_hash"] != prev_hash:
            return {"ok": False, "rows_checked": len(rows), "first_bad_id": entry["id"], "legacy_rows": legacy}
        prev_hash = entry["entry_hash"]
    return {"ok": True, "rows_checked": len(rows), "first_bad_id": None, "legacy_rows": legacy}


# ── idempotency cache ──────────────────────────────────────────────
def get_idempotent(key: str) -> dict | None:
    _ensure_db()
    conn = _connect()
    try:
        row = conn.execute("SELECT result FROM tool_call_log WHERE key = ?", (key,)).fetchone()
        return json.loads(row["result"]) if row else None
    finally:
        conn.close()


def store_idempotent(key: str, tool_name: str, arguments: dict, result: dict) -> None:
    _ensure_db()
    with transaction() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO tool_call_log (key, tool_name, arguments, result, ts) VALUES (?, ?, ?, ?, ?)",
            (key, tool_name, json_dumps(arguments), json_dumps(result), utcnow()),
        )