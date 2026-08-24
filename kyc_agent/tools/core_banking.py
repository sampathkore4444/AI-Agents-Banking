"""
Core Banking Tool — MCP tool stub.

In production this would call the bank's core banking system
for customer lookups, account creation, and data retrieval.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def query_core_banking(
    query_type: str,
    identifier: str,
    filters: dict | None = None,
) -> dict:
    """
    Query the core banking system for customer data, account status, or transaction history.

    Supported query_types: customer_lookup, account_status, transaction_history
    """
    logger.info("Core banking query: type=%s, identifier=%s", query_type, identifier)

    # ── In production: call core banking API ──
    # response = await httpx.AsyncClient().get(
    #     f"{settings.core_banking_api_url}/v1/{query_type}/{identifier}",
    #     headers={"Authorization": f"Bearer {settings.core_banking_api_key}"},
    # )

    # ── Stub ──
    id_hash = hashlib.md5(identifier.encode()).hexdigest()

    if query_type == "customer_lookup":
        return {
            "customer_id": f"CUST-{id_hash[:8].upper()}",
            "name": f"Customer {identifier}",
            "status": "active",
            "kyc_status": "pending",
            "account_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
    elif query_type == "account_status":
        return {
            "account_number": f"ACC-{id_hash[:10].upper()}",
            "status": "active",
            "balance": 0.0,
            "account_type": "business_current",
            "opened_at": datetime.utcnow().isoformat(),
        }
    elif query_type == "transaction_history":
        return {
            "account_number": identifier,
            "transactions": [],
            "total_count": 0,
        }
    else:
        return {"error": f"Unknown query_type: {query_type}"}


async def create_customer_profile(
    personal_info: dict,
    address: dict,
    kyc_result: str,
    risk_rating: str,
    employment_info: dict | None = None,
    documents_verified: list[str] | None = None,
) -> dict:
    """
    Create a customer profile in the core banking system after KYC approval.

    Returns the new customer ID and account number.
    """
    logger.info("Creating customer profile: kyc_result=%s, risk=%s", kyc_result, risk_rating)

    # ── In production: call core banking API ──
    # response = await httpx.AsyncClient().post(
    #     f"{settings.core_banking_api_url}/v1/customers",
    #     headers={"Authorization": f"Bearer {settings.core_banking_api_key}"},
    #     json={...},
    # )

    # ── Stub ──
    customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
    account_number = f"ACC-{uuid.uuid4().hex[:10].upper()}"

    status = "active" if kyc_result == "approved" else "pending_review"
    if risk_rating == "high":
        status = "restricted"

    result = {
        "customer_id": customer_id,
        "account_number": account_number,
        "personal_info": personal_info,
        "address": address,
        "kyc_result": kyc_result,
        "risk_rating": risk_rating,
        "documents_verified": documents_verified or [],
        "status": status,
        "created_at": datetime.utcnow().isoformat(),
    }

    logger.info("Customer profile created: %s, account: %s", customer_id, account_number)
    return result
