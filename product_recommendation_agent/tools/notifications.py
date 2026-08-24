"""
Notifications Tool — Customer outreach and offer notifications.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
NOTIFICATION_DB: list[dict] = []

NOTIFICATION_TEMPLATES = {
    "product_recommendation": {
        "subject": "We think you'll love this",
        "body": "Based on your profile, we recommend {product_name}. {description}",
        "channels": ["email", "push"],
    },
    "offer_notification": {
        "subject": "Special offer just for you",
        "body": "Hi {customer_name}! {offer_description}. Limited time — expires {end_date}.",
        "channels": ["email", "sms", "push"],
    },
    "cross_sell": {
        "subject": "Complete your financial picture",
        "body": "Hi {customer_name}! You might also benefit from {product_name}. {benefit}",
        "channels": ["email", "push"],
    },
    "win_back": {
        "subject": "We miss you!",
        "body": "Hi {customer_name}! Come back and enjoy {offer}. Your loyalty matters to us.",
        "channels": ["email", "sms"],
    },
    "rate_alert": {
        "subject": "Rate change notification",
        "body": "The APY on your {product_name} has changed to {new_rate}%. {details}",
        "channels": ["email"],
    },
}


async def send_product_recommendation(
    customer_id: str,
    product_id: str,
    product_name: str,
    description: str,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send product recommendation notification."""
    template = NOTIFICATION_TEMPLATES["product_recommendation"]
    use_channels = channels or template["channels"]

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": "product_recommendation",
        "product_id": product_id,
        "channels": use_channels,
        "subject": template["subject"],
        "body": template["body"].format(product_name=product_name, description=description),
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "customer_id": customer_id,
        "type": "product_recommendation",
        "channels_sent": use_channels,
        "message": f"Recommendation sent for {product_name}.",
    }


async def send_offer_notification(
    customer_id: str,
    customer_name: str,
    offer_id: str,
    offer_description: str,
    end_date: str,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send promotional offer notification."""
    template = NOTIFICATION_TEMPLATES["offer_notification"]
    use_channels = channels or template["channels"]

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": "offer_notification",
        "offer_id": offer_id,
        "channels": use_channels,
        "subject": template["subject"],
        "body": template["body"].format(customer_name=customer_name, offer_description=offer_description, end_date=end_date),
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "customer_id": customer_id,
        "type": "offer_notification",
        "channels_sent": use_channels,
        "message": f"Offer notification sent to {customer_name}.",
    }


async def send_cross_sell_notification(
    customer_id: str,
    customer_name: str,
    product_name: str,
    benefit: str,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send cross-sell notification."""
    template = NOTIFICATION_TEMPLATES["cross_sell"]
    use_channels = channels or template["channels"]

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": "cross_sell",
        "channels": use_channels,
        "subject": template["subject"],
        "body": template["body"].format(customer_name=customer_name, product_name=product_name, benefit=benefit),
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "customer_id": customer_id,
        "type": "cross_sell",
        "channels_sent": use_channels,
        "message": f"Cross-sell notification sent for {product_name}.",
    }


async def get_notification_history(
    customer_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    """Get notification history for a customer."""
    notifs = [n for n in NOTIFICATION_DB if n["customer_id"] == customer_id]
    notifs.sort(key=lambda x: x["sent_at"], reverse=True)
    return {
        "customer_id": customer_id,
        "total_notifications": len(notifs),
        "notifications": notifs[:limit],
    }


async def get_notification_stats() -> dict[str, Any]:
    """Get notification statistics."""
    types: dict[str, int] = {}
    channels: dict[str, int] = {}
    for n in NOTIFICATION_DB:
        types[n.get("type", "unknown")] = types.get(n.get("type", "unknown"), 0) + 1
        for ch in n.get("channels", []):
            channels[ch] = channels.get(ch, 0) + 1

    return {
        "total_notifications": len(NOTIFICATION_DB),
        "by_type": types,
        "by_channel": channels,
    }
