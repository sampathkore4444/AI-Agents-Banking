"""
Bakong Registration Tool — MCP tool stub.

Sathapana is a member bank of the NBC-operated Bakong payment system. After
KYC approval the account is linked via the configured
`integrations.bakong.BakongProvider` (live member-bank API in production).
"""

from __future__ import annotations


def register_bakong(customer_id: str, account_id: str, mobile_number: str, currency: str) -> dict:
    """Link an onboarded account to Bakong for mobile payments."""
    from integrations import get_providers
    from db import log_action

    result = get_providers().bakong.link(customer_id, account_id, mobile_number, currency)
    log_action("bakong", "register_bakong", result)
    return result