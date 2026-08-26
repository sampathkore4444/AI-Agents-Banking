"""
Notification Tool — MCP tool stub.

In production this would call the bank's notification service
for email, Slack, Teams, and in-app messages to employees.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

TEMPLATES = {
    "knowledge_article_found": "Found relevant article: {title} — {url}",
    "ticket_created": "Support ticket {ticket_id} created: {title}",
    "ticket_updated": "Ticket {ticket_id} status updated to: {status}",
    "training_reminder": "Reminder: {training_name} due by {deadline}",
    "policy_update": "Policy updated: {policy_name} — Version {version}",
    "system_outage": "System alert: {system_name} is {status} — {details}",
}


async def send_notification(
    recipient_id: str,
    channel: str,
    template_id: str,
    variables: dict | None = None,
) -> dict:
    """
    Send an internal notification to an employee via email, Slack, or Teams.
    """
    logger.info("Sending notification: template=%s, channel=%s, recipient=%s", template_id, channel, recipient_id)

    template = TEMPLATES.get(template_id, "")
    if template and variables:
        try:
            message = template.format(**variables)
        except KeyError as e:
            message = f"[Missing variable: {e}] {template}"
    else:
        message = template or f"[No template found for {template_id}]"

    notification_id = str(uuid.uuid4())

    result = {
        "notification_id": notification_id,
        "recipient_id": recipient_id,
        "channel": channel,
        "template_id": template_id,
        "message_preview": message[:200],
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }

    logger.info("Notification sent: %s via %s", notification_id, channel)
    return result
