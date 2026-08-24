"""
SGLang Agent — LLM orchestration using SGLang (structured generation).

Setup:
    1. Install SGLang: pip install sglang
    2. Start server: python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 30000
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from llm.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SGLangAgent(BaseAgent):
    def __init__(self, model_name: str = "meta-llama/Llama-3.1-8B-Instruct", sglang_url: str = "http://localhost:30000", max_steps: int = 10, temperature: float = 0.1, max_tokens: int = 4096) -> None:
        super().__init__(model_name=model_name, max_steps=max_steps)
        self.sglang_url = sglang_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = httpx.AsyncClient(base_url=self.sglang_url, timeout=120.0)

    async def call_llm(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload: dict[str, Any] = {"model": self.model_name, "messages": messages, "temperature": self.temperature, "max_tokens": self.max_tokens, "stream": False}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        try:
            response = await self._client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot connect to SGLang at {self.sglang_url}")
        choice = data["choices"][0]
        message = choice["message"]
        tool_calls = [{"id": tc.get("id", f"sglang_{i}"), "name": tc.get("function", {}).get("name", ""), "arguments": json.loads(tc.get("function", {}).get("arguments", "{}")) if isinstance(tc.get("function", {}).get("arguments", ""), str) else tc.get("function", {}).get("arguments", {})} for i, tc in enumerate(message.get("tool_calls", []))]
        usage = data.get("usage", {})
        return {"content": message.get("content", ""), "tool_calls": tool_calls, "finish_reason": choice.get("finish_reason", "stop") or ("tool_calls" if tool_calls else "stop"), "usage": {"prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0)}}

    async def health_check(self) -> dict:
        try:
            response = await self._client.get("/v1/models")
            models = [m["id"] for m in response.json().get("data", [])]
            return {"status": "healthy" if self.model_name in models else "model_not_found", "available_models": models}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}


async def main():
    agent = SGLangAgent()
    print("Checking SGLang connection...")
    health = await agent.health_check()
    if health["status"] != "healthy":
        print(f"ERROR: {health['status']}. Start: python -m sglang.launch_server --model {agent.model_name} --port 30000")
        return
    print(f"✓ Connected. Cross-Border Payment Agent ready.\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        response = await agent.run(query)
        print(f"\nAgent: {response.answer}\n[{len(response.tool_calls)} tools, {response.total_duration_ms:.0f}ms]\n")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
