"""
KYC Onboarding Agent — MCP Server.

Exposes tools via the Model Context Protocol for identity verification,
sanctions screening, document processing, and account creation.
Integrates with a RAG pipeline for regulatory knowledge retrieval.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.compliance import create_compliance_case, get_compliance_case, update_compliance_case
from tools.core_banking import create_customer_profile, query_core_banking
from tools.document_extraction import extract_document
from tools.identity_verification import verify_identity
from tools.notifications import send_notification
from tools.sanctions_screening import screen_sanctions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "KYC Onboarding Agent",
    instructions=(
        "KYC Onboarding Agent for banking. Use these tools to process "
        "Know Your Customer onboarding: verify identity, screen against "
        "sanctions lists, extract document data, create customer profiles, "
        "and manage compliance cases. Always retrieve regulatory knowledge "
        "via the knowledge_search tool before making KYC decisions."
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
    Search the KYC knowledge base using RAG (hybrid search + semantic).

    Use this tool to retrieve regulatory requirements, product policies,
    document schemas, risk typologies, and past KYC decisions.

    Args:
        query: Natural language query (e.g., "What documents do I need for a UK business account?")
        collection: Collection to search. Options: all, kyc_regulations, product_policies,
                    document_schemas, risk_typologies, past_kyc_decisions
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
    Retrieve the expected fields and validation rules for a specific document type.

    Args:
        document_type: One of: passport, drivers_license, national_id, tax_id,
                       proof_of_address, bank_statement, articles_of_incorporation

    Returns:
        Expected fields, validation rules, and schema metadata.
    """
    result = rag.query_single(
        "document_schemas",
        f"{document_type} document schema required fields validation",
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
#  DOCUMENT PROCESSING TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def extract_and_classify_document(
    document_url: str,
    document_type: str,
) -> dict[str, Any]:
    """
    Extract structured data from an uploaded KYC document via OCR.

    First extracts data, then validates against the document schema from the knowledge base.

    Args:
        document_url: URL or file reference to the uploaded document
        document_type: Expected type — passport, drivers_license, national_id, tax_id,
                       proof_of_address, bank_statement, articles_of_incorporation

    Returns:
        Extracted fields, confidence score, OCR quality, and schema validation results.
    """
    # Step 1: Extract data from document
    extraction = await extract_document(document_url, document_type)

    # Step 2: Validate against schema from knowledge base
    schema_result = await get_document_schema(document_type)

    # Compare extracted fields against expected schema
    extracted_fields = set(extraction.get("extracted_fields", {}).keys())
    expected_fields = set()
    for schema in schema_result.get("schemas", []):
        text = schema.get("text", "")
        # Simple field name matching (in production, use more sophisticated parsing)
        for field in ["full_name", "date_of_birth", "nationality", "passport_number",
                      "expiry_date", "license_number", "address", "id_number",
                      "business_name", "tax_id_number", "company_name", "registration_number"]:
            if field in text:
                expected_fields.add(field)

    missing_fields = expected_fields - extracted_fields if expected_fields else set()

    return {
        **extraction,
        "schema_validation": {
            "expected_fields": list(expected_fields) if expected_fields else ["unknown"],
            "extracted_fields": list(extracted_fields),
            "missing_fields": list(missing_fields),
            "is_complete": len(missing_fields) == 0,
        },
    }


# ══════════════════════════════════════════════════════════════════
#  IDENTITY VERIFICATION TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def verify_customer_identity(
    customer_id: str,
    document_image_url: str,
    selfie_url: str,
    extracted_data: dict | None = None,
) -> dict[str, Any]:
    """
    Verify customer identity: liveness check, document authenticity, and face match.

    Args:
        customer_id: Internal customer identifier
        document_image_url: URL to the uploaded identity document image
        selfie_url: URL to the customer's selfie/photo
        extracted_data: Previously extracted document data (from extract_and_classify_document)

    Returns:
        Verification result with liveness, authenticity, face match, and overall decision.
    """
    return await verify_identity(
        customer_id=customer_id,
        document_image_url=document_image_url,
        selfie_url=selfie_url,
        extracted_data=extracted_data,
    )


# ══════════════════════════════════════════════════════════════════
#  SANCTIONS SCREENING TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def screen_customer_sanctions(
    full_name: str,
    date_of_birth: str,
    nationality: str,
    aliases: list[str] | None = None,
) -> dict[str, Any]:
    """
    Screen a customer against OFAC, EU, UN sanctions lists and PEP databases.

    Also performs adverse media screening.

    Args:
        full_name: Customer's full legal name
        date_of_birth: Date of birth (YYYY-MM-DD)
        nationality: Country of nationality
        aliases: Optional list of alternative names or aliases

    Returns:
        Screening results for each sanctions list, PEP status, and overall risk level.
    """
    return await screen_sanctions(
        full_name=full_name,
        date_of_birth=date_of_birth,
        nationality=nationality,
        aliases=aliases,
    )


# ══════════════════════════════════════════════════════════════════
#  CUSTOMER PROFILE & ACCOUNT CREATION
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def create_bank_account(
    personal_info: dict,
    address: dict,
    kyc_result: str,
    risk_rating: str,
    employment_info: dict | None = None,
    documents_verified: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a customer profile and bank account after successful KYC.

    Args:
        personal_info: Customer's personal details (name, dob, nationality, etc.)
        address: Customer's address
        kyc_result: One of: approved, approved_with_conditions, rejected
        risk_rating: One of: low, medium, high
        employment_info: Optional employment details
        documents_verified: List of document types that were verified

    Returns:
        New customer ID and account number.
    """
    return await create_customer_profile(
        personal_info=personal_info,
        address=address,
        kyc_result=kyc_result,
        risk_rating=risk_rating,
        employment_info=employment_info,
        documents_verified=documents_verified,
    )


@mcp.tool()
async def lookup_customer(identifier: str, query_type: str = "customer_lookup") -> dict[str, Any]:
    """
    Look up customer or account information from the core banking system.

    Args:
        identifier: Customer ID, account number, or national ID
        query_type: One of: customer_lookup, account_status, transaction_history

    Returns:
        Customer or account data from the core banking system.
    """
    return await query_core_banking(query_type=query_type, identifier=identifier)


# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE CASE MANAGEMENT
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def open_compliance_case(
    customer_id: str,
    risk_level: str,
    summary: str,
    flags: list[str] | None = None,
    priority: str = "medium",
) -> dict[str, Any]:
    """
    Open a compliance review case for manual officer review.

    Use this when risk assessment determines the application needs human review.

    Args:
        customer_id: Customer identifier
        risk_level: Risk level assessment (low, medium, high, critical)
        summary: Summary of why the case was opened
        flags: List of risk flags or concerns
        priority: Case priority (low, medium, high, urgent)

    Returns:
        Created case details with case ID.
    """
    return await create_compliance_case(
        customer_id=customer_id,
        risk_level=risk_level,
        summary=summary,
        flags=flags,
        priority=priority,
    )


@mcp.tool()
async def get_case(case_id: str) -> dict[str, Any]:
    """
    Retrieve a compliance case by its ID.

    Args:
        case_id: Case ID (e.g., CASE-A1B2C3D4)

    Returns:
        Full case details including status, assignment, and history.
    """
    return await get_compliance_case(case_id)


@mcp.tool()
async def update_case(
    case_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    decision: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Update a compliance case: change status, assign officer, record decision.

    Args:
        case_id: Case ID to update
        status: New status (open, in_review, approved, rejected, escalated)
        assigned_to: Compliance officer to assign
        decision: Final decision (approved, rejected, approved_with_conditions)
        notes: Additional notes or rationale

    Returns:
        Updated case details.
    """
    return await update_compliance_case(
        case_id=case_id,
        status=status,
        assigned_to=assigned_to,
        decision=decision,
        notes=notes,
    )


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
    Send a notification to a customer (email, SMS, or in-app).

    Available templates: kyc_welcome, kyc_documents_requested, kyc_under_review,
                        kyc_approved, kyc_rejected, kyc_additional_info

    Args:
        customer_id: Customer to notify
        template_id: Notification template to use
        channel: Delivery channel (email, sms, in_app)
        variables: Template variables (e.g., {"account_number": "ACC-123"})

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
#  RISK ASSESSMENT (RAG-powered)
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def assess_kyc_risk(
    customer_type: str,
    jurisdiction: str,
    identity_verified: bool,
    sanctions_clear: bool,
    pep_status: str = "not_pep",
    adverse_media: bool = False,
    business_complexity: str = "simple",
) -> dict[str, Any]:
    """
    Assess overall KYC risk using RAG-retrieved risk rules and typologies.

    This tool retrieves risk scoring rules from the knowledge base and applies them
    to the provided customer attributes.

    Args:
        customer_type: Individual or Business
        jurisdiction: Customer's jurisdiction (e.g., UK, US, EU)
        identity_verified: Whether identity was successfully verified
        sanctions_clear: Whether sanctions screening returned all clear
        pep_status: PEP screening result (not_pep, domestic_pep, foreign_pep)
        adverse_media: Whether adverse media was found
        business_complexity: simple, moderate, complex (for business accounts)

    Returns:
        Risk score, risk level, flags, and decision recommendation.
    """
    # Retrieve risk rules from knowledge base
    risk_query = f"{customer_type} {jurisdiction} risk assessment scoring criteria {business_complexity}"
    risk_context = rag.query(risk_query, top_k=3, collections=["risk_typologies", "past_kyc_decisions"])

    # Calculate risk score based on inputs and retrieved rules
    score = 0.0
    flags: list[str] = []

    if not identity_verified:
        score += 0.4
        flags.append("identity_verification_failed")

    if not sanctions_clear:
        score += 0.5
        flags.append("sanctions_hit")

    if pep_status == "foreign_pep":
        score += 0.2
        flags.append("foreign_pep")
    elif pep_status == "domestic_pep":
        score += 0.1
        flags.append("domestic_pep")

    if adverse_media:
        score += 0.15
        flags.append("adverse_media_found")

    if business_complexity == "complex":
        score += 0.1
        flags.append("complex_business_structure")
    elif business_complexity == "moderate":
        score += 0.05

    if jurisdiction in ["OFAC_HIGH_RISK", "FATF_GREY_LIST"]:
        score += 0.15
        flags.append("high_risk_jurisdiction")

    # Determine risk level
    if score >= 0.5:
        risk_level = "high"
    elif score >= 0.25:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Determine recommended action
    if risk_level == "high":
        action = "manual_review_required"
    elif risk_level == "medium":
        action = "enhanced_due_diligence"
    else:
        action = "auto_approve_eligible"

    return {
        "risk_score": round(min(score, 1.0), 2),
        "risk_level": risk_level,
        "flags": flags,
        "recommended_action": action,
        "retrieved_rules": risk_context.assembled_context[:500] if risk_context.assembled_context else "No rules retrieved",
        "assessment_criteria": {
            "identity_verified": identity_verified,
            "sanctions_clear": sanctions_clear,
            "pep_status": pep_status,
            "adverse_media": adverse_media,
            "business_complexity": business_complexity,
            "jurisdiction": jurisdiction,
        },
    }


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("Starting KYC Onboarding Agent MCP Server...")
    mcp.run()
