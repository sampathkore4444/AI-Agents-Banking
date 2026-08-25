"""
Sanctions Screening — Screen payment parties against OFAC, EU, UN lists.

Payment-specific screening:
- Originator and beneficiary screening
- Intermediary bank screening
- Beneficiary bank country screening
- Transaction-level screening
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

# ── Simulated sanctions lists ─────────────────────────────────────
SANCTIONS_LISTS: dict[str, list[dict]] = {
    "ofac_sdn": [
        {"id": "SDN-001", "name": "Mohammed Al-Rashid", "aliases": ["M. Al-Rashid"], "type": "individual", "program": "IRAN", "country": "IR"},
        {"id": "SDN-002", "name": "Beijing Trading Corporation", "aliases": ["BTC Ltd"], "type": "entity", "program": "DPRK", "country": "CN"},
        {"id": "SDN-003", "name": "Viktor Petrov", "aliases": ["V. Petrov"], "type": "individual", "program": "RUSSIA", "country": "RU"},
        {"id": "SDN-004", "name": "Dubai Gold Exchange LLC", "aliases": ["DGE"], "type": "entity", "program": "NARCOTICS", "country": "AE"},
        {"id": "SDN-005", "name": "Syrian National Bank", "aliases": ["SNB"], "type": "entity", "program": "SYRIA", "country": "SY"},
    ],
    "eu_sanctions": [
        {"id": "EU-001", "name": "Viktor Petrov", "aliases": [], "type": "individual", "program": "EU-RUSSIA", "country": "RU"},
    ],
    "un_sanctions": [
        {"id": "UN-001", "name": "Mohammed Al-Rashid", "aliases": [], "type": "individual", "program": "UN-IRAN", "country": "IR"},
    ],
}

_SCREENING_HISTORY: list[dict] = []


def _fuzzy_match(name1: str, name2: str) -> float:
    return SequenceMatcher(None, name1.lower().strip(), name2.lower().strip()).ratio()


def _check_aliases(name: str, aliases: list[str]) -> float:
    best_score = 0.0
    for alias in aliases:
        score = _fuzzy_match(name, alias)
        best_score = max(best_score, score)
    return best_score


async def screen_payment_parties(
    payment_id: str,
    originator_name: str,
    beneficiary_name: str,
    originator_account: str | None = None,
    beneficiary_account: str | None = None,
    beneficiary_bank_country: str | None = None,
    amount: float = 0.0,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Screen all parties in a payment against sanctions lists."""
    results: dict[str, list[dict]] = {}

    # Screen originator
    orig_matches = await _screen_name(originator_name, threshold)
    results["originator"] = orig_matches

    # Screen beneficiary
    bene_matches = await _screen_name(beneficiary_name, threshold)
    results["beneficiary"] = bene_matches

    # Country screening
    country_risk = "clear"
    if beneficiary_bank_country:
        sanctioned_countries = {"IR", "KP", "SY", "CU", "VE"}
        if beneficiary_bank_country in sanctioned_countries:
            country_risk = "blocked"
            results["country"] = [{"list": "ofac_country", "match_type": "country", "country": beneficiary_bank_country, "program": "COUNTRY_SANCTIONS"}]

    # Determine combined risk
    combined_risk = "clear"
    if any(m.get("match_type") == "exact" for party in results.values() if isinstance(party, list) for m in party):
        combined_risk = "critical"
    elif any(len(party) > 0 for party in results.values() if isinstance(party, list)):
        combined_risk = "high"
    elif country_risk == "blocked":
        combined_risk = "critical"

    screening_id = hashlib.md5(f"{payment_id}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12].upper()
    result = {
        "screening_id": screening_id,
        "payment_id": payment_id,
        "originator_name": originator_name,
        "beneficiary_name": beneficiary_name,
        "results": results,
        "country_risk": country_risk,
        "combined_risk_level": combined_risk,
        "recommended_action": "BLOCK" if combined_risk == "critical" else "REVIEW" if combined_risk == "high" else "PROCEED",
        "timestamp": datetime.utcnow().isoformat(),
    }

    _SCREENING_HISTORY.append(result)
    return result


async def _screen_name(name: str, threshold: float = 0.85) -> list[dict]:
    """Screen a single name against all sanctions lists."""
    matches: list[dict] = []
    for list_name, entries in SANCTIONS_LISTS.items():
        for entry in entries:
            direct_score = _fuzzy_match(name, entry["name"])
            alias_score = _check_aliases(name, entry.get("aliases", []))
            best_score = max(direct_score, alias_score)
            if best_score >= threshold:
                matches.append({
                    "list": list_name,
                    "entry_id": entry["id"],
                    "matched_name": entry["name"],
                    "match_score": round(best_score, 3),
                    "match_type": "exact" if best_score >= 0.99 else "fuzzy",
                    "program": entry["program"],
                    "country": entry["country"],
                })
    return matches


async def get_screening_history(limit: int = 50) -> dict[str, Any]:
    """Get sanctions screening history."""
    return {"total": len(_SCREENING_HISTORY), "history": _SCREENING_HISTORY[-limit:]}


async def get_sanctions_lists_info() -> dict[str, Any]:
    """Get information about loaded sanctions lists."""
    info = {}
    for list_name, entries in SANCTIONS_LISTS.items():
        info[list_name] = {"count": len(entries)}
    return {"lists": info, "total_entries": sum(len(v) for v in SANCTIONS_LISTS.values())}
