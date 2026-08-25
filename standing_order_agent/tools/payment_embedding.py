"""
Payment Embedding Tools — Natural language understanding for payment intents.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from typing import Any

import numpy as np


# ── Intent patterns ──────────────────────────────────────────────
_INTENT_PATTERNS = [
    {"intent": "create_rent", "keywords": ["rent", "landlord", "apartment"], "frequency": "monthly", "day": 1},
    {"intent": "create_utility", "keywords": ["electric", "gas", "water", "utility"], "frequency": "monthly", "day": 15},
    {"intent": "create_insurance", "keywords": ["insurance", "premium"], "frequency": "monthly", "day": 10},
    {"intent": "create_subscription", "keywords": ["netflix", "spotify", "hulu", "subscription", "streaming"], "frequency": "monthly", "day": 1},
    {"intent": "create_loan", "keywords": ["loan payment", "car payment", "student loan", "mortgage"], "frequency": "monthly", "day": 1},
    {"intent": "create_savings", "keywords": ["save", "savings", "transfer to savings"], "frequency": "monthly", "day": 15},
    {"intent": "modify_amount", "keywords": ["change amount", "update amount", "increase", "decrease", "different amount"], "frequency": None, "day": None},
    {"intent": "cancel", "keywords": ["cancel", "stop", "discontinue", "remove"], "frequency": None, "day": None},
    {"intent": "list_orders", "keywords": ["list", "show", "view", "what are my", "my standing orders"], "frequency": None, "day": None},
    {"intent": "pause", "keywords": ["pause", "suspend", "temporarily stop"], "frequency": None, "day": None},
]


async def parse_payment_intent(natural_language_input: str) -> dict[str, Any]:
    """Parse natural language into structured payment intent."""
    text = natural_language_input.lower()

    # Detect intent
    detected_intent = None
    best_score = 0
    for pattern in _INTENT_PATTERNS:
        matches = sum(1 for kw in pattern["keywords"] if kw in text)
        score = matches / len(pattern["keywords"]) if pattern["keywords"] else 0
        if score > best_score:
            best_score = score
            detected_intent = pattern

    if not detected_intent or best_score < 0.3:
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "raw_input": natural_language_input,
            "suggestion": "Could you clarify what you'd like to do? For example: 'Pay my rent on the 1st of every month' or 'Set up auto-pay for my electric bill'.",
        }

    # Extract amount
    amount_match = re.search(r'\$[\d,]+\.?\d*|\d+\.?\d*\s*(?:dollars|bucks)', text)
    amount = None
    if amount_match:
        amount_str = amount_match.group().replace("$", "").replace(",", "").replace("dollars", "").replace("bucks", "").strip()
        try:
            amount = float(amount_str)
        except ValueError:
            pass

    # Extract frequency override
    frequency = detected_intent["frequency"]
    if "weekly" in text:
        frequency = "weekly"
    elif "biweekly" in text or "every two weeks" in text:
        frequency = "biweekly"
    elif "quarterly" in text or "every quarter" in text:
        frequency = "quarterly"
    elif "annually" in text or "yearly" in text or "once a year" in text:
        frequency = "annual"
    elif "daily" in text or "every day" in text:
        frequency = "daily"

    # Extract day of month
    day = detected_intent["day"]
    day_match = re.search(r'(?:on the |day )(\d{1,2})(?:st|nd|rd|th)?', text)
    if day_match:
        day = int(day_match.group(1))

    # Extract payee name
    payee = None
    payee_match = re.search(r'(?:to|for|pay)\s+(.+?)(?:\s+on|\s+every|\s+each|\s+monthly|\s+weekly|\s+\$)', text)
    if payee_match:
        payee = payee_match.group(1).strip().title()

    # Build structured result
    result = {
        "intent": detected_intent["intent"],
        "confidence": round(best_score, 2),
        "raw_input": natural_language_input,
        "extracted_entities": {
            "amount": amount,
            "frequency": frequency,
            "day_of_month": day,
            "payee_name": payee,
        },
    }

    # Build suggested API call
    if detected_intent["intent"].startswith("create"):
        result["suggested_action"] = {
            "tool": "create_standing_order",
            "params": {
                "payee_name": payee,
                "amount": amount,
                "frequency": frequency,
                "start_date": datetime.utcnow().strftime("%Y-%m-%d"),
            },
            "missing_fields": [k for k, v in result["extracted_entities"].items() if v is None and k != "day_of_month"],
        }
    elif detected_intent["intent"] == "modify_amount":
        result["suggested_action"] = {
            "tool": "update_standing_order",
            "params": {"amount": amount},
            "missing_fields": ["standing_order_id"] if True else [],
        }
    elif detected_intent["intent"] == "cancel":
        result["suggested_action"] = {
            "tool": "cancel_standing_order",
            "params": {},
            "missing_fields": ["standing_order_id"],
        }

    return result


async def embed_payment_pattern(pattern_data: dict[str, Any]) -> dict[str, Any]:
    """Create an embedding vector for a payment pattern."""
    # Create a 128-dim embedding from payment features
    features = _extract_features(pattern_data)
    embedding = _create_embedding(features)

    return {
        "pattern_id": pattern_data.get("pattern_id", str(uuid.uuid4())[:8]),
        "embedding_dim": len(embedding),
        "embedding": embedding[:16],  # Return first 16 dims for display
        "features": features,
    }


async def match_payment_patterns(
    payment: dict[str, Any],
    known_patterns: list[dict[str, Any]] | None = None,
    threshold: float = 0.8,
) -> dict[str, Any]:
    """Match a payment against known patterns using cosine similarity."""
    payment_features = _extract_features(payment)
    payment_embedding = np.array(_create_embedding(payment_features))

    if not known_patterns:
        # Use default patterns
        known_patterns = [
            {"pattern_id": "rent_monthly", "features": {"amount_range": "1000-3000", "frequency": "monthly", "category": "housing"}},
            {"pattern_id": "utility_monthly", "features": {"amount_range": "50-300", "frequency": "monthly", "category": "utility"}},
            {"pattern_id": "subscription_monthly", "features": {"amount_range": "10-50", "frequency": "monthly", "category": "subscription"}},
            {"pattern_id": "loan_monthly", "features": {"amount_range": "200-2000", "frequency": "monthly", "category": "loan"}},
        ]

    matches = []
    for pattern in known_patterns:
        pattern_embedding = np.array(_create_embedding(pattern.get("features", {})))
        similarity = _cosine_similarity(payment_embedding, pattern_embedding)
        if similarity >= threshold:
            matches.append({
                "pattern_id": pattern["pattern_id"],
                "similarity": round(float(similarity), 4),
                "features": pattern.get("features", {}),
            })

    matches.sort(key=lambda m: m["similarity"], reverse=True)

    return {
        "payment_features": payment_features,
        "match_count": len(matches),
        "matches": matches,
        "best_match": matches[0] if matches else None,
    }


async def detect_recurring_pattern(
    payments: list[dict[str, Any]],
    min_occurrences: int = 3,
) -> dict[str, Any]:
    """Detect recurring payment patterns from history."""
    if len(payments) < min_occurrences:
        return {"detected": False, "reason": f"Need at least {min_occurrences} payments to detect patterns"}

    # Group by payee
    by_payee: dict[str, list[dict]] = {}
    for p in payments:
        payee = p.get("payee_name", "unknown")
        by_payee.setdefault(payee, []).append(p)

    patterns = []
    for payee, payee_payments in by_payee.items():
        if len(payee_payments) < min_occurrences:
            continue

        amounts = [p.get("amount", 0) for p in payee_payments]
        avg_amount = sum(amounts) / len(amounts)
        amount_variance = sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)
        is_consistent = amount_variance < (avg_amount * 0.1) ** 2  # Within 10%

        # Detect frequency
        dates = sorted([datetime.fromisoformat(p.get("date", "2024-01-01")) for p in payee_payments])
        if len(dates) >= 2:
            intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
            avg_interval = sum(intervals) / len(intervals)

            if 25 <= avg_interval <= 35:
                detected_freq = "monthly"
            elif 5 <= avg_interval <= 9:
                detected_freq = "weekly"
            elif 12 <= avg_interval <= 16:
                detected_freq = "biweekly"
            elif 85 <= avg_interval <= 95:
                detected_freq = "quarterly"
            else:
                detected_freq = f"every_{avg_interval}_days"
        else:
            detected_freq = "unknown"

        patterns.append({
            "payee_name": payee,
            "detected_frequency": detected_freq,
            "average_amount": round(avg_amount, 2),
            "amount_consistent": is_consistent,
            "occurrences": len(payee_payments),
            "date_range": f"{dates[0].date()} to {dates[-1].date()}",
            "recommendation": f"Set up standing order for ${avg_amount:,.2f} {detected_freq} to {payee}",
        })

    return {
        "detected": len(patterns) > 0,
        "pattern_count": len(patterns),
        "patterns": patterns,
    }


def _extract_features(data: dict) -> dict[str, Any]:
    """Extract numeric/categorical features from payment data."""
    amount = data.get("amount", 0)
    if amount < 50:
        amount_range = "micro"
    elif amount < 200:
        amount_range = "small"
    elif amount < 1000:
        amount_range = "medium"
    elif amount < 5000:
        amount_range = "large"
    else:
        amount_range = "very_large"

    return {
        "amount_range": amount_range,
        "amount": amount,
        "frequency": data.get("frequency", "monthly"),
        "payment_method": data.get("payment_method", "ach_debit"),
        "category": data.get("category", "general"),
        "is_recurring": data.get("is_recurring", True),
        "has_variable_amount": data.get("has_variable_amount", False),
    }


def _create_embedding(features: dict) -> list[float]:
    """Create a 128-dim embedding from features."""
    np.random.seed(hash(str(features)) % (2**31))
    raw = np.random.randn(128).astype(np.float32)
    # Normalize
    norm = np.linalg.norm(raw)
    if norm > 0:
        raw = raw / norm
    return raw.tolist()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
