"""
Notification Tool — MCP tool stub for reconciliation alerts and reports.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

RECON_TEMPLATES = {
    "reconciliation_complete": "Reconciliation for account {account_number} completed. Matched: {matched_count}/{total_entries} entries ({match_rate}%). Exceptions: {exception_count}.",
    "exception_escalation": "EXCEPTION ESCALATION: {exception_type} on {account_number} — ${amount:,.2f} discrepancy. Aging: {aging_days} days. Assigned to: {assigned_to}.",
    "daily_recon_summary": "Daily Reconciliation Summary — Date: {date}. Accounts reconciled: {accounts_reconciled}. Total matched: {total_matched}. Open exceptions: {open_exceptions}. Total exception amount: ${exception_amount:,.2f}.",
    "discrepancy_alert": "DISCREPANCY ALERT: ${amount:,.2f} mismatch on {account_number} (Bank: ${bank_amount:,.2f} vs Ledger: ${ledger_amount:,.2f}). Reference: {reference}.",
    "reconciliation_overdue": "RECONCILIATION OVERDUE: Account {account_number} reconciliation is {days_overdue} days overdue. Please complete by {deadline}.",
    "month_end_complete": "Month-End Reconciliation Complete for {period}. All accounts reconciled. Total adjustments: {adjustment_count}. Net adjustment: ${net_adjustment:,.2f}.",
}


async def send_recon_notification(
    recipient_id: str,
    template_id: str,
    channel: str = "email",
    variables: dict | None = None,
) -> dict:
    """Send a reconciliation notification."""
    template = RECON_TEMPLATES.get(template_id, "")

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

    logger.info("Recon notification sent: %s via %s", template_id, channel)
    return result


async def send_exception_alert(
    exception_id: str,
    exception_type: str,
    amount: float,
    account_number: str,
    assigned_to: str,
    aging_days: int,
) -> dict:
    """Send an exception escalation alert."""
    return await send_recon_notification(
        recipient_id=assigned_to,
        template_id="exception_escalation",
        channel="slack",
        variables={
            "exception_type": exception_type,
            "account_number": account_number,
            "amount": amount,
            "aging_days": aging_days,
            "assigned_to": assigned_to,
        },
    )
