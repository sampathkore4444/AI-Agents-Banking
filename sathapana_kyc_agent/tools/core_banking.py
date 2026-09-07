"""
Core Banking Tool — MCP tool stub with SQLite persistence.

PII is encrypted at rest (`customers.pii_encrypted`, Fernet) and decrypted on
read. Only de-identified fields (risk_rating, currency, kyc_result, type)
remain in plaintext indexable columns. In production this calls Sathapana's
core banking system (Temenos/OLB); the identifiers are the same.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import db
from security import crypto

ALLOWED_CURRENCIES = ("USD", "KHR")

ACC_ACCOUNT_TYPES = ("retail_savings", "current", "sme_loan", "corporate")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_customer_pii(customer_id: str) -> dict | None:
    """Return decrypted PII for a customer, or None if unknown."""
    conn = db._connect()
    try:
        row = conn.execute("SELECT pii_encrypted FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
    finally:
        conn.close()
    if not row or not row["pii_encrypted"]:
        return None
    try:
        return json.loads(crypto.decrypt(row["pii_encrypted"]))
    except Exception:  # noqa: BLE001 — treat unreadable PII as unknown
        return None


def _pii_blob(personal_info: dict, address: dict) -> str:
    pii = {
        "full_name": personal_info.get("full_name") or personal_info.get("full_name_latin", "Unknown"),
        "dob": personal_info.get("date_of_birth") or personal_info.get("dob"),
        "nationality": personal_info.get("nationality", "KH"),
        "address": {k: v for k, v in (address or {}).items() if v},
    }
    return crypto.encrypt(json.dumps(pii, ensure_ascii=False))


def lookup_customer(identifier: str, query_type: str = "customer_lookup") -> dict:
    """Look up customer or account information in the core banking system."""
    db.init_db()
    conn = db._connect()
    try:
        if query_type == "customer_lookup":
            row = conn.execute("SELECT * FROM customers WHERE customer_id = ?", (identifier,)).fetchone()
            if not row:
                return {"customer_id": f"CUST-{uuid.uuid4().hex[:8].upper()}", "name": f"Prospective {crypto.mask(identifier)}", "status": "prospective", "kyc_status": "pending", "account_count": 0}
            pii = get_customer_pii(row["customer_id"]) or {"full_name": row["full_name"]}
            return {"customer_id": row["customer_id"], "name": pii.get("full_name"), "status": row["kyc_result"], "kyc_status": row["kyc_result"], "risk_rating": row["risk_rating"], "currency": row["currency"], "customer_type": row["customer_type"], "account_count": 0, "pii": pii}
        if query_type == "account_status":
            row = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (identifier,)).fetchone()
            if not row:
                return {"error": f"Account {identifier} not found"}
            return {"account_id": row["account_id"], "customer_id": row["customer_id"], "currency": row["currency"], "account_type": row["account_type"], "status": row["status"], "bakong_id": row["bakong_id"], "opened_at": row["opened_at"]}
        return {"error": f"Unknown query_type: {query_type}. Supported: customer_lookup, account_status"}
    finally:
        conn.close()


def create_customer_profile(
    personal_info: dict,
    address: dict,
    kyc_result: str,
    risk_rating: str,
    currency: str = "USD",
    customer_type: str = "individual",
    documents_verified: list[str] | None = None,
    kyc_case_id: str | None = None,
) -> dict:
    """Create a customer profile after successful KYC (PII encrypted at rest)."""
    db.init_db()
    if currency not in ALLOWED_CURRENCIES:
        return {"error": f"Currency must be one of {ALLOWED_CURRENCIES}"}
    if kyc_result not in ("approved", "approved_with_conditions", "rejected"):
        return {"error": "kyc_result must be approved / approved_with_conditions / rejected"}

    customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
    created_at = _now()
    pii_encrypted = _pii_blob(personal_info, address)
    pseudonym = "tk:" + crypto.tokenize((personal_info.get("full_name") or personal_info.get("full_name_latin", "Unknown")))

    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO customers (customer_id, full_name, customer_type, dob, nationality, currency, kyc_result, risk_rating, kyc_case_id, pii_encrypted, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                customer_id,
                pseudonym,
                customer_type,
                None,
                None,
                currency,
                kyc_result,
                risk_rating,
                kyc_case_id,
                pii_encrypted,
                created_at,
            ),
        )
        db.log_action("core_banking", "create_customer_profile", {"customer_id": customer_id, "kyc_result": kyc_result, "risk_rating": risk_rating}, "ok", conn=conn)

    return {
        "customer_id": customer_id,
        "status": "active" if kyc_result == "approved" else "approved_with_conditions" if kyc_result == "approved_with_conditions" else "rejected",
        "currency": currency,
        "risk_rating": risk_rating,
        "documents_verified": documents_verified or [],
        "pii_encrypted_at_rest": True,
        "created_at": created_at,
    }


def open_account(
    customer_id: str,
    account_type: str = "retail_savings",
    currency: str = "USD",
) -> dict:
    """Open an account for an approved customer."""
    db.init_db()
    if account_type not in ACC_ACCOUNT_TYPES:
        return {"error": f"account_type must be one of {ACC_ACCOUNT_TYPES}"}
    if currency not in ALLOWED_CURRENCIES:
        return {"error": f"Currency must be one of {ALLOWED_CURRENCIES}"}

    with db.transaction() as conn:
        cust = conn.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
        if not cust:
            return {"error": f"Customer {customer_id} not found"}
        if cust["kyc_result"] == "rejected":
            return {"error": "Cannot open account for a rejected customer"}
        account_id = f"ACC-{uuid.uuid4().hex[:10].upper()}"
        conn.execute(
            "INSERT INTO accounts (account_id, customer_id, currency, account_type, status, opened_at) VALUES (?, ?, ?, ?, ?, ?)",
            (account_id, customer_id, currency, account_type, "active", _now()),
        )
        db.log_action("core_banking", "open_account", {"account_id": account_id, "customer_id": customer_id, "currency": currency}, "ok", conn=conn)

    return {"account_id": account_id, "customer_id": customer_id, "currency": currency, "account_type": account_type, "status": "active", "opened_at": _now()}