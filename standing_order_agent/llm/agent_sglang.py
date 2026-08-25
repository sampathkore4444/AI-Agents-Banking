"""
SGLang Backend for Standing Order & Bill Payment Agent.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import httpx as _httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx package not installed. Install with: pip install httpx")


class SGLangStandingOrderAgent:
    """Standing order agent using SGLang for optimized inference."""

    MODEL = "meta-llama/Llama-3.1-8B-Instruct"

    SYSTEM_PROMPT = """You are a Standing Order & Bill Payment Agent for a bank.

Your role: Help customers manage recurring payments and bill pay schedules.

Capabilities:
- Set up, modify, or cancel standing orders
- Search and recommend billers
- Parse natural language payment requests
- Explain payment schedules and calendars
- Troubleshoot payment failures
- Ensure regulatory compliance (Reg E, NACHA)

Guidelines:
- Always confirm details before creating/modifying standing orders
- Explain any fees, limits, or restrictions clearly
- For amounts > $10,000, mention that manager approval may be needed
- Always provide standing order IDs for tracking
- Be helpful and patient with customers
"""

    def __init__(self, base_url: str = "http://localhost:30000", model: str | None = None) -> None:
        self.base_url = base_url
        self.model = model or self.MODEL
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None and HTTPX_AVAILABLE:
            self._client = _httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self._client

    async def chat(self, message: str, context: str = "", history: list[dict] | None = None) -> str:
        """Chat with the standing order agent via SGLang."""
        client = self._get_client()
        if client is None:
            return self._simulate_response(message)

        messages: list[dict[str, str]] = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if history:
            messages.extend(history[-10:])

        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})

        messages.append({"role": "user", "content": message})

        try:
            response = await client.post("/v1/chat/completions", json={
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.3,
            })
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"SGLang error: {e}")
            return self._simulate_response(message)

    async def structured_output(self, message: str, output_format: dict) -> dict[str, Any]:
        """Get structured output from SGLang (SGLang advantage)."""
        prompt = f"{message}\n\nReturn output in this format: {output_format}"
        response = await self.chat(prompt)
        try:
            import json
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            return {"raw_response": response, "format": output_format}

    def _simulate_response(self, message: str) -> str:
        """Simulate a response when SGLang is not available."""
        return f"[SGLang Simulated] I can help with your standing order request. In production, this would be processed by a {self.MODEL} model running on SGLang for optimized inference."
