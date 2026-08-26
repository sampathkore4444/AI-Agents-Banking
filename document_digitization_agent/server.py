"""
Document Digitization & Extraction Agent — MCP Server.

Exposes tools via the Model Context Protocol for document classification,
OCR extraction, data validation, data enrichment, and document management.
Integrates with a RAG pipeline for document processing knowledge retrieval.

Covers use case 10.1: Document Digitization & Extraction Agent.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.data_enrichment import (
    enrich_bank_statement_data,
    enrich_contract_data,
    enrich_financial_statement_data,
    enrich_invoice_data,
)
from tools.data_validation import cross_validate_documents, validate_extracted_data
from tools.document_classification import batch_classify, classify_document, get_supported_document_types
from tools.notifications import send_notification
from tools.batch_processing import batch_classify_and_extract, batch_extract_only, batch_validate_only
from tools.ocr_extraction import extract_document_data, extract_mrz, extract_table_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Document Digitization & Extraction Agent",
    instructions=(
        "Document Digitization & Extraction Agent for banking. Use these tools to process "
        "banking documents: classify document types, extract structured data via OCR, "
        "validate extracted data against schemas, enrich data with additional context, "
        "and manage document processing workflows. Always retrieve extraction schemas "
        "and validation rules via the knowledge_search tool before processing documents."
    ),
)

# ── Initialize RAG pipeline (shared across tool calls) ───────────
rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def knowledge_search(
    query: str,
    collection: str = "all",
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Search the document processing knowledge base using RAG (hybrid search + semantic).

    Use this tool to retrieve extraction schemas, validation rules, classification criteria,
    OCR best practices, and past extraction decisions.

    Args:
        query: Natural language query (e.g., "What fields are required for invoice extraction?")
        collection: Collection to search. Options: all, document_classification, extraction_schemas,
                    validation_rules, ocr_best_practices, past_extraction_decisions,
                    industry_document_standards, banking_document_templates
        top_k: Number of results to return (default 5)

    Returns:
        Retrieved chunks with scores, sources, and assembled context.
    """
    logger.info("Knowledge search: query='%s', collection=%s", query, collection)

    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)

    return {
        "query": result.query_rewrite,
        "results_count": len(result.chunks),
        "chunks": [
            {
                "text": c.text,
                "score": round(c.score, 3),
                "collection": c.collection,
                "metadata": c.metadata,
            }
            for c in result.chunks
        ],
        "assembled_context": result.assembled_context,
    }


@mcp.tool()
async def get_document_schema(document_type: str) -> dict[str, Any]:
    """
    Retrieve the expected fields, validation rules, and extraction schema for a document type.

    Args:
        document_type: One of: invoice, contract, bank_statement, tax_return, payslip,
                       proof_of_address, identity_document, financial_statement,
                       loan_application, corporate_resolution

    Returns:
        Expected fields, validation rules, and schema metadata.
    """
    result = rag.query_single(
        "extraction_schemas",
        f"{document_type} document schema required fields validation rules",
        n_results=3,
    )
    return {
        "document_type": document_type,
        "schemas_found": len(result),
        "schemas": [
            {"text": c.text, "metadata": c.metadata, "score": round(c.score, 3)}
            for c in result
        ],
    }


# ══════════════════════════════════════════════════════════════════
#  DOCUMENT CLASSIFICATION TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def classify_document_tool(
    document_url: str,
    hint: str | None = None,
) -> dict[str, Any]:
    """
    Classify a document into a category using document embeddings.

    Automatically detects document type and routes to the appropriate extraction pipeline.

    Args:
        document_url: URL or file reference to the document
        hint: Optional hint about expected document type

    Returns:
        Classification with document type, category, confidence, and extraction pipeline.
    """
    return await classify_document(document_url, hint)


@mcp.tool()
async def batch_classify_documents(
    document_urls: list[str],
) -> dict[str, Any]:
    """
    Classify multiple documents in a batch.

    Returns classifications for each document with summary statistics.

    Args:
        document_urls: List of document URLs to classify

    Returns:
        Batch classification results with type distribution and summary.
    """
    return await batch_classify(document_urls)


@mcp.tool()
async def get_supported_document_types() -> dict[str, Any]:
    """
    Return all supported document types and their metadata.

    Useful for understanding what documents can be processed and their required fields.
    """
    return await get_supported_document_types()


# ══════════════════════════════════════════════════════════════════
#  OCR EXTRACTION TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def extract_document(
    document_url: str,
    document_type: str,
    page_range_start: int | None = None,
    page_range_end: int | None = None,
) -> dict[str, Any]:
    """
    Extract structured data from a document using OCR.

    Extracts fields according to the document type's schema. Returns extracted data
    with per-field confidence scores and overall quality metrics.

    Args:
        document_url: URL or file reference to the document
        document_type: Type of document (invoice, contract, bank_statement, etc.)
        page_range_start: Optional start page (default: first page)
        page_range_end: Optional end page (default: last page)

    Returns:
        Extracted fields, confidence scores, OCR quality, and processing metrics.
    """
    page_range = None
    if page_range_start is not None and page_range_end is not None:
        page_range = (page_range_start, page_range_end)

    return await extract_document_data(document_url, document_type, page_range)


@mcp.tool()
async def extract_table_from_document(
    document_url: str,
    page_number: int = 1,
) -> dict[str, Any]:
    """
    Extract tabular data from a specific page of a document.

    Returns structured table data with headers and rows.

    Args:
        document_url: URL or file reference to the document
        page_number: Page number to extract tables from (default: 1)

    Returns:
        Tables with headers, rows, and confidence scores.
    """
    return await extract_table_data(document_url, page_number)


@mcp.tool()
async def extract_mrz_data(
    document_url: str,
) -> dict[str, Any]:
    """
    Extract Machine Readable Zone (MRZ) from passport or ID document.

    Parses MRZ codes with checksum validation.

    Args:
        document_url: URL or file reference to passport/ID document

    Returns:
        Parsed MRZ data with checksum validation status.
    """
    return await extract_mrz(document_url)


# ══════════════════════════════════════════════════════════════════
#  DATA VALIDATION TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def validate_document_data(
    document_type: str,
    extracted_fields: dict,
    schema_rules: dict | None = None,
) -> dict[str, Any]:
    """
    Validate extracted fields against schema rules and business logic.

    Checks required fields, data types, business rules, and cross-field consistency.

    Args:
        document_type: Type of document (invoice, contract, bank_statement, etc.)
        extracted_fields: Dict of field_name -> value from extraction
        schema_rules: Optional custom validation rules override

    Returns:
        Validation result with pass/fail status, errors, and warnings.
    """
    return await validate_extracted_data(document_type, extracted_fields, schema_rules)


@mcp.tool()
async def cross_validate_multiple_documents(
    documents: list[dict],
) -> dict[str, Any]:
    """
    Cross-validate data across multiple related documents.

    Verifies consistency of names, dates, amounts across documents
    (e.g., payslip income matches tax return income).

    Args:
        documents: List of dicts with 'document_type' and 'extracted_fields'

    Returns:
        Cross-validation result with discrepancies and consistency status.
    """
    return await cross_validate_documents(documents)


# ══════════════════════════════════════════════════════════════════
#  DATA ENRICHMENT TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def enrich_invoice(
    extracted_fields: dict,
) -> dict[str, Any]:
    """
    Enrich extracted invoice data with additional context.

    Adds vendor verification, payment terms normalization, tax rate calculation,
    currency conversion, and duplicate detection.

    Args:
        extracted_fields: Dict of extracted fields from invoice

    Returns:
        Enriched data with additional metadata and analysis.
    """
    return await enrich_invoice_data(extracted_fields)


@mcp.tool()
async def enrich_bank_statement(
    extracted_fields: dict,
) -> dict[str, Any]:
    """
    Enrich bank statement data with cash flow analysis.

    Adds savings rate, spending categories, income stability,
    irregularity detection, and creditworthiness scoring.

    Args:
        extracted_fields: Dict of extracted fields from bank statement

    Returns:
        Enriched data with cash flow analysis and creditworthiness score.
    """
    return await enrich_bank_statement_data(extracted_fields)


@mcp.tool()
async def enrich_contract(
    extracted_fields: dict,
) -> dict[str, Any]:
    """
    Enrich contract data with risk analysis.

    Adds contract risk scoring, missing clause detection,
    renewal reminder dates, and value benchmarking.

    Args:
        extracted_fields: Dict of extracted fields from contract

    Returns:
        Enriched data with risk analysis and contract metadata.
    """
    return await enrich_contract_data(extracted_fields)


@mcp.tool()
async def enrich_financial_statement(
    extracted_fields: dict,
) -> dict[str, Any]:
    """
    Enrich financial statement data with ratio analysis.

    Adds liquidity ratios, profitability ratios, leverage ratios,
    and financial health scoring.

    Args:
        extracted_fields: Dict of extracted fields from financial statement

    Returns:
        Enriched data with financial ratios and health score.
    """
    return await enrich_financial_statement_data(extracted_fields)


# ══════════════════════════════════════════════════════════════════
#  DOCUMENT PROCESSING WORKFLOW
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def process_document(
    document_url: str,
    document_type: str | None = None,
    auto_enrich: bool = True,
) -> dict[str, Any]:
    """
    End-to-end document processing: classify → extract → validate → enrich.

    Processes a document through the full extraction pipeline.
    If document_type is not provided, auto-classifies first.

    Args:
        document_url: URL or file reference to the document
        document_type: Optional type hint (auto-classified if not provided)
        auto_enrich: Whether to enrich extracted data (default: True)

    Returns:
        Complete processing result with classification, extraction, validation, and enrichment.
    """
    logger.info("Processing document: %s", document_url)

    # Step 1: Classify if type not provided
    if not document_type:
        classification = await classify_document(document_url)
        document_type = classification.get("document_type", "unknown")
    else:
        classification = {"document_type": document_type, "confidence": 1.0}

    # Step 2: Extract data
    extraction = await extract_document_data(document_url, document_type)

    # Step 3: Validate
    validation = await validate_extracted_data(document_type, extraction.get("extracted_fields", {}))

    # Step 4: Enrich (optional)
    enrichment = None
    if auto_enrich and validation.get("is_valid", False):
        enrichment_map = {
            "invoice": enrich_invoice_data,
            "bank_statement": enrich_bank_statement_data,
            "contract": enrich_contract_data,
            "financial_statement": enrich_financial_statement_data,
        }
        enrich_func = enrichment_map.get(document_type)
        if enrich_func:
            enrichment = await enrich_func(extraction.get("extracted_fields", {}))

    result = {
        "processing_id": extraction.get("extraction_id"),
        "document_url": document_url,
        "document_type": document_type,
        "classification": classification,
        "extraction": {
            "fields": extraction.get("extracted_fields"),
            "confidence": extraction.get("overall_confidence"),
            "quality": extraction.get("ocr_quality"),
        },
        "validation": {
            "is_valid": validation.get("is_valid"),
            "errors": validation.get("errors"),
            "warnings": validation.get("warnings"),
            "recommendation": validation.get("recommendation"),
        },
        "enrichment": enrichment,
        "status": (
            "processed" if validation.get("is_valid")
            else "needs_review" if validation.get("recommendation") == "accept_with_review"
            else "rejected"
        ),
    }

    logger.info("Document processing complete: type=%s, status=%s", document_type, result["status"])
    return result


# ══════════════════════════════════════════════════════════════════
#  BATCH PROCESSING
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def batch_process_documents(
    document_urls: list[str],
    document_type: str | None = None,
    auto_validate: bool = True,
    auto_enrich: bool = True,
    max_concurrent: int | None = None,
) -> dict[str, Any]:
    """
    Process multiple documents in a batch: classify → extract → validate → enrich.

    If document_type is provided, skips classification and uses that type for all docs.
    Handles errors gracefully — one failed document doesn't stop the batch.

    Args:
        document_urls: List of document URLs to process
        document_type: Optional forced type for all docs (skips classification)
        auto_validate: Whether to validate extracted data (default: True)
        auto_enrich: Whether to enrich extracted data (default: True)
        max_concurrent: Max concurrent OCR calls (default: 5)

    Returns:
        Batch results with per-document details and summary statistics.
    """
    return await batch_classify_and_extract(
        document_urls=document_urls,
        document_type=document_type,
        auto_validate=auto_validate,
        auto_enrich=auto_enrich,
        max_concurrent=max_concurrent,
    )


@mcp.tool()
async def batch_extract_documents(
    document_urls: list[str],
    document_types: dict[str, str] | None = None,
    max_concurrent: int | None = None,
) -> dict[str, Any]:
    """
    Batch extraction only (no validation/enrichment) — faster for bulk processing.

    Args:
        document_urls: List of document URLs to extract from
        document_types: Optional mapping of url → document_type
        max_concurrent: Max concurrent OCR calls (default: 5)

    Returns:
        Extraction results for each document.
    """
    return await batch_extract_only(
        document_urls=document_urls,
        document_types=document_types,
        max_concurrent=max_concurrent,
    )


@mcp.tool()
async def batch_validate_documents(
    extractions: list[dict],
) -> dict[str, Any]:
    """
    Batch validation — validate multiple extracted datasets at once.

    Args:
        extractions: List of dicts with 'document_type' and 'extracted_fields'

    Returns:
        Validation results for each document.
    """
    return await batch_validate_only(extractions)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def notify_customer(
    customer_id: str,
    template_id: str,
    channel: str = "email",
    variables: dict | None = None,
) -> dict[str, Any]:
    """
    Send a notification to a customer about document processing status.

    Available templates: doc_received, doc_processed, doc_needs_review,
                        doc_rejected, extraction_complete, validation_failed, batch_complete

    Args:
        customer_id: Customer to notify
        template_id: Notification template to use
        channel: Delivery channel (email, sms, in_app)
        variables: Template variables (e.g., {"document_type": "invoice"})

    Returns:
        Notification delivery status and ID.
    """
    return await send_notification(
        recipient_type="customer",
        recipient_id=customer_id,
        channel=channel,
        template_id=template_id,
        variables=variables,
    )


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("Starting Document Digitization & Extraction Agent MCP Server...")
    mcp.run()
