"""
Document Extraction Tool — MCP tool stub.

Delegates OCR to the configured `integrations.ocr.OcrProvider` (Khmer-capable
OCR in production). Canonical field schemas per document type re-exported
from the OCR integration.
"""

from __future__ import annotations

from integrations.ocr import EXTRACTION_SCHEMAS, KHMER_OCR_DOCS  # noqa: F401  (re-exported for callers)


def extract_document(document_url: str, document_type: str) -> dict:
    """Extract structured data from an uploaded KYC document via the OCR provider."""
    from integrations import get_providers

    return get_providers().ocr.extract(document_url, document_type)