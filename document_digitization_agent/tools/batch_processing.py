"""
Batch Processing Tool — MCP tool.

Handles batch document classification, extraction, validation, and enrichment.
Processes multiple documents efficiently with parallel classification and
sequential type-based extraction.

Features:
- Parallel document classification (embeddings are batched)
- Type-based extraction routing (same-type docs use cached schemas)
- Error isolation (one failed doc doesn't stop the batch)
- Aggregated summary with statistics
- Configurable concurrency limits
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import Counter
from datetime import datetime
from typing import Any

from config import settings
from tools.document_classification import classify_document
from tools.ocr_extraction import extract_document_data
from tools.data_validation import validate_extracted_data
from tools.data_enrichment import (
    enrich_bank_statement_data,
    enrich_contract_data,
    enrich_financial_statement_data,
    enrich_invoice_data,
)

logger = logging.getLogger(__name__)

# Max concurrent OCR calls (avoids overwhelming API rate limits)
MAX_CONCURRENT_OCR = 5
MAX_CONCURRENT_CLASSIFY = 10


async def batch_classify_and_extract(
    document_urls: list[str],
    document_type: str | None = None,
    auto_validate: bool = True,
    auto_enrich: bool = True,
    max_concurrent: int | None = None,
) -> dict:
    """
    Full batch pipeline: classify → extract → validate → enrich for multiple documents.

    If document_type is provided, skips classification and uses that type for all docs.

    Args:
        document_urls: List of document URLs to process
        document_type: Optional forced type (skips classification)
        auto_validate: Whether to validate extracted data (default: True)
        auto_enrich: Whether to enrich extracted data (default: True)
        max_concurrent: Max concurrent OCR calls (default: 5)

    Returns:
        Batch results with per-document details and summary statistics.
    """
    batch_id = str(uuid.uuid4())[:12]
    concurrency = max_concurrent or MAX_CONCURRENT_OCR
    total_docs = len(document_urls)

    logger.info("Batch %s: processing %d documents (concurrency=%d)", batch_id, total_docs, concurrency)

    # ── Phase 1: Classify all documents ──────────────────────────
    classifications = {}
    if document_type:
        # Skip classification — use provided type for all
        for url in document_urls:
            classifications[url] = {
                "document_type": document_type,
                "confidence": 1.0,
                "skipped_classification": True,
            }
    else:
        # Classify in parallel (lightweight — embeddings only)
        classify_sem = asyncio.Semaphore(MAX_CONCURRENT_CLASSIFY)

        async def _classify_one(url: str) -> tuple[str, dict]:
            async with classify_sem:
                try:
                    result = await classify_document(url)
                    return url, result
                except Exception as e:
                    logger.warning("Classification failed for %s: %s", url, e)
                    return url, {"document_type": "unknown", "confidence": 0.0, "error": str(e)}

        classify_tasks = [_classify_one(url) for url in document_urls]
        classify_results = await asyncio.gather(*classify_tasks)
        for url, result in classify_results:
            classifications[url] = result

    # ── Phase 2: Group by type for efficient extraction ──────────
    type_groups: dict[str, list[str]] = {}
    for url in document_urls:
        doc_type = classifications[url].get("document_type", "unknown")
        if doc_type not in type_groups:
            type_groups[doc_type] = []
        type_groups[doc_type].append(url)

    logger.info("Batch %s: classified into %d types: %s", batch_id, len(type_groups), {k: len(v) for k, v in type_groups.items()})

    # ── Phase 3: Extract + Validate + Enrich (with concurrency) ──
    ocr_sem = asyncio.Semaphore(concurrency)
    results = []

    async def _process_one(url: str) -> dict:
        doc_type = classifications[url].get("document_type", "unknown")
        doc_result = {
            "document_url": url,
            "document_type": doc_type,
            "classification": classifications[url],
            "extraction": None,
            "validation": None,
            "enrichment": None,
            "status": "pending",
            "error": None,
        }

        try:
            # Extract
            async with ocr_sem:
                extraction = await extract_document_data(url, doc_type)
            doc_result["extraction"] = {
                "fields": extraction.get("extracted_fields"),
                "confidence": extraction.get("overall_confidence"),
                "quality": extraction.get("ocr_quality"),
                "provider": extraction.get("provider"),
            }

            # Validate
            if auto_validate:
                validation = await validate_extracted_data(doc_type, extraction.get("extracted_fields", {}))
                doc_result["validation"] = {
                    "is_valid": validation.get("is_valid"),
                    "error_count": validation.get("error_count"),
                    "warning_count": validation.get("warning_count"),
                    "recommendation": validation.get("recommendation"),
                }

            # Enrich
            if auto_enrich and doc_result.get("validation", {}).get("is_valid", True):
                enrich_func = {
                    "invoice": enrich_invoice_data,
                    "bank_statement": enrich_bank_statement_data,
                    "contract": enrich_contract_data,
                    "financial_statement": enrich_financial_statement_data,
                }.get(doc_type)

                if enrich_func:
                    enrichment = await enrich_func(extraction.get("extracted_fields", {}))
                    doc_result["enrichment"] = {
                        "enrichments_applied": enrichment.get("enrichments_applied"),
                        "metadata_keys": list(enrichment.get("enrichment_metadata", {}).keys()),
                    }

            # Determine status
            if extraction.get("ocr_quality") == "failed":
                doc_result["status"] = "ocr_failed"
            elif doc_result.get("validation") and not doc_result["validation"].get("is_valid"):
                doc_result["status"] = "validation_failed"
            else:
                doc_result["status"] = "processed"

        except Exception as e:
            logger.error("Processing failed for %s: %s", url, e)
            doc_result["status"] = "error"
            doc_result["error"] = str(e)

        return doc_result

    # Run all document processing
    process_tasks = [_process_one(url) for url in document_urls]
    results = await asyncio.gather(*process_tasks)

    # ── Phase 4: Build summary statistics ────────────────────────
    status_counts = Counter(r["status"] for r in results)
    type_counts = Counter(r["document_type"] for r in results)

    confidences = [r["extraction"]["confidence"] for r in results if r.get("extraction") and r["extraction"].get("confidence") is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    provider_counts = Counter(
        r["extraction"]["provider"] for r in results
        if r.get("extraction") and r["extraction"].get("provider")
    )

    validation_results = [r["validation"] for r in results if r.get("validation")]
    valid_count = sum(1 for v in validation_results if v.get("is_valid"))

    enriched_count = sum(1 for r in results if r.get("enrichment"))

    batch_result = {
        "batch_id": batch_id,
        "total_documents": total_docs,
        "documents": results,
        "summary": {
            "status_distribution": dict(status_counts),
            "type_distribution": dict(type_counts),
            "ocr_providers_used": dict(provider_counts),
            "average_confidence": round(avg_confidence, 3),
            "classification_stats": {
                "auto_classified": sum(1 for c in classifications.values() if not c.get("skipped_classification")),
                "type_provided": sum(1 for c in classifications.values() if c.get("skipped_classification")),
            },
            "validation_stats": {
                "validated": len(validation_results),
                "valid": valid_count,
                "invalid": len(validation_results) - valid_count,
            },
            "enrichment_stats": {
                "enriched": enriched_count,
            },
            "performance": {
                "concurrency_limit": concurrency,
            },
        },
        "started_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        "Batch %s complete: %d processed, %d failed, avg_confidence=%.2f",
        batch_id,
        status_counts.get("processed", 0),
        status_counts.get("error", 0) + status_counts.get("ocr_failed", 0),
        avg_confidence,
    )

    return batch_result


async def batch_extract_only(
    document_urls: list[str],
    document_types: dict[str, str] | None = None,
    max_concurrent: int | None = None,
) -> dict:
    """
    Batch extraction only (no validation/enrichment) — faster for bulk processing.

    Args:
        document_urls: List of document URLs to extract from
        document_types: Optional mapping of url → document_type (skips classification)
        max_concurrent: Max concurrent OCR calls (default: 5)

    Returns:
        Extraction results for each document.
    """
    batch_id = str(uuid.uuid4())[:12]
    concurrency = max_concurrent or MAX_CONCURRENT_OCR
    ocr_sem = asyncio.Semaphore(concurrency)

    logger.info("Batch extract %s: %d documents", batch_id, len(document_urls))

    async def _extract_one(url: str) -> dict:
        doc_type = (document_types or {}).get(url, "unknown")
        try:
            async with ocr_sem:
                result = await extract_document_data(url, doc_type)
            return {
                "document_url": url,
                "document_type": doc_type,
                "fields": result.get("extracted_fields"),
                "confidence": result.get("overall_confidence"),
                "quality": result.get("ocr_quality"),
                "provider": result.get("provider"),
                "status": "extracted",
            }
        except Exception as e:
            return {
                "document_url": url,
                "document_type": doc_type,
                "status": "error",
                "error": str(e),
            }

    tasks = [_extract_one(url) for url in document_urls]
    results = await asyncio.gather(*tasks)

    status_counts = Counter(r["status"] for r in results)

    return {
        "batch_id": batch_id,
        "total_documents": len(document_urls),
        "documents": results,
        "summary": {
            "extracted": status_counts.get("extracted", 0),
            "errors": status_counts.get("error", 0),
        },
    }


async def batch_validate_only(
    extractions: list[dict],
) -> dict:
    """
    Batch validation — validate multiple extracted datasets.

    Args:
        extractions: List of dicts with 'document_type' and 'extracted_fields'

    Returns:
        Validation results for each document.
    """
    batch_id = str(uuid.uuid4())[:12]

    async def _validate_one(ext: dict) -> dict:
        doc_type = ext.get("document_type", "unknown")
        fields = ext.get("extracted_fields", {})
        try:
            result = await validate_extracted_data(doc_type, fields)
            return {
                "document_type": doc_type,
                "is_valid": result.get("is_valid"),
                "error_count": result.get("error_count"),
                "warning_count": result.get("warning_count"),
                "recommendation": result.get("recommendation"),
                "status": "validated",
            }
        except Exception as e:
            return {
                "document_type": doc_type,
                "status": "error",
                "error": str(e),
            }

    tasks = [_validate_one(ext) for ext in extractions]
    results = await asyncio.gather(*tasks)

    valid_count = sum(1 for r in results if r.get("is_valid"))

    return {
        "batch_id": batch_id,
        "total_documents": len(extractions),
        "documents": results,
        "summary": {
            "valid": valid_count,
            "invalid": len(results) - valid_count,
        },
    }
