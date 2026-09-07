"""
Sathapana Bank KYC Agent — HTTP REST + OpenAPI (Swagger) server.

Dependency-free (stdlib `http.server`) HTTP API exposing the same toolbox the
MCP server does, plus a compliance-officer surface (approvals, cases, audit).

Endpoints:
    GET  /                       Swagger UI (loads /openapi.json)
    GET  /openapi.json           Auto-generated OpenAPI 3.0 spec
    GET  /api/v1/health          Liveness + backend status
    GET  /api/v1/tools           List tools + risk levels + schemas
    POST /api/v1/tools/{tool}    Invoke a tool (body = tool arguments)
    GET  /api/v1/approvals/pending
    POST /api/v1/approvals/{request_id}/decide
    GET  /api/v1/cases/{case_id}
    GET  /api/v1/audit/verify
    GET  /api/v1/audit/last
    GET  /api/v1/providers

The OpenAPI document is generated from `ToolRegistry` inputSchema definitions,
so the Swagger surface always matches the code. Auth: the same hardcoded
`MCP_AUTH_TOKEN` from .env, sent as `Authorization: Bearer <token>`.

Run with:  python main.py serve-api [--host 0.0.0.0] [--port 8000]
"""

from __future__ import annotations

import hmac
import json
import logging
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import db
from config import settings
from integrations import get_providers
from server import RateLimiter
from tools import get_registry
from workflow.approvals import build_approval_workflow

logger = logging.getLogger(__name__)

API_NAME = "sathapana-kyc-api"
API_VERSION = "1.0.0"
SWAGGER_UI_VERSION = "5"
ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {"type": "string", "description": "Human-readable error message."},
        "code": {"type": "string", "description": "Stable machine-readable error code.", "example": "not_found"},
    },
    "required": ["error"],
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _schema_for_tool(tool: dict) -> dict:
    """Return an OpenAPI request schema for one registered tool."""
    schema = {"type": "object"}
    properties = tool["inputSchema"].get("properties", {}) or {}
    cleaned = {}
    for name, prop in properties.items():
        p = {k: v for k, v in prop.items() if k not in ("default",)}
        cleaned[name] = p
    schema["properties"] = cleaned
    required = tool["inputSchema"].get("required")
    if required:
        schema["required"] = required
    return schema


def build_openapi(registry) -> dict:
    """Generate the OpenAPI 3.0 document from the ToolRegistry."""
    tools = sorted(registry._tools.items())
    tool_names = [name for name, _ in tools]

    paths: dict[str, Any] = {}

    paths["/api/v1/health"] = {
        "get": {
            "summary": "Liveness and provider backends",
            "tags": ["System"],
            "security": [],
            "responses": {
                "200": {
                    "description": "OK",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "additionalProperties": {}, "example": {"status": "ok"}}
                        }
                    },
                }
            },
        }
    }

    paths["/api/v1/tools"] = {
        "get": {
            "summary": "List tools, risk levels and JSON schemas",
            "tags": ["Tools"],
            "security": [{"bearerAuth": []}],
            "responses": {
                "200": {
                    "description": "Tool catalog",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"tools": {"type": "array", "items": {"type": "object"}}, "count": {"type": "integer"}},
                            }
                        }
                    },
                }
            },
        }
    }

    paths["/api/v1/tools/{tool}"] = {
        "post": {
            "summary": "Invoke a KYC agent tool",
            "description": (
                "Calls the same ToolRegistry used by the MCP server and the agent loop. "
                "Body is the tool's arguments as defined in GET /api/v1/tools. Optionally pass "
                "`_idempotency_key` to make the call replay-safe (deduplicated via tool_call_log)."
            ),
            "tags": ["Tools"],
            "security": [{"bearerAuth": []}],
            "parameters": [
                {
                    "name": "tool",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "enum": tool_names},
                    "description": "Tool name (see list above).",
                }
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "arguments": {"description": "Tool arguments."},
                                "_idempotency_key": {"type": "string", "description": "Replay guard. Repeating the same key returns the cached result."},
                            },
                            "required": ["arguments"],
                        },
                        "example": {"arguments": {"full_name": "Sok Channda", "date_of_birth": "1990-01-01", "nationality": "KH"}},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Tool result",
                    "content": {"application/json": {"schema": {"type": "object", "additionalProperties": True}}},
                },
                "400": {"description": "Invalid arguments", "content": {"application/json": {"schema": ERROR_SCHEMA}}},
                "401": {"description": "Missing or invalid auth token", "content": {"application/json": {"schema": ERROR_SCHEMA}}},
                "404": {"description": "Unknown tool", "content": {"application/json": {"schema": ERROR_SCHEMA}}},
                "429": {"description": "Rate limit exceeded", "content": {"application/json": {"schema": ERROR_SCHEMA}}},
                "500": {"description": "Client error returned by tool", "content": {"application/json": {"schema": ERROR_SCHEMA}}},
            },
        }
    }

    paths["/api/v1/approvals/pending"] = {
        "get": {
            "summary": "List pending HITL approvals (oldest deadline first)",
            "tags": ["Approvals"],
            "security": [{"bearerAuth": []}],
            "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}}],
            "responses": {"200": {"description": "Pending approval requests", "content": {"application/json": {"schema": {"type": "array"}}}}},
        }
    }

    paths["/api/v1/approvals/{request_id}/decide"] = {
        "post": {
            "summary": "Decide a pending approval (approve / approve_with_conditions / reject)",
            "description": (
                "Executes the underlying high-risk tool on approval (idempotently), so an "
                "approved decision performs the side effect exactly once."
            ),
            "tags": ["Approvals"],
            "security": [{"bearerAuth": []}],
            "parameters": [{"name": "request_id", "in": "path", "required": True, "schema": {"type": "string"}, "example": "APR-1A2B3C4D"}],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "decision": {"type": "string", "enum": ["approved", "approved_with_conditions", "rejected"]},
                                "decided_by": {"type": "string", "example": "MLRO-001"},
                                "notes": {"type": "string"},
                            },
                            "required": ["decision"],
                        }
                    }
                },
            },
            "responses": {
                "200": {"description": "Decision applied", "content": {"application/json": {"schema": {"type": "object"}}}},
                "400": {"description": "Invalid decision", "content": {"application/json": {"schema": ERROR_SCHEMA}}},
            },
        }
    }

    paths["/api/v1/cases/{case_id}"] = {
        "get": {
            "summary": "Retrieve a compliance case by ID",
            "tags": ["Compliance"],
            "security": [{"bearerAuth": []}],
            "parameters": [{"name": "case_id", "in": "path", "required": True, "schema": {"type": "string"}, "example": "CASE-235F7A27"}],
            "responses": {
                "200": {"description": "Compliance case", "content": {"application/json": {"schema": {"type": "object"}}}},
                "404": {"description": "Unknown case", "content": {"application/json": {"schema": ERROR_SCHEMA}}},
            },
        }
    }

    paths["/api/v1/audit/verify"] = {
        "get": {
            "summary": "Verify the tamper-evident audit chain",
            "tags": ["Audit"],
            "security": [{"bearerAuth": []}],
            "responses": {"200": {"description": "Chain integrity report", "content": {"application/json": {"schema": {"type": "object"}}}}},
        }
    }

    paths["/api/v1/audit/last"] = {
        "get": {
            "summary": "Last audit entries",
            "tags": ["Audit"],
            "security": [{"bearerAuth": []}],
            "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}}],
            "responses": {"200": {"description": "Audit entries (PII-redacted)", "content": {"application/json": {"schema": {"type": "array"}}}}},
        }
    }

    paths["/api/v1/providers"] = {
        "get": {
            "summary": "Active vendor provider backends (stub vs http)",
            "tags": ["System"],
            "security": [{"bearerAuth": []}],
            "responses": {"200": {"description": "Provider map", "content": {"application/json": {"schema": {"type": "object"}}}}},
        }
    }

    schema_components: dict[str, Any] = {}
    for name, tool in tools:
        schema_components[f"Tool{name.replace('_', ' ').title().replace(' ', '')}Args"] = _schema_for_tool(tool)

    return {
        "openapi": "3.0.3",
        "info": {
            "title": f"{settings.bank_name} — KYC Onboarding Agent API",
            "description": (
                "REST gateway for the Sathapana KYC onboarding agent. Exposes the same "
                "ToolRegistry as the MCP server, plus the compliance-officer surface "
                "(HITL approval queue, compliance cases, audit verification) powered by "
                "the DB-backed ApprovalWorkflow and hash-chained audit log. "
                "Authorize once with the API token to call any secured endpoint."
            ),
            "version": API_VERSION,
            "termsOfService": "Internal use only",
            "contact": {"name": "Sathapana MLRO / Compliance"},
        },
        "servers": [{"url": "/", "description": "Agent API (edit host per deployment)"}],
        "security": [{"bearerAuth": []}],
        "tags": [{"name": "Tools", "description": "Registry-driven KYC tools"}, {"name": "Approvals", "description": "Human-in-the-loop decisions"}, {"name": "Compliance", "description": "Compliance case retrieval"}, {"name": "Audit", "description": "Tamper-evident audit trail"}, {"name": "System", "description": "Health and configuration"}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "token", "description": f"Token from KYC_MCP_AUTH_TOKEN in .env (current value set: {bool(settings.mcp_auth_token)})."}
            },
            "schemas": schema_components,
        },
    }


def _swagger_ui_html() -> str:
    """Minimal Swagger UI bootstrap served at /."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{API_NAME} — Swagger UI</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_UI_VERSION}/swagger-ui.css"/>
</head>
<body style="margin:0;padding:16px 2vw">
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_UI_VERSION}/swagger-ui-bundle.js"></script>
<script>
window.onload = function () {{
  window.ui = SwaggerUIBundle({{
    url: '/openapi.json',
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: 'BaseLayout',
  }});
}};
</script>
</body>
</html>"""


class ApiKyCServer:
    """HTTP/OpenAPI server for the KYC tools and compliance surface."""

    def __init__(self) -> None:
        self.registry = get_registry()
        self.approvals = build_approval_workflow()
        self.auth_token = settings.mcp_auth_token
        self.rate_limiter = RateLimiter(settings.mcp_rate_limit_rpm)
        self.max_payload = settings.mcp_max_payload_bytes
        self.openapi = build_openapi(self.registry)

    # ── security ──────────────────────────────────────────────────
    def _authorized(self, headers: dict[str, str]) -> bool:
        if not self.auth_token:
            return True
        supplied = (
            headers.get("x-api-key")
            or headers.get("authorization", "").removeprefix("Bearer ").strip()
            or headers.get("authorization", "").removeprefix("Token ").strip()
        )
        return bool(supplied) and hmac.compare_digest(str(supplied), self.auth_token)

    # ── routing ───────────────────────────────────────────────────
    def dispatch(self, method: str, path: str, query: dict[str, str], body: dict | None, headers: dict[str, str]) -> tuple[int, dict | str]:
        if not self._authorized(headers):
            return 401, {"error": "Unauthorized: missing or invalid auth token", "code": "unauthorized"}

        if method == "GET" and path == "/api/v1/health":
            providers = get_providers().summary()
            return 200, {
                "status": "ok",
                "name": API_NAME,
                "version": API_VERSION,
                "timestamp": _utcnow(),
                "providers": providers,
                "auth_enabled": bool(self.auth_token),
            }
        if method == "GET" and path == "/api/v1/tools":
            catalog = [
                {"name": t["name"], "description": t["description"], "risk_level": t["risk_level"], "inputSchema": t["inputSchema"]}
                for t in self.registry._tools.values()
            ]
            return 200, {"count": len(catalog), "tools": catalog}
        if method == "POST" and path.startswith("/api/v1/tools/"):
            return self._invoke_tool(path[len("/api/v1/tools/") :], body)
        if method == "GET" and path == "/api/v1/approvals/pending":
            limit = int(query.get("limit", 50))
            return 200, self.approvals.pending(limit=limit)
        if method == "POST" and "/decide" in path and path.startswith("/api/v1/approvals/"):
            request_id = path[len("/api/v1/approvals/") : -len("/decide")]
            return self._decide(request_id, body)
        if method == "GET" and path.startswith("/api/v1/cases/") and path != "/api/v1/cases/":
            return self._get_case(path[len("/api/v1/cases/") :])
        if method == "GET" and path == "/api/v1/audit/verify":
            return 200, db.verify_audit_chain()
        if method == "GET" and path == "/api/v1/audit/last":
            limit = int(query.get("limit", 20))
            return 200, db.last_audit_entries(limit=limit)
        if method == "GET" and path == "/api/v1/providers":
            return 200, get_providers().summary()
        return 404, {"error": f"Not found: {method} {path}", "code": "not_found"}

    def _invoke_tool(self, tool_name: str, body: dict | None) -> tuple[int, dict]:
        tool = self.registry.get(tool_name)
        if not tool:
            return 404, {"error": f"Unknown tool: {tool_name}", "code": "unknown_tool"}
        body = body or {}
        arguments = body.get("arguments", {})
        if not isinstance(arguments, dict):
            return 400, {"error": "'arguments' must be an object", "code": "invalid_arguments"}
        idem = body.get("_idempotency_key")
        result = self.registry.invoke(tool_name, arguments, idempotency_key=idem)
        if "error" in result:
            return 400, result
        return 200, result

    def _decide(self, request_id: str, body: dict | None) -> tuple[int, dict]:
        body = body or {}
        decision = body.get("decision", "")
        if decision not in ("approved", "approved_with_conditions", "rejected"):
            return 400, {"error": f"decision must be approved / approved_with_conditions / rejected, got {decision!r}", "code": "invalid_decision"}
        result = self.approvals.decide(
            request_id,
            decision,
            decided_by=body.get("decided_by") or "api/officer",
            notes=body.get("notes", ""),
            executor=self.registry.invoke,
        )
        if "error" in result:
            return 400, result
        return 200, result

    def _get_case(self, case_id: str) -> tuple[int, dict]:
        import tools.compliance as compliance

        case = compliance.get_compliance_case(case_id)
        if isinstance(case, dict) and "error" in case:
            return 404, case
        return 200, case


class _Handler(BaseHTTPRequestHandler):
    server: "KYCHTTPServer"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # silence request logging
        if self.server.log_requests:
            logger.info("%s %s", self.command, self.path)

    def _route(self) -> None:
        api = self.server.api
        parse = urlparse(self.path)
        path = parse.path.rstrip("/") or "/"
        if not api.rate_limiter.try_acquire():
            return self._send(429, {"error": "Rate limit exceeded", "code": "rate_limited"})
        if self.command in ("GET", "DELETE", "HEAD"):
            query = {k: v[0] for k, v in parse_qs(parse.query).items()}
            status, payload = api.dispatch(self.command, path, query, None, {k.lower(): v for k, v in self.headers.items()})
            return self._send(status, payload)
        # POST / PUT
        length = int(self.headers.get("content-length") or 0)
        if length > api.max_payload:
            return self._send(413, {"error": f"Payload exceeds limit ({api.max_payload} bytes)", "code": "payload_too_large"})
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8")) if raw.strip() else {}
        except json.JSONDecodeError:
            return self._send(400, {"error": "Invalid JSON body", "code": "parse_error"})
        query = {}
        status, payload = api.dispatch(self.command, path, query, body, {k.lower(): v for k, v in self.headers.items()})
        self._send(status, payload)

    def _send(self, status: int, payload: dict | str) -> None:
        if isinstance(payload, str):
            body = payload.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        else:
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parse = urlparse(self.path)
        if parse.path in ("/", "/ui"):
            return self._send(200, _swagger_ui_html())
        if parse.path == "/openapi.json":
            return self._send(200, self.server.api.openapi)
        self._route()

    def do_POST(self) -> None:
        self._route()

    def do_DELETE(self) -> None:  # allow HEAD-style health checks
        self._route()


class KYCHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr: tuple[str, int], api: ApiKyCServer, log_requests: bool = False) -> None:
        self.api = api
        self.log_requests = log_requests
        super().__init__(addr, _Handler)


def serve(host: str = "127.0.0.1", port: int = 8000, log_requests: bool = False) -> None:
    """Run the HTTP/OpenAPI server (blocks)."""
    db.init_db()
    api = ApiKyCServer()
    httpd = KYCHTTPServer((host, port), api, log_requests=log_requests)
    if not settings.mcp_tls_cert and not settings.mcp_auth_token:
        logger.warning("API server running WITHOUT auth token (set KYC_MCP_AUTH_TOKEN in .env)")
    print(f"  {API_NAME} v{API_VERSION} -> http://{host}:{port}")
    print(f"  Swagger UI: http://{host}:{port}/")
    print(f"  OpenAPI   : http://{host}:{port}/openapi.json")
    print(f"  Auth token configured: {bool(api.auth_token)}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    serve()