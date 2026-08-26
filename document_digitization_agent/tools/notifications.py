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
    "doc_received": "We have received your document ({document_type}). Processing will begin shortly.",
    "doc_processed": "Your document ({document_type}) has been processed successfully. Reference: {extraction_id}.",
    "doc_needs_review": "Your document ({document_type}) requires manual review. Our team will contact you within {timeline}.",
    "doc_rejected": "Your document ({document_type}) could not be processed. Reason: {reason}. Please re-upload a clearer version.",
    "extraction_complete": "Document extraction complete for {document_type}. {field_count} fields extracted with {confidence}% confidence.",
    "validation_failed": "Document validation failed for {document_type}. Issues: {issues}",
    "batch_complete": "Batch processing complete. {total} documents processed: {successful} successful, {failed} failed.",
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

    # In production: call notification service
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
