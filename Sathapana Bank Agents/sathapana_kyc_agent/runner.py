"""
Deterministic end-to-end KYC onboarding runner.

Executes the full Sathapana onboarding journey against the real tool
handlers (RAG + MCP tools + audit trail + approval workflow + saga) with no
LLM required. Used by `python main.py demo`. Each scenario's screening
outcomes can be pinned via `force_*` fields to demonstrate low / medium /
high-risk journeys. High-risk actions (customer profile, accounts, case
updates) run through the `OnboardingSaga`, so approval requests, SLA
deadlines and idempotent step keys are exercised exactly as they will be in
production.
"""

from __future__ import annotations

import logging

import db
from tools import get_registry
from workflow.onboarding import build_saga

logger = logging.getLogger(__name__)

# ── Scenario templates ────────────────────────────────────────────
# `force_screening` pins the sanctions/PEP tool output so the demo is
# deterministic (the hash-based stub otherwise varies by name).
SCENARIOS = {
    "retail_low_risk": {
        "name": "Sok Channda",
        "customer_type": "individual",
        "currency": "USD",
        "sector": "retail_savings",
        "cash_intensive": False,
        "custom_docs": ["national_id", "family_book", "proof_of_address"],
        "force_identity_fail": False,
        "force_identity_verified": True,
        "force_screening": {"un_result": "clear", "nbc_cambodia_result": "clear", "ofac_result": "clear", "eu_result": "clear", "pep_status": "not_pep", "adverse_media": False, "risk_level": "low", "onboarding_prohibited": False},
        "force_ubo_clean": True,
    },
    "sme_medium_risk": {
        "name": "Ratanak Trading Co., Ltd",
        "customer_type": "business",
        "currency": "KHR",
        "sector": "fuel_trading",  # cash-intensive trading
        "cash_intensive": True,
        "custom_docs": ["business_registration", "tax_certificate", "bank_statement", "collateral"],
        "ubo": [
            {"full_name": "Ratanak Sok", "date_of_birth": "1980-05-11", "nationality": "KH", "ownership_pct": 100, "identified": True},
        ],
        "force_identity_fail": False,
        "force_identity_verified": True,
        "force_screening": {"un_result": "clear", "nbc_cambodia_result": "clear", "ofac_result": "clear", "eu_result": "clear", "pep_status": "domestic_pep", "adverse_media": False, "risk_level": "medium", "onboarding_prohibited": False},
        "force_ubo_clean": True,
    },
    "casino_high_risk": {
        "name": "Lucky Dragon Gaming Co.",
        "customer_type": "business",
        "currency": "USD",
        "sector": "casino",
        "cash_intensive": True,
        "custom_docs": ["business_registration", "tax_certificate", "bank_statement"],
        "ubo": [
            {"full_name": "Dara Lim", "date_of_birth": "1975-01-30", "nationality": "KH", "ownership_pct": 60, "identified": True},
            {"full_name": "Wei Chen", "date_of_birth": "1981-07-22", "nationality": "CN", "ownership_pct": 40, "identified": True},
        ],
        "force_identity_fail": False,
        "force_identity_verified": True,
        "force_screening": {"un_result": "clear", "nbc_cambodia_result": "clear", "ofac_result": "clear", "eu_result": "clear", "pep_status": "not_pep", "adverse_media": True, "risk_level": "medium", "onboarding_prohibited": False},
        "force_ubo_clean": True,
    },
}


def _apply_forced_screening(screen: dict, scenario: dict) -> dict:
    forced = scenario.get("force_screening")
    if forced:
        screen.update(forced)
    return screen


def _run_saga_steps(registry, steps: list[tuple[str, dict | object]], scenario: dict) -> tuple[str, dict[str, dict]]:
    """Execute onboarding steps through the saga; return (session_id, outputs)."""
    import json as _json

    saga = build_saga(registry=registry)
    session = saga.start(scenario=scenario.get("name", ""), customer_key=scenario.get("name", ""))
    session = saga.run_functional(session["session_id"], steps)
    outputs: dict[str, dict] = {}
    for step in session.get("steps", []):
        try:
            outputs[step["step"]] = _json.loads(step["output"])
        except Exception:  # noqa: BLE001
            outputs[step["step"]] = {}
    return session["session_id"], outputs


def run_scenario(scenario: dict, verbose: bool = True) -> dict:
    """Run a full onboarding journey for one customer scenario."""
    registry = get_registry()
    customer_id = f"CUST-{scenario['name'][:6].replace(' ', '')[:6]}-{abs(hash(scenario['name'])) % 1000}"
    currency = scenario.get("currency", "USD")
    customer_type = scenario.get("customer_type", "individual")

    def v(msg: str) -> None:
        if verbose:
            print(f"  {msg}")

    v(f"  >> Starting onboarding for {scenario['name']} ({customer_type}, {currency})")
    db.log_action("runner", "onboarding_start", {"customer": scenario["name"], "type": customer_type, "currency": currency})

    # 1. Retrieve NBC requirements via RAG
    rag_context = registry.invoke("knowledge_search", {"query": f"{customer_type} KYC required documents Cambodia {scenario['sector']}", "top_k": 3})
    v(f"  1) RAG: retrieved {rag_context.get('results_count', 0)} regulatory chunks  - e.g. {(rag_context.get('chunks') or [{}])[0].get('text', '')[:90]}...")
    db.log_action("runner", "rag_requirements", {"results": rag_context.get("results_count")})

    # 2. Extract uploaded documents
    docs_verified = []
    for doc_type in scenario["custom_docs"]:
        extraction = registry.invoke("extract_and_classify_document", {"document_url": f"s3://sathapana-kyc/{scenario['name']}/{doc_type}.pdf", "document_type": doc_type})
        if "error" in extraction:
            return {"status": "error", "reason": extraction["error"]}
        schema_ok = extraction.get("schema_validation", {}).get("is_complete", False)
        v(f"  2) Document '{doc_type}': ocr_quality={extraction.get('ocr_quality')}, schema_complete={schema_ok}")
        if schema_ok:
            docs_verified.append(doc_type)

    # 3. Identity verification
    identity = registry.invoke("verify_customer_identity", {"customer_id": customer_id, "document_image_url": f"{scenario['name']}/doc.jpg", "selfie_url": f"{scenario['name']}/selfie.jpg", "nationality": "KH"})
    if scenario.get("force_identity_fail"):
        identity["overall_result"] = "rejected"
        identity["liveness_check"] = "fail"
    if scenario.get("force_identity_verified"):
        identity["overall_result"] = "verified"
        identity["liveness_check"] = "pass"
        identity["face_match"] = 0.98
    v(f"  3) Identity: liveness={identity.get('liveness_check')}, face_match={identity.get('face_match')}, result={identity.get('overall_result')}")

    # 4. Sanctions + PEP screening
    screen = _apply_forced_screening(
        registry.invoke("screen_customer_sanctions", {"full_name": scenario["name"], "date_of_birth": "1990-01-01", "nationality": "KH"}),
        scenario,
    )
    v(f"  4) Screening: UN={screen.get('un_result')} NBC={screen.get('nbc_cambodia_result')} OFAC={screen.get('ofac_result')} PEP={screen.get('pep_status')} adverse={screen.get('adverse_media')} -> risk={screen.get('risk_level')} prohibited={screen.get('onboarding_prohibited')}")

    # 5. UBO screening (business only)
    ubo_result = {"decision": "clear", "threshold_applied_pct": 25}
    if customer_type == "business":
        ubo_result = registry.invoke("screen_ubo", {"owners": scenario.get("ubo", []), "risk_level": screen.get("risk_level", "low")})
        if scenario.get("force_ubo_clean"):
            ubo_result["decision"] = "clear"
            ubo_result["blocked_names"] = []
            ubo_result["unidentified_ownership"] = []
        v(f"  5) UBO screening: threshold={ubo_result.get('threshold_applied_pct')}%, decision={ubo_result.get('decision')}, blocked={ubo_result.get('blocked_names')}")

    # 6. Risk assessment (RAG-informed)
    risk = registry.invoke("assess_kyc_risk", {
        "customer_type": customer_type,
        "jurisdiction": "KH",
        "sector": scenario.get("sector", ""),
        "identity_verified": identity.get("overall_result") == "verified",
        "sanctions_clear": screen.get("onboarding_prohibited", False) is False and screen.get("un_result", "") == "clear",
        "pep_status": screen.get("pep_status", "not_pep"),
        "adverse_media": screen.get("adverse_media", False),
        "business_complexity": "simple" if customer_type == "individual" else "moderate",
        "cash_intensive": scenario.get("cash_intensive", False),
        "ubo_screened": ubo_result.get("decision") != "verify" if customer_type == "business" else True,
    })
    v(f"  6) Risk assessment: score={risk.get('risk_score')} level={risk.get('risk_level')} action={risk.get('recommended_action')} flags={risk.get('flags')}")

    # Onboarding gate
    prohibited = screen.get("onboarding_prohibited", False) or ubo_result.get("blocked_names")
    if prohibited or identity.get("overall_result") == "rejected":
        outcome = _decline(scenario, customer_id, screen, identity, ubo_result, registry)
        return outcome

    level = risk.get("risk_level")
    if level == "high":
        outcome = _decline(scenario, customer_id, screen, identity, ubo_result, registry, str_to_camfiu=True, reason="high risk / EDD unsatisfied")
        return outcome
    if level == "medium":
        outcome = _review_and_approve(scenario, customer_id, screen, identity, ubo_result, risk, docs_verified, registry)
        return outcome
    return _approve(scenario, customer_id, screen, identity, ubo_result, risk, docs_verified, registry, verbose)


def _decline(scenario: dict, customer_id: str, screen: dict, identity: dict, ubo_result: dict, registry, str_to_camfiu: bool = False, reason: str = "") -> dict:
    case = None
    flags = []
    if screen.get("onboarding_prohibited"):
        flags.append("sanctions_hit")
    if identity.get("overall_result") == "rejected":
        flags.append("identity_failed")
    if ubo_result.get("blocked_names"):
        flags.extend(ubo_result.get("blocked_names", []))
    if str_to_camfiu:
        case = registry.invoke("open_compliance_case", {"customer_id": customer_id, "risk_level": "high", "summary": f"Onboarding declined: {reason}", "flags": flags, "priority": "urgent", "file_str_to_camfiu": True, "customer_pii": {"full_name": scenario["name"], "nationality": "KH"}})
    notify = registry.invoke("notify_customer", {"recipient_id": customer_id, "channel": "sms", "template_id": "kyc_rejected", "variables": {"customer_name": scenario["name"]}})
    db.log_action("runner", "onboarding_declined", {"customer": scenario["name"], "reason": reason, "str": str_to_camfiu})
    return {"status": "declined", "reason": reason or flags, "str_filed_camfiu": str_to_camfiu, "case": (case or {}).get("case_id"), "notification": notify.get("notification_id")}


def _approve(scenario: dict, customer_id: str, screen: dict, identity: dict, ubo_result: dict, risk: dict, docs_verified: list, registry, verbose: bool) -> dict:
    def v(msg: str) -> None:
        if verbose:
            print(f"  {msg}")

    steps: list[tuple[str, object]] = [
        ("create_customer_profile", lambda o: ("create_customer_profile", {
            "personal_info": {"full_name": scenario["name"], "nationality": "KH"},
            "address": {"village": "Phsar Depo", "commune": "Toul Tompoung", "district": "Chamkar Mon", "province": "Phnom Penh"},
            "kyc_result": "approved", "risk_rating": "low",
            "currency": scenario.get("currency", "USD"), "customer_type": scenario.get("customer_type", "individual"),
            "documents_verified": docs_verified,
        })),
        ("open_account", lambda o: ("open_account", {"customer_id": o["create_customer_profile"]["customer_id"], "account_type": "retail_savings" if scenario["customer_type"] == "individual" else "sme_loan", "currency": scenario.get("currency", "USD")})),
        ("register_bakong", lambda o: ("register_bakong", {"customer_id": o["create_customer_profile"]["customer_id"], "account_id": o["open_account"]["account_id"], "mobile_number": "012-345678", "currency": scenario.get("currency", "USD")})),
        ("notify_customer", lambda o: ("notify_customer", {"recipient_id": o["create_customer_profile"]["customer_id"], "template_id": "kyc_approved", "variables": {"customer_name": scenario["name"], "product": "account", "account_id": o["open_account"]["account_id"]}})),
    ]
    session_id, outputs = _run_saga_steps(registry, steps, scenario)
    profile = outputs.get("create_customer_profile", {})
    account = outputs.get("open_account", {})
    bakong = outputs.get("register_bakong", {})

    v(f"  7) SAGA {session_id} complete (approval auto-granted, idempotent steps)")
    v(f"     Approved -> customer={profile.get('customer_id')} account={account.get('account_id')} ({account.get('currency')}) Bakong={bakong.get('bakong_id')}")
    db.log_action("runner", "onboarding_approved", {"customer": scenario["name"], "account": account.get("account_id"), "bakong": bakong.get("bakong_id"), "session": session_id})
    return {"status": "approved", "customer_id": profile.get("customer_id"), "account_id": account.get("account_id"), "bakong_id": bakong.get("bakong_id"), "risk": "low", "session": session_id}


def _review_and_approve(scenario: dict, customer_id: str, screen: dict, identity: dict, ubo_result: dict, risk: dict, docs_verified: list, registry) -> dict:
    # Medium risk → compliance case for officer review (human-in-the-loop)
    case = registry.invoke("open_compliance_case", {
        "customer_id": customer_id, "risk_level": risk.get("risk_level"), "summary": f"EDD required for {scenario['name']}", "flags": risk.get("flags", [])})
    print(f"  [HITL] compliance officer reviews case {case['case_id']}...")

    steps: list[tuple[str, object]] = [
        ("update_case", lambda o: ("update_case", {"case_id": case["case_id"], "status": "approved", "assigned_to": "MLRO", "decision": "approved_with_conditions", "notes": "EDD complete; source of funds verified."})),
        ("create_customer_profile", lambda o: ("create_customer_profile", {
            "personal_info": {"full_name": scenario["name"], "nationality": "KH"},
            "address": {"village": "Kbal Koh", "commune": "Prek Pnov", "district": "Prek Pnov", "province": "Phnom Penh"},
            "kyc_result": "approved_with_conditions", "risk_rating": "medium",
            "currency": scenario.get("currency", "USD"), "customer_type": scenario.get("customer_type", "individual"),
            "documents_verified": docs_verified, "kyc_case_id": case["case_id"],
        })),
        ("open_account", lambda o: ("open_account", {"customer_id": o["create_customer_profile"]["customer_id"], "account_type": "sme_loan", "currency": scenario.get("currency", "USD")})),
        ("register_bakong", lambda o: ("register_bakong", {"customer_id": o["create_customer_profile"]["customer_id"], "account_id": o["open_account"]["account_id"], "mobile_number": "016-987654", "currency": scenario.get("currency", "USD")})),
        ("notify_customer", lambda o: ("notify_customer", {"recipient_id": o["create_customer_profile"]["customer_id"], "template_id": "kyc_approved", "variables": {"customer_name": scenario["name"], "product": "account", "account_id": o["open_account"]["account_id"]}})),
    ]
    session_id, outputs = _run_saga_steps(registry, steps, scenario)
    profile = outputs.get("create_customer_profile", {})
    account = outputs.get("open_account", {})

    db.log_action("runner", "onboarding_approved_with_conditions", {"customer": scenario["name"], "case": case["case_id"], "account": account.get("account_id"), "session": session_id})
    return {"status": "approved_with_conditions", "customer_id": profile.get("customer_id"), "account_id": account.get("account_id"), "bakong_id": outputs.get("register_bakong", {}).get("bakong_id"), "case_id": case["case_id"], "risk": "medium", "session": session_id}


def run_demo() -> dict:
    """Run all three scenarios and return a summary."""
    db.init_db()
    print("=" * 70)
    print("SATHAPANA BANK - KYC ONBOARDING END-TO-END DEMO")
    print("=" * 70)
    outcomes = {}
    for key, scenario in SCENARIOS.items():
        print(f"\n{'-' * 70}\nScenario: {key}\n{'-' * 70}")
        outcomes[key] = run_scenario(scenario)
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for key, outcome in outcomes.items():
        status = outcome.get("status", "error")
        print(f"  {key:24s} -> {status}")
        print(f"      details: { {k: v for k, v in outcome.items() if k not in ('notification',)} }")
    print("\nAudit trail (last 10 actions):")
    for entry in db.last_audit_entries(10):
        print(f"  [{entry['ts'][:19]}] {entry['agent']:10s} {entry['action']}  {entry['status']}")
    return outcomes