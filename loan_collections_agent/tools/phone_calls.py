"""
Phone Calls Tool — MCP tool stub for collections.

Handles outbound collection calls, call scripting, outcome tracking,
call scheduling, voicemail drops, and FDCPA-compliant call procedures.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory call store
_call_log: list[dict] = []
_scheduled_calls: dict[str, dict] = {}

# FDCPA-compliant call scripts by stage
CALL_SCRIPTS = {
    "early_stage": {
        "opening": "Hello, this is {collector_name} calling from {bank_name}. Am I speaking with {borrower_name}? This is an attempt to collect a debt and any information obtained will be used for that purpose. I'm calling regarding your {product_type} account which is currently {delinquency_days} days past due.",
        "payment_reminder": "I understand things come up. I'm calling to see if we can help you get your account current. Your past due amount is ${past_due_amount:,.2f}. Would you be able to make a payment today?",
        "payment_options": "We have a few options available: 1) You can pay the full past due amount of ${past_due_amount:,.2f} today, 2) We can set up a short-term payment plan, or 3) If you're experiencing financial difficulty, we have hardship programs. Which would you prefer?",
        "closing": "Thank you for your time, {borrower_name}. I'll note our conversation in your file. Is there a good time to follow up? Remember, you can also reach us at {contact_number} or visit our online portal to make a payment.",
        "voicemail": "Hello {borrower_name}, this is {collector_name} from {bank_name} calling about your {product_type} account. Please call us back at {contact_number} at your earliest convenience. This is an attempt to collect a debt.",
    },
    "mid_stage": {
        "opening": "Hello, this is {collector_name} from {bank_name}. May I speak with {borrower_name}? I'm calling about your {product_type} account which is now {delinquency_days} days past due with a balance of ${balance:,.2f}. This is an attempt to collect a debt.",
        "hardship_assessment": "I understand you may be going through a difficult time. Can you tell me a bit about your current situation? I want to find a solution that works for both of us. Are you currently employed? Have your expenses changed recently?",
        "payment_plan_offer": "Based on what you've shared, I'd like to offer you a payment plan. We can spread your past due amount of ${past_due_amount:,.2f} over {plan_months} months at ${monthly_amount:,.2f}/month. Would that work for you?",
        "settlement_offer": "I have a settlement offer for you. If you can make a payment of ${settlement_amount:,.2f} by {deadline}, we can consider your account settled. This would be {settlement_percentage}% of your current balance. Please note, forgiven debt over $600 may be reported as taxable income.",
        "closing": "I've noted our discussion. Your account reference is {account_id}. If your situation changes, please call us at {contact_number}. We want to help you resolve this.",
        "voicemail": "Hello {borrower_name}, this is {collector_name} from {bank_name}. We'd like to discuss options for your {product_type} account. Please call us at {contact_number}. This is an attempt to collect a debt.",
    },
    "late_stage": {
        "opening": "Hello, this is {collector_name} from {bank_name} calling about {borrower_name}'s account. This is an attempt to collect a debt. Your {product_type} account ({account_id}) is {delinquency_days} days past due with an outstanding balance of ${balance:,.2f}.",
        "demand": "Despite previous attempts to contact you, your account remains past due. We need to resolve this matter promptly. What is your plan for bringing this account current?",
        "settlement_ultimatum": "We're prepared to offer a final settlement of ${settlement_amount:,.2f} ({settlement_percentage}% of balance) if accepted by {deadline}. If we don't reach an agreement, we may need to consider other recovery options. I strongly encourage you to take advantage of this offer.",
        "legal_notice": "I want to inform you that if we cannot resolve this matter, {bank_name} may pursue legal remedies which could include a lawsuit, wage garnishment, or other collection actions permitted by law. This is not a threat — it's information about what may happen.",
        "closing": "I've documented our conversation. Your account reference is {account_id}. You have until {deadline} to respond to our offer. If you have questions, call us at {contact_number}.",
        "voicemail": "Hello, this is {collector_name} from {bank_name} calling about an important matter regarding your account. Please call us immediately at {contact_number}. This is an attempt to collect a debt.",
    },
}

# Call outcome templates
CALL_OUTCOMES = {
    "promised_to_pay": {
        "description": "Borrower promised to make a payment",
        "follow_up_days": 7,
        "next_action": "Follow up to confirm payment was made",
    },
    "payment_made": {
        "description": "Payment received during or immediately after call",
        "follow_up_days": 30,
        "next_action": "Send payment confirmation, schedule next check-in",
    },
    "hardship_identified": {
        "description": "Borrower reported financial hardship",
        "follow_up_days": 3,
        "next_action": "Initiate hardship assessment, request documentation",
    },
    "payment_plan_agreed": {
        "description": "Borrower agreed to a payment plan",
        "follow_up_days": 14,
        "next_action": "Send plan confirmation, set up autopay reminder",
    },
    "settlement_agreed": {
        "description": "Borrower agreed to settlement terms",
        "follow_up_days": 3,
        "next_action": "Send settlement agreement, process payment",
    },
    "no_answer": {
        "description": "No answer, left voicemail",
        "follow_up_days": 3,
        "next_action": "Retry call, try alternate number or email",
    },
    "wrong_number": {
        "description": "Reached wrong person",
        "follow_up_days": 1,
        "next_action": "Verify contact information, try alternate number",
    },
    "refused_to_pay": {
        "description": "Borrower refused to make payment",
        "follow_up_days": 14,
        "next_action": "Escalate to supervisor, consider alternative approach",
    },
    "disputed_debt": {
        "description": "Borrower disputed the debt",
        "follow_up_days": 0,
        "next_action": "CEASE collection activity, send verification within 30 days",
    },
    "ceased_requested": {
        "description": "Borrower requested cease of communication",
        "follow_up_days": 0,
        "next_action": "STOP all contact (except lawsuit notification), update account",
    },
    "callback_scheduled": {
        "description": "Borrower asked to call back at specific time",
        "follow_up_days": 0,
        "next_action": "Schedule callback for requested time",
    },
}


async def initiate_call(
    account_id: str,
    borrower_name: str,
    phone_number: str,
    collector_name: str,
    bank_name: str,
    collection_stage: str,
    product_type: str,
    delinquency_days: int,
    balance: float,
    past_due_amount: float,
    daily_attempts: int = 0,
) -> dict:
    """
    Initiate an outbound collection call with FDCPA-compliant scripting.

    Returns the call script, compliance checklist, and call metadata.
    """
    logger.info("Initiating call: account=%s, stage=%s, borrower=%s", account_id, collection_stage, borrower_name)

    call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"

    # Get script for stage
    script = CALL_SCRIPTS.get(collection_stage, CALL_SCRIPTS["early_stage"])

    # Build personalized script
    script_vars = {
        "collector_name": collector_name,
        "bank_name": bank_name,
        "borrower_name": borrower_name,
        "product_type": product_type,
        "delinquency_days": delinquency_days,
        "balance": f"{balance:,.2f}",
        "past_due_amount": f"{past_due_amount:,.2f}",
        "account_id": account_id,
        "contact_number": "1-800-555-0199",
    }

    personalized_script = {}
    for key, template in script.items():
        try:
            personalized_script[key] = template.format(**script_vars)
        except KeyError:
            personalized_script[key] = template

    # FDCPA pre-call checklist
    compliance_checklist = [
        {"item": "Call during permitted hours (8AM-9PM local)", "status": "check"},
        {"item": f"Daily attempts: {daily_attempts}/3 (FDCPA max)", "status": "ok" if daily_attempts < 3 else "BLOCKED"},
        {"item": "Borrower not on Do Not Call list", "status": "check"},
        {"item": "No cease and desist on file", "status": "check"},
        {"item": "No attorney representation on file", "status": "check"},
        {"item": "Validation notice sent within 5 days", "status": "check"},
        {"item": "Recording consent obtained (if applicable)", "status": "check"},
    ]

    # Determine if call should proceed
    can_proceed = daily_attempts < 3
    blocked_reason = None if can_proceed else f"Daily attempt limit reached ({daily_attempts}/3)"

    call = {
        "call_id": call_id,
        "account_id": account_id,
        "borrower_name": borrower_name,
        "phone_number": phone_number,
        "collector_name": collector_name,
        "collection_stage": collection_stage,
        "initiated_at": datetime.utcnow().isoformat(),
        "status": "initiated" if can_proceed else "blocked",
        "blocked_reason": blocked_reason,
        "script": personalized_script,
        "compliance_checklist": compliance_checklist,
        "can_proceed": can_proceed,
    }

    _call_log.append(call)
    return call


async def record_call_outcome(
    call_id: str,
    outcome: str,
    call_duration_seconds: int,
    notes: str | None = None,
    borrower_promised_amount: float | None = None,
    borrower_promised_date: str | None = None,
    recording_consent: bool = False,
    new_information: dict | None = None,
) -> dict:
    """
    Record the outcome of a collection call.

    outcome: key from CALL_OUTCOMES (promised_to_pay, no_answer, disputed_debt, etc.)
    """
    logger.info("Recording call outcome: call=%s, outcome=%s", call_id, outcome)

    # Find the call
    call = None
    for c in _call_log:
        if c["call_id"] == call_id:
            call = c
            break

    if not call:
        return {"error": f"Call {call_id} not found"}

    outcome_info = CALL_OUTCOMES.get(outcome, {})

    # Calculate follow-up date
    follow_up_days = outcome_info.get("follow_up_days", 7)
    follow_up_date = (datetime.utcnow() + timedelta(days=follow_up_days)).strftime("%Y-%m-%d") if follow_up_days > 0 else None

    result = {
        "call_id": call_id,
        "account_id": call["account_id"],
        "outcome": outcome,
        "outcome_description": outcome_info.get("description", outcome),
        "call_duration_seconds": call_duration_seconds,
        "call_duration_display": f"{call_duration_seconds // 60}m {call_duration_seconds % 60}s",
        "notes": notes,
        "recording_consent": recording_consent,
        "borrower_promised_amount": borrower_promised_amount,
        "borrower_promised_date": borrower_promised_date,
        "new_information": new_information,
        "next_action": outcome_info.get("next_action", "Review and follow up"),
        "follow_up_date": follow_up_date,
        "recorded_at": datetime.utcnow().isoformat(),
    }

    # Special handling for critical outcomes
    if outcome == "disputed_debt":
        result["urgent_action"] = "CEASE all collection activity. Send debt verification within 30 days."
        result["compliance_flag"] = "FDCPA §1692g(b) — verification required"
    elif outcome == "ceased_requested":
        result["urgent_action"] = "STOP all communication immediately. Only lawsuit notifications permitted."
        result["compliance_flag"] = "FDCPA §1692c(c) — cease and desist"
    elif outcome == "promised_to_pay":
        result["compliance_flag"] = "Document promise for follow-up tracking"

    # Update call record
    call["outcome"] = outcome
    call["outcome_recorded_at"] = datetime.utcnow().isoformat()
    call["call_duration_seconds"] = call_duration_seconds

    _call_log.append({"type": "outcome", **result})
    return result


async def schedule_callback(
    account_id: str,
    borrower_name: str,
    phone_number: str,
    callback_date: str,
    callback_time: str,
    reason: str,
    collector_id: str,
    notes: str | None = None,
) -> dict:
    """Schedule a follow-up call to a borrower."""
    logger.info("Scheduling callback: account=%s, date=%s, time=%s", account_id, callback_date, callback_time)

    callback_id = f"CB-{uuid.uuid4().hex[:8].upper()}"

    callback = {
        "callback_id": callback_id,
        "account_id": account_id,
        "borrower_name": borrower_name,
        "phone_number": phone_number,
        "callback_date": callback_date,
        "callback_time": callback_time,
        "reason": reason,
        "collector_id": collector_id,
        "notes": notes,
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
    }

    _scheduled_calls[callback_id] = callback
    return callback


async def get_call_history(account_id: str, limit: int = 10) -> dict:
    """Get call history for an account."""
    calls = [c for c in _call_log if c.get("account_id") == account_id and c.get("call_id")]
    calls.sort(key=lambda x: x.get("initiated_at", ""), reverse=True)

    total_calls = len(calls)
    outcomes = {}
    for c in calls:
        o = c.get("outcome", "pending")
        outcomes[o] = outcomes.get(o, 0) + 1

    return {
        "account_id": account_id,
        "total_calls": total_calls,
        "calls": calls[:limit],
        "outcome_summary": outcomes,
    }


async def get_scheduled_callbacks(collector_id: str | None = None, date: str | None = None) -> dict:
    """Get scheduled callbacks, optionally filtered by collector or date."""
    callbacks = list(_scheduled_calls.values())

    if collector_id:
        callbacks = [c for c in callbacks if c.get("collector_id") == collector_id]
    if date:
        callbacks = [c for c in callbacks if c.get("callback_date") == date]

    callbacks.sort(key=lambda x: (x.get("callback_date", ""), x.get("callback_time", "")))

    return {
        "total_scheduled": len(callbacks),
        "callbacks": callbacks,
    }


async def leave_voicemail(
    account_id: str,
    borrower_name: str,
    collector_name: str,
    bank_name: str,
    product_type: str,
    phone_number: str,
    collection_stage: str,
) -> dict:
    """Leave a FDCPA-compliant voicemail."""
    logger.info("Leaving voicemail: account=%s, stage=%s", account_id, collection_stage)

    script = CALL_SCRIPTS.get(collection_stage, CALL_SCRIPTS["early_stage"])
    voicemail_template = script.get("voicemail", "")

    voicemail_text = voicemail_template.format(
        collector_name=collector_name,
        bank_name=bank_name,
        borrower_name=borrower_name,
        product_type=product_type,
        contact_number="1-800-555-0199",
    )

    call_id = f"VM-{uuid.uuid4().hex[:8].upper()}"

    result = {
        "call_id": call_id,
        "account_id": account_id,
        "type": "voicemail",
        "borrower_name": borrower_name,
        "phone_number": phone_number,
        "voicemail_text": voicemail_text,
        "collection_stage": collection_stage,
        "status": "left",
        "left_at": datetime.utcnow().isoformat(),
        "fdcpa_compliant": True,
        "disclosure": "Includes 'attempt to collect a debt' disclosure",
    }

    _call_log.append(result)
    return result


async def get_call_stats(collector_id: str | None = None) -> dict:
    """Get call statistics for reporting."""
    calls = _call_log
    if collector_id:
        calls = [c for c in calls if c.get("collector_name") == collector_id]

    total = len([c for c in calls if c.get("call_id")])
    outcomes = {}
    total_duration = 0
    total_vm = 0

    for c in calls:
        if c.get("outcome"):
            o = c["outcome"]
            outcomes[o] = outcomes.get(o, 0) + 1
        if c.get("call_duration_seconds"):
            total_duration += c["call_duration_seconds"]
        if c.get("type") == "voicemail":
            total_vm += 1

    return {
        "total_calls": total,
        "total_voicemails": total_vm,
        "total_duration_seconds": total_duration,
        "total_duration_display": f"{total_duration // 3600}h {(total_duration % 3600) // 60}m",
        "outcome_breakdown": outcomes,
        "promised_to_pay_rate": round(outcomes.get("promised_to_pay", 0) / max(total, 1) * 100, 1),
        "contact_rate": round((total - outcomes.get("no_answer", 0) - outcomes.get("wrong_number", 0)) / max(total, 1) * 100, 1),
    }
