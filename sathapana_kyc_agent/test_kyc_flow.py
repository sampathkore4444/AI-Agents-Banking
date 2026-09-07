"""End-to-end tests for the Sathapana KYC Onboarding Agent."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json

import db
import seed_knowledge
from config import settings
from tools import get_rag, get_registry


def _clean_seed() -> None:
    rag = get_rag()
    for full in list(rag.store.list_collections()):
        rag.store.reset(full)
    for name in seed_knowledge.COLLECTIONS:
        rag.store.get_or_create_collection(f"{settings.vector_collection_prefix}_{name}")
    seed_knowledge.seed(rag)


# ── Registry ──────────────────────────────────────────────────────
def test_registry_builds_15_tools() -> None:
    reg = get_registry()
    names = reg.get_names()
    assert len(names) == 15
    assert {"knowledge_search", "assess_kyc_risk", "screen_customer_sanctions", "screen_ubo", "open_account", "register_bakong"} <= set(names)
    assert reg.risk("open_account") == "high"
    assert reg.risk("knowledge_search") == "safe"
    schemas = reg.schemas_for_llm()
    assert all(s["type"] == "function" for s in schemas)


def test_registry_invoke_unknown_tool() -> None:
    reg = get_registry()
    assert "error" in reg.invoke("does_not_exist", {})


# ── Knowledge base / RAG ──────────────────────────────────────────
def test_seed_populates_all_collections() -> None:
    rag = get_rag()
    _clean_seed()
    for name in seed_knowledge.COLLECTIONS:
        assert rag.collection_count(name) > 0, name


def test_knowledge_search_nbc_edd() -> None:
    reg = get_registry()
    result = reg.invoke("knowledge_search", {"query": "enhanced due diligence politically exposed person requirements", "top_k": 3})
    assert result["results_count"] >= 1, result
    assert any("EDD" in c["text"] or "Enhanced Due Diligence" in c["text"] for c in result["chunks"])
    assert result["assembled_context"]


def test_knowledge_search_casino_typology() -> None:
    reg = get_registry()
    result = reg.invoke("knowledge_search", {"query": "casino gambling junket high risk Cambodia", "top_k": 3})
    texts = " ".join(c["text"] for c in result["chunks"]).lower()
    assert "casino" in texts or "gambling" in texts


def test_document_schema_national_id() -> None:
    reg = get_registry()
    result = reg.invoke("get_document_schema", {"document_type": "national_id"})
    assert result["schemas_found"] >= 1
    schemas = result["schemas"]
    fields = [f for s in schemas for f in s["metadata"].get("fields", [])]
    assert "full_name_kh" in fields


# ── Document extraction ───────────────────────────────────────────
def test_extract_national_id_schema_complete() -> None:
    reg = get_registry()
    result = reg.invoke("extract_and_classify_document", {"document_url": "s3://sathapana-kyc/test/national_id.pdf", "document_type": "national_id"})
    assert "error" not in result
    assert result["schema_validation"]["is_complete"] is True
    assert result["khmer_ocr_supported"] is True
    assert result["ocr_quality"] in ("high", "medium")


def test_extract_unsupported_document() -> None:
    reg = get_registry()
    result = reg.invoke("extract_and_classify_document", {"document_url": "x.pdf", "document_type": "birth_certificate"})
    assert "error" in result


# ── Identity verification ─────────────────────────────────────────
def test_identity_verification_structure() -> None:
    reg = get_registry()
    result = reg.invoke("verify_customer_identity", {"customer_id": "CUST-TEST1", "document_image_url": "s3://sathapana-kyc/test/nid.jpg", "selfie_url": "s3://sathapana-kyc/test/selfie.jpg"})
    assert result["overall_result"] in ("verified", "manual_review", "rejected")
    assert "liveness_check" in result and "face_match" in result


# ── Screening ─────────────────────────────────────────────────────
def test_screen_sanctions_structure() -> None:
    reg = get_registry()
    result = reg.invoke("screen_customer_sanctions", {"full_name": "Test Applicant", "date_of_birth": "1990-01-01", "nationality": "KH"})
    for key in ("un_result", "nbc_cambodia_result", "ofac_result", "eu_result", "pep_status", "onboarding_prohibited", "risk_level"):
        assert key in result


def test_screen_sanctions_hit_forces_prohibited(monkeypatch) -> None:
    import integrations.sanctions as sanctions_mod

    monkeypatch.setattr(sanctions_mod, "_hash_val", lambda text: 0)
    result = sanctions_mod.StubSanctionsProvider().screen("Sanctioned Person", "1980-01-01", "KH")
    assert result["un_result"] == "potential_match"
    assert result["onboarding_prohibited"] is True
    assert result["risk_level"] == "critical"


def test_ubo_thresholds() -> None:
    from tools.screening import screen_ubo

    owners = [
        {"full_name": "Owner A", "date_of_birth": "1970-01-01", "nationality": "KH", "ownership_pct": 30, "identified": True},
        {"full_name": "Owner B", "date_of_birth": "1971-01-01", "nationality": "KH", "ownership_pct": 12, "identified": True},
    ]
    default = screen_ubo(owners, risk_level="low")
    assert default["threshold_applied_pct"] == 25
    captured_default = {o["full_name"] for o in default["owners"] if o["captured_as_ubo"]}
    assert captured_default == {"Owner A"}

    high = screen_ubo(owners, risk_level="high")
    assert high["threshold_applied_pct"] == 10
    captured_high = {o["full_name"] for o in high["owners"] if o["captured_as_ubo"]}
    assert captured_high == {"Owner A", "Owner B"}


# ── Risk assessment ───────────────────────────────────────────────
def test_assess_risk_low() -> None:
    reg = get_registry()
    result = reg.invoke("assess_kyc_risk", {"customer_type": "individual", "sector": "retail_savings", "identity_verified": True, "sanctions_clear": True, "pep_status": "not_pep", "adverse_media": False, "cash_intensive": False})
    assert result["risk_level"] == "low"
    assert result["recommended_action"] == "auto_approve_eligible"


def test_assess_risk_medium_pep() -> None:
    reg = get_registry()
    result = reg.invoke("assess_kyc_risk", {"customer_type": "individual", "sector": "retail_savings", "identity_verified": True, "sanctions_clear": True, "pep_status": "domestic_pep", "adverse_media": False})
    assert result["risk_level"] == "medium"
    assert "domestic_pep_edd_required" in result["flags"]


def test_assess_risk_high_casino() -> None:
    reg = get_registry()
    result = reg.invoke("assess_kyc_risk", {"customer_type": "business", "sector": "casino", "identity_verified": True, "sanctions_clear": True, "pep_status": "not_pep", "adverse_media": True, "cash_intensive": True})
    assert result["risk_level"] == "high"
    assert result["recommended_action"] == "manual_review_required"
    assert "gambling_sector_high_risk" in result["flags"]


# ── Core banking / compliance / bakong ────────────────────────────
def test_core_banking_flow() -> None:
    reg = get_registry()
    profile = reg.invoke("create_customer_profile", {"personal_info": {"full_name": "Test KYC Person", "nationality": "KH"}, "address": {"province": "Phnom Penh"}, "kyc_result": "approved", "risk_rating": "low", "currency": "KHR", "customer_type": "individual"})
    assert "error" not in profile
    account = reg.invoke("open_account", {"customer_id": profile["customer_id"], "account_type": "retail_savings", "currency": "KHR"})
    assert account["currency"] == "KHR"
    assert account["status"] == "active"

    bad_currency = reg.invoke("open_account", {"customer_id": profile["customer_id"], "currency": "EUR"})
    assert "error" in bad_currency

    lookup = reg.invoke("lookup_customer", {"identifier": profile["customer_id"]})
    assert lookup["customer_id"] == profile["customer_id"]
    assert lookup["kyc_status"] == "approved"


def test_compliance_case_with_str() -> None:
    reg = get_registry()
    case = reg.invoke("open_compliance_case", {"customer_id": "CUST-TEST2", "risk_level": "high", "summary": "Suspicious cash flows and gambling links", "flags": ["gambling_sector_high_risk"], "priority": "urgent", "file_str_to_camfiu": True, "customer_pii": {"full_name": "Suspect KYC", "nationality": "KH"}})
    assert "error" not in case
    assert case["risk_level"] == "high"
    assert case["status"] == "open"
    assert case["str_filed_camfiu"]["authority"] == "Cambodia Financial Intelligence Unit (CAMFIU)"

    updated = reg.invoke("update_case", {"case_id": case["case_id"], "status": "approved", "assigned_to": "MLRO", "decision": "approved_with_conditions"})
    assert updated["status"] == "approved"
    assert updated["assigned_to"] == "MLRO"


def test_bakong_and_notification() -> None:
    reg = get_registry()
    bakong = reg.invoke("register_bakong", {"customer_id": "CUST-TEST3", "account_id": "ACC-TEST3", "mobile_number": "012-345678", "currency": "USD"})
    assert bakong["status"] == "linked"
    assert bakong["bakong_id"].startswith("BKNG-")

    note = reg.invoke("notify_customer", {"recipient_id": "CUST-TEST3", "template_id": "kyc_approved", "variables": {"customer_name": "Channda", "product": "savings", "account_id": "ACC-X"}})
    assert note["status"] == "queued"
    assert "Channda" in note["message"]


# ── Audit trail ───────────────────────────────────────────────────
def test_audit_trail_recorded() -> None:
    db.init_db()
    before = len(db.last_audit_entries(1000))
    get_registry().invoke("create_customer_profile", {"personal_info": {"full_name": "Audit Check", "nationality": "KH"}, "address": {"province": "Phnom Penh"}, "kyc_result": "approved", "risk_rating": "low"})
    after = len(db.last_audit_entries(1000))
    assert after > before


# ── Runner scenarios ──────────────────────────────────────────────
def test_runner_retail_approved() -> None:
    import runner

    outcome = runner.run_scenario(runner.SCENARIOS["retail_low_risk"], verbose=False)
    assert outcome["status"] == "approved"
    assert outcome["account_id"] and outcome["bakong_id"]


def test_runner_sme_conditions() -> None:
    import runner

    outcome = runner.run_scenario(runner.SCENARIOS["sme_medium_risk"], verbose=False)
    assert outcome["status"] == "approved_with_conditions"
    assert outcome["case_id"]


def test_runner_casino_declined_with_str() -> None:
    import runner

    outcome = runner.run_scenario(runner.SCENARIOS["casino_high_risk"], verbose=False)
    assert outcome["status"] == "declined"
    assert outcome["str_filed_camfiu"] is True


# ── MCP server handlers ───────────────────────────────────────────
def test_mcp_server_handlers() -> None:
    from server import MCPKyCServer

    srv = MCPKyCServer()
    init = json.loads(srv._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}))
    assert init["result"]["serverInfo"]["name"] == "sathapana-kyc"

    listed = json.loads(srv._handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    assert len(listed["result"]["tools"]) == 15
    assert any(t["name"] == "assess_kyc_risk" for t in listed["result"]["tools"])

    called = json.loads(srv._handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "screen_customer_sanctions", "arguments": {"full_name": "Server Test", "date_of_birth": "1990-01-01"}}}))
    assert called["result"]["isError"] is False
    assert "screen_sanctions" in called["result"]["content"][0]["text"] or called["result"]["content"][0]["text"].startswith("{")

    unknown = json.loads(srv._handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nope"}}))
    assert "error" in unknown