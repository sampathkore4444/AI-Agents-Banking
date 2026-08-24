"""
Notification Tool — MCP tool stub for collections communications.

Handles FDCPA-compliant notifications via email, SMS, and physical mail.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

COLLECTIONS_TEMPLATES = {
    # Early-stage reminders
    "payment_reminder": "Hi {borrower_name}, this is a friendly reminder that your {product_type} payment of ${payment_amount:,.2f} was due on {due_date}. Please make your payment at your earliest convenience. If you've already paid, please disregard this message.",
    "past_due_notice": "Dear {borrower_name}, our records show that your {product_type} account ({account_id}) is now {delinquency_days} days past due with an outstanding balance of ${balance:,.2f}. Please contact us to discuss payment options. We're here to help.",

    # Mid-stage outreach
    "hardship_inquiry": "Dear {borrower_name}, we understand that circumstances may have changed. If you're experiencing financial difficulty, we have programs that may help. Please call us at {contact_number} to discuss options like payment plans, deferment, or hardship programs.",
    "payment_plan_offer": "Dear {borrower_name}, we'd like to help you get your {product_type} account back on track. We've prepared a payment plan option: ${monthly_amount:,.2f}/month for {total_months} months. Contact us to review and accept this plan.",

    # Late-stage / formal
    "demand_letter": "Dear {borrower_name}, despite previous attempts to contact you, your {product_type} account ({account_id}) remains past due. The current balance is ${balance:,.2f}. You have {days_to_respond} days to respond before further action is taken. This is an attempt to collect a debt.",

    # Settlement
    "settlement_offer": "Dear {borrower_name}, we're offering to settle your account ({account_id}) for ${settlement_amount:,.2f} ({settlement_percentage}% of the ${balance:,.2f} balance). This offer expires on {deadline}. Please note: forgiven debt over $600 may be reported as taxable income (IRS Form 1099-C).",

    # Hardship program
    "forbearance_approved": "Dear {borrower_name}, your request for forbearance has been approved. Your payments will be reduced/suspended for {forbearance_months} months starting {start_date}. During this period, {interest_note}. Please contact us if your situation changes.",

    # Compliance-required
    "validation_notice": "NOTICE: This is an attempt to collect a debt. Any information obtained will be used for that purpose. You have the right to dispute this debt within 30 days. If you dispute the debt in writing within 30 days, we will obtain verification and mail it to you. You have the right to request the name and address of the original creditor.",

    # Confirmation
    "payment_confirmation": "Thank you, {borrower_name}. We've received your payment of ${payment_amount:,.2f} on {payment_date}. Your new balance is ${new_balance:,.2f}. {next_payment_note}",
    "plan_confirmation": "Dear {borrower_name}, your payment plan (ID: {plan_id}) has been confirmed. Monthly payment: ${monthly_amount:,.2f}, Duration: {total_months} months, Total: ${total_amount:,.2f}. Your first payment is due on {first_payment_date}.",
}


async def send_notification(
    recipient_type: str,
    recipient_id: str,
    channel: str,
    template_id: str,
    variables: dict | None = None,
    fdcpa_compliant: bool = True,
) -> dict:
    """
    Send a FDCPA-compliant notification to a borrower.

    channel: "email", "sms", "mail", "phone"
    """
    logger.info("Sending notification: template=%s, recipient=%s, channel=%s", template_id, recipient_id, channel)

    template = COLLECTIONS_TEMPLATES.get(template_id, "")

    # FDCPA compliance: add required disclosures for certain channels
    if fdcpa_compliant:
        if template_id in ("demand_letter", "validation_notice", "settlement_offer"):
            # These are FDCPA-regulated communications
            if "attempt to collect a debt" not in template.lower():
                template += "\n\nThis is an attempt to collect a debt. Any information obtained will be used for that purpose."

    if template and variables:
        try:
            message = template.format(**variables)
        except KeyError as e:
            message = f"[Template variable missing: {e}] {template}"
    else:
        message = template or f"[No template found for {template_id}]"

    result = {
        "notification_id": str(uuid.uuid4()),
        "recipient_type": recipient_type,
        "recipient_id": recipient_id,
        "channel": channel,
        "template_id": template_id,
        "message_preview": message[:300],
        "message_length": len(message),
        "fdcpa_compliant": fdcpa_compliant,
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
        "retention_required": True,
        "retention_period": "7 years",
    }

    logger.info("Notification sent: %s via %s", template_id, channel)
    return result


async def send_validation_notice(
    account_id: str,
    borrower_name: str,
    amount_owed: float,
    creditor_name: str,
    channel: str = "mail",
) -> dict:
    """Send FDCPA-required validation notice within 5 days of initial communication."""
    return await send_notification(
        recipient_type="borrower",
        recipient_id=account_id,
        channel=channel,
        template_id="validation_notice",
        variables={
            "borrower_name": borrower_name,
            "account_id": account_id,
            "amount_owed": f"{amount_owed:,.2f}",
            "creditor_name": creditor_name,
        },
        fdcpa_compliant=True,
    )


async def send_demand_letter(
    account_id: str,
    borrower_name: str,
    product_type: str,
    balance: float,
    days_to_respond: int = 30,
    channel: str = "mail",
) -> dict:
    """Send formal demand letter for late-stage collections."""
    return await send_notification(
        recipient_type="borrower",
        recipient_id=account_id,
        channel=channel,
        template_id="demand_letter",
        variables={
            "borrower_name": borrower_name,
            "product_type": product_type,
            "account_id": account_id,
            "balance": f"{balance:,.2f}",
            "days_to_respond": days_to_respond,
        },
        fdcpa_compliant=True,
    )
