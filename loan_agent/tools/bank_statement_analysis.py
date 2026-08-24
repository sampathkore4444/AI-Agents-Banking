"""
Bank Statement Analysis Tool — MCP tool stub.

Deep analysis of bank statements for credit scoring:
- Transaction categorization (income, expenses, recurring, one-time)
- Spending pattern analysis
- Income stability detection
- Irregularity detection (NSF fees, overdrafts, large unexplained deposits)
- Cash flow analysis
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Transaction categories
CATEGORIES = {
    "income": ["payroll", "direct_deposit", "transfer_in", "refund", "dividend", "interest"],
    "housing": ["rent", "mortgage", "property_tax", "hoa", "home_insurance"],
    "utilities": ["electric", "gas", "water", "internet", "phone", "sewage"],
    "transportation": ["car_payment", "gas", "insurance", "parking", "toll", "ride_share"],
    "food": ["groceries", "restaurants", "coffee", "delivery"],
    "financial": ["savings", "investment", "loan_payment", "credit_card_payment", "insurance"],
    "personal": ["clothing", "health", "entertainment", "subscription", "gym"],
    "irregular": ["nsf_fee", "overdraft", "late_fee", "gambling", "cash_withdrawal"],
}


async def analyze_bank_statement(
    customer_id: str,
    statement_url: str,
    statement_months: int = 6,
) -> dict:
    """
    Perform deep analysis of bank statements for credit scoring.

    Categorizes transactions, analyzes spending patterns, detects irregularities,
    and provides cash flow metrics for underwriting.
    """
    logger.info("Analyzing bank statement for customer %s (%d months)", customer_id, statement_months)

    # Stub: generate plausible analysis
    stmt_hash = hashlib.md5(f"{customer_id}{statement_url}".encode()).hexdigest()
    hash_val = int(stmt_hash[:8], 16)

    # Monthly income (stable vs variable)
    base_income = 4000 + (hash_val % 8000)
    income_stability = 0.85 + (hash_val % 15) / 100.0
    monthly_income = [round(base_income * (0.95 + (i % 3) * 0.025), 2) for i in range(statement_months)]

    # Monthly expenses breakdown
    monthly_expenses = []
    for month in range(statement_months):
        expenses = {
            "housing": round(base_income * (0.25 + (hash_val % 10) / 100), 2),
            "utilities": round(150 + (hash_val % 200), 2),
            "transportation": round(300 + (hash_val % 400), 2),
            "food": round(400 + (hash_val % 600), 2),
            "financial": round(base_income * (0.1 + (hash_val % 15) / 100), 2),
            "personal": round(200 + (hash_val % 500), 2),
        }
        expenses["total"] = sum(expenses.values())
        monthly_expenses.append(expenses)

    # Calculate averages
    avg_monthly_income = round(sum(monthly_income) / len(monthly_income), 2)
    avg_monthly_expenses = round(sum(m["total"] for m in monthly_expenses) / len(monthly_expenses), 2)
    avg_monthly_savings = round(avg_monthly_income - avg_monthly_expenses, 2)
    savings_rate = round(avg_monthly_savings / max(avg_monthly_income, 1), 4)

    # Detect irregularities
    irregularities = []
    if hash_val % 100 < 15:  # 15% chance of NSF
        irregularities.append({"type": "nsf_fee", "count": 1 + hash_val % 3, "severity": "medium"})
    if hash_val % 100 < 10:  # 10% chance of overdraft
        irregularities.append({"type": "overdraft", "count": 1, "severity": "high"})
    if hash_val % 100 < 20:  # 20% chance of large cash withdrawal
        irregularities.append({"type": "large_cash_withdrawal", "amount": round(1000 + hash_val % 5000, 2), "severity": "low"})

    # Income trend (stable, increasing, decreasing)
    income_trend = "stable" if income_stability > 0.9 else "increasing" if monthly_income[-1] > monthly_income[0] else "decreasing"

    # Minimum balance check
    min_balance = round(500 + hash_val % 5000, 2)

    # Detect recurring payments
    recurring_payments = []
    if hash_val % 2 == 0:
        recurring_payments.append({"description": "Netflix", "amount": 15.99, "frequency": "monthly"})
    if hash_val % 3 == 0:
        recurring_payments.append({"description": "Gym membership", "amount": 49.99, "frequency": "monthly"})
    if hash_val % 4 == 0:
        recurring_payments.append({"description": "Car insurance", "amount": 150.00, "frequency": "monthly"})

    # Overall assessment
    risk_signals = []
    if income_stability < 0.85:
        risk_signals.append("unstable_income")
    if savings_rate < 0:
        risk_signals.append("negative_cash_flow")
    if len([i for i in irregularities if i["severity"] == "high"]) > 0:
        risk_signals.append("high_severity_irregularities")
    if min_balance < 500:
        risk_signals.append("low_minimum_balance")

    # Creditworthiness score (0-100)
    creditworthiness = 50
    if income_stability > 0.9: creditworthiness += 15
    if savings_rate > 0.1: creditworthiness += 15
    if len(irregularities) == 0: creditworthiness += 10
    if min_balance > 2000: creditworthiness += 10
    if income_trend == "increasing": creditworthiness += 5
    creditworthiness -= len(risk_signals) * 5
    creditworthiness = max(0, min(100, creditworthiness))

    result = {
        "analysis_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "statement_months_analyzed": statement_months,
        "income_analysis": {
            "average_monthly_income": avg_monthly_income,
            "income_stability_score": round(income_stability, 3),
            "income_trend": income_trend,
            "monthly_income": monthly_income,
        },
        "expense_analysis": {
            "average_monthly_expenses": avg_monthly_expenses,
            "expense_breakdown": {
                "housing": round(sum(m["housing"] for m in monthly_expenses) / len(monthly_expenses), 2),
                "utilities": round(sum(m["utilities"] for m in monthly_expenses) / len(monthly_expenses), 2),
                "transportation": round(sum(m["transportation"] for m in monthly_expenses) / len(monthly_expenses), 2),
                "food": round(sum(m["food"] for m in monthly_expenses) / len(monthly_expenses), 2),
                "financial": round(sum(m["financial"] for m in monthly_expenses) / len(monthly_expenses), 2),
                "personal": round(sum(m["personal"] for m in monthly_expenses) / len(monthly_expenses), 2),
            },
        },
        "cash_flow": {
            "average_monthly_savings": avg_monthly_savings,
            "savings_rate": savings_rate,
            "minimum_balance": min_balance,
        },
        "recurring_payments": recurring_payments,
        "irregularities": irregularities,
        "irregularity_count": len(irregularities),
        "risk_signals": risk_signals,
        "creditworthiness_score": creditworthiness,
        "analyzed_at": datetime.utcnow().isoformat(),
    }

    logger.info("Bank statement analysis complete: creditworthiness=%d, irregularities=%d", creditworthiness, len(irregularities))
    return result
