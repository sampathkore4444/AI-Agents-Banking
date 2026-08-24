"""
Notifications Tool — Fraud alerts and customer notifications.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
NOTIFICATION_DB: list[dict] = []
ALERT_TEMPLATES = {
    "fraud_alert": {
        "subject": "Fraud Alert — Unusual Activity Detected",
        "body": "We detected unusual activity on your account. A transaction of {amount} at {merchant} was flagged. If this was you, no action is needed. If not, please contact us immediately.",
        "channels": ["sms", "email", "push"],
    },
    "card_blocked": {
        "subject": "Card Blocked — Suspicious Activity",
        "body": "Your card ending in {last_four} has been temporarily blocked due to suspicious activity. Please call us at 1-800-XXX-XXXX to verify and unblock.",
        "channels": ["sms", "email"],
    },
    "transaction_blocked": {
        "subject": "Transaction Blocked",
        "body": "A transaction of {amount} at {merchant} was blocked. If you did not authorize this, please ignore this message. If you did, please verify via the app.",
        "channels": ["sms", "push"],
    },
    "login_alert": {
        "subject": "New Login Detected",
        "body": "A new login to your account was detected from {location} on {device}. If this was not you, please change your password immediately.",
        "channels": ["email", "push"],
    },
    "dispute_received": {
        "subject": "Dispute Received",
        "body": "We have received your dispute for transaction {transaction_id}. We will investigate and respond within 10 business days.",
        "channels": ["email"],
    },
    "dispute_resolved": {
        "subject": "Dispute Resolution",
        "body": "Your dispute for transaction {transaction_id} has been {resolution}. {details}",
        "channels": ["email"],
    },
    "sar_filed": {
        "subject": "Compliance Report Filed",
        "body": "A Suspicious Activity Report has been filed for case {case_id}. This is an internal notification — do not disclose to the customer.",
        "channels": ["internal_email"],
    },
}


async def send_fraud_alert(
    customer_id: str,
    transaction_id: str,
    amount: float,
    merchant: str,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send fraud alert notification to customer."""
    template = ALERT_TEMPLATES["fraud_alert"]
    use_channels = channels or ["sms", "email"]

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": "fraud_alert",
        "transaction_id": transaction_id,
        "channels": use_channels,
        "subject": template["subject"],
        "body": template["body"].format(amount=f"${amount:.2f}", merchant=merchant),
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "customer_id": customer_id,
        "type": "fraud_alert",
        "channels_sent": use_channels,
        "message": f"Fraud alert sent to customer {customer_id} via {', '.join(use_channels)}.",
    }


async def send_card_blocked_notification(
    customer_id: str,
    card_last_four: str,
    reason: str,
) -> dict[str, Any]:
    """Notify customer that their card has been blocked."""
    template = ALERT_TEMPLATES["card_blocked"]

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": "card_blocked",
        "channels": ["sms", "email"],
        "subject": template["subject"],
        "body": template["body"].format(last_four=card_last_four),
        "reason": reason,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "customer_id": customer_id,
        "type": "card_blocked",
        "message": f"Card blocked notification sent for card ending in {card_last_four}.",
    }


async def send_transaction_blocked_notification(
    customer_id: str,
    transaction_id: str,
    amount: float,
    merchant: str,
) -> dict[str, Any]:
    """Notify customer that a transaction was blocked."""
    template = ALERT_TEMPLATES["transaction_blocked"]

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": "transaction_blocked",
        "channels": ["sms", "push"],
        "subject": template["subject"],
        "body": template["body"].format(amount=f"${amount:.2f}", merchant=merchant),
        "transaction_id": transaction_id,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "customer_id": customer_id,
        "type": "transaction_blocked",
        "message": f"Transaction blocked notification sent for {transaction_id}.",
    }


async def send_login_alert(
    customer_id: str,
    location: str,
    device: str,
) -> dict[str, Any]:
    """Notify customer of new login."""
    template = ALERT_TEMPLATES["login_alert"]

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": "login_alert",
        "channels": ["email", "push"],
        "subject": template["subject"],
        "body": template["body"].format(location=location, device=device),
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "customer_id": customer_id,
        "type": "login_alert",
        "message": f"Login alert sent to customer {customer_id}.",
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


async def send_compliance_notification(
    case_id: str,
    notification_type: str,
    details: str,
) -> dict[str, Any]:
    """Send internal compliance notification (SAR filing, etc.)."""
    template = ALERT_TEMPLATES.get(notification_type, {"subject": f"Compliance: {notification_type}", "body": details})

    notification = {
        "notification_id": f"NOTIF-{int(datetime.utcnow().timestamp())}",
        "case_id": case_id,
        "type": notification_type,
        "channels": ["internal_email"],
        "subject": template["subject"],
        "body": template["body"].format(case_id=case_id) if "{case_id}" in template["body"] else details,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    NOTIFICATION_DB.append(notification)

    return {
        "notification_id": notification["notification_id"],
        "case_id": case_id,
        "type": notification_type,
        "message": f"Internal compliance notification sent for case {case_id}.",
    }
