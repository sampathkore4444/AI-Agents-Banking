"""
Credit Bureau Tool — MCP tool stub.

In production this would call Experian, Equifax, or TransUnion.
Returns simulated credit report data for development.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def get_credit_report(
    customer_name: str,
    date_of_birth: str,
    ssn_last_four: str,
    address: dict | None = None,
) -> dict:
    """
    Retrieve a credit report from the credit bureau.

    Returns credit score, credit history, outstanding debts, and payment history.
    """
    logger.info("Fetching credit report for %s (DOB: %s)", customer_name, date_of_birth)

    # Stub: deterministic result based on input
    name_hash = hashlib.md5(f"{customer_name}{ssn_last_four}".encode()).hexdigest()
    hash_val = int(name_hash[:8], 16)

    # Generate plausible credit score (300-850 range)
    credit_score = 580 + (hash_val % 270)  # Range: 580-849

    # Determine credit grade
    if credit_score >= 750:
        grade = "A"
    elif credit_score >= 700:
        grade = "B"
    elif credit_score >= 650:
        grade = "C"
    elif credit_score >= 600:
        grade = "D"
    else:
        grade = "F"

    # Generate credit factors
    payment_history_score = "excellent" if credit_score > 750 else "good" if credit_score > 650 else "fair" if credit_score > 600 else "poor"
    credit_utilization = round(min(max(hash_val % 100 / 100.0, 0.05), 0.95), 2)
    credit_age_years = 2 + (hash_val % 25)

    # Generate open accounts
    num_accounts = 3 + (hash_val % 12)

    # Generate outstanding debts
    total_debt = round(1000 + (hash_val % 49000), 2)

    # Derogatory marks
    derogatory = 0 if credit_score > 700 else 1 if credit_score > 650 else 2 + (hash_val % 3)

    # Inquiries
    inquiries_last_2yr = 0 if credit_score > 700 else 1 + (hash_val % 5)

    result = {
        "report_id": str(uuid.uuid4()),
        "customer_name": customer_name,
        "credit_score": credit_score,
        "credit_grade": grade,
        "credit_factors": {
            "payment_history": payment_history_score,
            "credit_utilization": credit_utilization,
            "credit_age_years": credit_age_years,
            "num_open_accounts": num_accounts,
            "total_outstanding_debt": total_debt,
            "derogatory_marks": derogatory,
            "hard_inquiries_last_2yr": inquiries_last_2yr,
        },
        "accounts": [
            {"type": "credit_card", "balance": round(total_debt * 0.3, 2), "limit": round(total_debt * 0.3 / max(credit_utilization, 0.1), 2)},
            {"type": "auto_loan", "balance": round(total_debt * 0.4, 2), "monthly_payment": round(total_debt * 0.4 / 48, 2)},
            {"type": "student_loan", "balance": round(total_debt * 0.3, 2), "monthly_payment": round(total_debt * 0.3 / 120, 2)},
        ],
        "score_range": {"min": 300, "max": 850},
        "bureau": "simulated",
        "retrieved_at": datetime.utcnow().isoformat(),
    }

    logger.info("Credit report retrieved: score=%d, grade=%s", credit_score, grade)
    return result
