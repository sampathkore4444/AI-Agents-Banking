"""
Document Extraction & Classification Tool — MCP tool stub.

In production this would call an OCR service (AWS Textract, Google Vision, etc.)
with document classification. Here we return simulated results.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Simulated extraction templates per document type
EXTRACTION_SCHEMAS = {
    "passport": ["full_name", "nationality", "date_of_birth", "passport_number", "expiry_date"],
    "drivers_license": ["full_name", "date_of_birth", "license_number", "address", "expiry_date"],
    "national_id": ["full_name", "date_of_birth", "id_number", "nationality"],
    "tax_id": ["business_name", "tax_id_number", "jurisdiction", "registration_date"],
    "proof_of_address": ["full_name", "address", "utility_provider", "issue_date"],
    "bank_statement": ["account_holder", "account_number", "balance", "statement_period"],
    "articles_of_incorporation": ["company_name", "registration_number", "registered_address", "incorporation_date"],
}


async def extract_document(
    document_url: str,
    document_type: str,
) -> dict:
    """
    Extract structured data from an uploaded KYC document.

    Returns extracted fields, confidence score, and OCR quality assessment.
    """
    logger.info("Extracting document type=%s from %s", document_type, document_url)

    # ── In production: call OCR API ──
    # response = await httpx.AsyncClient().post(
    #     f"{settings.ocr_api_url}/v1/extract",
    #     files={"document": open(document_url, "rb")},
    #     data={"type": document_type},
    # )

    # ── Stub: generate plausible extracted fields ──
    url_hash = hashlib.md5(document_url.encode()).hexdigest()
    confidence = round(min(max(int(url_hash[:4], 16) / 1000.0, 0.65), 0.99), 2)
    quality = "high" if confidence > 0.85 else "medium" if confidence > 0.7 else "low"

    schema = EXTRACTION_SCHEMAS.get(document_type, ["text_content"])
    extracted_fields = {}
    for field_name in schema:
        extracted_fields[field_name] = f"extracted_{field_name}"

    result = {
        "extraction_id": str(uuid.uuid4()),
        "document_url": document_url,
        "document_type": document_type,
        "extracted_fields": extracted_fields,
        "confidence_score": confidence,
        "ocr_quality": quality,
        "schema_validated": True,
        "extracted_at": datetime.utcnow().isoformat(),
    }

    logger.info("Document extraction complete: confidence=%s, quality=%s", confidence, quality)
    return result
