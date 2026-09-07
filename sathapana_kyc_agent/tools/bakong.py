"""
Bakong Registration Tool — MCP tool stub.

Sathapana is a member bank of the NBC-operated Bakong payment system.
After KYC approval, the customer's account can be linked to a Bakong
profile for mobile money. In production this calls the Bakong member
bank API; here we simulate the linkage.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def register_bakong(customer_id: str, account_id: str, mobile_number: str, currency: str) -> dict:
    """Link an onboarded account to Bakong for mobile payments."""
    bakong_id = f"BKNG-{uuid.uuid4().hex[:10].upper()}"
    result = {
        "bakong_id": bakong_id,
        "customer_id": customer_id,
        "account_id": account_id,
        "mobile_number": mobile_number,
        "currency": currency,
        "status": "linked",
        "nbc_simulated": True,
        "linked_at": datetime.now(timezone.utc).isoformat(),
    }
    from db import log_action

    log_action("bakong", "register_bakong", result)
    return result