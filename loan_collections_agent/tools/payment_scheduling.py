"""
Payment Scheduling Tool — MCP tool stub for collections.

Manages payment plan creation, modification, and tracking.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory payment plan store
_payment_plans: dict[str, dict] = {}


async def create_payment_plan(
    account_id: str,
    plan_type: str,
    monthly_amount: float,
    total_months: int,
    start_date: str | None = None,
    interest_rate: float | None = None,
    first_payment_date: str | None = None,
) -> dict:
    """
    Create a new payment plan for a delinquent account.

    plan_type: "standard", "graduated", "interest_only", "hardship", "settlement"
    """
    logger.info("Creating payment plan: account=%s, type=%s, amount=%.2f", account_id, plan_type, monthly_amount)

    plan_id = f"PP-{uuid.uuid4().hex[:8].upper()}"
    start = start_date or datetime.utcnow().strftime("%Y-%m-%d")
    first_payment = first_payment_date or (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d")

    # Generate schedule
    schedule = []
    current_date = datetime.strptime(first_payment, "%Y-%m-%d")
    for i in range(total_months):
        payment_date = (current_date + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        schedule.append({
            "installment": i + 1,
            "due_date": payment_date,
            "amount": round(monthly_amount, 2),
            "status": "scheduled",
            "paid_amount": 0.0,
        })

    total_amount = round(monthly_amount * total_months, 2)

    plan = {
        "plan_id": plan_id,
        "account_id": account_id,
        "plan_type": plan_type,
        "monthly_amount": round(monthly_amount, 2),
        "total_months": total_months,
        "total_amount": total_amount,
        "start_date": start,
        "first_payment_date": first_payment,
        "interest_rate": interest_rate,
        "status": "active",
        "payments_completed": 0,
        "payments_remaining": total_months,
        "total_paid": 0.0,
        "balance_remaining": total_amount,
        "schedule": schedule,
        "created_at": datetime.utcnow().isoformat(),
    }

    _payment_plans[plan_id] = plan
    logger.info("Payment plan created: %s", plan_id)
    return plan


async def get_payment_plan(plan_id: str) -> dict:
    """Retrieve a payment plan by ID."""
    plan = _payment_plans.get(plan_id)
    if not plan:
        return {"error": f"Payment plan {plan_id} not found"}
    return plan


async def get_plans_for_account(account_id: str) -> list[dict]:
    """Get all payment plans for an account."""
    return [p for p in _payment_plans.values() if p["account_id"] == account_id]


async def record_payment(plan_id: str, amount: float, payment_date: str | None = None) -> dict:
    """Record a payment against a payment plan."""
    plan = _payment_plans.get(plan_id)
    if not plan:
        return {"error": f"Payment plan {plan_id} not found"}

    payment_date = payment_date or datetime.utcnow().strftime("%Y-%m-%d")

    # Find the next unpaid installment
    for installment in plan["schedule"]:
        if installment["status"] == "scheduled":
            installment["status"] = "paid"
            installment["paid_amount"] = amount
            installment["payment_date"] = payment_date
            break

    plan["payments_completed"] += 1
    plan["payments_remaining"] -= 1
    plan["total_paid"] = round(plan["total_paid"] + amount, 2)
    plan["balance_remaining"] = round(plan["balance_remaining"] - amount, 2)

    # Check if plan is completed
    if plan["payments_remaining"] <= 0:
        plan["status"] = "completed"
        plan["completed_date"] = datetime.utcnow().isoformat()
        logger.info("Payment plan %s COMPLETED", plan_id)

    logger.info("Payment recorded for plan %s: $%.2f", plan_id, amount)
    return plan


async def modify_payment_plan(
    plan_id: str,
    new_monthly_amount: float | None = None,
    new_total_months: int | None = None,
    reason: str | None = None,
) -> dict:
    """Modify an existing payment plan (restructure)."""
    plan = _payment_plans.get(plan_id)
    if not plan:
        return {"error": f"Payment plan {plan_id} not found"}

    old_amount = plan["monthly_amount"]
    old_months = plan["total_months"]

    if new_monthly_amount:
        plan["monthly_amount"] = round(new_monthly_amount, 2)
    if new_total_months:
        plan["total_months"] = new_total_months

    # Recalculate remaining schedule
    remaining_balance = plan["balance_remaining"]
    new_months = plan["total_months"] - plan["payments_completed"]
    plan["payments_remaining"] = max(new_months, 0)

    # Update future schedule
    current_date = datetime.utcnow()
    for installment in plan["schedule"]:
        if installment["status"] == "scheduled":
            installment["amount"] = round(plan["monthly_amount"], 2)

    plan["modification_history"] = plan.get("modification_history", [])
    plan["modification_history"].append({
        "date": datetime.utcnow().isoformat(),
        "old_monthly_amount": old_amount,
        "new_monthly_amount": plan["monthly_amount"],
        "old_total_months": old_months,
        "new_total_months": plan["total_months"],
        "reason": reason or "Restructured",
    })

    plan["status"] = "modified"
    logger.info("Payment plan %s modified", plan_id)
    return plan


async def create_settlement_offer(
    account_id: str,
    settlement_amount: float,
    settlement_percentage: float,
    payment_terms: str,
    deadline_days: int = 30,
    includes_release: bool = True,
) -> dict:
    """Create a settlement offer for an account."""
    logger.info("Creating settlement offer: account=%s, amount=%.2f (%.0f%%)", account_id, settlement_amount, settlement_percentage)

    offer_id = f"SO-{uuid.uuid4().hex[:8].upper()}"
    deadline = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")

    offer = {
        "offer_id": offer_id,
        "account_id": account_id,
        "settlement_amount": round(settlement_amount, 2),
        "settlement_percentage": round(settlement_percentage, 1),
        "payment_terms": payment_terms,
        "deadline": deadline,
        "deadline_days": deadline_days,
        "includes_release": includes_release,
        "tax_notice": "Forgiven debt over $600 may be reported to IRS as taxable income (Form 1099-C).",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }

    return offer


async def check_account_eligibility(account_id: str, program_type: str) -> dict:
    """Check if an account is eligible for a specific program."""
    logger.info("Checking eligibility: account=%s, program=%s", account_id, program_type)

    # Find account in seed data or return generic check
    account = None
    for acc in _accounts.values():
        if acc["account_id"] == account_id:
            account = acc
            break

    if not account:
        return {"error": f"Account {account_id} not found"}

    eligibility = {
        "account_id": account_id,
        "program_type": program_type,
        "eligible": True,
        "conditions": [],
        "reasons": [],
    }

    if program_type == "forbearance":
        if account["delinquency_days"] > 90:
            eligibility["eligible"] = False
            eligibility["reasons"].append("Account exceeds 90-day delinquency threshold for forbearance")
        if not account.get("hardship_flag"):
            eligibility["conditions"].append("Hardship documentation required")
        eligibility["conditions"].append("Trial payment period: 3 months")

    elif program_type == "modification":
        if account["delinquency_days"] > 180:
            eligibility["eligible"] = False
            eligibility["reasons"].append("Account exceeds 180-day threshold — consider charge-off")
        eligibility["conditions"].append("Financial assessment required")
        eligibility["conditions"].append("Trial payment period: 3 months")
        eligibility["conditions"].append("Investor approval required")

    elif program_type == "settlement":
        if account["delinquency_days"] < 60:
            eligibility["eligible"] = False
            eligibility["reasons"].append("Settlement not typically offered before 60 days delinquent")
        if account.get("collateral") and account["collateral"].get("value", 0) > account["current_balance"]:
            eligibility["conditions"].append("Collateral value exceeds balance — may prefer repossession over settlement")

    elif program_type == "payment_plan":
        eligibility["eligible"] = True
        eligibility["conditions"].append("Borrower must demonstrate ability to make payments")

    return eligibility


# Need to import _accounts for eligibility check
from tools.account_management import _accounts
