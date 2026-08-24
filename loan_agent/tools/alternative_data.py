"""
Alternative Data Tool — MCP tool stub.

Gathers non-traditional credit data for customers with thin credit files:
- Rent payment history
- Utility payment history
- Phone/internet payment history
- Subscription service payments
- Employment stability
- Education level
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_alternative_data(
    customer_id: str,
    data_types: list[str] | None = None,
) -> dict:
    """
    Gather alternative credit data for customers with limited credit history.

    Useful for:
    - Young adults with thin credit files
    - Immigrants with no US credit history
    - Customers with credit issues rebuilding
    """
    logger.info("Checking alternative data for customer %s", customer_id)

    data_types = data_types or ["rent", "utilities", "phone", "employment"]

    # Stub: generate plausible alternative data
    cust_hash = hashlib.md5(customer_id.encode()).hexdigest()
    hash_val = int(cust_hash[:8], 16)

    results = {}

    if "rent" in data_types:
        rent_paid_on_time = 0.85 + (hash_val % 15) / 100.0
        results["rent"] = {
            "source": "rent_payment_service",
            "monthly_rent": round(1200 + hash_val % 1800, 2),
            "months_tracked": 12 + hash_val % 24,
            "payments_on_time": round(rent_paid_on_time * (12 + hash_val % 24)),
            "payments_late": round((1 - rent_paid_on_time) * (12 + hash_val % 24)),
            "on_time_rate": round(rent_paid_on_time, 3),
            "landlord_verified": hash_val % 3 == 0,
            "score_impact": "positive" if rent_paid_on_time > 0.9 else "neutral" if rent_paid_on_time > 0.7 else "negative",
        }

    if "utilities" in data_types:
        util_paid_on_time = 0.90 + (hash_val % 10) / 100.0
        results["utilities"] = {
            "source": "utility_payment_data",
            "providers": ["electric", "gas", "water", "internet"],
            "months_tracked": 12 + hash_val % 36,
            "payments_on_time": round(util_paid_on_time * (12 + hash_val % 36)),
            "payments_late": round((1 - util_paid_on_time) * (12 + hash_val % 36)),
            "on_time_rate": round(util_paid_on_time, 3),
            "disconnects": 0 if util_paid_on_time > 0.95 else 1 if hash_val % 5 == 0 else 0,
            "score_impact": "positive" if util_paid_on_time > 0.95 else "neutral",
        }

    if "phone" in data_types:
        phone_paid_on_time = 0.88 + (hash_val % 12) / 100.0
        results["phone"] = {
            "source": "carrier_payment_data",
            "carrier": "major_carrier",
            "months_tracked": 12 + hash_val % 24,
            "payments_on_time": round(phone_paid_on_time * (12 + hash_val % 24)),
            "on_time_rate": round(phone_paid_on_time, 3),
            "plan_type": "postpaid",
            "score_impact": "positive" if phone_paid_on_time > 0.9 else "neutral",
        }

    if "employment" in data_types:
        results["employment"] = {
            "source": "employment_verification",
            "current_employer_years": 1 + hash_val % 10,
            "total_work_experience_years": 3 + hash_val % 20,
            "industry": ["technology", "healthcare", "finance", "education", "manufacturing"][hash_val % 5],
            "job_stability": "stable" if hash_val % 100 > 20 else "moderate",
            "income_trend": "increasing" if hash_val % 3 == 0 else "stable",
        }

    if "education" in data_types:
        results["education"] = {
            "source": "education_verification",
            "highest_degree": ["high_school", "bachelors", "masters", "doctorate"][hash_val % 4],
            "institution_type": "accredited",
            "field_of_study": "business",
        }

    # Calculate alternative credit score
    total_score = 0
    factors = []
    for data_type, data in results.items():
        if "on_time_rate" in data:
            total_score += data["on_time_rate"] * 100
            factors.append(f"{data_type}: {data['on_time_rate']*100:.0f}% on-time")
        elif "current_employer_years" in data:
            total_score += min(data["current_employer_years"] * 5, 30)
            factors.append(f"employment: {data['current_employer_years']} years")

    alternative_score = round(total_score / max(len(results), 1), 1)

    # Determine if alternative data is sufficient
    sufficient_data = len(results) >= 3
    confidence = round(min(0.5 + len(results) * 0.1, 0.95), 2)

    result = {
        "check_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "data_sources_checked": list(results.keys()),
        "data": results,
        "alternative_credit_score": alternative_score,
        "confidence_score": confidence,
        "sufficient_data": sufficient_data,
        "key_factors": factors,
        "recommendation": (
            "Alternative data supports creditworthiness" if alternative_score > 75
            else "Alternative data shows some concerns" if alternative_score > 50
            else "Insufficient alternative data to support application"
        ),
        "checked_at": datetime.utcnow().isoformat(),
    }

    logger.info("Alternative data check: score=%.1f, sources=%d", alternative_score, len(results))
    return result
