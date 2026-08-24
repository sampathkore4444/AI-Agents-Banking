"""
Ollama Agent — LLM orchestration using Ollama (local inference).

Ollama runs open-source models locally (Llama 3, Mistral, Qwen, etc.).
Best for: Development, privacy-sensitive deployments, cost control.

Setup:
    1. Install Ollama: https://ollama.ai
    2. Pull a model: ollama pull llama3.1:8b
    3. Start server: ollama serve (usually runs on port 11434)
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from llm.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OllamaAgent(BaseAgent):
    """
    KYC Agent powered by Ollama.

    Supports any model available in Ollama (llama3.1, mistral, qwen2.5, etc.).
    Uses Ollama's /api/chat endpoint with tool calling.
    """

    def __init__(
        self,
        model_name: str = "llama3.1:8b",
        ollama_url: str = "http://localhost:11434",
        max_steps: int = 10,
        temperature: float = 0.1,
    ) -> None:
        super().__init__(model_name=model_name, max_steps=max_steps)
        self.ollama_url = ollama_url.rstrip("/")
        self.temperature = temperature
        self._client = httpx.AsyncClient(base_url=self.ollama_url, timeout=60.0)

    async def call_llm(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """
        Call Ollama's chat API with optional tool definitions.

        Ollama supports tool calling for compatible models (llama3.1, mistral, etc.).
        """
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        # Ollama uses a slightly different tool format
        if tools:
            ollama_tools = []
            for tool in tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["function"]["name"],
                        "description": tool["function"]["description"],
                        "parameters": tool["function"]["parameters"],
                    },
                })
            payload["tools"] = ollama_tools

        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Ollama API error: %s", e.response.text)
            raise RuntimeError(f"Ollama API error: {e}") from e
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.ollama_url}. "
                "Make sure Ollama is running: ollama serve"
            )

        # Parse Ollama response
        message = data.get("message", {})
        content = message.get("content", "")
        tool_calls_raw = message.get("tool_calls", [])

        # Convert to our standard format
        tool_calls = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            args = func.get("arguments", {})
            # Ollama may return arguments as a string, parse it
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({
                "id": f"ollama_{len(tool_calls)}",
                "name": func.get("name", ""),
                "arguments": args,
            })

        # Determine finish reason
        finish_reason = "tool_calls" if tool_calls else "stop"

        # Token usage (Ollama provides this)
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }

        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
            "usage": usage,
        }

    async def health_check(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = await self._client.get("/api/tags")
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            available = any(self.model_name in m for m in models)
            if not available:
                logger.warning(
                    "Model '%s' not found. Available: %s. Pull it with: ollama pull %s",
                    self.model_name, models, self.model_name,
                )
            return available
        except Exception:
            return False


# ── Standalone runner ─────────────────────────────────────────────
async def main():
    """Run the Ollama agent interactively."""
    agent = OllamaAgent(model_name="llama3.1:8b")

    # Health check
    print("Checking Ollama connection...")
    if not await agent.health_check():
        print("ERROR: Ollama is not running or model not found.")
        print("1. Start Ollama: ollama serve")
        print("2. Pull model: ollama pull llama3.1:8b")
        return

    print(f"✓ Connected to Ollama with model: {agent.model_name}")
    print("KYC Onboarding Agent ready. Type 'quit' to exit.\n")

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
