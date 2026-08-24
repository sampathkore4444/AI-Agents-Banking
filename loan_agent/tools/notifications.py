"""
Notification Tool — MCP tool stub for loan application updates.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

TEMPLATES = {
    "application_received": "Your {loan_type} application for ${loan_amount:,.2f} has been received. Application ID: {application_id}. We'll review your documents and get back to you within 2-3 business days.",
    "documents_needed": "We need additional documents to process your loan application: {documents}. Please upload them at your earliest convenience.",
    "application_approved": "Congratulations! Your {loan_type} application has been approved for ${loan_amount:,.2f} at {interest_rate}% APR. Your monthly payment will be ${monthly_payment:,.2f}.",
    "application_declined": "We regret to inform you that your loan application could not be approved at this time. Reason: {reason}. You may reapply after {reapply_period}.",
    "application_under_review": "Your loan application is currently under manual review by our underwriting team. We'll update you within 5 business days.",
    "payment_reminder": "Reminder: Your {loan_type} payment of ${payment_amount:,.2f} is due on {due_date}.",
}


async def send_notification(
    recipient_type: str,
    recipient_id: str,
    channel: str,
    template_id: str,
    variables: dict | None = None,
) -> dict:
    """Send a notification to a customer or internal staff."""
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
        "recipient_type": recipient_type,
        "recipient_id": recipient_id,
        "channel": channel,
        "template_id": template_id,
        "message_preview": message[:200],
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }

    logger.info("Notification sent: %s", template_id)
    return result
