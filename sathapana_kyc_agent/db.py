"""
Shared SQLite access for the Sathapana KYC agent.

Provides the database connection and schema creation for audit logging,
customer/account records (simulated core banking), and compliance cases.
All rows carry audit-friendly timestamps so the agent can satisfy NBC
record-keeping expectations.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    agent       TEXT NOT NULL,
    action      TEXT NOT NULL,
    detail      TEXT,
    status      TEXT NOT NULL DEFAULT 'ok'
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name   TEXT NOT NULL,
    customer_type TEXT NOT NULL DEFAULT 'individual',
    dob         TEXT,
    nationality TEXT,
    currency    TEXT NOT NULL DEFAULT 'USD',
    kyc_result  TEXT NOT NULL,
    risk_rating TEXT NOT NULL,
    kyc_case_id TEXT,
    created_at  TEXT NOT NULL
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
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if missing. Called once at startup."""
    conn = _connect()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Audit trail ───────────────────────────────────────────────────
def log_action(agent: str, action: str, detail: dict | None = None, status: str = "ok") -> None:
    """Append an entry to the audit log."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO audit_log (ts, agent, action, detail, status) VALUES (?, ?, ?, ?, ?)",
            (utcnow(), agent, action, json_dumps(detail), status),
        )
        conn.commit()
    finally:
        conn.close()


def json_dumps(obj: dict | None) -> str:
    import json

    return json.dumps(obj or {}, ensure_ascii=False, default=str)


def last_audit_entries(limit: int = 20) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()