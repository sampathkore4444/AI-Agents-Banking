"""
Payment Fraud Notifications — Alerts and notifications for payment fraud.

Manages:
- Payment blocked alerts (to customer and operations)
- Payment review notifications
- Fraud investigation alerts
- Compliance notifications
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

_NOTIFICATIONS: list[dict] = []


async def send_payment_blocked_alert(
    payment_id: str,
    payer_account_id: str,
    payer_name: str,
    amount: float,
    payee_name: str,
    reason: str,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send alert when payment is blocked."""
    notif_id = f"PF-BLOCK-{hashlib.md5(payment_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "payment_blocked",
        "payment_id": payment_id,
        "account_id": payer_account_id,
        "subject": f"Payment Blocked: ${amount:,.2f} to {payee_name}",
        "message": f"Your payment of ${amount:,.2f} to {payee_name} has been blocked. Reason: {reason}. Please contact your bank to verify this transaction.",
        "channels": channels or ["sms", "email", "push"],
        "priority": "critical",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent", "channels": channels or ["sms", "email", "push"]}


async def send_payment_review_notification(
    payment_id: str,
    payer_account_id: str,
    amount: float,
    payee_name: str,
    risk_score: float,
    red_flags: list[str],
) -> dict[str, Any]:
    """Send notification when payment is held for review."""
    notif_id = f"PF-REVIEW-{hashlib.md5(payment_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "payment_review",
        "payment_id": payment_id,
        "account_id": payer_account_id,
        "subject": f"Payment Under Review: ${amount:,.2f} to {payee_name}",
        "message": f"Your payment of ${amount:,.2f} to {payee_name} is under review. Risk score: {risk_score:.0f}. Flags: {', '.join(red_flags[:3])}. You will be notified once the review is complete.",
        "channels": ["sms", "email"],
        "priority": "high",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def send_fraud_confirmation(
    payment_id: str,
    payer_account_id: str,
    is_fraud: bool,
    action_taken: str,
) -> dict[str, Any]:
    """Send confirmation after fraud investigation."""
    notif_id = f"PF-CONFIRM-{hashlib.md5(payment_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "fraud_confirmation",
        "payment_id": payment_id,
        "account_id": payer_account_id,
        "subject": "Payment Fraud Investigation Complete",
        "message": f"The investigation for payment {payment_id} is complete. {'Fraud was confirmed.' if is_fraud else 'No fraud was found.'} Action: {action_taken}.",
        "channels": ["email"],
        "priority": "normal",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def send_operations_alert(
    payment_id: str,
    alert_type: str,
    message: str,
    priority: str = "high",
) -> dict[str, Any]:
    """Send internal operations alert."""
    notif_id = f"PF-OPS-{hashlib.md5(payment_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": f"operations_{alert_type}",
        "payment_id": payment_id,
        "subject": f"Operations Alert: {alert_type}",
        "message": message,
        "recipient": "fraud_operations_team",
        "channels": ["internal"],
        "priority": priority,
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def get_notification_history(account_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get notification history."""
    if account_id:
        filtered = [n for n in _NOTIFICATIONS if n.get("account_id") == account_id]
    else:
        filtered = _NOTIFICATIONS
    return {"total": len(filtered), "notifications": filtered[-limit:]}
