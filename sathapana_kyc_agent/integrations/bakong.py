"""Bakong (NBC mobile-money system) link provider adapters."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from integrations.base import post_json


class BakongProvider(ABC):
    @abstractmethod
    def link(self, customer_id: str, account_id: str, mobile_number: str, currency: str) -> dict:
        """Register an account to a Bakong profile."""


class StubBakongProvider(BakongProvider):
    """Simulated Bakong member-bank linkage."""

    def link(self, customer_id: str, account_id: str, mobile_number: str, currency: str) -> dict:
        return {
            "bakong_id": f"BKNG-{uuid.uuid4().hex[:10].upper()}",
            "customer_id": customer_id,
            "account_id": account_id,
            "mobile_number": mobile_number,
            "currency": currency,
            "status": "linked",
            "nbc_simulated": True,
            "linked_at": datetime.now(timezone.utc).isoformat(),
            "provider": "stub",
        }


class HttpBakongProvider(BakongProvider):
    """Calls the Bakong member-bank API (config: NBC_BAKONG_API_URL)."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/") + "/link"
        self.token = token

    def link(self, customer_id: str, account_id: str, mobile_number: str, currency: str) -> dict:
        payload = {
            "account_id": account_id,
            "customer_reference": customer_id,
            "mobile_number": mobile_number,
            "currency": currency,
        }
        result = post_json(self.url, self.token, payload)
        result.setdefault("provider", "http")
        result.setdefault("status", "linked")
        return result