"""
AML Notifications — Compliance Alerts and Notifications.

Manages:
- AML alert notifications (to compliance officers)
- SAR filing confirmations
- CTR filing confirmations
- Escalation notifications
- Regulatory deadline reminders
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

# ── In-memory store ───────────────────────────────────────────────
_NOTIFICATIONS: list[dict] = []


async def send_aml_alert(
    case_id: str,
    alert_type: str,
    subject: str,
    message: str,
    recipient: str = "compliance_team",
    priority: str = "high",
) -> dict[str, Any]:
    """Send an AML alert notification."""
    notif_id = f"AML-NOT-{hashlib.md5(f'{case_id}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:8].upper()}"

    notif = {
        "notification_id": notif_id,
        "case_id": case_id,
        "alert_type": alert_type,
        "subject": subject,
        "message": message,
        "recipient": recipient,
        "priority": priority,
        "channel": "internal",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }

    _NOTIFICATIONS.append(notif)
    return {
        "notification_id": notif_id,
        "status": "sent",
        "recipient": recipient,
    }


async def send_sar_filing_confirmation(
    sar_id: str,
    customer_name: str,
    amount_involved: float,
    filing_date: str,
) -> dict[str, Any]:
    """Send SAR filing confirmation."""
    notif_id = f"SAR-CONF-{hashlib.md5(sar_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "sar_filing_confirmation",
        "subject": f"SAR Filed: {sar_id}",
        "message": f"SAR {sar_id} filed successfully for {customer_name}. Amount involved: ${amount_involved:,.2f}. Filed on: {filing_date}. Retain copy for 5 years.",
        "recipient": "compliance_officer",
        "priority": "normal",
        "channel": "internal",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def send_ctr_filing_confirmation(ctr_id: str, amount: float, customer_name: str) -> dict[str, Any]:
    """Send CTR filing confirmation."""
    notif_id = f"CTR-CONF-{hashlib.md5(ctr_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "ctr_filing_confirmation",
        "subject": f"CTR Filed: {ctr_id}",
        "message": f"CTR {ctr_id} filed for {customer_name}. Amount: ${amount:,.2f}.",
        "recipient": "compliance_officer",
        "priority": "normal",
        "channel": "internal",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def send_escalation_notification(
    case_id: str,
    escalation_reason: str,
    escalate_to: str,
    law_enforcement_referral: bool = False,
) -> dict[str, Any]:
    """Send escalation notification."""
    priority = "critical" if law_enforcement_referral else "high"
    notif_id = f"ESC-{hashlib.md5(case_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "escalation",
        "subject": f"Case Escalated: {case_id}",
        "message": f"Case {case_id} escalated to {escalate_to}. Reason: {escalation_reason}" + (". Law enforcement referral initiated." if law_enforcement_referral else ""),
        "recipient": escalate_to,
        "priority": priority,
        "channel": "internal",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def send_deadline_reminder(case_id: str, deadline_type: str, deadline_date: str) -> dict[str, Any]:
    """Send deadline reminder."""
    notif_id = f"REMIND-{hashlib.md5(f'{case_id}{deadline_type}'.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "deadline_reminder",
        "subject": f"Deadline Reminder: {deadline_type}",
        "message": f"{deadline_type} for case {case_id} is due on {deadline_date}.",
        "recipient": "compliance_team",
        "priority": "high",
        "channel": "internal",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def send_sar_continuing_reminder(sar_id: str, next_deadline: str) -> dict[str, Any]:
    """Send continuing SAR 90-day filing reminder."""
    notif_id = f"SAR-REMIND-{hashlib.md5(sar_id.encode()).hexdigest()[:8].upper()}"
    notif = {
        "notification_id": notif_id,
        "alert_type": "sar_continuing_reminder",
        "subject": f"Continuing SAR Due: {sar_id}",
        "message": f"Continuing activity SAR for {sar_id} is due on {next_deadline}. Review and file within the 90-day window.",
        "recipient": "compliance_officer",
        "priority": "high",
        "channel": "internal",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
    }
    _NOTIFICATIONS.append(notif)
    return {"notification_id": notif_id, "status": "sent"}


async def get_notification_history(recipient: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get notification history."""
    if recipient:
        filtered = [n for n in _NOTIFICATIONS if n["recipient"] == recipient]
    else:
        filtered = _NOTIFICATIONS

    return {"total": len(filtered), "notifications": filtered[-limit:]}
