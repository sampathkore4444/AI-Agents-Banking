"""
Debtor Embedding Tool — MCP tool stub.

Creates ML embeddings of debtor financial profiles for clustering
and matching against successful past resolution strategies.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory embedding store
_embeddings: dict[str, dict] = {}


async def embed_debtor_profile(
    account_id: str,
    borrower_name: str,
    delinquency_days: int,
    outstanding_balance: float,
    monthly_payment: float,
    annual_income: float | None = None,
    debt_to_income: float | None = None,
    has_collateral: bool = False,
    collateral_value: float | None = None,
    employment_years: int | None = None,
    credit_score: int | None = None,
    num_dependents: int | None = None,
    previous_delinquencies: int = 0,
    account_age_months: int = 0,
) -> dict:
    """
    Create ML embedding of debtor financial profile.

    In production, this would use a trained model (XGBoost, LightGBM, or neural network)
    to generate a high-dimensional embedding. This stub uses deterministic synthetic
    embeddings based on input features.
    """
    logger.info("Embedding debtor profile: %s (%s)", account_id, borrower_name)

    # Generate synthetic 128-dimensional embedding
    feature_string = f"{account_id}{delinquency_days}{outstanding_balance}{monthly_payment}"
    hash_val = int(hashlib.md5(feature_string.encode()).hexdigest()[:16], 16)

    # Generate embedding vector (deterministic based on input)
    embedding = []
    for i in range(128):
        # Use hash-based pseudo-random values
        seed = (hash_val + i * 7919) % 10000
        embedding.append(round((seed / 10000.0) * 2 - 1, 4))  # Range: -1 to 1

    # Determine risk cluster
    risk_cluster = _assign_risk_cluster(
        delinquency_days, outstanding_balance, has_collateral,
        credit_score, previous_delinquencies, debt_to_income
    )

    # Estimate default probability
    default_prob = _estimate_default_probability(
        delinquency_days, outstanding_balance, monthly_payment,
        has_collateral, credit_score, previous_delinquencies
    )

    # Find similar historical profiles
    similar_profiles = await _find_similar_profiles(embedding, account_id)

    # Generate resolution probability by strategy
    resolution_probs = _calculate_resolution_probabilities(
        delinquency_days, outstanding_balance, risk_cluster, has_collateral
    )

    result = {
        "account_id": account_id,
        "borrower_name": borrower_name,
        "embedding": {
            "dimensions": 128,
            "vector_preview": embedding[:10],
            "vector_full": embedding,
        },
        "risk_cluster": risk_cluster,
        "default_probability": round(default_prob, 3),
        "similar_historical_profiles": similar_profiles,
        "resolution_probabilities": resolution_probs,
        "profile_features": {
            "delinquency_days": delinquency_days,
            "outstanding_balance": outstanding_balance,
            "monthly_payment": monthly_payment,
            "annual_income": annual_income,
            "debt_to_income": debt_to_income,
            "has_collateral": has_collateral,
            "collateral_value": collateral_value,
            "employment_years": employment_years,
            "credit_score": credit_score,
            "num_dependents": num_dependents,
            "previous_delinquencies": previous_delinquencies,
            "account_age_months": account_age_months,
        },
        "embedded_at": datetime.utcnow().isoformat(),
    }

    __embeddings[account_id] = result
    logger.info("Profile embedded: cluster=%s, default_prob=%.3f", risk_cluster, default_prob)
    return result


def _assign_risk_cluster(
    delinquency_days: int,
    balance: float,
    has_collateral: bool,
    credit_score: int | None,
    previous_delinquencies: int,
    dti: float | None,
) -> dict:
    """Assign risk cluster based on profile features."""
    # Score-based clustering
    risk_score = 0

    # Delinquency weight
    if delinquency_days > 120:
        risk_score += 40
    elif delinquency_days > 90:
        risk_score += 30
    elif delinquency_days > 60:
        risk_score += 20
    elif delinquency_days > 30:
        risk_score += 10

    # Balance weight
    if balance > 50000:
        risk_score += 20
    elif balance > 20000:
        risk_score += 15
    elif balance > 10000:
        risk_score += 10
    elif balance > 5000:
        risk_score += 5

    # Collateral reduces risk
    if has_collateral:
        risk_score -= 15

    # Credit score
    if credit_score:
        if credit_score < 580:
            risk_score += 20
        elif credit_score < 650:
            risk_score += 10
        elif credit_score > 720:
            risk_score -= 10

    # Previous delinquencies
    risk_score += min(previous_delinquencies * 5, 20)

    # DTI
    if dti and dti > 0.50:
        risk_score += 15
    elif dti and dti > 0.43:
        risk_score += 10

    # Assign cluster
    if risk_score >= 60:
        cluster = "high_risk"
        label = "High Risk — Recovery Unlikely"
    elif risk_score >= 40:
        cluster = "elevated_risk"
        label = "Elevated Risk — Aggressive Intervention Needed"
    elif risk_score >= 20:
        cluster = "moderate_risk"
        label = "Moderate Risk — Standard Collection + Flexibility"
    else:
        cluster = "low_risk"
        label = "Low Risk — Reminder + Payment Plan Likely Sufficient"

    return {
        "cluster": cluster,
        "label": label,
        "risk_score": risk_score,
        "risk_range": "0-100",
    }


def _estimate_default_probability(
    delinquency_days: int,
    balance: float,
    monthly_payment: float,
    has_collateral: bool,
    credit_score: int | None,
    previous_delinquencies: int,
) -> float:
    """Estimate probability of default (synthetic — production uses ML model)."""
    base_prob = 0.10

    # Delinquency impact
    base_prob += delinquency_days * 0.003

    # Balance impact (larger = harder to recover)
    if balance > 50000:
        base_prob += 0.15
    elif balance > 20000:
        base_prob += 0.10
    elif balance > 10000:
        base_prob += 0.05

    # Collateral reduces default
    if has_collateral:
        base_prob -= 0.15

    # Credit score
    if credit_score:
        if credit_score < 580:
            base_prob += 0.20
        elif credit_score < 650:
            base_prob += 0.10
        elif credit_score > 720:
            base_prob -= 0.10

    # Previous delinquencies
    base_prob += min(previous_delinquencies * 0.05, 0.20)

    return max(0.01, min(base_prob, 0.99))


def _calculate_resolution_probabilities(
    delinquency_days: int,
    balance: float,
    risk_cluster: dict,
    has_collateral: bool,
) -> dict:
    """Estimate resolution probability for each strategy type."""
    cluster = risk_cluster["cluster"]

    base_probs = {
        "full_repayment": 0.8 if cluster == "low_risk" else 0.5 if cluster == "moderate_risk" else 0.2,
        "payment_plan": 0.7 if cluster in ("low_risk", "moderate_risk") else 0.3,
        "forbearance": 0.6 if delinquency_days <= 60 else 0.3,
        "modification": 0.5 if cluster in ("low_risk", "moderate_risk") else 0.2,
        "settlement": 0.3 if cluster == "low_risk" else 0.5 if cluster == "moderate_risk" else 0.7,
        "charge_off": 0.05 if cluster == "low_risk" else 0.15 if cluster == "moderate_risk" else 0.4,
    }

    if has_collateral:
        base_probs["repossession"] = 0.3
        base_probs["voluntary_surrender"] = 0.2
    else:
        base_probs["repossession"] = 0.0
        base_probs["voluntary_surrender"] = 0.0

    return {k: round(v, 2) for k, v in base_probs.items()}


async def _find_similar_profiles(embedding: list[float], exclude_id: str) -> list[dict]:
    """Find similar historical debtor profiles (simulated)."""
    similar = [
        {
            "profile_id": "PROF-001",
            "scenario": "Single parent, medical hardship, mortgage delinquency 52 days",
            "original_balance": 220000,
            "resolution": "Forbearance + modified payment plan",
            "outcome": "success",
            "recovery_rate": 0.98,
            "similarity_score": 0.91,
        },
        {
            "profile_id": "PROF-002",
            "scenario": "Self-employed, seasonal income, personal loan delinquency 85 days",
            "original_balance": 12000,
            "resolution": "Income-driven repayment with seasonal adjustment",
            "outcome": "success",
            "recovery_rate": 1.0,
            "similarity_score": 0.86,
        },
        {
            "profile_id": "PROF-003",
            "scenario": "Young professional, job loss, auto loan delinquency 110 days",
            "original_balance": 25000,
            "resolution": "Settlement at 40% with 12-month plan",
            "outcome": "partial_success",
            "recovery_rate": 0.40,
            "similarity_score": 0.82,
        },
    ]

    return similar
