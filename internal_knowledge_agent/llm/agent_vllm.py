"""
vLLM Agent — LLM orchestration using vLLM (high-throughput inference).

vLLM is a fast and easy-to-use library for LLM inference and serving.
Best for: Production deployments, high throughput, multi-user scenarios.

Setup:
    1. Install vLLM: pip install vllm
    2. Start server: vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from llm.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VLLMAgent(BaseAgent):
    """
    Document Digitization Agent powered by vLLM.

    Uses OpenAI-compatible API served by vLLM.
    Supports continuous batching, PagedAttention, and tensor parallelism.
    """

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
        vllm_url: str = "http://localhost:8000",
        max_steps: int = 10,
        temperature: float = 0.1,
    ) -> None:
        super().__init__(model_name=model_name, max_steps=max_steps)
        self.vllm_url = vllm_url.rstrip("/")
        self.temperature = temperature
        self._client = httpx.AsyncClient(base_url=self.vllm_url, timeout=120.0)

    async def call_llm(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """Call vLLM's OpenAI-compatible chat API."""
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 2048,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            response = await self._client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("vLLM API error: %s", e.response.text)
            raise RuntimeError(f"vLLM API error: {e}") from e
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to vLLM at {self.vllm_url}. "
                "Make sure vLLM is running: vllm serve <model>"
            )

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        tool_calls_raw = message.get("tool_calls", [])
        finish_reason = choice.get("finish_reason", "stop")

        tool_calls = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({
                "id": tc.get("id", f"vllm_{len(tool_calls)}"),
                "name": func.get("name", ""),
                "arguments": args,
            })

        usage = data.get("usage", {})

        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
        }

    async def health_check(self) -> dict:
        """Check if vLLM server is running and healthy."""
        try:
            response = await self._client.get("/v1/models")
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            available = any(self.model_name in m for m in models)
            return {"status": "healthy" if available else "model_not_found", "models": models}
        except Exception as e:
            return {"status": "error", "error": str(e)}


async def main():
    """Run the vLLM agent interactively."""
    agent = VLLMAgent(model_name="meta-llama/Llama-3.1-8B-Instruct")

    print("Checking vLLM connection...")
    health = await agent.health_check()
    if health.get("status") != "healthy":
        print("ERROR: vLLM is not running or model not found.")
        print("Start server: vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000")
        return

    print(f"✓ Connected to vLLM with model: {agent.model_name}")
    print("Document Digitization Agent ready. Type 'quit' to exit.\n")

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
