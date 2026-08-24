"""
Notification Tool — MCP tool stub for customer service.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

TEMPLATES = {
    "welcome": "Hello {name}! Welcome to {bank_name}. How can I help you today?",
    "dispute_filed": "Your dispute {dispute_id} has been filed. Expected resolution: {expected_date}.",
    "dispute_update": "Update on dispute {dispute_id}: Status is now {status}.",
    "complaint_acknowledged": "We've received your complaint {complaint_id}. Our team will review it within 24 hours.",
    "complaint_resolved": "Your complaint {complaint_id} has been resolved. {resolution}",
    "account_alert": "Account Alert: {alert_type} on your {account_type} account.",
    "feedback_request": "How was your experience today? Please rate your interaction (1-5).",
    "escalation_notice": "You're being connected to a human agent. Estimated wait: {wait_time} minutes.",
}


async def send_notification(
    recipient_id: str,
    template_id: str,
    channel: str = "email",
    variables: dict | None = None,
) -> dict:
    """Send a notification to a customer."""
    logger.info("Sending notification: template=%s, recipient=%s", template_id, recipient_id)

    template = TEMPLATES.get(template_id, "")
    if template and variables:
        try:
            message = template.format(**variables)
        except KeyError as e:
            message = f"[Template variable missing: {e}] {template}"
    else:
        message = template or f"[No template found for {template_id}]"

    result = {
        "notification_id": str(uuid.uuid4()),
        "recipient_id": recipient_id,
        "channel": channel,
        "template_id": template_id,
        "message_preview": message[:200],
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }

    logger.info("Notification sent: %s via %s", template_id, channel)
    return result
