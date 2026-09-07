"""
Sathapana Bank KYC Onboarding Agent — MCP server (stdio).

A minimal, dependency-free Model Context Protocol server speaking
JSON-RPC 2.0 over stdio (newline-delimited). Implements `initialize`,
`tools/list`, `tools/call`, and `ping`. Wrap your deployment in the
official `mcp` runtime (python stdio transport) or connect as a client
to `python server.py`.

Protocol reference: modelcontextprotocol.io/specification/2025-03-26
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
from typing import Any

import db
from tools import get_registry

logging.basicConfig(level=logging.INFO, format="[mcp] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _result_for_response(msg_id: Any, result: dict) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}, ensure_ascii=False)


def _error_response(msg_id: Any, code: int, message: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}, ensure_ascii=False)


class MCPKyCServer:
    """MCP JSON-RPC server over stdio for the Sathapana KYC tools."""

    NAME = "sathapana-kyc"
    VERSION = "0.1.0"
    PROTOCOL_VERSION = "2025-03-26"

    def __init__(self) -> None:
        self.registry = get_registry()
        self.queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._reader_ready = threading.Event()

    # ── transport ─────────────────────────────────────────────────
    def _start_reader(self) -> None:
        def _read() -> None:
            for line in sys.stdin.buffer:
                if line.strip():
                    asyncio.run_coroutine_threadsafe(self.queue.put(line), self.loop).result()
            asyncio.run_coroutine_threadsafe(self.queue.put(None), self.loop).result()

        thread = threading.Thread(target=_read, daemon=True)
        thread.start()

    async def _emit(self, text: str) -> None:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()

    # ── protocol handlers ─────────────────────────────────────────
    def _handle(self, request: dict) -> str:
        msg_id = request.get("id")
        method = request.get("method", "")

        if method == "initialize":
            params = request.get("params", {})
            return _result_for_response(
                msg_id,
                {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
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
            tool = self.registry.get(name)
            if not tool:
                return _error_response(msg_id, -32602, f"Unknown tool: {name}")
            logger.info("tools/call %s args=%s", name, json.dumps(args)[:200])
            result = self.registry.invoke(name, args)
            payload = json.dumps(result, ensure_ascii=False, indent=2) if not isinstance(result, str) else result
            return _result_for_response(
                msg_id,
                {"content": [{"type": "text", "text": payload}], "isError": False, "structure": {"results": True}},
            )
        if method.startswith("notifications/"):
            return ""
        return _error_response(msg_id, -32601, f"Method not found: {method}")

    # ── run loop ──────────────────────────────────────────────────
    async def run(self) -> None:
        db.init_db()
        self.loop = asyncio.get_running_loop()
        self._start_reader()
        logger.info("MCP server '%s' v%s listening on stdio", self.NAME, self.VERSION)
        while True:
            line = await self.queue.get()
            if line is None:
                break
            try:
                request = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            if "id" not in request:  # notification
                try:
                    self._handle(request)
                except Exception:  # noqa: BLE001
                    pass
                continue
            try:
                response_text = await asyncio.to_thread(self._handle, request)
            except Exception as exc:  # noqa: BLE001
                response_text = _error_response(request.get("id"), -32603, f"Internal error: {exc}")
            if response_text:
                await self._emit(response_text)


def main() -> None:
    asyncio.run(MCPKyCServer().run())


if __name__ == "__main__":
    main()