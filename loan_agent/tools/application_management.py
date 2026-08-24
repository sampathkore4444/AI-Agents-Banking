"""
Loan Application Management Tool — MCP tool stub.

Handles loan application lifecycle: create, update, status, underwriting decision.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory application store
_applications: dict[str, dict] = {}


async def create_loan_application(
    customer_id: str,
    loan_type: str,
    loan_amount: float,
    purpose: str,
    term_months: int,
    property_address: dict | None = None,
) -> dict:
    """Create a new loan application."""
    logger.info("Creating loan application: customer=%s, type=%s, amount=$%.2f", customer_id, loan_type, loan_amount)

    app_id = f"LOAN-{uuid.uuid4().hex[:8].upper()}"
    application = {
        "application_id": app_id,
        "customer_id": customer_id,
        "loan_type": loan_type,
        "loan_amount": loan_amount,
        "purpose": purpose,
        "term_months": term_months,
        "property_address": property_address,
        "status": "submitted",
        "substage": "document_collection",
        "documents_received": [],
        "documents_required": ["payslip", "bank_statement", "tax_return", "id_document", "proof_of_address"],
        "credit_check_done": False,
        "income_verified": False,
        "underwriting_decision": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _applications[app_id] = application
    logger.info("Loan application created: %s", app_id)
    return application


async def get_application(application_id: str) -> dict:
    """Retrieve a loan application by ID."""
    app = _applications.get(application_id)
    if not app:
        return {"error": f"Application {application_id} not found"}
    return app


async def update_application(
    application_id: str,
    status: str | None = None,
    substage: str | None = None,
    documents_received: list[str] | None = None,
    credit_check_done: bool | None = None,
    income_verified: bool | None = None,
    underwriting_decision: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update a loan application."""
    app = _applications.get(application_id)
    if not app:
        return {"error": f"Application {application_id} not found"}

    if status:
        app["status"] = status
    if substage:
        app["substage"] = substage
    if documents_received:
        app["documents_received"] = list(set(app["documents_received"] + documents_received))
    if credit_check_done is not None:
        app["credit_check_done"] = credit_check_done
    if income_verified is not None:
        app["income_verified"] = income_verified
    if underwriting_decision:
        app["underwriting_decision"] = underwriting_decision
    if notes:
        app["notes"] = notes
    app["updated_at"] = datetime.utcnow().isoformat()

    logger.info("Loan application %s updated: status=%s", application_id, status)
    return app


async def calculate_affordability(
    annual_income: float,
    monthly_debts: float,
    loan_amount: float,
    interest_rate: float,
    term_months: int,
) -> dict:
    """Calculate loan affordability metrics."""
    monthly_income = annual_income / 12
    monthly_rate = interest_rate / 100 / 12

    # Monthly payment (amortization)
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    else:
        monthly_payment = loan_amount / term_months

    total_debt_to_income = (monthly_debts + monthly_payment) / monthly_income
    front_end_ratio = monthly_payment / monthly_income
    back_end_ratio = total_debt_to_income

    # Total cost of loan
    total_paid = monthly_payment * term_months
    total_interest = total_paid - loan_amount

    # Pass/fail criteria
    max_dti = 0.43
    max_front = 0.28
    passes_dti = back_end_ratio <= max_dti
    passes_front = front_end_ratio <= max_front

    return {
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "term_months": term_months,
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "annual_income": annual_income,
        "monthly_income": round(monthly_income, 2),
        "monthly_existing_debts": monthly_debts,
        "front_end_ratio": round(front_end_ratio, 4),
        "back_end_ratio": round(back_end_ratio, 4),
        "max_dti_allowed": max_dti,
        "passes_dti_check": passes_dti,
        "passes_front_end_check": passes_front,
        "affordable": passes_dti and passes_front,
        "debt_to_income_pct": round(total_debt_to_income * 100, 1),
    }
