"""
PEP (Politically Exposed Persons) Screening — Identification and Risk Assessment.

Capabilities:
- PEP identification and classification
- Risk tier assignment (low/medium/high)
- Enhanced due diligence triggers
- Ongoing monitoring
- RCA (Relatives and Close Associates) tracking
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

# ── Simulated PEP database ────────────────────────────────────────
PEP_DATABASE: list[dict] = [
    {
        "id": "PEP-001", "name": "Ahmad Al-Farsi", "country": "AE",
        "role": "Minister of Finance", "category": "foreign_pep",
        "risk_level": "high", "since": "2018-01-01",
        "aliases": ["A. Al-Farsi", "Ahmed Al Farsi"],
    },
    {
        "id": "PEP-002", "name": "Maria Santos", "country": "BR",
        "role": "Federal Judge", "category": "domestic_pep",
        "risk_level": "medium", "since": "2020-06-15",
        "aliases": ["M. Santos"],
    },
    {
        "id": "PEP-003", "name": "Li Wei Zhang", "country": "CN",
        "role": "Senior Executive, State-Owned Enterprise", "category": "foreign_pep",
        "risk_level": "high", "since": "2019-03-10",
        "aliases": ["L.W. Zhang", "Zhang Wei"],
    },
    {
        "id": "PEP-004", "name": "Nikolai Volkov", "country": "RU",
        "role": "Deputy Minister of Defense", "category": "foreign_pep",
        "risk_level": "high", "since": "2017-09-01",
        "aliases": ["N. Volkov", "Volkov Nikolai"],
    },
    {
        "id": "PEP-005", "name": "Patricia Okafor", "country": "NG",
        "role": "State Governor", "category": "domestic_pep",
        "risk_level": "medium", "since": "2021-05-20",
        "aliases": ["P. Okafor"],
    },
    {
        "id": "PEP-006", "name": "United Nations Development Programme", "country": "Global",
        "role": "International Organization", "category": "international_pep",
        "risk_level": "low", "since": "1965-01-01",
        "aliases": ["UNDP"],
    },
]

_RCA_LINKS: list[dict] = [
    {"pep_id": "PEP-001", "rca_name": "Fatima Al-Farsi", "relationship": "spouse", "country": "AE"},
    {"pep_id": "PEP-001", "rca_name": "Omar Al-Farsi", "relationship": "son", "country": "AE"},
    {"pep_id": "PEP-003", "rca_name": "Zhang Mei", "relationship": "spouse", "country": "CN"},
    {"pep_id": "PEP-004", "rca_name": "Elena Volkov", "relationship": "spouse", "country": "GB"},
]

_PEP_SCREENING_HISTORY: dict[str, dict] = {}


def _fuzzy_match(name1: str, name2: str) -> float:
    from difflib import SequenceMatcher
    return SequenceMatcher(None, name1.lower().strip(), name2.lower().strip()).ratio()


async def screen_for_pep(
    name: str,
    country: str | None = None,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Screen an individual against PEP database."""
    matches: list[dict] = []

    for pep in PEP_DATABASE:
        if pep["category"] == "international_pep":
            continue

        direct_score = _fuzzy_match(name, pep["name"])
        alias_score = max((_fuzzy_match(name, a) for a in pep.get("aliases", [])), default=0.0)
        best_score = max(direct_score, alias_score)

        if best_score >= threshold:
            matches.append({
                "pep_id": pep["id"],
                "matched_name": pep["name"],
                "match_score": round(best_score, 3),
                "match_type": "exact" if best_score >= 0.99 else "fuzzy",
                "country": pep["country"],
                "role": pep["role"],
                "category": pep["category"],
                "risk_level": pep["risk_level"],
            })

    screening_id = hashlib.md5(f"{name}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12].upper()

    result = {
        "screening_id": screening_id,
        "name": name,
        "is_pep": len(matches) > 0,
        "matches": matches,
        "risk_level": "high" if matches else "clear",
        "requires_edd": len(matches) > 0,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _PEP_SCREENING_HISTORY[screening_id] = result
    return result


async def get_pep_profile(pep_id: str) -> dict[str, Any]:
    """Get detailed PEP profile."""
    for pep in PEP_DATABASE:
        if pep["pep_id"] == pep_id or pep["id"] == pep_id:
            rca = [r for r in _RCA_LINKS if r["pep_id"] == pep["id"]]
            return {
                **pep,
                "relatives_close_associates": rca,
                "rca_count": len(rca),
            }
    return {"error": "PEP not found"}


async def assess_pep_risk(
    pep_id: str,
    country_risk: str = "medium",
    business_type: str = "retail_banking",
    transaction_volume: str = "normal",
) -> dict[str, Any]:
    """Assess risk level for a PEP relationship."""
    pep = None
    for p in PEP_DATABASE:
        if p["id"] == pep_id:
            pep = p
            break
    if not pep:
        return {"error": "PEP not found"}

    risk_score = 0.0
    factors: list[str] = []

    # Base risk from PEP category
    category_risks = {"foreign_pep": 30, "domestic_pep": 20, "international_pep": 10}
    risk_score += category_risks.get(pep["category"], 20)
    factors.append(f"Category: {pep['category']}")

    # Country risk
    country_risks = {"high": 30, "medium": 15, "low": 5}
    risk_score += country_risks.get(country_risk, 15)
    factors.append(f"Country risk: {country_risk}")

    # Business type
    high_risk_business = ["corporate_banking", "private_banking", "trade_finance", "correspondent_banking"]
    if business_type in high_risk_business:
        risk_score += 15
        factors.append(f"Business type: {business_type} (elevated)")

    # Transaction volume
    if transaction_volume == "high":
        risk_score += 10
        factors.append("High transaction volume")

    # RCA risk
    rca = [r for r in _RCA_LINKS if r["pep_id"] == pep_id]
    if rca:
        risk_score += 5
        factors.append(f"{len(rca)} relatives/close associates")

    risk_score = min(risk_score, 100.0)
    if risk_score >= 70:
        risk_tier = "high"
        edd_depth = "comprehensive"
    elif risk_score >= 40:
        risk_tier = "medium"
        edd_depth = "enhanced"
    else:
        risk_tier = "low"
        edd_depth = "standard"

    return {
        "pep_id": pep_id,
        "pep_name": pep["name"],
        "risk_score": round(risk_score, 2),
        "risk_tier": risk_tier,
        "edd_depth": edd_depth,
        "requires_senior_management_approval": risk_tier in ("high", "medium"),
        "monitoring_frequency": "monthly" if risk_tier == "high" else "quarterly" if risk_tier == "medium" else "annually",
        "risk_factors": factors,
        "recommendation": _get_recommendation(risk_tier),
        "timestamp": datetime.utcnow().isoformat(),
    }


async def get_rca_links(pep_id: str) -> dict[str, Any]:
    """Get relatives and close associates for a PEP."""
    links = [r for r in _RCA_LINKS if r["pep_id"] == pep_id]
    return {
        "pep_id": pep_id,
        "rca_count": len(links),
        "relatives_close_associates": links,
    }


async def get_pep_screening_history(limit: int = 50) -> dict[str, Any]:
    """Get PEP screening history."""
    entries = list(_PEP_SCREENING_HISTORY.values())[-limit:]
    return {"total_screenings": len(_PEP_SCREENING_HISTORY), "history": entries}


def _get_recommendation(risk_tier: str) -> str:
    recommendations = {
        "high": "Comprehensive EDD required. Senior management approval mandatory. Enhanced ongoing monitoring. Document source of funds and wealth. Annual relationship review.",
        "medium": "Enhanced due diligence required. Relationship manager approval. Semi-annual monitoring. Document business purpose and expected activity.",
        "low": "Standard due diligence sufficient. Periodic PEP screening (annual). Monitor for changes in PEP status.",
    }
    return recommendations.get(risk_tier, "Standard monitoring")
