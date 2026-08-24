"""
SGLang Agent — LLM orchestration using SGLang (structured generation language).

SGLang is a fast serving framework for LLMs with structured output support.
Best for: Complex structured outputs, constrained decoding.

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
    """
    Payment Reconciliation Agent powered by SGLang.

    SGLang provides OpenAI-compatible API with structured output support.
    """

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
        sglang_url: str = "http://localhost:30000",
        max_steps: int = 10,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> None:
        super().__init__(model_name=model_name, max_steps=max_steps)
        self.sglang_url = sglang_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = httpx.AsyncClient(base_url=self.sglang_url, timeout=120.0)

    async def call_llm(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """Call SGLang's OpenAI-compatible chat completions endpoint."""
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            response = await self._client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("SGLang API error: %s", e.response.text)
            raise RuntimeError(f"SGLang API error: {e}") from e
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to SGLang at {self.sglang_url}. "
                "Start SGLang with: python -m sglang.launch_server --model <model> --port 30000"
            )

        choice = data["choices"][0]
        message = choice["message"]
        content = message.get("content", "")
        tool_calls_raw = message.get("tool_calls", [])
        finish_reason = choice.get("finish_reason", "stop")

        tool_calls = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            args = func.get("arguments", "")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({
                "id": tc.get("id", f"sglang_{len(tool_calls)}"),
                "name": func.get("name", ""),
                "arguments": args,
            })

        usage = data.get("usage", {})

        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason or ("tool_calls" if tool_calls else "stop"),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
        }

    async def health_check(self) -> dict:
        """Check SGLang server status."""
        try:
            response = await self._client.get("/v1/models")
            response.raise_for_status()
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            available = self.model_name in models
            return {
                "status": "healthy" if available else "model_not_found",
                "available_models": models,
                "requested_model": self.model_name,
            }
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}


async def main():
    """Run the SGLang agent interactively."""
    agent = SGLangAgent(model_name="meta-llama/Llama-3.1-8B-Instruct")

    print("Checking SGLang connection...")
    health = await agent.health_check()
    if health["status"] != "healthy":
        print(f"ERROR: SGLang is not healthy. Status: {health['status']}")
        print("Start SGLang with: python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 30000")
        return

    print(f"✓ Connected to SGLang with model: {agent.model_name}")
    print("Payment Reconciliation Agent ready. Type 'quit' to exit.\n")

    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue

        response = await agent.run(query)
        print(f"\nAgent: {response.answer}")
        print(f"[{len(response.tool_calls)} tools called, {response.total_duration_ms:.0f}ms]\n")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
