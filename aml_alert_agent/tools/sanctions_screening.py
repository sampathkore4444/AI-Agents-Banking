"""
Sanctions Screening — OFAC, EU, UN Sanctions Lists.

Screening capabilities:
- Name screening against SDN, EU, UN lists
- Country/region screening
- Vessel screening
- Fuzzy matching with configurable thresholds
- Hit dispositioning and audit trail
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

# ── Simulated sanctions lists ─────────────────────────────────────
SANCTIONS_LISTS: dict[str, list[dict]] = {
    "ofac_sdn": [
        {"id": "SDN-001", "name": "Mohammed Al-Rashid", "aliases": ["M. Al-Rashid", "Mohammed Rashid"], "type": "individual", "program": "IRAN", "country": "IR", "reason": "IRGC financier"},
        {"id": "SDN-002", "name": "Beijing Trading Corporation", "aliases": ["BTC Ltd", "Beijing Trading Co"], "type": "entity", "program": "DPRK", "country": "CN", "reason": "DPRK weapons procurement"},
        {"id": "SDN-003", "name": "Viktor Petrov", "aliases": ["V. Petrov", "Victor Petrov"], "type": "individual", "program": "RUSSIA", "country": "RU", "reason": "Oligarch sanctions"},
        {"id": "SDN-004", "name": "Dubai Gold Exchange LLC", "aliases": ["DGE", "Dubai Gold Exchange"], "type": "entity", "program": "NARCOTICS", "country": "AE", "reason": "Narcotics trafficking facilitation"},
        {"id": "SDN-005", "name": "Syrian National Bank", "aliases": ["SNB", "Bank of Syria"], "type": "entity", "program": "SYRIA", "country": "SY", "reason": "Syrian government financial arm"},
    ],
    "eu_sanctions": [
        {"id": "EU-001", "name": "Viktor Petrov", "aliases": ["V. Petrov"], "type": "individual", "program": "EU-RUSSIA", "country": "RU", "reason": "EU Russia sanctions"},
        {"id": "EU-002", "name": "Eastern Mediterranean Trading", "aliases": ["EMT Corp"], "type": "entity", "program": "EU-SYRIA", "country": "SY", "reason": "Syria sanctions"},
    ],
    "un_sanctions": [
        {"id": "UN-001", "name": "Mohammed Al-Rashid", "aliases": [], "type": "individual", "program": "UN-IRAN", "country": "IR", "reason": "UN Iran sanctions"},
        {"id": "UN-002", "name": "Pyongyang Industrial Development", "aliases": ["PID"], "type": "entity", "program": "UN-DPRK", "country": "KP", "reason": "UN DPRK sanctions"},
    ],
}

_SCREENING_HISTORY: dict[str, dict] = {}


def _fuzzy_match(name1: str, name2: str) -> float:
    """Calculate fuzzy similarity between two names."""
    name1_lower = name1.lower().strip()
    name2_lower = name2.lower().strip()
    return SequenceMatcher(None, name1_lower, name2_lower).ratio()


def _check_aliases(name: str, aliases: list[str]) -> float:
    """Check name against aliases, return best match score."""
    best_score = 0.0
    for alias in aliases:
        score = _fuzzy_match(name, alias)
        best_score = max(best_score, score)
    return best_score


async def screen_name(
    name: str,
    name_type: str = "individual",
    threshold: float = 0.85,
    lists: list[str] | None = None,
) -> dict[str, Any]:
    """Screen a name against sanctions lists."""
    matches: list[dict] = []
    target_lists = lists or list(SANCTIONS_LISTS.keys())

    for list_name in target_lists:
        entries = SANCTIONS_LISTS.get(list_name, [])
        for entry in entries:
            # Direct name match
            direct_score = _fuzzy_match(name, entry["name"])
            alias_score = _check_aliases(name, entry.get("aliases", []))
            best_score = max(direct_score, alias_score)

            if best_score >= threshold:
                match_type = "exact" if best_score >= 0.99 else "fuzzy"
                matches.append({
                    "list": list_name,
                    "entry_id": entry["id"],
                    "matched_name": entry["name"],
                    "match_score": round(best_score, 3),
                    "match_type": match_type,
                    "sanction_type": entry["type"],
                    "program": entry["program"],
                    "country": entry["country"],
                    "reason": entry["reason"],
                })

    screening_id = hashlib.md5(f"{name}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12].upper()

    result = {
        "screening_id": screening_id,
        "name": name,
        "name_type": name_type,
        "lists_screened": target_lists,
        "matches_found": len(matches),
        "matches": matches,
        "risk_level": "critical" if any(m["match_type"] == "exact" for m in matches) else "high" if matches else "clear",
        "recommended_action": "BLOCK" if matches else "proceed",
        "timestamp": datetime.utcnow().isoformat(),
    }

    _SCREENING_HISTORY[screening_id] = result
    return result


async def screen_entity(
    entity_name: str,
    jurisdiction: str | None = None,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Screen an entity against sanctions lists."""
    result = await screen_name(entity_name, name_type="entity", threshold=threshold)

    # Additional entity-specific checks
    if jurisdiction:
        high_risk_jurisdictions = {"IR", "KP", "SY", "CU", "VE", "MM"}
        if jurisdiction in high_risk_jurisdictions:
            result["jurisdiction_risk"] = "high"
            result["recommended_action"] = "ENHANCED_DUE_DILIGENCE"
        else:
            result["jurisdiction_risk"] = "low"

    return result


async def screen_vessel(
    vessel_name: str,
    imo_number: str | None = None,
    flag_state: str | None = None,
) -> dict[str, Any]:
    """Screen a vessel against sanctions lists (for trade-based AML)."""
    result = await screen_name(vessel_name, name_type="vessel")

    if flag_state:
        sanctioned_flags = {"IR", "KP", "SY"}
        if flag_state in sanctioned_flags:
            result["flag_state_risk"] = "critical"
            result["recommended_action"] = "BLOCK"
            result["flag_state_flagged"] = True

    return result


async def screen_transaction(
    transaction_id: str,
    originator_name: str,
    beneficiary_name: str,
    originator_country: str,
    beneficiary_country: str,
    amount: float,
) -> dict[str, Any]:
    """Screen all parties in a transaction."""
    orig_result = await screen_name(originator_name, name_type="originator")
    bene_result = await screen_name(beneficiary_name, name_type="beneficiary")

    combined_risk = "clear"
    if orig_result["risk_level"] == "critical" or bene_result["risk_level"] == "critical":
        combined_risk = "critical"
    elif orig_result["matches_found"] > 0 or bene_result["matches_found"] > 0:
        combined_risk = "high"

    return {
        "transaction_id": transaction_id,
        "originator_screening": orig_result,
        "beneficiary_screening": bene_result,
        "combined_risk_level": combined_risk,
        "recommended_action": "BLOCK" if combined_risk == "critical" else "REVIEW" if combined_risk == "high" else "PROCEED",
        "amount": amount,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def get_screening_history(limit: int = 50) -> dict[str, Any]:
    """Get screening history."""
    entries = list(_SCREENING_HISTORY.values())[-limit:]
    return {
        "total_screenings": len(_SCREENING_HISTORY),
        "history": entries,
    }


async def get_sanctions_lists_info() -> dict[str, Any]:
    """Get information about loaded sanctions lists."""
    info = {}
    for list_name, entries in SANCTIONS_LISTS.items():
        info[list_name] = {"count": len(entries), "entries": [{"id": e["id"], "name": e["name"], "type": e["type"]} for e in entries]}
    return {"lists": info, "total_entries": sum(len(v) for v in SANCTIONS_LISTS.values())}
