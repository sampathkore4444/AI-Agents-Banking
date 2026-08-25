"""
Notification Tools — Multi-channel notifications for standing order events.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
_notification_log: list[dict[str, Any]] = []


async def send_setup_confirmation(
    standing_order_id: str,
    account_id: str,
    customer_name: str,
    payee_name: str,
    amount: float,
    frequency: str,
    next_execution: str,
) -> dict[str, Any]:
    """Send confirmation when a standing order is created."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    message = (
        f"Standing order confirmed!\n"
        f"ID: {standing_order_id}\n"
        f"To: {payee_name}\n"
        f"Amount: ${amount:,.2f}\n"
        f"Frequency: {frequency}\n"
        f"Next payment: {next_execution}"
    )

    _log_notification(notif_id, account_id, "setup_confirmation", message, ["email", "push"], customer_name)
    return {"success": True, "notification_id": notif_id, "type": "setup_confirmation"}


async def send_modification_notice(
    standing_order_id: str,
    account_id: str,
    customer_name: str,
    changes: list[str],
) -> dict[str, Any]:
    """Send notice when a standing order is modified."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    changes_text = "\n".join(f"  - {c}" for c in changes)
    message = f"Standing order {standing_order_id} has been updated:\n{changes_text}"

    _log_notification(notif_id, account_id, "modification_notice", message, ["email"], customer_name)
    return {"success": True, "notification_id": notif_id, "type": "modification_notice"}


async def send_cancellation_notice(
    standing_order_id: str,
    account_id: str,
    customer_name: str,
    payee_name: str,
    reason: str,
) -> dict[str, Any]:
    """Send notice when a standing order is cancelled."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    message = f"Standing order to {payee_name} ({standing_order_id}) has been cancelled.\nReason: {reason}"

    _log_notification(notif_id, account_id, "cancellation_notice", message, ["email", "push", "sms"], customer_name)
    return {"success": True, "notification_id": notif_id, "type": "cancellation_notice"}


async def send_payment_failed_alert(
    standing_order_id: str,
    account_id: str,
    customer_name: str,
    payee_name: str,
    amount: float,
    failure_reason: str,
    retry_date: str | None = None,
) -> dict[str, Any]:
    """Send alert when a payment fails."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    message = (
        f"Payment Failed!\n"
        f"Standing Order: {standing_order_id}\n"
        f"To: {payee_name}\n"
        f"Amount: ${amount:,.2f}\n"
        f"Reason: {failure_reason}"
    )
    if retry_date:
        message += f"\nScheduled retry: {retry_date}"
    else:
        message += "\nThis standing order has been suspended. Please update your account."

    _log_notification(notif_id, account_id, "payment_failed", message, ["email", "push", "sms"], customer_name)
    return {"success": True, "notification_id": notif_id, "type": "payment_failed"}


async def send_suspension_notice(
    standing_order_id: str,
    account_id: str,
    customer_name: str,
    payee_name: str,
    reason: str,
) -> dict[str, Any]:
    """Send notice when a standing order is suspended."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    message = (
        f"Standing Order Suspended\n"
        f"ID: {standing_order_id}\n"
        f"To: {payee_name}\n"
        f"Reason: {reason}\n"
        f"Please contact us to reactivate or modify this standing order."
    )

    _log_notification(notif_id, account_id, "suspension_notice", message, ["email", "push", "sms"], customer_name)
    return {"success": True, "notification_id": notif_id, "type": "suspension_notice"}


async def send_amount_change_alert(
    standing_order_id: str,
    account_id: str,
    customer_name: str,
    payee_name: str,
    old_amount: float,
    new_amount: float,
) -> dict[str, Any]:
    """Send alert when a biller changes the payment amount."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    pct_change = ((new_amount - old_amount) / old_amount) * 100 if old_amount > 0 else 0
    message = (
        f"Amount Change Alert\n"
        f"Standing Order to {payee_name} ({standing_order_id})\n"
        f"Previous: ${old_amount:,.2f}\n"
        f"New: ${new_amount:,.2f} ({pct_change:+.1f}%)\n"
        f"If you did not expect this change, please review your standing order."
    )

    _log_notification(notif_id, account_id, "amount_change", message, ["email", "push"], customer_name)
    return {"success": True, "notification_id": notif_id, "type": "amount_change"}


async def send_daily_summary(account_id: str, customer_name: str, summary: dict[str, Any]) -> dict[str, Any]:
    """Send daily summary of standing order activity."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    message = (
        f"Daily Standing Order Summary\n"
        f"Active orders: {summary.get('active_count', 0)}\n"
        f"Payments today: {summary.get('payments_today', 0)}\n"
        f"Total processed: ${summary.get('total_processed', 0):,.2f}\n"
        f"Upcoming this week: {summary.get('upcoming_week', 0)} payments"
    )

    _log_notification(notif_id, account_id, "daily_summary", message, ["email"], customer_name)
    return {"success": True, "notification_id": notif_id, "type": "daily_summary"}


async def get_notification_log(
    account_id: str | None = None,
    notification_type: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Get notification log."""
    results = _notification_log.copy()

    if account_id:
        results = [n for n in results if n["account_id"] == account_id]
    if notification_type:
        results = [n for n in results if n["type"] == notification_type]

    results = sorted(results, key=lambda n: n["sent_at"], reverse=True)[:limit]
    return {"count": len(results), "notifications": results}


def _log_notification(
    notif_id: str, account_id: str, notif_type: str,
    message: str, channels: list[str], recipient: str,
) -> None:
    _notification_log.append({
        "notification_id": notif_id,
        "account_id": account_id,
        "type": notif_type,
        "message": message,
        "channels": channels,
        "recipient": recipient,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    })
