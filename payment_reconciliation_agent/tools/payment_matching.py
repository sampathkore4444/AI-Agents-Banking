"""
Payment Matching Tool — MCP tool stub for reconciliation.

Handles auto-matching of bank statement entries to internal ledger entries
using exact match, fuzzy match, and embedding-based semantic matching.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def auto_match_payments(
    bank_entries: list[dict],
    ledger_entries: list[dict],
    match_threshold: float = 0.95,
    amount_tolerance_pct: float = 0.01,
    date_tolerance_days: int = 2,
) -> dict:
    """
    Run auto-matching engine against bank and ledger entries.

    Returns matched pairs, unmatched items, and confidence scores.
    """
    logger.info("Running auto-match: %d bank entries, %d ledger entries", len(bank_entries), len(ledger_entries))

    matched = []
    unmatched_bank = []
    unmatched_ledger = []

    used_ledger_ids = set()

    for bank_entry in bank_entries:
        best_match = None
        best_score = 0.0

        for ledger_entry in ledger_entries:
            if ledger_entry.get("id") in used_ledger_ids:
                continue

            score = _calculate_match_score(bank_entry, ledger_entry, amount_tolerance_pct, date_tolerance_days)

            if score > best_score:
                best_score = score
                best_match = ledger_entry

        if best_match and best_score >= match_threshold:
            matched.append({
                "match_id": f"MATCH-{uuid.uuid4().hex[:8].upper()}",
                "bank_entry": bank_entry,
                "ledger_entry": best_match,
                "confidence_score": round(best_score, 3),
                "match_type": _get_match_type(bank_entry, best_match, best_score),
                "matched_at": datetime.utcnow().isoformat(),
            })
            used_ledger_ids.add(best_match.get("id"))
        else:
            unmatched_bank.append({
                "entry": bank_entry,
                "best_candidate_score": round(best_score, 3) if best_score > 0 else None,
                "reason": "No match above threshold" if best_score > 0 else "No candidates found",
            })

    for ledger_entry in ledger_entries:
        if ledger_entry.get("id") not in used_ledger_ids:
            unmatched_ledger.append({
                "entry": ledger_entry,
                "reason": "No matching bank entry found",
            })

    return {
        "total_bank_entries": len(bank_entries),
        "total_ledger_entries": len(ledger_entries),
        "matched_count": len(matched),
        "unmatched_bank_count": len(unmatched_bank),
        "unmatched_ledger_count": len(unmatched_ledger),
        "match_rate": round(len(matched) / max(len(bank_entries), 1) * 100, 1),
        "matched": matched,
        "unmatched_bank": unmatched_bank,
        "unmatched_ledger": unmatched_ledger,
        "summary": {
            "exact_matches": len([m for m in matched if m["match_type"] == "exact"]),
            "fuzzy_matches": len([m for m in matched if m["match_type"] == "fuzzy"]),
            "semantic_matches": len([m for m in matched if m["match_type"] == "semantic"]),
        },
    }


async def match_single_payment(
    bank_entry: dict,
    ledger_entries: list[dict],
    amount_tolerance_pct: float = 0.01,
    date_tolerance_days: int = 2,
) -> dict:
    """Match a single bank entry against all ledger entries and return ranked candidates."""
    logger.info("Matching single payment: ref=%s, amount=$%s", bank_entry.get("reference", ""), bank_entry.get("amount", 0))

    candidates = []
    for ledger_entry in ledger_entries:
        score = _calculate_match_score(bank_entry, ledger_entry, amount_tolerance_pct, date_tolerance_days)
        if score > 0.3:
            candidates.append({
                "ledger_entry": ledger_entry,
                "score": round(score, 3),
                "match_type": _get_match_type(bank_entry, ledger_entry, score),
                "match_details": _get_match_details(bank_entry, ledger_entry),
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "bank_entry": bank_entry,
        "total_candidates": len(candidates),
        "top_candidates": candidates[:5],
        "auto_matchable": candidates[0]["score"] >= 0.95 if candidates else False,
    }


async def embed_payment_reference(
    reference: str,
    amount: float,
    date: str,
    counterparty: str,
    description: str = "",
) -> dict:
    """Create embedding of payment reference for semantic matching."""
    import hashlib

    feature_string = f"{reference}{amount}{date}{counterparty}{description}"
    hash_val = int(hashlib.md5(feature_string.encode()).hexdigest()[:16], 16)

    embedding = []
    for i in range(128):
        seed = (hash_val + i * 7919) % 10000
        embedding.append(round((seed / 10000.0) * 2 - 1, 4))

    return {
        "reference": reference,
        "embedding_dimensions": 128,
        "embedding_preview": embedding[:10],
        "embedding_full": embedding,
        "embedded_at": datetime.utcnow().isoformat(),
    }


def _calculate_match_score(
    bank_entry: dict,
    ledger_entry: dict,
    amount_tolerance_pct: float,
    date_tolerance_days: int,
) -> float:
    """Calculate match score between bank and ledger entries."""
    score = 0.0
    weights = {"reference": 0.40, "amount": 0.35, "date": 0.15, "counterparty": 0.10}

    # Reference matching
    bank_ref = str(bank_entry.get("reference", "")).strip().upper()
    ledger_ref = str(ledger_entry.get("reference", "")).strip().upper()
    if bank_ref and ledger_ref:
        if bank_ref == ledger_ref:
            score += weights["reference"]
        elif bank_ref in ledger_ref or ledger_ref in bank_ref:
            score += weights["reference"] * 0.8
        elif _fuzzy_reference_match(bank_ref, ledger_ref):
            score += weights["reference"] * 0.5

    # Amount matching
    bank_amt = float(bank_entry.get("amount", 0))
    ledger_amt = float(ledger_entry.get("amount", 0))
    if bank_amt > 0 and ledger_amt > 0:
        diff_pct = abs(bank_amt - ledger_amt) / max(bank_amt, ledger_amt)
        if diff_pct <= 0.0001:
            score += weights["amount"]
        elif diff_pct <= amount_tolerance_pct:
            score += weights["amount"] * 0.9
        elif diff_pct <= 0.05:
            score += weights["amount"] * 0.5

    # Date matching
    bank_date = bank_entry.get("date", "")
    ledger_date = ledger_entry.get("date", "")
    if bank_date and ledger_date:
        try:
            from datetime import timedelta
            b_date = datetime.strptime(bank_date[:10], "%Y-%m-%d")
            l_date = datetime.strptime(ledger_date[:10], "%Y-%m-%d")
            day_diff = abs((b_date - l_date).days)
            if day_diff == 0:
                score += weights["date"]
            elif day_diff <= date_tolerance_days:
                score += weights["date"] * 0.7
            elif day_diff <= 5:
                score += weights["date"] * 0.3
        except ValueError:
            pass

    # Counterparty matching
    bank_cp = str(bank_entry.get("counterparty", "")).lower()
    ledger_cp = str(ledger_entry.get("counterparty", "")).lower()
    if bank_cp and ledger_cp:
        if bank_cp == ledger_cp:
            score += weights["counterparty"]
        elif bank_cp in ledger_cp or ledger_cp in bank_cp:
            score += weights["counterparty"] * 0.7
        elif _fuzzy_name_match(bank_cp, ledger_cp):
            score += weights["counterparty"] * 0.4

    return min(score, 1.0)


def _fuzzy_reference_match(ref1: str, ref2: str) -> bool:
    """Check if references are similar enough for fuzzy match."""
    clean1 = ref1.replace("-", "").replace(" ", "")
    clean2 = ref2.replace("-", "").replace(" ", "")
    if clean1 == clean2:
        return True
    if len(clean1) >= 6 and len(clean2) >= 6:
        if clean1[-6:] == clean2[-6:]:
            return True
    return False


def _fuzzy_name_match(name1: str, name2: str) -> bool:
    """Check if counterparty names are similar."""
    words1 = set(name1.split())
    words2 = set(name2.split())
    if not words1 or not words2:
        return False
    overlap = len(words1 & words2) / max(len(words1), len(words2))
    return overlap >= 0.5


def _get_match_type(bank_entry: dict, ledger_entry: dict, score: float) -> str:
    """Determine match type based on score."""
    if score >= 0.95:
        return "exact"
    elif score >= 0.80:
        return "fuzzy"
    else:
        return "semantic"


def _get_match_details(bank_entry: dict, ledger_entry: dict) -> dict:
    """Get detailed match breakdown."""
    details = {}

    bank_ref = str(bank_entry.get("reference", "")).strip()
    ledger_ref = str(ledger_entry.get("reference", "")).strip()
    details["reference_match"] = bank_ref == ledger_ref if bank_ref and ledger_ref else None

    bank_amt = float(bank_entry.get("amount", 0))
    ledger_amt = float(ledger_entry.get("amount", 0))
    details["amount_match"] = abs(bank_amt - ledger_amt) < 0.01 if bank_amt and ledger_amt else None
    details["amount_difference"] = round(abs(bank_amt - ledger_amt), 2) if bank_amt and ledger_amt else None

    details["date_match"] = bank_entry.get("date") == ledger_entry.get("date") if bank_entry.get("date") and ledger_entry.get("date") else None

    return details
