"""OCR / document extraction provider adapters (Khmer-capable OCR in prod)."""

from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from integrations.base import post_json

# Canonical field schemas per Cambodia KYC document type
EXTRACTION_SCHEMAS = {
    "national_id": ["full_name_kh", "full_name_latin", "gender", "date_of_birth", "id_number", "address", "issue_date", "expiry_date"],
    "passport": ["full_name", "nationality", "date_of_birth", "passport_number", "issue_date", "expiry_date", "mrz"],
    "family_book": ["household_head", "members", "address", "book_number", "issuing_commune"],
    "business_registration": ["company_name", "registration_number", "registration_date", "registered_address", "legal_form", "directors", "authorized_capital"],
    "tax_certificate": ["taxpayer_name", "vatin", "patent_year", "patent_series", "business_activity", "address"],
    "proof_of_address": ["full_name", "address", "document_type", "issue_date", "reference"],
    "bank_statement": ["account_holder", "account_number", "balance", "statement_period", "currency"],
    "collateral": ["owner_name", "certificate_number", "parcel_id", "encumbrance_status"],
}

KHMER_OCR_DOCS = ("national_id", "family_book", "business_registration")


class OcrProvider(ABC):
    @abstractmethod
    def extract(self, document_url: str, document_type: str) -> dict:
        """Return structured fields extracted from a KYC document."""


class StubOcrProvider(OcrProvider):
    """Simulated OCR for development (Khmer-script aware flag)."""

    def extract(self, document_url: str, document_type: str) -> dict:
        if document_type not in EXTRACTION_SCHEMAS:
            return {"error": f"Unsupported document_type: {document_type}. Supported: {list(EXTRACTION_SCHEMAS)}"}

        url_hash = hashlib.md5(document_url.encode()).hexdigest()
        confidence = round(min(max(int(url_hash[:4], 16) / 1000.0, 0.65), 0.99), 2)
        quality = "high" if confidence > 0.85 else "medium" if confidence > 0.7 else "low"

        return {
            "extraction_id": "ocr_stub_" + url_hash[:10],
            "document_url": document_url,
            "document_type": document_type,
            "extracted_fields": {f: f"extracted_{f}" for f in EXTRACTION_SCHEMAS[document_type]},
            "confidence_score": confidence,
            "ocr_quality": quality,
            "khmer_ocr_supported": document_type in KHMER_OCR_DOCS,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "provider": "stub",
        }


class HttpOcrProvider(OcrProvider):
    """Calls a live OCR service with Khmer support (config: OCR_API_URL/TOKEN)."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def extract(self, document_url: str, document_type: str) -> dict:
        payload: dict[str, Any] = {
            "document_url": document_url,
            "document_type": document_type,
            "expect_fields": EXTRACTION_SCHEMAS.get(document_type, []),
            "languages": ["km", "en"],
        }
        result = post_json(self.url, self.token, payload)
        result.setdefault("provider", "http")
        result.setdefault("extraction_id", str(uuid.uuid4()))
        return result