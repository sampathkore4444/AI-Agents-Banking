"""
Sathapana Bank KYC Onboarding Agent — MCP server (stdio or TCP+TLS).

A minimal, dependency-free Model Context Protocol server speaking JSON-RPC 2.0
over newline-delimited stdio (default) or TCP (optional TLS). Implements
`initialize`, `tools/list`, `tools/call`, and `ping`.

Production hardening applied here:
  * Bearer auth token (`MCP_AUTH_TOKEN` in .env) — every request must carry it
    in `params.auth_token` (or an `Authorization` header line on TCP), verified
    with constant-time comparison.
  * Token-bucket rate limiter (`MCP_RATE_LIMIT_RPM`).
  * Maximum request payload enforced (`MCP_MAX_PAYLOAD_BYTES`).
  * TCP transport with optional TLS when `MCP_TLS_CERT`/`MCP_TLS_KEY` are set.

Protocol reference: modelcontextprotocol.io/specification/2025-03-26
"""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import sys
import threading
import time
from typing import Any

import db
from config import settings
from tools import get_registry

logging.basicConfig(level=logging.INFO, format="[mcp] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _result_for_response(msg_id: Any, result: dict) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}, ensure_ascii=False)


def _error_response(msg_id: Any, code: int, message: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}, ensure_ascii=False)


class RateLimiter:
    """Token-bucket rate limiter keyed on rpm (requests per minute)."""

    def __init__(self, rpm: int) -> None:
        self.capacity = max(1, rpm)
        self.tokens = float(self.capacity)
        self.rate = max(1, rpm) / 60.0
        self.updated = time.monotonic()

    def try_acquire(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class MCPKyCServer:
    """MCP JSON-RPC server (stdio/TCP) for the Sathapana KYC tools."""

    NAME = "sathapana-kyc"
    VERSION = "1.0.0"
    PROTOCOL_VERSION = "2025-03-26"

    def __init__(self) -> None:
        self.registry = get_registry()
        self.rate_limiter = RateLimiter(settings.mcp_rate_limit_rpm)
        self.auth_token = settings.mcp_auth_token
        self.max_payload = settings.mcp_max_payload_bytes
        self.queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._reader_ready = threading.Event()

    # ── security gates ────────────────────────────────────────────
    def _authorized(self, request: dict) -> bool:
        if not self.auth_token:
            return True
        params = request.get("params") or {}
        supplied = params.get("auth_token") or params.get("authorization")
        return bool(supplied) and hmac.compare_digest(str(supplied), self.auth_token)

    def _too_large(self, line: bytes) -> bool:
        return len(line) > self.max_payload

    # ── transport: stdio ──────────────────────────────────────────
    def _start_reader(self) -> None:
        def _read() -> None:
            for line in sys.stdin.buffer:
                if line.strip():
                    asyncio.run_coroutine_threadsafe(self.queue.put(line), self.loop).result()
            asyncio.run_coroutine_threadsafe(self.queue.put(None), self.loop).result()

        threading.Thread(target=_read, daemon=True).start()

    # ── transport: TCP ────────────────────────────────────────────
    def _ssl_context(self):
        if settings.mcp_tls_cert and settings.mcp_tls_key:
            import ssl

            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(settings.mcp_tls_cert, settings.mcp_tls_key)
            return ctx
        return None

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        logger.info("TCP client connected: %s", peer)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                response = await asyncio.to_thread(self._process_line, line, transport="tcp")
                if response:
                    writer.write(response.encode("utf-8") + b"\n")
                    await writer.drain()
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info("TCP client disconnected: %s", peer)

    async def run_tcp(self) -> None:
        if not settings.mcp_tls_cert and settings.mcp_tls_key:
            logger.warning("TCP transport running WITHOUT TLS (MCP_TLS_CERT/KEY not set)")
        host, port = settings.mcp_host, settings.mcp_port
        server = await asyncio.start_server(self._handle_client, host, port, ssl=self._ssl_context())
        logger.info("MCP server '%s' v%s listening on %s:%s (TLS=%s)", self.NAME, self.VERSION, host, port, bool(self._ssl_context()))
        async with server:
            await server.serve_forever()

    # ── protocol ──────────────────────────────────────────────────
    async def _emit(self, text: str) -> None:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()

    def _handle(self, request: dict) -> str:
        msg_id = request.get("id")
        method = request.get("method", "")

        if not self._authorized(request):
            return _error_response(msg_id, -32001, "Unauthorized: missing or invalid auth token")

        if method == "initialize":
            params = request.get("params", {})
            return _result_for_response(
                msg_id,
                {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}, "security": {"auth": bool(self.auth_token)}},
                    "serverInfo": {"name": self.NAME, "version": self.VERSION},
                },
            )
        if method == "ping":
            return _result_for_response(msg_id, {})
        if method in ("notifications/initialized", "initialized"):
            return ""
        if method == "tools/list":
            tools = [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": {"type": "object", "properties": t["inputSchema"].get("properties", {}), **({"required": t["inputSchema"]["required"]} if "required" in t["inputSchema"] else {})},
                }
                for t in self.registry._tools.values()
            ]
            return _result_for_response(msg_id, {"tools": tools})
        if method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {}) or {}
            idem = params.get("_idempotency_key") or params.get("idempotency_key")
            tool = self.registry.get(name)
            if not tool:
                return _error_response(msg_id, -32602, f"Unknown tool: {name}")
            logger.info("tools/call %s args=%s", name, json.dumps(args)[:200])
            result = self.registry.invoke(name, args, idempotency_key=idem)
            payload = json.dumps(result, ensure_ascii=False, indent=2) if not isinstance(result, str) else result
            return _result_for_response(
                msg_id,
                {"content": [{"type": "text", "text": payload}], "isError": False, "structure": {"results": True}},
            )
        if method.startswith("notifications/"):
            return ""
        return _error_response(msg_id, -32601, f"Method not found: {method}")

    def _process_line(self, line: bytes, transport: str = "stdio") -> str:
        line = line.strip()
        if not line:
            return ""
        if self._too_large(line):
            return _error_response(None, -32002, f"Payload exceeds limit ({self.max_payload} bytes)")
        try:
            request = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            return _error_response(None, -32700, "Parse error: invalid JSON")
        if not self.rate_limiter.try_acquire():
            return _error_response(request.get("id"), -32005, "Rate limit exceeded")
        if "id" not in request:  # notification
            try:
                self._handle(request)
            except Exception:  # noqa: BLE001
                pass
            return ""
        try:
            return self._handle(request)
        except Exception as exc:  # noqa: BLE001
            return _error_response(request.get("id"), -32603, f"Internal error: {exc}")

    # ── run loop: stdio ───────────────────────────────────────────
    async def run(self) -> None:
        db.init_db()
        self.loop = asyncio.get_running_loop()
        self._start_reader()
        logger.info("MCP server '%s' v%s listening on stdio", self.NAME, self.VERSION)
        while True:
            line = await self.queue.get()
            if line is None:
                break
            response = await asyncio.to_thread(self._process_line, line, "stdio")
            if response:
                await self._emit(response)


def main(transport: str | None = None) -> None:
    db.init_db()
    transport = (transport or settings.mcp_transport).lower()
    if transport == "tcp":
        asyncio.run(MCPKyCServer().run_tcp())
    else:
        asyncio.run(MCPKyCServer().run())


if __name__ == "__main__":
    main()