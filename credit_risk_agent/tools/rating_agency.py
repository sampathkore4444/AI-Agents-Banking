"""
Rating Agency Tool — MCP tool stub.

Provides credit rating data from rating agencies:
- Current ratings (Moody's, S&P, Fitch)
- Rating history
- Outlook and watch status
- Rating transition matrices
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

RATING_SCALE = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"]
RATING_NUMERIC = {r: i for i, r in enumerate(RATING_SCALE)}


async def get_credit_rating(borrower_id: str) -> dict:
    """Get current credit rating from major agencies."""
    logger.info("Fetching credit rating for %s", borrower_id)
    b_hash = hashlib.md5(borrower_id.encode()).hexdigest()
    hv = int(b_hash[:8], 16)

    rating_idx = 8 + hv % 12  # BBB- to CCC range
    rating = RATING_SCALE[rating_idx]
    outlooks = ["stable", "positive", "negative", "developing"]
    outlook = outlooks[hv % 4]

    return {
        "borrower_id": borrower_id,
        "ratings": {
            "moody": {"rating": rating, "outlook": outlook, "last_action": "2024-06-15"},
            "sp": {"rating": rating, "outlook": outlook, "last_action": "2024-06-10"},
            "fitch": {"rating": rating, "outlook": outlook, "last_action": "2024-05-28"},
        },
        "composite_rating": rating,
        "numeric_score": RATING_NUMERIC.get(rating, 10),
        "investment_grade": rating_idx <= 10,  # BBB- and above
        "watch_status": "watch_negative" if outlook == "negative" else "none",
        "last_rating_change": "2024-03-15",
        "retrieved_at": datetime.utcnow().isoformat(),
    }


async def check_rating_transition(borrower_id: str) -> dict:
    """Check recent rating actions and transition probability."""
    logger.info("Checking rating transition for %s", borrower_id)
    b_hash = hashlib.md5(borrower_id.encode()).hexdigest()
    hv = int(b_hash[:8], 16)

    rating_idx = 8 + hv % 12
    current_rating = RATING_SCALE[rating_idx]

    # 1-year transition probabilities (simplified)
    transition_probs = {}
    if rating_idx > 0:
        transition_probs["upgrade"] = round(0.05 + (hv % 10) / 100, 2)
    else:
        transition_probs["upgrade"] = 0.0
    transition_probs["stable"] = round(0.80 + (hv % 10) / 100, 2)
    if rating_idx < len(RATING_SCALE) - 1:
        transition_probs["downgrade"] = round(0.05 + (hv % 10) / 100, 2)
    else:
        transition_probs["downgrade"] = 0.0
    transition_probs["default"] = round(0.01 + (hv % 3) / 100, 3)

    # Normalize
    total = sum(transition_probs.values())
    transition_probs = {k: round(v / total, 4) for k, v in transition_probs.items()}

    return {
        "borrower_id": borrower_id,
        "current_rating": current_rating,
        "numeric_score": RATING_NUMERIC.get(current_rating, 10),
        "transition_probabilities_1yr": transition_probs,
        "probability_of_default_1yr": transition_probs["default"],
        "probability_of_downgrade_1yr": transition_probs["downgrade"],
        "checked_at": datetime.utcnow().isoformat(),
    }
