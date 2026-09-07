"""Production-hardening tests for the Sathapana KYC agent.

Covers: encryption round-trip + PII redaction, tamper-evident audit chain,
PII-at-rest storage, approval workflow lifecycle + SLA expiry, idempotent tool
replay, saga compensation + resume, CAMFIU STR schema validation, MCP rate
limiter, MCP auth gate, and a real TCP MCP round-trip.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

import db
from config import settings
from security import crypto
from tools import get_registry


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "kyc_test.db"))
    db.init_db()
    return tmp_path


# ── crypto / PII ──────────────────────────────────────────────────
def test_encryption_roundtrip() -> None:
    token = crypto.encrypt("Sok Channda")
    assert token.startswith("enc:v1:")
    assert crypto.is_encrypted(token)
    assert crypto.decrypt(token) == "Sok Channda"
    assert crypto.mask("Sok Channda") == "Sok ******"
    assert crypto.tokenize("DOC-NID-123") != "DOC-NID-123"


def test_redact_pii_recursive() -> None:
    detail = {"full_name": "Ann Vichea", "id_number": "0102030405", "amount": 500, "customer": {"email": "ann@example.com", "zone": "downtown"}}
    red = crypto.redact_pii(detail)
    assert red["full_name"] != "Ann Vichea"
    assert red["id_number"] != "0102030405"
    assert red["amount"] == 500
    assert red["customer"]["email"] != "ann@example.com"
    assert red["customer"]["zone"] == "downtown"
    assert crypto.looks_like_sec_number("0102030405")


# ── audit chain ───────────────────────────────────────────────────
def test_audit_chain_detects_tamper() -> None:
    db.log_action("test", "alpha", {"note": "entry one"}, "ok")
    db.log_action("test", "beta", {"amount": 100}, "ok")
    assert db.verify_audit_chain()["ok"] is True

    with db.transaction() as conn:
        conn.execute("UPDATE audit_log SET ts = '2099-01-01T00:00:00' WHERE id = (SELECT MAX(id) FROM audit_log)")
    result = db.verify_audit_chain()
    assert result["ok"] is False
    assert result["first_bad_id"] is not None


def test_audit_log_redacts_pii() -> None:
    db.log_action("test", "create_customer_profile", {"full_name": "Secret Person", "customer_id": "CUST-SECRET", "risk_rating": "low"}, "ok")
    entry = db.last_audit_entries(1)[0]
    detail = json.loads(entry["detail"])
    assert "Secret Person" not in json.dumps(detail)
    assert detail["full_name"] != "Secret Person"


def test_customer_profile_pii_encrypted_at_rest() -> None:
    reg = get_registry()
    profile = reg.invoke("create_customer_profile", {"personal_info": {"full_name": "Srey Touch", "nationality": "KH", "date_of_birth": "1990-05-05"}, "address": {"province": "Siem Reap"}, "kyc_result": "approved", "risk_rating": "low", "currency": "KHR", "customer_type": "individual"})
    assert "error" not in profile
    conn = db._connect()
    try:
        row = conn.execute("SELECT full_name, pii_encrypted FROM customers WHERE customer_id = ?", (profile["customer_id"],)).fetchone()
    finally:
        conn.close()
    assert row["full_name"].startswith("tk:")
    assert row["full_name"] != "Srey Touch"
    assert row["pii_encrypted"].startswith("enc:v1:")

    lookup = reg.invoke("lookup_customer", {"identifier": profile["customer_id"]})
    assert lookup["name"] == "Srey Touch"
    assert lookup["pii"]["dob"] == "1990-05-05"


# ── approval workflow ─────────────────────────────────────────────
def test_approval_lifecycle() -> None:
    from workflow.approvals import build_approval_workflow

    wf = build_approval_workflow(officer_id="MLRO-001", sla_seconds=300)
    req = wf.submit("open_account", {"customer_id": "CUST-NOPE", "account_type": "retail_savings", "currency": "USD"}, requested_by="ut")
    assert req["status"] == "pending"
    assert "decision_deadline" in req and req["decision_deadline"] > req["requested_at"]

    rejected = wf.decide(req["request_id"], "rejected", decided_by="MLRO-002", notes="false positive")
    assert rejected["executed"] is False
    assert "Rejected" in rejected["message"]
    assert wf.get(req["request_id"])["status"] == "decided"

    second = wf.submit("open_account", {"customer_id": "CUST-NOPE", "account_type": "retail_savings", "currency": "USD"}, requested_by="ut")
    approved = wf.decide(second["request_id"], "approved", decided_by="MLRO-001", executor=get_registry().invoke)
    assert approved["executed"] is True
    assert "error" in approved["result"]  # customer does not exist
    duplicate = wf.decide(second["request_id"], "approved", executor=get_registry().invoke)
    assert "error" in duplicate


def test_approval_sla_expiry() -> None:
    from workflow.approvals import ApprovalWorkflow

    wf = ApprovalWorkflow(officer_id="MLRO-001", sla_seconds=-1)
    req = wf.submit("update_case", {"case_id": "CASE-SLA"}, requested_by="ut")
    expired = wf.expire_overdue(executor=None)
    assert any(e["request_id"] == req["request_id"] and e["sla_expired"] for e in expired)
    assert wf.get(req["request_id"])["status"] == "decided"


# ── idempotency ───────────────────────────────────────────────────
def test_idempotent_replay_deduplicates() -> None:
    reg = get_registry()
    args = {"full_name": "Idem Person", "date_of_birth": "1990-01-01", "nationality": "KH"}
    first = reg.invoke("screen_customer_sanctions", args, idempotency_key="ut-idem-1")
    second = reg.invoke("screen_customer_sanctions", args, idempotency_key="ut-idem-1")
    assert "idempotent_replay" in second
    assert second["result"]["result"] == first


# ── saga ──────────────────────────────────────────────────────────
def _saga_smoke_steps():
    return [
        ("notify_customer", lambda o: ("notify_customer", {"recipient_id": "CUST-SAGA", "template_id": "kyc_under_review"})),
        ("bad_tool", lambda o: ("does_not_exist", {})),
    ]


def test_saga_compensation_and_resume() -> None:
    from workflow.onboarding import build_saga

    saga = build_saga()
    session = saga.start(scenario="ut_saga", customer_key="ut_saga")
    aborted = saga.run_functional(session["session_id"], _saga_smoke_steps())
    assert aborted["status"] == "aborted"
    assert aborted["current_step"] == "bad_tool"
    executed_steps = {s["step"] for s in aborted["steps"] if s["status"] == "executed"}
    assert "notify_customer" in executed_steps

    resumed = saga.run_functional(
        session["session_id"],
        [("notify_customer", lambda o: ("notify_customer", {"recipient_id": "CUST-SAGA", "template_id": "kyc_under_review"})),
         ("bad_tool", lambda o: ("notify_customer", {"recipient_id": "CUST-SAGA", "template_id": "kyc_approved"}))],
    )
    assert resumed["status"] == "complete"
    steps_after = {s["step"] for s in resumed["steps"]}
    assert "bad_tool" in steps_after


# ── CAMFIU STR schema validation ──────────────────────────────────
def test_str_validation_rejects_missing_customer() -> None:
    from integrations.camfiu import build_str_record

    record, info = build_str_record({"case_id": "CASE-1", "summary": "Suspicious cash flows from gambling and cross-border remittances", "flags": ["gambling"]}, customer=None, agent_id="ut")
    assert record is None
    assert "customer.full_name" in info["validation_error"]["missing_fields"]


def test_str_validation_accepts_valid_and_rejects_bad_amounts() -> None:
    from integrations.camfiu import build_str_record

    customer = {"customer_id": "CUST-1", "full_name": "Meas Sok", "nationality": "KH"}
    case = {"case_id": "CASE-2", "risk_level": "high", "summary": "Repeated cash deposits above threshold with gambling links and no source explanation", "flags": ["gambling_sector_high_risk"], "amounts": [{"currency": "USD", "amount": 4000.0}]}
    record, info = build_str_record(case, customer=customer, agent_id="ut")
    assert record is not None
    assert record.str_reference.startswith("STR-")
    assert info["validated"] is True

    bad = {"case_id": "CASE-3", "risk_level": "high", "summary": "Settlement after reversal with very large round amounts repeatedly occurring across multiple accounts", "flags": [], "amounts": [{"currency": "USD", "amount": 0}]}
    record2, info2 = build_str_record(bad, customer=customer, agent_id="ut")
    assert record2 is None
    assert "amounts" in ",".join(info2["validation_error"]["missing_fields"]) or info2["validation_error"]["missing_fields"]


def test_camfiu_report_through_provider() -> None:
    from integrations.camfiu import build_str_record
    from integrations import get_providers

    customer = {"customer_id": "CUST-1", "full_name": "Meas Sok", "nationality": "KH"}
    case = {"case_id": "CASE-9", "risk_level": "medium", "summary": "Casino-linked cash withdrawals with underwritten source of funds investigation trigger", "flags": ["gambling"]}
    record, _ = build_str_record(case, customer=customer, agent_id="ut")
    result = get_providers().camfiu.file(record)
    assert result["str_reference"].startswith("STR-")
    assert result["authority"] == "Cambodia Financial Intelligence Unit (CAMFIU)"


# ── MCP hardening ─────────────────────────────────────────────────
def test_rate_limiter_bucket() -> None:
    from server import RateLimiter

    rl = RateLimiter(rpm=5)
    assert [rl.try_acquire() for _ in range(5)] == [True] * 5
    assert rl.try_acquire() is False


def test_server_auth_gate(monkeypatch) -> None:
    monkeypatch.setattr(settings, "mcp_auth_token", "s3cr3t")
    from server import MCPKyCServer

    srv = MCPKyCServer()
    denied = json.loads(srv._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
    assert denied["error"]["code"] == -32001
    allowed = json.loads(srv._handle({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"auth_token": "s3cr3t"}}))
    assert allowed["result"]["serverInfo"]["name"] == "sathapana-kyc"
    monkeypatch.setattr(settings, "mcp_auth_token", "")


def test_server_payload_cap(monkeypatch) -> None:
    monkeypatch.setattr(settings, "mcp_auth_token", "")
    monkeypatch.setattr(settings, "mcp_max_payload_bytes", 500)
    from server import MCPKyCServer

    srv = MCPKyCServer()
    line = b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{"padding":"' + b"x" * 1000 + b'"}}'
    resp = json.loads(srv._process_line(line))
    assert resp["error"]["code"] == -32002
    monkeypatch.setattr(settings, "mcp_max_payload_bytes", 262144)


def test_mcp_tcp_roundtrip(monkeypatch) -> None:
    monkeypatch.setattr(settings, "mcp_auth_token", "tcp-token")

    async def _run() -> dict:
        from server import MCPKyCServer

        srv = MCPKyCServer()
        server = await asyncio.start_server(srv._handle_client, "127.0.0.1", 0, ssl=None)
        port = server.sockets[0].getsockname()[1]
        task = asyncio.create_task(server.serve_forever())

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write((json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"auth_token": "tcp-token"}}) + "\n").encode())
        await writer.drain()
        raw = await asyncio.wait_for(reader.readline(), timeout=5)
        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()
        task.cancel()
        return json.loads(raw)

    result = asyncio.run(_run())
    assert result["result"]["serverInfo"]["name"] == "sathapana-kyc"
    monkeypatch.setattr(settings, "mcp_auth_token", "")


# ── HTTP REST / OpenAPI (Swagger) surface ─────────────────────────
def test_openapi_spec_generated() -> None:
    from api_server import build_openapi

    spec = build_openapi(get_registry())
    assert spec["openapi"].startswith("3.0")
    assert spec["info"]["title"] == f"{settings.bank_name} — KYC Onboarding Agent API"
    paths = spec["paths"]
    assert "/api/v1/tools/{tool}" in paths
    assert "/api/v1/approvals/{request_id}/decide" in paths
    tool_param = paths["/api/v1/tools/{tool}"]["post"]["parameters"][0]
    assert "screen_customer_sanctions" in tool_param["schema"]["enum"]
    assert "bearerAuth" in spec["components"]["securitySchemes"]
    schemas = spec["components"]["schemas"]
    assert schemas and "ToolScreenCustomerSanctionsArgs" in schemas
    assert spec["info"]["version"]


def _http(method, url, body=None, token=None) -> tuple[int, str]:
    import urllib.request

    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    else:
        data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def test_api_server_http_roundtrip(monkeypatch) -> None:
    import threading

    from api_server import ApiKyCServer, KYCHTTPServer

    monkeypatch.setattr(settings, "mcp_auth_token", "api-token")
    api = ApiKyCServer()
    httpd = KYCHTTPServer(("127.0.0.1", 0), api)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"

    try:
        # unauthenticated → 401
        status, _ = _http("GET", f"{base}/api/v1/health")
        assert status == 401
        # authenticated health
        status, raw = _http("GET", f"{base}/api/v1/health", token="api-token")
        assert status == 200
        assert json.loads(raw)["status"] == "ok"
        # openapi serves the spec without auth
        status, raw = _http("GET", f"{base}/openapi.json")
        assert status == 200
        assert json.loads(raw)["openapi"].startswith("3.0")
        # invoke a tool via REST
        status, raw = _http("POST", f"{base}/api/v1/tools/notify_customer", {"arguments": {"recipient_id": "CUST-REST", "template_id": "kyc_approved"}}, token="api-token")
        assert status == 200
        result = json.loads(raw)
        assert result["notification_id"].startswith("ntf_")
        # unknown tool → 404
        status, _ = _http("POST", f"{base}/api/v1/tools/nope", {"arguments": {}}, token="api-token")
        assert status == 404
        # pending approvals endpoint
        status, raw = _http("GET", f"{base}/api/v1/approvals/pending?limit=10", token="api-token")
        assert status == 200
        assert isinstance(json.loads(raw), list)
    finally:
        httpd.shutdown()
        httpd.server_close()
        t.join(timeout=5)
    monkeypatch.setattr(settings, "mcp_auth_token", "")