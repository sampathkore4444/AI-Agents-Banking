"""
Notifications Tool — Lead outreach and follow-up notifications.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
NOTIFICATION_DB: list[dict] = []

TEMPLATES = {
    "welcome": {"subject": "Welcome! We're glad you're interested", "body": "Hi {name}! Thank you for your interest in {product}. We'd love to help you find the right solution."},
    "follow_up": {"subject": "Following up on your inquiry", "body": "Hi {name}! We wanted to follow up on your interest in {product}. Do you have any questions?"},
    "qualification_complete": {"subject": "Great news — you're pre-qualified!", "body": "Hi {name}! Based on our review, you're pre-qualified for {product}. Let's schedule a consultation."},
    "appointment_reminder": {"subject": "Appointment reminder", "body": "Hi {name}! This is a reminder about your appointment with {advisor} on {date} at {time}."},
    "nurture": {"subject": "Here's something you might find helpful", "body": "Hi {name}! We thought you might find this information about {product} useful."},
    "rate_alert": {"subject": "Rates are changing — act now", "body": "Hi {name}! Current {product} rates are at {rate}. Lock in before they change."},
}


async def send_notification(
    lead_id: str,
    template_id: str,
    channels: list[str],
    variables: dict | None = None,
) -> dict[str, Any]:
    """Send a notification to a lead."""
    template = TEMPLATES.get(template_id, {"subject": "Notification", "body": "You have an update."})

    vars_merged = variables or {}
    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "lead_id": lead_id,
        "template": template_id,
        "channels": channels,
        "subject": template["subject"],
        "body": template["body"].format(**vars_merged) if vars_merged else template["body"],
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "lead_id": lead_id,
        "channels_sent": channels,
        "message": f"Notification sent via {', '.join(channels)}.",
    }


async def send_welcome(lead_id: str, name: str, product: str) -> dict[str, Any]:
    """Send welcome notification."""
    return await send_notification(lead_id, "welcome", ["email"], {"name": name, "product": product})


async def send_follow_up(lead_id: str, name: str, product: str) -> dict[str, Any]:
    """Send follow-up notification."""
    return await send_notification(lead_id, "follow_up", ["email", "sms"], {"name": name, "product": product})


async def send_qualification_complete(lead_id: str, name: str, product: str) -> dict[str, Any]:
    """Send qualification complete notification."""
    return await send_notification(lead_id, "qualification_complete", ["email", "sms"], {"name": name, "product": product})


async def send_appointment_reminder(
    lead_id: str,
    name: str,
    advisor: str,
    date: str,
    time: str,
) -> dict[str, Any]:
    """Send appointment reminder."""
    return await send_notification(lead_id, "appointment_reminder", ["email", "sms"], {"name": name, "advisor": advisor, "date": date, "time": time})


async def get_notification_history(lead_id: str) -> dict[str, Any]:
    """Get notification history for a lead."""
    notifs = [n for n in NOTIFICATION_DB if n["lead_id"] == lead_id]
    notifs.sort(key=lambda x: x["sent_at"], reverse=True)
    return {"lead_id": lead_id, "total": len(notifs), "notifications": notifs}


async def get_templates() -> dict[str, Any]:
    """Get all notification templates."""
    return {"templates": list(TEMPLATES.keys())}
