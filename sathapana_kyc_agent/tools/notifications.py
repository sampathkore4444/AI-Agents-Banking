"""
Notification Tool — MCP tool stub.

In production this sends SMS via Cambodian telco aggregators (Smart, Metfone,
Cellcard), email, or in-app push. Returns simulated delivery results.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

TEMPLATES = {
    "kyc_welcome": "Welcome to Sathapana Bank, {customer_name}!",
    "kyc_documents_requested": "Dear {customer_name}, we need more documents for your KYC: {missing}.",
    "kyc_under_review": "Your application is under compliance review. We will update you within 24 hours.",
    "kyc_approved": "Congratulations {customer_name}! Your {product} account {account_id} is ready.",
    "kyc_rejected": "We are unable to proceed with your application. Contact your branch or CAMFIU.",
    "kyc_additional_info": "Please provide additional information to complete verification: {items}.",
}


def send_notification(
    recipient_type: str,
    recipient_id: str,
    channel: str = "sms",
    template_id: str = "kyc_under_review",
    variables: dict | None = None,
) -> dict:
    """Send a notification to a customer, officer, or relationship manager."""
    message = TEMPLATES.get(template_id, "Sathapana Bank notification.")
    try:
        message = message.format(**(variables or {}))
    except KeyError:
        pass

    return {
        "notification_id": str(uuid.uuid4()),
        "recipient_type": recipient_type,
        "recipient_id": recipient_id,
        "channel": channel,
        "template_id": template_id,
        "message": message,
        "status": "queued",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }