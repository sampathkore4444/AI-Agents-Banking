"""
Ollama Agent — local LLM orchestration for the Sathapana KYC agent.

Leverages the installed `ollama` Python client. Any tool-calling model in
Ollama can be used (llama3.1, qwen2.5, mistral, etc.).

Setup:
    1. ollama serve
    2. ollama pull llama3.1:8b
"""

from __future__ import annotations

import json
import logging
from typing import Any

import ollama

from llm.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OllamaAgent(BaseAgent):
    """KYC Agent powered by a local Ollama model."""

    def __init__(
        self,
        model_name: str = "llama3.1:8b",
        host: str = "http://localhost:11434",
        max_steps: int = 10,
        temperature: float = 0.1,
        auto_approve: bool = False,
    ) -> None:
        super().__init__(model_name=model_name, max_steps=max_steps, auto_approve=auto_approve, run_id="ollama")
        self._client = ollama.AsyncClient(host=host)
        self.temperature = temperature

    async def call_llm(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload: dict[str, Any] = {"model": self.model_name, "messages": messages, "options": {"temperature": self.temperature}}
        if tools:
            payload["tools"] = tools

        data = await self._client.chat(**payload)
        message = data.get("message", {})
        content = message.get("content", "")

        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({"id": f"ollama_{len(tool_calls)}", "name": func.get("name", ""), "arguments": args})

        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": "tool_calls" if tool_calls else "stop",
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        }

    async def health_check(self) -> tuple[bool, str]:
        try:
            models = await self._client.list()
            names = [m.get("model", "") or m.get("name", "") for m in models.get("models", [])]
            if any(self.model_name in n for n in names):
                return True, f"model {self.model_name} available"
            return False, f"model missing; run: ollama pull {self.model_name}"
        except Exception as exc:  # noqa: BLE001
            return False, f"cannot reach Ollama at localhost:11434 ({exc}). Start with: ollama serve"