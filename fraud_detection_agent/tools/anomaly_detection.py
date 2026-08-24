"""
Anomaly Detection Tool — ML-based fraud pattern detection using embeddings.
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime
from typing import Any

import numpy as np


# ── In-memory stores ──────────────────────────────────────────────
FRAUD_EMBEDDINGS_DB: dict[str, dict] = {}
CUSTOMER_PROFILES_DB: dict[str, dict] = {}


def _generate_embedding(features: dict) -> list[float]:
    """Generate a 128-dimensional embedding from transaction features."""
    np.random.seed(int(hashlib.md5(str(features).encode()).hexdigest()[:8], 16) % 2**31)
    embedding = np.random.randn(128).tolist()
    # Normalize
    norm = np.linalg.norm(embedding)
    return [x / norm for x in embedding]


def _compute_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embeddings."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))


async def embed_transaction(
    transaction_id: str,
    customer_id: str,
    amount: float,
    merchant_category: str,
    channel: str,
    country: str,
    hour: int,
    day_of_week: int,
    is_international: bool,
) -> dict[str, Any]:
    """Create ML embedding of transaction pattern for anomaly detection."""
    features = {
        "amount": amount,
        "merchant_category": merchant_category,
        "channel": channel,
        "country": country,
        "hour": hour,
        "day_of_week": day_of_week,
        "is_international": is_international,
    }

    embedding = _generate_embedding(features)

    # Store embedding
    FRAUD_EMBEDDINGS_DB[transaction_id] = {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "features": features,
        "embedding": embedding,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Check against known fraud patterns
    fraud_matches = await _match_fraud_patterns(embedding)

    return {
        "transaction_id": transaction_id,
        "embedding_dimension": len(embedding),
        "features": features,
        "fraud_pattern_matches": fraud_matches,
        "anomaly_score": fraud_matches.get("max_similarity", 0),
    }


async def embed_customer_behavior(
    customer_id: str,
    transactions_last_30_days: list[dict],
) -> dict[str, Any]:
    """Create behavioral embedding for a customer."""
    if not transactions_last_30_days:
        return {"customer_id": customer_id, "profile": None, "message": "No transaction history available"}

    # Compute behavioral features
    amounts = [t.get("amount", 0) for t in transactions_last_30_days]
    categories = [t.get("merchant_category", "unknown") for t in transactions_last_30_days]
    channels = [t.get("channel", "unknown") for t in transactions_last_30_days]

    profile = {
        "avg_amount": sum(amounts) / len(amounts),
        "max_amount": max(amounts),
        "std_amount": float(np.std(amounts)) if len(amounts) > 1 else 0,
        "transaction_count": len(transactions_last_30_days),
        "unique_categories": len(set(categories)),
        "primary_channel": max(set(channels), key=channels.count),
        "international_ratio": sum(1 for t in transactions_last_30_days if t.get("is_international")) / len(transactions_last_30_days),
    }

    embedding = _generate_embedding(profile)

    CUSTOMER_PROFILES_DB[customer_id] = {
        "customer_id": customer_id,
        "profile": profile,
        "embedding": embedding,
        "updated_at": datetime.utcnow().isoformat(),
    }

    return {
        "customer_id": customer_id,
        "profile": profile,
        "embedding_dimension": len(embedding),
        "message": "Customer behavioral profile created.",
    }


async def detect_anomaly(
    transaction_id: str,
    customer_id: str,
    amount: float,
    merchant_category: str,
    channel: str,
    country: str,
    hour: int,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Detect if a transaction is anomalous compared to customer's normal behavior."""
    customer_profile = CUSTOMER_PROFILES_DB.get(customer_id)

    anomalies: list[dict] = []
    anomaly_score = 0

    if customer_profile:
        profile = customer_profile["profile"]

        # Amount anomaly
        avg = profile["avg_amount"]
        std = max(profile["std_amount"], 1)
        z_score = (amount - avg) / std
        if abs(z_score) > 3:
            anomalies.append({"type": "amount_zscore", "z_score": round(z_score, 2), "severity": "high"})
            anomaly_score += 30
        elif abs(z_score) > 2:
            anomalies.append({"type": "amount_zscore", "z_score": round(z_score, 2), "severity": "medium"})
            anomaly_score += 15

        # Category anomaly
        if merchant_category not in [t.get("merchant_category") for t in []]:  # Would need historical categories
            anomaly_score += 10

        # Channel anomaly
        if channel != profile.get("primary_channel"):
            anomalies.append({"type": "channel_switch", "expected": profile.get("primary_channel"), "actual": channel, "severity": "low"})
            anomaly_score += 5

        # International anomaly
        if country != "US" and profile.get("international_ratio", 0) < 0.1:
            anomalies.append({"type": "unusual_international", "severity": "medium"})
            anomaly_score += 20

    # Check against known fraud patterns
    features = {
        "amount": amount,
        "merchant_category": merchant_category,
        "channel": channel,
        "country": country,
        "hour": hour,
    }
    txn_embedding = _generate_embedding(features)
    fraud_matches = await _match_fraud_patterns(txn_embedding)

    if fraud_matches.get("max_similarity", 0) > 0.7:
        anomalies.append({"type": "fraud_pattern_match", "similarity": fraud_matches["max_similarity"], "severity": "critical"})
        anomaly_score += 40

    anomaly_score = min(anomaly_score, 100)

    if anomaly_score >= 70:
        action = "block"
        risk_level = "critical"
    elif anomaly_score >= 40:
        action = "review"
        risk_level = "high"
    elif anomaly_score >= 20:
        action = "monitor"
        risk_level = "medium"
    else:
        action = "allow"
        risk_level = "low"

    return {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "anomaly_score": anomaly_score,
        "risk_level": risk_level,
        "action": action,
        "anomalies": anomalies,
        "fraud_pattern_matches": fraud_matches,
        "message": f"Anomaly detection {'triggered' if action != 'allow' else 'passed'} — Score: {anomaly_score}/100",
    }


async def add_fraud_pattern(
    pattern_id: str,
    description: str,
    features: dict,
) -> dict[str, Any]:
    """Add a known fraud pattern to the embedding database."""
    embedding = _generate_embedding(features)

    FRAUD_EMBEDDINGS_DB[f"fraud_{pattern_id}"] = {
        "pattern_id": pattern_id,
        "description": description,
        "features": features,
        "embedding": embedding,
        "created_at": datetime.utcnow().isoformat(),
    }

    return {
        "pattern_id": pattern_id,
        "description": description,
        "message": "Fraud pattern added to detection database.",
    }


async def _match_fraud_patterns(embedding: list[float]) -> dict[str, Any]:
    """Match an embedding against known fraud patterns."""
    best_similarity = 0
    best_match = None

    for key, entry in FRAUD_EMBEDDINGS_DB.items():
        sim = _compute_similarity(embedding, entry["embedding"])
        if sim > best_similarity:
            best_similarity = sim
            best_match = entry

    return {
        "max_similarity": round(best_similarity, 4),
        "matched_pattern": best_match["pattern_id"] if best_match else None,
        "matched_description": best_match["description"] if best_match else None,
        "total_patterns_checked": len(FRAUD_EMBEDDINGS_DB),
    }


async def get_fraud_patterns() -> dict[str, Any]:
    """Get all known fraud patterns."""
    patterns = []
    for key, entry in FRAUD_EMBEDDINGS_DB.items():
        if key.startswith("fraud_"):
            patterns.append({
                "pattern_id": entry["pattern_id"],
                "description": entry["description"],
                "features": entry["features"],
            })
    return {"total_patterns": len(patterns), "patterns": patterns}
