"""
vLLM Backend for Financial Statement Analysis Agent.
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


class VLLMFinancialAnalysisAgent:
    """Financial analysis agent using vLLM for high-throughput inference."""

    MODEL = "meta-llama/Llama-3.1-8B-Instruct"

    SYSTEM_PROMPT = """You are a Financial Statement Analysis Agent for a bank.

Your role: Analyze financial statements for credit assessment, audit support, and investment due diligence.

Capabilities:
- Parse balance sheets, income statements, and cash flow statements
- Calculate financial ratios (liquidity, leverage, profitability, efficiency)
- Perform DuPont analysis and Altman Z-Score calculations
- Compare against industry benchmarks and peers
- Detect financial deterioration trends
- Check GAAP compliance
- Generate executive summaries

Guidelines:
- Always validate data before analysis
- Use industry context when interpreting ratios
- Clearly state assumptions and limitations
- Highlight material findings prominently
- Distinguish facts from analytical judgments
"""

    def __init__(self, base_url: str = "http://localhost:8000", model: str | None = None) -> None:
        self.base_url = base_url
        self.model = model or self.MODEL
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None and HTTPX_AVAILABLE:
            self._client = _httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self._client

    async def chat(self, message: str, context: str = "", history: list[dict] | None = None) -> str:
        """Chat via vLLM."""
        client = self._get_client()
        if client is None:
            return f"[vLLM Simulated] Financial analysis request received. In production, processed by {self.MODEL}."

        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-10:])
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": message})

        try:
            response = await client.post("/v1/chat/completions", json={"model": self.model, "messages": messages, "max_tokens": 1000, "temperature": 0.3})
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"vLLM error: {e}")
            return f"[vLLM Error] {e}"

    async def batch_analyze(self, requests: list[dict]) -> list[str]:
        """Batch process multiple financial analyses (vLLM advantage)."""
        results = []
        for req in requests:
            results.append(await self.chat(str(req)))
        return results
