"""
Notification Tool — MCP tool stub.

In production this would call the bank's notification service
for email, SMS, and in-app messages.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Notification templates
TEMPLATES = {
    "kyc_welcome": "Welcome to {bank_name}! Your account {account_number} has been created successfully.",
    "kyc_documents_requested": "Please upload the following documents to complete your KYC: {documents}",
    "kyc_under_review": "Your application is under review. We'll notify you within {timeline}.",
    "kyc_approved": "Great news! Your account has been approved and is now active.",
    "kyc_rejected": "We regret to inform you that your application could not be approved. Reason: {reason}",
    "kyc_additional_info": "We need additional information to process your application: {details}",
}


async def send_notification(
    recipient_type: str,
    recipient_id: str,
    channel: str,
    template_id: str,
    variables: dict | None = None,
) -> dict:
    """
    Send a notification to a customer or internal staff member.

    Supports email, SMS, and in-app channels.
    """
    logger.info("Sending notification: template=%s, channel=%s, recipient=%s", template_id, channel, recipient_id)

    template = TEMPLATES.get(template_id, "")
    if template and variables:
        try:
            message = template.format(**variables)
        except KeyError as e:
            message = f"[Template variable missing: {e}] {template}"
    else:
        message = template or f"[No template found for {template_id}]"

    # ── In production: call notification service ──
    # await httpx.AsyncClient().post(
    #     f"{settings.notification_api_url}/v1/send",
    #     json={"recipient_id": recipient_id, "channel": channel, "message": message},
    # )

    notification_id = str(uuid.uuid4())

    result = {
        "notification_id": notification_id,
        "recipient_type": recipient_type,
        "recipient_id": recipient_id,
        "channel": channel,
        "template_id": template_id,
        "message_preview": message[:200],
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }

    logger.info("Notification sent: %s via %s", notification_id, channel)
    return result
