"""
Document Extraction Tool — MCP tool stub (Sathapana/NBC localised).

In production this calls an OCR service with Khmer script support
(Google Vision, AWS Textract, VNPT, local OCR) and document classification.
Returns simulated results for development; document types follow
Cambodia's accepted identity/registration documents.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

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


def extract_document(document_url: str, document_type: str) -> dict:
    """Extract structured data from an uploaded KYC document."""
    if document_type not in EXTRACTION_SCHEMAS:
        return {"error": f"Unsupported document_type: {document_type}. Supported: {list(EXTRACTION_SCHEMAS)}"}

    url_hash = hashlib.md5(document_url.encode()).hexdigest()
    confidence = round(min(max(int(url_hash[:4], 16) / 1000.0, 0.65), 0.99), 2)
    quality = "high" if confidence > 0.85 else "medium" if confidence > 0.7 else "low"

    extracted_fields = {f: f"extracted_{f}" for f in EXTRACTION_SCHEMAS[document_type]}

    return {
        "extraction_id": str(uuid.uuid4()),
        "document_url": document_url,
        "document_type": document_type,
        "extracted_fields": extracted_fields,
        "confidence_score": confidence,
        "ocr_quality": quality,
        "khmer_ocr_supported": document_type in ("national_id", "family_book", "business_registration"),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }