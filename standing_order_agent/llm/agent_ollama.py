"""
Ollama LLM Backend for Standing Order & Bill Payment Agent.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import ollama as _ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("ollama package not installed. Install with: pip install ollama")


class OllamaStandingOrderAgent:
    """Standing order agent using Ollama for local LLM inference."""

    MODEL = "llama3.1:8b"

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

    def __init__(self, model: str | None = None, base_url: str = "http://localhost:11434") -> None:
        self.model = model or self.MODEL
        self.base_url = base_url
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None and OLLAMA_AVAILABLE:
            self._client = _ollama.Client(host=self.base_url)
        return self._client

    async def chat(self, message: str, context: str = "", history: list[dict] | None = None) -> str:
        """Chat with the standing order agent."""
        client = self._get_client()
        if client is None:
            return self._simulate_response(message)

        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if history:
            messages.extend(history[-10:])

        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})

        messages.append({"role": "user", "content": message})

        try:
            response = client.chat(model=self.model, messages=messages, options={"temperature": 0.3, "num_predict": 1000})
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._simulate_response(message)

    async def parse_payment_request(self, request: str) -> dict[str, Any]:
        """Parse a natural language payment request."""
        prompt = f"""Parse this payment request into structured data. Return JSON:
{{
    "intent": "create|modify|cancel|list",
    "payee_name": "string or null",
    "amount": number or null,
    "frequency": "daily|weekly|biweekly|monthly|quarterly|annual" or null,
    "day_of_month": number or null,
    "start_date": "YYYY-MM-DD" or null,
    "confidence": 0.0-1.0
}}

Request: {request}"""
        response = await self.chat(prompt)
        try:
            import json
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            return {"intent": "unknown", "confidence": 0.0, "raw": response}

    def _simulate_response(self, message: str) -> str:
        """Simulate a response when Ollama is not available."""
        lower = message.lower()
        if "rent" in lower and ("pay" in lower or "set up" in lower):
            return "I can help you set up a rent payment. I'll create a monthly standing order for the 1st of each month. Please provide: 1) Payee name (landlord/property manager), 2) Payment amount, 3) Source account, 4) Payee bank details."
        elif "cancel" in lower:
            return "I can help you cancel a standing order. Please provide the standing order ID or the payee name you'd like to cancel."
        elif "list" in lower or "show" in lower:
            return "I'll retrieve your active standing orders. Please provide your account ID."
        else:
            return "I'm the Standing Order & Bill Payment Agent. I can help you with: creating new standing orders, modifying existing ones, cancelling payments, searching for billers, and checking payment schedules. What would you like to do?"
