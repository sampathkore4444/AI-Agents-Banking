"""
Document Classification Tool — MCP tool stub.

Classifies uploaded documents into categories using document embeddings.
Routes documents to appropriate extraction pipelines.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Document categories and their descriptions
DOCUMENT_CATEGORIES = {
    "invoice": {
        "category": "accounts_payable",
        "description": "Vendor invoices, bills, purchase orders",
        "extraction_pipeline": "financial_extraction",
        "required_fields": ["vendor_name", "invoice_number", "invoice_date", "total_amount"],
    },
    "contract": {
        "category": "legal",
        "description": "Service agreements, loan agreements, NDAs, leases",
        "extraction_pipeline": "legal_extraction",
        "required_fields": ["contract_title", "parties", "effective_date", "total_value"],
    },
    "bank_statement": {
        "category": "financial",
        "description": "Bank account statements, transaction records",
        "extraction_pipeline": "financial_extraction",
        "required_fields": ["account_holder", "statement_period", "opening_balance", "closing_balance"],
    },
    "tax_return": {
        "category": "financial",
        "description": "IRS tax returns, W-2s, 1099s",
        "extraction_pipeline": "financial_extraction",
        "required_fields": ["taxpayer_name", "tax_year", "adjusted_gross_income"],
    },
    "payslip": {
        "category": "financial",
        "description": "Employee pay stubs, salary statements",
        "extraction_pipeline": "financial_extraction",
        "required_fields": ["employee_name", "pay_period", "gross_pay", "net_pay"],
    },
    "proof_of_address": {
        "category": "kyc",
        "description": "Utility bills, bank statements for address verification",
        "extraction_pipeline": "kyc_extraction",
        "required_fields": ["full_name", "address", "issue_date"],
    },
    "identity_document": {
        "category": "kyc",
        "description": "Passports, driving licences, national IDs",
        "extraction_pipeline": "kyc_extraction",
        "required_fields": ["full_name", "date_of_birth", "document_number"],
    },
    "financial_statement": {
        "category": "financial",
        "description": "Balance sheets, income statements, cash flow statements",
        "extraction_pipeline": "financial_extraction",
        "required_fields": ["company_name", "reporting_period", "total_assets"],
    },
    "loan_application": {
        "category": "lending",
        "description": "Loan application forms and supporting documents",
        "extraction_pipeline": "lending_extraction",
        "required_fields": ["borrower_name", "loan_type", "requested_amount"],
    },
    "corporate_resolution": {
        "category": "legal",
        "description": "Board resolutions, shareholder resolutions",
        "extraction_pipeline": "legal_extraction",
        "required_fields": ["company_name", "resolution_date", "authorized_action"],
    },
}


async def classify_document(
    document_url: str,
    hint: str | None = None,
) -> dict:
    """
    Classify a document into a category using document embeddings.

    Uses semantic similarity to match document content against known categories.
    Routes to appropriate extraction pipeline.

    Args:
        document_url: URL or file reference to the document
        hint: Optional hint about expected document type

    Returns:
        Classification result with document type, category, confidence, and pipeline routing.
    """
    logger.info("Classifying document: url=%s, hint=%s", document_url, hint)

    # In production: call classification API with document embeddings
    # response = await httpx.AsyncClient().post(
    #     f"{settings.classification_api_url}/v1/classify",
    #     json={"document_url": document_url, "hint": hint},
    # )

    # Stub: simulate classification based on URL hash
    url_hash = hashlib.md5(document_url.encode()).hexdigest()
    category_idx = int(url_hash[:2], 16) % len(DOCUMENT_CATEGORIES)
    doc_type = list(DOCUMENT_CATEGORIES.keys())[category_idx]

    # If hint provided, boost that type's confidence
    if hint and hint in DOCUMENT_CATEGORIES:
        doc_type = hint
        confidence = 0.92 + (int(url_hash[:2], 16) % 8) / 100
    else:
        confidence = 0.75 + (int(url_hash[:2], 16) % 20) / 100

    category_info = DOCUMENT_CATEGORIES[doc_type]

    # Generate alternative classifications
    alternatives = []
    for alt_type, alt_info in DOCUMENT_CATEGORIES.items():
        if alt_type != doc_type:
            alt_conf = 0.1 + (int(url_hash[:2], 16) % 30) / 100
            alternatives.append({
                "document_type": alt_type,
                "category": alt_info["category"],
                "confidence": round(alt_conf, 3),
            })
    alternatives.sort(key=lambda x: x["confidence"], reverse=True)

    result = {
        "classification_id": str(uuid.uuid4()),
        "document_url": document_url,
        "document_type": doc_type,
        "category": category_info["category"],
        "category_description": category_info["description"],
        "extraction_pipeline": category_info["extraction_pipeline"],
        "required_fields": category_info["required_fields"],
        "confidence": round(confidence, 3),
        "alternatives": alternatives[:3],
        "hint_used": hint,
        "classified_at": datetime.utcnow().isoformat(),
    }

    logger.info("Document classified as %s (confidence=%.2f)", doc_type, confidence)
    return result


async def batch_classify(
    document_urls: list[str],
) -> dict:
    """
    Classify multiple documents in a batch.

    Returns classifications for each document with summary statistics.
    """
    logger.info("Batch classifying %d documents", len(document_urls))

    classifications = []
    for url in document_urls:
        result = await classify_document(url)
        classifications.append(result)

    # Summary statistics
    type_counts = {}
    for c in classifications:
        doc_type = c["document_type"]
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    avg_confidence = (
        sum(c["confidence"] for c in classifications) / len(classifications)
        if classifications else 0
    )

    result = {
        "batch_id": str(uuid.uuid4()),
        "total_documents": len(document_urls),
        "classifications": classifications,
        "summary": {
            "type_distribution": type_counts,
            "average_confidence": round(avg_confidence, 3),
            "low_confidence_count": sum(1 for c in classifications if c["confidence"] < 0.7),
        },
        "classified_at": datetime.utcnow().isoformat(),
    }

    logger.info("Batch classification complete: %d documents, avg confidence=%.2f",
                len(classifications), avg_confidence)
    return result


async def get_supported_document_types() -> dict:
    """Return all supported document types and their metadata."""
    return {
        "total_types": len(DOCUMENT_CATEGORIES),
        "types": {
            name: {
                "category": info["category"],
                "description": info["description"],
                "extraction_pipeline": info["extraction_pipeline"],
                "required_fields": info["required_fields"],
            }
            for name, info in DOCUMENT_CATEGORIES.items()
        },
    }
