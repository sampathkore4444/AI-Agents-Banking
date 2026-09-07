"""Sanctions / PEP screening provider adapters.

Production: point the HTTP provider at a real sanctions feed
(Dow Jones, Refinitiv, LexisNexis, or the NBC list) — the tool layer only
depends on `SanctionsProvider.screen(...)`.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from integrations.base import post_json


def _hash_val(text: str) -> int:
    return int(hashlib.md5(text.lower().encode()).hexdigest()[:8], 16) % 100


class SanctionsProvider(ABC):
    @abstractmethod
    def screen(self, full_name: str, date_of_birth: str, nationality: str, aliases: list[str]) -> dict:
        """Return a screening result dict (list verdicts, PEP, adverse media)."""


class StubSanctionsProvider(SanctionsProvider):
    """Deterministic hash-based results for development and offline tests."""

    def screen(self, full_name: str, date_of_birth: str, nationality: str, aliases: list[str] | None = None) -> dict:
        h = _hash_val(full_name)

        un_result = "clear" if h > 8 else "potential_match"
        nbc_result = "clear" if h > 8 else "potential_match"
        ofac_result = "clear" if h > 10 else "potential_match"
        eu_result = "clear" if h > 10 else "potential_match"

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
            "screening_id": "scr_stub_" + hashlib.md5(full_name.encode()).hexdigest()[:10],
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
            "provider": "stub",
        }


class HttpSanctionsProvider(SanctionsProvider):
    """Calls a live sanctions/PEP API (config: SANCTIONS_API_URL/TOKEN)."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def screen(self, full_name: str, date_of_birth: str, nationality: str, aliases: list[str] | None = None) -> dict:
        payload: dict[str, Any] = {
            "customer": {"full_name": full_name, "date_of_birth": date_of_birth, "nationality": nationality, "aliases": aliases or []},
            "lists": ["unsc", "nbc_cambodia", "ofac", "eu", "kh_pep"],
        }
        result = post_json(self.url, self.token, payload)
        result.setdefault("provider", "http")
        result.setdefault("screened_at", datetime.now(timezone.utc).isoformat())
        return result