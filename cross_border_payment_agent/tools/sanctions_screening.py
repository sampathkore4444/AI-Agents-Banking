"""
Sanctions Screening Tool — MCP tool stub for cross-border payments.

Handles OFAC, EU, UN sanctions screening for cross-border payments.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Simulated sanctions lists
_SANCTIONS_LISTS = {
    "OFAC_SDN": [
        {"name": "BANK OF KUNLUN CO LTD", "country": "CN", "type": "entity", "reason": "Iran-related"},
        {"name": "NATIONAL IRANIAN OIL COMPANY", "country": "IR", "type": "entity", "reason": "Iran sanctions"},
        {"name": "DPRK FOREIGN TRADE BANK", "country": "KP", "type": "entity", "reason": "North Korea sanctions"},
    ],
    "EU_SANCTIONS": [
        {"name": "ROSMNEFT", "country": "RU", "type": "entity", "reason": "Russia/Ukraine sanctions"},
        {"name": "GAZPROMBANK", "country": "RU", "type": "entity", "reason": "Russia/Ukraine sanctions"},
    ],
    "UN_SANCTIONS": [
        {"name": "AL-QAIDA", "country": "GLOBAL", "type": "entity", "reason": "UNSC 1267"},
    ],
}


async def screen_sanctions(
    entity_name: str,
    country: str | None = None,
    entity_type: str = "individual",
    check_ofac: bool = True,
    check_eu: bool = True,
    check_un: bool = True,
) -> dict:
    """
    Screen an entity against sanctions lists.

    entity_type: "individual", "entity", "vessel", "aircraft"
    """
    logger.info("Screening sanctions: name=%s, country=%s", entity_name, country)

    matches = []
    screened_lists = []

    name_upper = entity_name.upper()

    if check_ofac:
        screened_lists.append("OFAC_SDN")
        for entry in _SANCTIONS_LISTS["OFAC_SDN"]:
            similarity = _name_similarity(name_upper, entry["name"])
            if similarity > 0.6:
                matches.append({
                    "list": "OFAC SDN",
                    "matched_name": entry["name"],
                    "country": entry["country"],
                    "type": entry["type"],
                    "reason": entry["reason"],
                    "similarity_score": round(similarity, 3),
                    "match_type": "exact" if similarity > 0.95 else "fuzzy" if similarity > 0.8 else "possible",
                })

    if check_eu:
        screened_lists.append("EU_SANCTIONS")
        for entry in _SANCTIONS_LISTS["EU_SANCTIONS"]:
            similarity = _name_similarity(name_upper, entry["name"])
            if similarity > 0.6:
                matches.append({
                    "list": "EU Sanctions",
                    "matched_name": entry["name"],
                    "country": entry["country"],
                    "type": entry["type"],
                    "reason": entry["reason"],
                    "similarity_score": round(similarity, 3),
                    "match_type": "exact" if similarity > 0.95 else "fuzzy" if similarity > 0.8 else "possible",
                })

    if check_un:
        screened_lists.append("UN_SANCTIONS")
        for entry in _SANCTIONS_LISTS["UN_SANCTIONS"]:
            similarity = _name_similarity(name_upper, entry["name"])
            if similarity > 0.6:
                matches.append({
                    "list": "UN Sanctions",
                    "matched_name": entry["name"],
                    "country": entry["country"],
                    "type": entry["type"],
                    "reason": entry["reason"],
                    "similarity_score": round(similarity, 3),
                    "match_type": "exact" if similarity > 0.95 else "fuzzy" if similarity > 0.8 else "possible",
                })

    # Determine result
    exact_matches = [m for m in matches if m["match_type"] == "exact"]
    fuzzy_matches = [m for m in matches if m["match_type"] == "fuzzy"]
    possible_matches = [m for m in matches if m["match_type"] == "possible"]

    if exact_matches:
        decision = "BLOCK"
        reason = "Exact match on sanctioned entity"
    elif fuzzy_matches:
        decision = "HOLD"
        reason = "Possible match requires manual review"
    elif possible_matches:
        decision = "REVIEW"
        reason = "Low-confidence match — enhanced screening recommended"
    else:
        decision = "CLEAR"
        reason = "No matches found on screened lists"

    return {
        "entity_name": entity_name,
        "country": country,
        "entity_type": entity_type,
        "lists_screened": screened_lists,
        "total_matches": len(matches),
        "exact_matches": len(exact_matches),
        "fuzzy_matches": len(fuzzy_matches),
        "possible_matches": len(possible_matches),
        "matches": matches,
        "decision": decision,
        "reason": reason,
        "screened_at": datetime.utcnow().isoformat(),
        "screening_id": str(uuid.uuid4())[:12],
    }


def _name_similarity(name1: str, name2: str) -> float:
    """Simple name similarity based on common words."""
    words1 = set(name1.replace(",", "").replace(".", "").split())
    words2 = set(name2.replace(",", "").replace(".", "").split())
    if not words1 or not words2:
        return 0.0
    common = words1 & words2
    return len(common) / max(len(words1), len(words2))
