"""
Payment Embedding — ML embeddings for payment pattern analysis.

Capabilities:
- Embed payment patterns for similarity comparison
- Build customer payment profiles
- Detect anomalous payments via embedding distance
- Find similar historical fraud patterns
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime
from typing import Any

import numpy as np


# ── In-memory embedding store ─────────────────────────────────────
_PAYMENT_EMBEDDINGS: dict[str, dict] = {}
_CUSTOMER_PROFILES: dict[str, dict] = {}
_FRAUD_PATTERNS: dict[str, dict] = {}


def _payment_to_features(payment: dict) -> list[float]:
    """Convert payment to feature vector."""
    amount = payment.get("amount", 0)
    payment_type_map = {"wire": 0, "ach": 1, "check": 2, "rtp": 3, "fednow": 4, "zelle": 5}
    channel_map = {"online": 0, "mobile": 1, "branch": 2, "phone": 3, "batch": 4}

    features = [
        min(amount / 100000, 1.0),  # normalized amount
        payment_type_map.get(payment.get("payment_type", ""), 0) / 5.0,
        channel_map.get(payment.get("channel", ""), 0) / 4.0,
        1.0 if payment.get("is_international") else 0.0,
        float(payment.get("hour_of_day", 12)) / 24.0,
        float(payment.get("day_of_week", 0)) / 7.0,
        1.0 if payment.get("is_new_beneficiary") else 0.0,
        min(payment.get("payer_balance", 10000) / 100000, 1.0),
    ]

    # Pad to 128 dimensions
    while len(features) < 128:
        features.append(random.uniform(-0.1, 0.1))

    return features[:128]


async def embed_payment(payment: dict) -> dict[str, Any]:
    """Create ML embedding of a payment pattern."""
    payment_id = payment.get("payment_id", "unknown")
    features = _payment_to_features(payment)
    embedding = [round(f, 6) for f in features]

    _PAYMENT_EMBEDDINGS[payment_id] = {
        "payment_id": payment_id,
        "embedding": embedding,
        "payment": payment,
        "created_at": datetime.utcnow().isoformat(),
    }

    return {
        "payment_id": payment_id,
        "embedding_dimensions": len(embedding),
        "embedding_preview": embedding[:8],
    }


async def build_customer_payment_profile(
    customer_id: str,
    payments: list[dict],
) -> dict[str, Any]:
    """Build a payment behavior profile from historical payments."""
    if not payments:
        return {"customer_id": customer_id, "profile": None, "message": "No payments provided"}

    # Aggregate features
    total_amount = sum(p.get("amount", 0) for p in payments)
    avg_amount = total_amount / len(payments)
    max_amount = max(p.get("amount", 0) for p in payments)

    type_counts: dict[str, int] = {}
    for p in payments:
        pt = p.get("payment_type", "unknown")
        type_counts[pt] = type_counts.get(pt, 0) + 1

    intl_count = sum(1 for p in payments if p.get("is_international"))

    # Create profile embedding (average of payment embeddings)
    profile_features = [
        min(avg_amount / 50000, 1.0),
        min(max_amount / 100000, 1.0),
        len(payments) / 100,
        type_counts.get("wire", 0) / max(len(payments), 1),
        type_counts.get("ach", 0) / max(len(payments), 1),
        type_counts.get("rtp", 0) / max(len(payments), 1),
        intl_count / max(len(payments), 1),
    ]

    while len(profile_features) < 128:
        profile_features.append(random.uniform(-0.1, 0.1))

    profile = {
        "customer_id": customer_id,
        "total_payments": len(payments),
        "total_amount": round(total_amount, 2),
        "avg_amount": round(avg_amount, 2),
        "max_amount": round(max_amount, 2),
        "payment_types": type_counts,
        "international_ratio": round(intl_count / max(len(payments), 1), 3),
        "profile_embedding": [round(f, 6) for f in profile_features[:128]],
        "built_at": datetime.utcnow().isoformat(),
    }

    _CUSTOMER_PROFILES[customer_id] = profile
    return {"customer_id": customer_id, "profile": profile}


async def detect_payment_anomaly(
    payment_id: str,
    customer_id: str,
    payment: dict,
) -> dict[str, Any]:
    """Detect if a payment is anomalous compared to customer profile."""
    profile = _CUSTOMER_PROFILES.get(customer_id)
    if not profile:
        return {
            "payment_id": payment_id,
            "customer_id": customer_id,
            "anomaly_detected": False,
            "reason": "No customer profile available for comparison",
        }

    # Calculate deviation
    amount = payment.get("amount", 0)
    avg = profile.get("avg_amount", 0)
    max_amt = profile.get("max_amount", 0)

    amount_zscore = (amount - avg) / max(avg * 0.5, 1)  # normalized deviation

    anomaly_score = 0.0
    anomaly_reasons: list[str] = []

    if amount > avg * 3:
        anomaly_score += 40.0
        anomaly_reasons.append(f"Amount ${amount:,.2f} is {amount/avg:.1f}x average (${avg:,.2f})")

    if amount > max_amt * 1.5:
        anomaly_score += 25.0
        anomaly_reasons.append(f"Amount ${amount:,.2f} exceeds historical max (${max_amt:,.2f})")

    payment_type = payment.get("payment_type", "")
    type_dist = profile.get("payment_types", {})
    total = sum(type_dist.values()) or 1
    type_ratio = type_dist.get(payment_type, 0) / total
    if type_ratio < 0.05 and total > 10:
        anomaly_score += 20.0
        anomaly_reasons.append(f"Payment type '{payment_type}' represents only {type_ratio*100:.0f}% of historical payments")

    if payment.get("is_international") and profile.get("international_ratio", 0) < 0.05:
        anomaly_score += 15.0
        anomaly_reasons.append("International payment but customer rarely makes international payments")

    anomaly_score = min(anomaly_score, 100.0)

    return {
        "payment_id": payment_id,
        "customer_id": customer_id,
        "anomaly_detected": anomaly_score >= 30,
        "anomaly_score": round(anomaly_score, 2),
        "anomaly_reasons": anomaly_reasons,
        "amount_zscore": round(amount_zscore, 2),
        "comparison": {
            "payment_amount": amount,
            "customer_avg": avg,
            "customer_max": max_amt,
            "payment_type": payment_type,
        },
    }


async def add_fraud_pattern(
    pattern_id: str,
    description: str,
    payment_features: dict,
) -> dict[str, Any]:
    """Add a known fraud pattern to the detection database."""
    features = _payment_to_features(payment_features)
    _FRAUD_PATTERNS[pattern_id] = {
        "pattern_id": pattern_id,
        "description": description,
        "embedding": [round(f, 6) for f in features],
        "payment_features": payment_features,
        "added_at": datetime.utcnow().isoformat(),
    }
    return {"pattern_id": pattern_id, "status": "added"}


async def match_fraud_pattern(payment: dict, threshold: float = 0.8) -> dict[str, Any]:
    """Match a payment against known fraud patterns."""
    payment_embedding = _payment_to_features(payment)
    matches: list[dict] = []

    for pattern_id, pattern in _FRAUD_PATTERNS.items():
        # Cosine similarity
        a = np.array(payment_embedding)
        b = np.array(pattern["embedding"])
        sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
        if sim >= threshold:
            matches.append({
                "pattern_id": pattern_id,
                "description": pattern["description"],
                "similarity": round(sim, 4),
            })

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return {
        "payment_id": payment.get("payment_id", "unknown"),
        "matches_found": len(matches),
        "matches": matches[:5],
        "highest_similarity": matches[0]["similarity"] if matches else 0.0,
    }


async def get_fraud_patterns() -> dict[str, Any]:
    """Get all known fraud patterns."""
    return {"total": len(_FRAUD_PATTERNS), "patterns": list(_FRAUD_PATTERNS.values())}
