"""
Ollama Agent — LLM orchestration using Ollama (local inference).

Setup:
    1. Install Ollama: https://ollama.ai
    2. Pull a model: ollama pull llama3.1:8b
    3. Start server: ollama serve
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from llm.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OllamaAgent(BaseAgent):
    def __init__(self, model_name: str = "llama3.1:8b", ollama_url: str = "http://localhost:11434", max_steps: int = 10, temperature: float = 0.1) -> None:
        super().__init__(model_name=model_name, max_steps=max_steps)
        self.ollama_url = ollama_url.rstrip("/")
        self.temperature = temperature
        self._client = httpx.AsyncClient(base_url=self.ollama_url, timeout=60.0)

    async def call_llm(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload: dict[str, Any] = {"model": self.model_name, "messages": messages, "stream": False, "options": {"temperature": self.temperature}}
        if tools:
            payload["tools"] = [{"type": "function", "function": {"name": t["function"]["name"], "description": t["function"]["description"], "parameters": t["function"]["parameters"]}} for t in tools]
        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot connect to Ollama at {self.ollama_url}. Start: ollama serve")
        message = data.get("message", {})
        tool_calls = [{"id": f"ollama_{i}", "name": tc.get("function", {}).get("name", ""), "arguments": tc.get("function", {}).get("arguments", {})} for i, tc in enumerate(message.get("tool_calls", []))]
        return {"content": message.get("content", ""), "tool_calls": tool_calls, "finish_reason": "tool_calls" if tool_calls else "stop", "usage": {"prompt_tokens": data.get("prompt_eval_count", 0), "completion_tokens": data.get("eval_count", 0)}}

    async def health_check(self) -> dict:
        try:
            response = await self._client.get("/api/tags")
            models = [m["name"] for m in response.json().get("models", [])]
            available = any(self.model_name in m for m in models)
            return {"status": "healthy" if available else "model_not_found", "available_models": models}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}


async def main():
    agent = OllamaAgent()
    print("Checking Ollama connection...")
    health = await agent.health_check()
    if health["status"] != "healthy":
        print(f"ERROR: {health['status']}. Start: ollama serve")
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
