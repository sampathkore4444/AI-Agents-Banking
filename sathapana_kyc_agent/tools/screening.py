"""
Sanctions, PEP and Beneficial Ownership Screening — MCP tool stubs.

Sathapana/NBC-aligned lists: UN Consolidated List (incl. UNSCR 1267/1989),
NBC/Cambodia-targeted financial sanctions, OFAC, EU, plus a domestic
Cambodian PEP list. Deterministic hash-based results for development.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from config import settings


def _hash_val(text: str) -> int:
    return int(hashlib.md5(text.lower().encode()).hexdigest()[:8], 16) % 100


def screen_customer_sanctions(
    full_name: str,
    date_of_birth: str,
    nationality: str = "KH",
    aliases: list[str] | None = None,
) -> dict:
    """Screen a customer against UNSC, NBC/Cambodia, OFAC and EU lists + PEP."""
    h = _hash_val(full_name)

    un_result = "clear" if h > 8 else "potential_match"
    nbc_result = "clear" if h > 8 else "potential_match"
    ofac_result = "clear" if h > 10 else "potential_match"
    eu_result = "clear" if h > 10 else "potential_match"

    # Domestic (Cambodia) PEP: high-level officials, ministers, deputies, etc.
    pep_status = "not_pep" if h > 20 else ("foreign_pep" if "kh" not in nationality.lower() else "domestic_pep")
    adverse_media = h < 6

    has_hits = any(r != "clear" for r in (un_result, nbc_result, ofac_result, eu_result))
    if has_hits:
        risk = "critical" if un_result != "clear" else "high"
    elif pep_status != "not_pep" or adverse_media:
        risk = "medium"
    else:
        risk = "low"

    return {
        "screening_id": str(uuid.uuid4()),
        "customer_name": full_name,
        "date_of_birth": date_of_birth,
        "nationality": nationality,
        "un_result": un_result,
        "nbc_cambodia_result": nbc_result,
        "ofac_result": ofac_result,
        "eu_result": eu_result,
        "pep_status": pep_status,
        "adverse_media": adverse_media,
        "risk_level": risk,
        "onboarding_prohibited": un_result != "clear",
        "screened_at": datetime.now(timezone.utc).isoformat(),
        "aliases_checked": aliases or [],
    }


def screen_ubo(owners: list[dict], risk_level: str = "low") -> dict:
    """
    Screen beneficial owners of a legal person.

    owners: list of {"full_name", "date_of_birth", "nationality", "ownership_pct"}.
    Applies the NBC/FATF default threshold and a lower risk-based threshold
    for higher-risk customers.
    """
    threshold = settings.ubo_high_risk_threshold_pct if risk_level in ("high", "critical") else settings.ubo_default_threshold_pct

    results = []
    blocked_names: list[str] = []
    unidentified_ownership: list[str] = []

    for owner in owners or []:
        pct = float(owner.get("ownership_pct", 0))
        name = owner.get("full_name", "")
        screening = _hash_val(name)

        captured = pct >= threshold
        hit = screening < 6
        pep = "not_pep" if screening > 20 else "domestic_pep"

        results.append(
            {
                "full_name": name,
                "nationality": owner.get("nationality", ""),
                "ownership_pct": pct,
                "captured_as_ubo": captured,
                "screening_hit": hit,
                "pep_status": pep,
            }
        )
        if hit:
            blocked_names.append(name)
        if owner.get("identified") is False or (owner.get("identified") is True and pct <= 0):
            unidentified_ownership.append(name)

    decision = "block" if blocked_names else "verify" if unidentified_ownership else "clear"
    return {
        "ubo_screening_id": str(uuid.uuid4()),
        "threshold_applied_pct": threshold,
        "reason": "risk-based" if risk_level in ("high", "critical") else "default (FATF-aligned)",
        "owners": results,
        "decision": decision,
        "blocked_names": blocked_names,
        "unidentified_ownership": unidentified_ownership,
    }