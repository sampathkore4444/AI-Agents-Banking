"""
Credit Scoring & Risk Assessment Tool — MCP tool stub.

Enhanced with:
- ML-based customer embedding and clustering
- Explainable decision generation
- Historical pattern matching
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def embed_customer_profile(
    customer_id: str,
    credit_score: int,
    annual_income: float,
    debt_to_income: float,
    loan_to_value: float,
    employment_years: int,
    credit_history_years: int,
    num_open_accounts: int,
    derogatory_marks: int,
) -> dict:
    """
    Create an embedding of the customer's financial profile for clustering.

    This embedding can be compared against historical profiles to:
    - Predict default probability based on similar profiles
    - Identify the customer's risk cluster
    - Find the best product match
    """
    logger.info("Embedding customer profile for %s", customer_id)

    # Generate a synthetic embedding (in production, use a trained model)
    # This creates a 128-dimensional vector representing the customer's profile
    import hashlib
    profile_str = f"{credit_score}_{annual_income}_{debt_to_income}_{loan_to_value}_{employment_years}"
    hash_obj = hashlib.md5(profile_str.encode())

    # Generate deterministic but plausible embedding values
    embedding = []
    for i in range(128):
        byte_val = hash_obj.digest()[i % 16]
        embedding.append(round((byte_val / 255.0) * 2 - 1, 4))  # Range: -1 to 1

    # Determine risk cluster based on profile characteristics
    if credit_score >= 750 and debt_to_income <= 0.28:
        cluster = "prime_borrower"
        cluster_description = "Low-risk prime borrower with excellent credit and low debt"
        default_probability = 0.02
    elif credit_score >= 700 and debt_to_income <= 0.36:
        cluster = "near_prime_borrower"
        cluster_description = "Near-prime borrower with good credit and manageable debt"
        default_probability = 0.05
    elif credit_score >= 650 and debt_to_income <= 0.43:
        cluster = "subprime_borrower"
        cluster_description = "Subprime borrower with fair credit and moderate debt"
        default_probability = 0.12
    elif credit_score >= 600:
        cluster = "high_risk_borrower"
        cluster_description = "High-risk borrower with below-average credit"
        default_probability = 0.25
    else:
        cluster = "very_high_risk_borrower"
        cluster_description = "Very high-risk borrower with poor credit profile"
        default_probability = 0.40

    # Find similar historical profiles (simulated)
    similar_profiles = [
        {"profile_id": f"HIST-{i}", "similarity": round(0.85 - i * 0.05, 2), "outcome": "repaid" if i < 3 else "defaulted"}
        for i in range(5)
    ]

    result = {
        "embedding_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "profile_embedding": embedding,
        "embedding_dimensions": len(embedding),
        "cluster": cluster,
        "cluster_description": cluster_description,
        "default_probability": default_probability,
        "similar_historical_profiles": similar_profiles,
        "profile_metrics": {
            "credit_score": credit_score,
            "annual_income": annual_income,
            "dti": debt_to_income,
            "ltv": loan_to_value,
            "employment_years": employment_years,
            "credit_history_years": credit_history_years,
        },
        "embedded_at": datetime.utcnow().isoformat(),
    }

    logger.info("Customer profile embedded: cluster=%s, default_prob=%.2f", cluster, default_probability)
    return result


async def assess_loan_risk(
    credit_score: int,
    annual_income: float,
    loan_amount: float,
    loan_to_value: float,
    debt_to_income: float,
    employment_type: str,
    loan_type: str,
) -> dict:
    """
    Assess loan risk and recommend underwriting decision.

    Returns risk score, decision recommendation, conditions, and pricing guidance.
    """
    logger.info("Assessing loan risk: credit=%d, income=$%.2f, amount=$%.2f", credit_score, annual_income, loan_amount)

    # Risk scoring model
    risk_score = 0
    risk_factors = []

    # Credit score factor (0-35 points)
    if credit_score >= 750:
        credit_risk = 5
    elif credit_score >= 700:
        credit_risk = 10
    elif credit_score >= 650:
        credit_risk = 20
        risk_factors.append("fair_credit_score")
    elif credit_score >= 600:
        credit_risk = 30
        risk_factors.append("below_average_credit")
    else:
        credit_risk = 35
        risk_factors.append("poor_credit_score")
    risk_score += credit_risk

    # DTI factor (0-25 points)
    if debt_to_income <= 0.28:
        dti_risk = 0
    elif debt_to_income <= 0.36:
        dti_risk = 10
        risk_factors.append("moderate_dti")
    elif debt_to_income <= 0.43:
        dti_risk = 20
        risk_factors.append("high_dti")
    else:
        dti_risk = 25
        risk_factors.append("very_high_dti")
    risk_score += dti_risk

    # LTV factor (0-20 points)
    if loan_to_value <= 0.80:
        ltv_risk = 0
    elif loan_to_value <= 0.90:
        ltv_risk = 10
        risk_factors.append("moderate_ltv")
    elif loan_to_value <= 0.95:
        ltv_risk = 15
        risk_factors.append("high_ltv")
    else:
        ltv_risk = 20
        risk_factors.append("very_high_ltv")
    risk_score += ltv_risk

    # Employment factor (0-10 points)
    if employment_type == "employed":
        emp_risk = 0
    elif employment_type == "self_employed":
        emp_risk = 5
        risk_factors.append("self_employed")
    else:
        emp_risk = 10
        risk_factors.append("non_traditional_employment")
    risk_score += emp_risk

    # Loan type factor (0-10 points)
    if loan_type == "conventional":
        type_risk = 0
    elif loan_type == "fha":
        type_risk = 5
    else:
        type_risk = 10
        risk_factors.append("non_standard_loan")
    risk_score += type_risk

    # Determine decision
    if risk_score <= 15:
        decision = "auto_approve"
        risk_level = "low"
    elif risk_score <= 35:
        decision = "approve_with_conditions"
        risk_level = "medium"
    elif risk_score <= 55:
        decision = "manual_underwriting_required"
        risk_level = "elevated"
    else:
        decision = "decline"
        risk_level = "high"

    # Interest rate guidance
    base_rate = 6.5
    rate_adjustment = risk_score * 0.05
    suggested_rate = round(base_rate + rate_adjustment, 2)

    # Conditions for approval
    conditions = []
    if risk_score > 15:
        if loan_to_value > 0.80:
            conditions.append("mortgage_insurance_required")
        if risk_score > 30:
            conditions.append("additional_documentation")
        if debt_to_income > 0.36:
            conditions.append("lower_loan_amount_recommended")
        if credit_score < 650:
            conditions.append("co_borrower_recommended")
        conditions = [c for c in conditions if c]

    # Build detailed explanation
    explanation_parts = []
    if credit_score < 650:
        explanation_parts.append(f"credit score of {credit_score} is below our preferred threshold")
    if debt_to_income > 0.43:
        explanation_parts.append(f"DTI ratio of {debt_to_income*100:.1f}% exceeds our 43% guideline")
    if loan_to_value > 0.95:
        explanation_parts.append(f"LTV ratio of {loan_to_value*100:.1f}% exceeds maximum")
    if employment_type != "employed":
        explanation_parts.append(f"{employment_type} employment requires additional documentation")

    result = {
        "assessment_id": str(uuid.uuid4()),
        "risk_score": risk_score,
        "max_risk_score": 100,
        "risk_level": risk_level,
        "decision": decision,
        "risk_factors": risk_factors,
        "conditions": conditions,
        "pricing": {
            "suggested_interest_rate": suggested_rate,
            "base_rate": base_rate,
            "risk_adjustment": round(rate_adjustment, 2),
        },
        "metrics": {
            "credit_score": credit_score,
            "debt_to_income": round(debt_to_income * 100, 1),
            "loan_to_value": round(loan_to_value * 100, 1),
            "annual_income": annual_income,
            "loan_amount": loan_amount,
        },
        "explanation": {
            "summary": f"Risk score: {risk_score}/100 ({risk_level} risk)",
            "key_factors": explanation_parts if explanation_parts else ["All criteria met"],
            "decision_rationale": f"Based on credit score ({credit_score}), DTI ({debt_to_income*100:.1f}%), and LTV ({loan_to_value*100:.1f}%)",
        },
        "assessed_at": datetime.utcnow().isoformat(),
    }

    logger.info("Risk assessment: score=%d, decision=%s, rate=%.2f%%", risk_score, decision, suggested_rate)
    return result
