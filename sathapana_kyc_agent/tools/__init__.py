"""
Tool registry for the Sathapana Bank KYC Onboarding Agent.

Centralizes every tool exposed over MCP and used by the agent loop, with
JSON schemas and risk levels for guardrails. Includes the RAG-powered
`assess_kyc_risk` that applies NBC/Cambodia risk factors.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import tools.bakong as bakong
import tools.compliance as compliance
import tools.core_banking as core_banking
import tools.document_extraction as document_extraction
import tools.identity_verification as identity_verification
import tools.notifications as notifications
import tools.screening as screening

from rag_pipeline import RAGPipeline

_rag: RAGPipeline | None = None


def get_rag() -> RAGPipeline:
    global _rag
    if _rag is None:
        _rag = RAGPipeline()
    return _rag


# ══════════════════════════════════════════════════════════════════
#  RAG-powered handlers
# ══════════════════════════════════════════════════════════════════


def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict:
    """Search NBC regulations, policies, schemas, typologies and past cases."""
    rag = get_rag()
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "query": result.query_rewrite,
        "results_count": len(result.chunks),
        "chunks": [
            {"text": c.text, "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata}
            for c in result.chunks
        ],
        "assembled_context": result.assembled_context,
    }


def get_document_schema(document_type: str) -> dict:
    rag = get_rag()
    result = rag.query_single("document_schemas", f"{document_type} document schema required fields validation", n_results=3)
    parsed = [json.loads(c.text) if c.text.startswith("{") else c.text for c in result]
    return {
        "document_type": document_type,
        "schemas_found": len(result),
        "schemas": [{"text": c.text, "metadata": c.metadata, "score": round(c.score, 3)} for c in result],
        "parsed_schemas": parsed,
    }


def assess_kyc_risk(
    customer_type: str,
    jurisdiction: str = "KH",
    sector: str = "",
    identity_verified: bool = False,
    sanctions_clear: bool = False,
    pep_status: str = "not_pep",
    adverse_media: bool = False,
    business_complexity: str = "simple",
    cash_intensive: bool = False,
    ubo_screened: bool = True,
) -> dict:
    """
    Assess overall KYC risk using NBC/Cambodia risk typologies from RAG.

    Cambodia-specific factors: casino/gaming, cash-intensive sectors,
    mandatory EDD for domestic PEPs, UN/NBC sanctions hits.
    """
    rag = get_rag()
    risk_query = f"{customer_type} {sector} Cambodia risk assessment criteria sanctions PEP cash intensive"
    context = rag.query(risk_query, top_k=3, collections=["risk_typologies", "nbc_regulations"])

    score = 0.0
    flags: list[str] = []

    if not identity_verified:
        score += 0.40
        flags.append("identity_verification_failed")
    if not sanctions_clear:
        score += 0.50
        flags.append("sanctions_hit_onboarding_prohibited")
    if pep_status in ("domestic_pep", "foreign_pep"):
        score += 0.25
        flags.append(f"{pep_status}_edd_required")
    if adverse_media:
        score += 0.15
        flags.append("adverse_media_found")

    sector_l = sector.lower()
    if any(k in sector_l for k in ("casino", "gaming", "gambling", "junket")):
        score += 0.35
        flags.append("gambling_sector_high_risk")
    if cash_intensive:
        score += 0.20
        flags.append("cash_intensive_high_risk")

    if business_complexity == "complex":
        score += 0.10
        flags.append("complex_business_structure")

    if not ubo_screened:
        score += 0.15
        flags.append("ubo_not_screened")

    if jurisdiction.upper() in ("KH",):
        pass  # domestic; risk weighed via sectors above

    score = min(round(score, 2), 1.0)
    if score >= 0.5:
        level = "high"
    elif score >= 0.25:
        level = "medium"
    else:
        level = "low"

    action = {
        "high": "manual_review_required",
        "medium": "enhanced_due_diligence",
        "low": "auto_approve_eligible",
    }[level]

    return {
        "risk_score": score,
        "risk_level": level,
        "flags": flags,
        "recommended_action": action,
        "retrieved_rules": context.assembled_context[:800] if context.assembled_context else "No rules retrieved",
        "assessment_criteria": {
            "customer_type": customer_type,
            "jurisdiction": jurisdiction,
            "sector": sector,
            "identity_verified": identity_verified,
            "sanctions_clear": sanctions_clear,
            "pep_status": pep_status,
            "adverse_media": adverse_media,
            "business_complexity": business_complexity,
            "cash_intensive": cash_intensive,
            "ubo_screened": ubo_screened,
        },
    }


# ══════════════════════════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════════════════════════

class ToolRegistry:
    """Registry of tools with JSON schemas and risk levels."""

    RISK_RANK = {"safe": 0, "low": 1, "medium": 2, "high": 3}

    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, parameters: dict, handler: Callable, risk_level: str = "safe", required: list[str] | None = None) -> None:
        params = dict(parameters)
        if required:
            params["required"] = required
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": params,
            "handler": handler,
            "risk_level": risk_level,
        }

    def get_names(self) -> list[str]:
        return list(self._tools.keys())

    def get(self, name: str) -> dict | None:
        return self._tools.get(name)

    def risk(self, name: str) -> str:
        tool = self._tools.get(name)
        return tool["risk_level"] if tool else "medium"

    def schemas_for_llm(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": {k: v for k, v in t["inputSchema"].items() if k != "required"},
                },
            }
            for t in self._tools.values()
        ]

    def descriptions(self) -> str:
        lines = []
        for t in self._tools.values():
            params = ", ".join(t["inputSchema"].get("properties", {}).keys())
            lines.append(f"- {t['name']} [{t['risk_level']}]: {t['description']} (params: {params})")
        return "\n".join(lines)

    def invoke(self, name: str, arguments: dict) -> dict:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        try:
            return tool["handler"](**arguments)
        except TypeError as exc:
            return {"error": f"Invalid arguments for {name}: {exc}"}
        except Exception as exc:  # noqa: BLE001 - surface tool errors to caller
            return {"error": f"{name} failed: {exc}"}


def build_registry() -> ToolRegistry:
    """Build the full Sathapana KYC tool registry."""
    reg = ToolRegistry()
    props = {"type": "object"}

    reg.register(
        "knowledge_search",
        "Search the Sathapana/NBC KYC knowledge base (regulations, policies, document schemas, risk typologies, past decisions) using RAG hybrid search.",
        {"properties": {"query": {"type": "string"}, "collection": {"type": "string", "default": "all"}, "top_k": {"type": "integer", "default": 5}}},
        knowledge_search, "safe", ["query"],
    )
    reg.register(
        "get_document_schema",
        "Retrieve the expected fields and validation rules for a Cambodia KYC document type (national_id, passport, family_book, business_registration, tax_certificate, proof_of_address, bank_statement, collateral).",
        {"properties": {"document_type": {"type": "string"}}},
        get_document_schema, "safe", ["document_type"],
    )
    reg.register(
        "assess_kyc_risk",
        "Assess overall KYC risk using NBC/Cambodia typologies (gambling, cash-intensive sectors, PEP EDD, sanctions).",
        {
            "properties": {
                "customer_type": {"type": "string"},
                "jurisdiction": {"type": "string", "default": "KH"},
                "sector": {"type": "string", "default": ""},
                "identity_verified": {"type": "boolean", "default": False},
                "sanctions_clear": {"type": "boolean", "default": False},
                "pep_status": {"type": "string", "default": "not_pep"},
                "adverse_media": {"type": "boolean", "default": False},
                "business_complexity": {"type": "string", "default": "simple"},
                "cash_intensive": {"type": "boolean", "default": False},
                "ubo_screened": {"type": "boolean", "default": True},
            }
        },
        assess_kyc_risk, "safe", ["customer_type"],
    )
    reg.register(
        "extract_and_classify_document",
        "OCR-extract structured data from an uploaded KYC document and validate against the schema in the knowledge base.",
        {"properties": {"document_url": {"type": "string"}, "document_type": {"type": "string"}}},
        _extract_and_classify, "low", ["document_url", "document_type"],
    )
    reg.register(
        "verify_customer_identity",
        "Verify identity: liveness check, document authenticity, and face match.",
        {"properties": {"customer_id": {"type": "string"}, "document_image_url": {"type": "string"}, "selfie_url": {"type": "string"}, "nationality": {"type": "string", "default": "KH"}, "extracted_data": {"type": "object", "default": None}}},
        _verify_identity_wrapper, "medium", ["customer_id", "document_image_url", "selfie_url"],
    )
    reg.register(
        "screen_customer_sanctions",
        "Screen against UN Consolidated List, NBC/Cambodia sanctions, OFAC and EU, plus Cambodia PEP-list status and adverse media.",
        {"properties": {"full_name": {"type": "string"}, "date_of_birth": {"type": "string"}, "nationality": {"type": "string", "default": "KH"}, "aliases": {"type": "array", "default": []}}},
        _screen_sanctions_wrapper, "medium", ["full_name", "date_of_birth"],
    )
    reg.register(
        "screen_ubo",
        "Screen beneficial owners of a legal person using the NBC default (25%) or risk-based (10%) threshold.",
        {"properties": {"owners": {"type": "array"}, "risk_level": {"type": "string", "default": "low"}}},
        _screen_ubo_wrapper, "medium", ["owners"],
    )
    reg.register(
        "lookup_customer",
        "Look up customer or account information in the core banking system.",
        {"properties": {"identifier": {"type": "string"}, "query_type": {"type": "string", "default": "customer_lookup"}}},
        _lookup_wrapper, "safe", ["identifier"],
    )
    reg.register(
        "create_customer_profile",
        "Create customer profile after KYC approval (approved / approved_with_conditions / rejected).",
        {"properties": {"personal_info": {"type": "object"}, "address": {"type": "object"}, "kyc_result": {"type": "string"}, "risk_rating": {"type": "string"}, "currency": {"type": "string", "default": "USD"}, "customer_type": {"type": "string", "default": "individual"}, "documents_verified": {"type": "array", "default": []}, "kyc_case_id": {"type": "string", "default": None}}},
        _create_profile_wrapper, "high", ["personal_info", "address", "kyc_result", "risk_rating"],
    )
    reg.register(
        "open_account",
        "Open a bank account (retail_savings, current, sme_loan, corporate) in USD or KHR.",
        {"properties": {"customer_id": {"type": "string"}, "account_type": {"type": "string", "default": "retail_savings"}, "currency": {"type": "string", "default": "USD"}}},
        _open_account_wrapper, "high", ["customer_id"],
    )
    reg.register(
        "register_bakong",
        "Link an onboarded account to the NBC Bakong mobile payment system.",
        {"properties": {"customer_id": {"type": "string"}, "account_id": {"type": "string"}, "mobile_number": {"type": "string"}, "currency": {"type": "string", "default": "USD"}}},
        _bakong_wrapper, "medium", ["customer_id", "account_id", "mobile_number"],
    )
    reg.register(
        "open_compliance_case",
        "Open a compliance review case for manual officer review; may file an STR to CAMFIU.",
        {"properties": {"customer_id": {"type": "string"}, "risk_level": {"type": "string"}, "summary": {"type": "string"}, "flags": {"type": "array", "default": []}, "priority": {"type": "string", "default": "medium"}, "file_str_to_camfiu": {"type": "boolean", "default": False}}},
        _open_case_wrapper, "medium", ["customer_id", "risk_level", "summary"],
    )
    reg.register(
        "get_case",
        "Retrieve a compliance case by ID.",
        {"properties": {"case_id": {"type": "string"}}},
        _get_case_wrapper, "safe", ["case_id"],
    )
    reg.register(
        "update_case",
        "Update a compliance case (status, assignment, decision, notes).",
        {"properties": {"case_id": {"type": "string"}, "status": {"type": "string", "default": None}, "assigned_to": {"type": "string", "default": None}, "decision": {"type": "string", "default": None}, "notes": {"type": "string", "default": None}}},
        _update_case_wrapper, "high", ["case_id"],
    )
    reg.register(
        "notify_customer",
        "Send a notification (sms/email/in_app) using Sathapana templates.",
        {"properties": {"recipient_type": {"type": "string", "default": "customer"}, "recipient_id": {"type": "string"}, "channel": {"type": "string", "default": "sms"}, "template_id": {"type": "string", "default": "kyc_under_review"}, "variables": {"type": "object", "default": None}}},
        _notify_wrapper, "low", ["recipient_id"],
    )

    return reg


# ══════════════════════════════════════════════════════════════════
#  Wrappers (async-compatible signatures kept for parity with MCP)
# ══════════════════════════════════════════════════════════════════

def _extract_and_classify(document_url: str, document_type: str) -> dict:
    extraction = document_extraction.extract_document(document_url, document_type)
    if "error" in extraction:
        return extraction
    expected = set(document_extraction.EXTRACTION_SCHEMAS.get(document_type, []))
    extracted = set(extraction.get("extracted_fields", {}).keys())
    missing = expected - extracted
    rag_schemas = get_document_schema(document_type).get("schemas_found", 0)
    extraction["schema_validation"] = {
        "expected_fields": list(expected) if expected else ["unknown"],
        "extracted_fields": list(extracted),
        "missing_fields": list(missing),
        "is_complete": len(missing) == 0 or not expected,
        "rag_schemas_consulted": rag_schemas,
    }
    return extraction


def _verify_identity_wrapper(**kw: Any) -> dict:
    return identity_verification.verify_identity(**kw)


def _screen_sanctions_wrapper(**kw: Any) -> dict:
    return screening.screen_customer_sanctions(**kw)


def _screen_ubo_wrapper(owners: list, risk_level: str = "low") -> dict:
    return screening.screen_ubo(owners, risk_level)


def _lookup_wrapper(identifier: str, query_type: str = "customer_lookup") -> dict:
    return core_banking.lookup_customer(identifier, query_type)


def _create_profile_wrapper(**kw: Any) -> dict:
    return core_banking.create_customer_profile(**kw)


def _open_account_wrapper(customer_id: str, account_type: str = "retail_savings", currency: str = "USD") -> dict:
    return core_banking.open_account(customer_id, account_type, currency)


def _bakong_wrapper(**kw: Any) -> dict:
    return bakong.register_bakong(**kw)


def _open_case_wrapper(customer_id: str, risk_level: str, summary: str, flags: list[str] | None = None, priority: str = "medium", file_str_to_camfiu: bool = False) -> dict:
    return compliance.create_compliance_case(customer_id, risk_level, summary, flags, priority, file_str_to_camfiu)


def _get_case_wrapper(case_id: str) -> dict:
    return compliance.get_compliance_case(case_id)


def _update_case_wrapper(case_id: str, status: str | None = None, assigned_to: str | None = None, decision: str | None = None, notes: str | None = None) -> dict:
    return compliance.update_compliance_case(case_id, status, assigned_to, decision, notes)


def _notify_wrapper(recipient_id: str, recipient_type: str = "customer", channel: str = "sms", template_id: str = "kyc_under_review", variables: dict | None = None) -> dict:
    return notifications.send_notification(recipient_type, recipient_id, channel, template_id, variables)


registry = None


def get_registry() -> ToolRegistry:
    global registry
    if registry is None:
        registry = build_registry()
    return registry