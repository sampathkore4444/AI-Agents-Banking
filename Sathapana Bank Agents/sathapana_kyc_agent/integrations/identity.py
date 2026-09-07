"""Identity verification provider adapters (liveness, document, face match)."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from integrations.base import post_json


class IdentityProvider(ABC):
    @abstractmethod
    def verify(self, customer_id: str, document_image_url: str, selfie_url: str, nationality: str, extracted_data: dict | None) -> dict:
        """Run liveness + document authenticity + face match."""


class StubIdentityProvider(IdentityProvider):
    """Deterministic md5-based simulation for development."""

    def verify(self, customer_id: str, document_image_url: str, selfie_url: str, nationality: str, extracted_data: dict | None = None) -> dict:
        doc_hash = hashlib.md5(document_image_url.encode()).hexdigest()
        is_valid_hash = int(doc_hash[:8], 16) % 100

        liveness = "pass" if is_valid_hash > 5 else "fail"
        authenticity = "authentic" if is_valid_hash > 5 else "suspected_fraud"
        face_match = round(min(max(is_valid_hash / 100.0, 0.4), 0.99), 2)

        if liveness == "pass" and authenticity == "authentic" and face_match > 0.7:
            overall = "verified"
        elif liveness == "fail" or authenticity == "suspected_fraud":
            overall = "rejected"
        else:
            overall = "manual_review"

        return {
            "verification_id": "vid_stub_" + doc_hash[:10],
            "customer_id": customer_id,
            "nationality": nationality,
            "liveness_check": liveness,
            "document_authenticity": authenticity,
            "face_match": face_match,
            "overall_result": overall,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "extracted_data_used": extracted_data or {},
            "provider": "stub",
        }


class HttpIdentityProvider(IdentityProvider):
    """Calls a live digital-identity vendor (config: IDENTITY_API_URL/TOKEN)."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def verify(self, customer_id: str, document_image_url: str, selfie_url: str, nationality: str, extracted_data: dict | None = None) -> dict:
        payload: dict[str, Any] = {
            "customer_id": customer_id,
            "documents": {"front": document_image_url},
            "biometrics": {"selfie": selfie_url},
            "nationality": nationality,
            "extracted_data": extracted_data or {},
        }
        result = post_json(self.url, self.token, payload)
        result.setdefault("provider", "http")
        return result