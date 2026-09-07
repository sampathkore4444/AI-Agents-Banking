"""
Sanctions, PEP and Beneficial Ownership Screening — MCP tool stubs.

Screening delegates to the configured `integrations.sanctions.SanctionsProvider`
(stub by default; point it at a live feed in production). UBO threshold logic
remains in-process (NBC/FATF rules).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from config import settings


def screen_customer_sanctions(
    full_name: str,
    date_of_birth: str,
    nationality: str = "KH",
    aliases: list[str] | None = None,
) -> dict:
    """Screen a customer against the configured sanctions/PEP provider."""
    from integrations import get_providers

    return get_providers().sanctions.screen(full_name, date_of_birth, nationality, aliases or [])


def _score_name(name: str) -> int:
    return int(hashlib.md5(name.lower().encode()).hexdigest()[:8], 16) % 100 if name else 100


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
        screening = _score_name(name)

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