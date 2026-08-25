"""
Calendar API Tools — Reminders, notifications, and calendar integration.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any


# ── In-memory stores ──────────────────────────────────────────────
_reminders: dict[str, dict[str, Any]] = {}
_calendar_events: dict[str, dict[str, Any]] = {}


async def create_payment_reminder(
    standing_order_id: str,
    account_id: str,
    payee_name: str,
    amount: float,
    scheduled_date: str,
    reminder_days: list[int] | None = None,
) -> dict[str, Any]:
    """Create payment reminders for a standing order."""
    if reminder_days is None:
        reminder_days = [3, 1, 0]

    reminders = []
    sched_dt = datetime.fromisoformat(scheduled_date)

    for days_before in reminder_days:
        reminder_id = f"REM-{uuid.uuid4().hex[:8].upper()}"
        reminder_date = sched_dt - timedelta(days=days_before)

        if reminder_date < datetime.utcnow():
            continue

        reminder = {
            "reminder_id": reminder_id,
            "standing_order_id": standing_order_id,
            "account_id": account_id,
            "payee_name": payee_name,
            "amount": amount,
            "scheduled_date": scheduled_date,
            "reminder_date": reminder_date.isoformat(),
            "days_before": days_before,
            "message": _build_reminder_message(payee_name, amount, days_before),
            "status": "scheduled",
            "channels": ["email", "push"],
            "created_at": datetime.utcnow().isoformat(),
        }

        _reminders[reminder_id] = reminder
        reminders.append(reminder)

    return {
        "success": True,
        "standing_order_id": standing_order_id,
        "reminder_count": len(reminders),
        "reminders": reminders,
    }


async def get_reminders(
    account_id: str | None = None,
    status: str | None = None,
    upcoming_only: bool = True,
) -> dict[str, Any]:
    """Get payment reminders."""
    results = list(_reminders.values())

    if account_id:
        results = [r for r in results if r["account_id"] == account_id]
    if status:
        results = [r for r in results if r["status"] == status]
    if upcoming_only:
        now = datetime.utcnow().isoformat()
        results = [r for r in results if r["reminder_date"] >= now]

    results.sort(key=lambda r: r["reminder_date"])
    return {"count": len(results), "reminders": results}


async def create_calendar_event(
    standing_order_id: str,
    title: str,
    description: str,
    event_date: str,
    event_type: str = "payment",
    reminders: list[int] | None = None,
) -> dict[str, Any]:
    """Create a calendar event for a payment."""
    event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

    event = {
        "event_id": event_id,
        "standing_order_id": standing_order_id,
        "title": title,
        "description": description,
        "event_date": event_date,
        "event_type": event_type,
        "reminders_minutes": reminders or [1440, 60],
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
    }

    _calendar_events[event_id] = event
    return {"success": True, "event_id": event_id, "title": title, "date": event_date}


async def get_calendar_events(
    start_date: str | None = None,
    end_date: str | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    """Get calendar events within a date range."""
    results = list(_calendar_events.values())

    if start_date:
        results = [e for e in results if e["event_date"] >= start_date]
    if end_date:
        results = [e for e in results if e["event_date"] <= end_date]
    if event_type:
        results = [e for e in results if e["event_type"] == event_type]

    results.sort(key=lambda e: e["event_date"])
    return {"count": len(results), "events": results}


async def send_payment_notification(
    standing_order_id: str,
    account_id: str,
    payee_name: str,
    amount: float,
    notification_type: str,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """Send a payment notification."""
    notif_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"
    if channels is None:
        channels = ["email", "push"]

    message = _build_notification_message(notification_type, payee_name, amount)

    notification = {
        "notification_id": notif_id,
        "standing_order_id": standing_order_id,
        "account_id": account_id,
        "type": notification_type,
        "message": message,
        "channels": channels,
        "payee_name": payee_name,
        "amount": amount,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
    }

    _reminders[notif_id] = notification
    return {
        "success": True,
        "notification_id": notif_id,
        "type": notification_type,
        "channels": channels,
    }


async def get_notification_history(account_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get notification history."""
    notifications = [r for r in _reminders.values() if r.get("type") in {"payment_scheduled", "payment_executed", "payment_failed", "payment_reminder"}]
    if account_id:
        notifications = [n for n in notifications if n.get("account_id") == account_id]
    notifications = sorted(notifications, key=lambda n: n.get("sent_at", ""), reverse=True)[:limit]
    return {"count": len(notifications), "notifications": notifications}


def _build_reminder_message(payee_name: str, amount: float, days_before: int) -> str:
    if days_before == 0:
        return f"Today: ${amount:,.2f} payment to {payee_name} is due."
    elif days_before == 1:
        return f"Tomorrow: ${amount:,.2f} payment to {payee_name} is due."
    else:
        return f"In {days_before} days: ${amount:,.2f} payment to {payee_name} is due."


def _build_notification_message(notification_type: str, payee_name: str, amount: float) -> str:
    match notification_type:
        case "payment_scheduled":
            return f"Payment of ${amount:,.2f} to {payee_name} has been scheduled."
        case "payment_executed":
            return f"Payment of ${amount:,.2f} to {payee_name} has been processed successfully."
        case "payment_failed":
            return f"Payment of ${amount:,.2f} to {payee_name} has failed. Please check your account."
        case "payment_reminder":
            return f"Reminder: Payment of ${amount:,.2f} to {payee_name} is coming up."
        case _:
            return f"Notification regarding ${amount:,.2f} payment to {payee_name}."
