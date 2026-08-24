"""
Notification Tool — MCP tool stub for cross-border payment notifications.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

XBORDER_TEMPLATES = {
    "payment_initiated": "Your international wire transfer of {amount} {currency} to {beneficiary_name} has been initiated. UETR: {uetr}. Estimated delivery: {delivery_date}.",
    "payment_processing": "Your wire transfer (UETR: {uetr}) is being processed. Current status: {status}. Your payment is moving through the correspondent banking chain.",
    "payment_completed": "Your wire transfer of {amount} {currency} has been delivered to {beneficiary_name}. UETR: {uetr}. Total fees: ${total_fees:.2f}.",
    "payment_hold": "Your wire transfer (UETR: {uetr}) has been held for compliance review. Reason: {reason}. Our compliance team will review within 24 hours.",
    "payment_rejected": "Your wire transfer (UETR: {uetr}) could not be processed. Reason: {reason}. Please contact your branch for assistance.",
    "quote_ready": "Your cross-border payment quote is ready. {amount} {source_currency} → {converted_amount} {target_currency}. Total cost: ${total_cost:.2f}. Valid for 30 minutes.",
}


async def send_xborder_notification(
    recipient_id: str,
    template_id: str,
    channel: str = "email",
    variables: dict | None = None,
) -> dict:
    """Send a cross-border payment notification."""
    template = XBORDER_TEMPLATES.get(template_id, "")

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
        "message_preview": message[:300],
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }

    logger.info("Cross-border notification sent: %s via %s", template_id, channel)
    return result
