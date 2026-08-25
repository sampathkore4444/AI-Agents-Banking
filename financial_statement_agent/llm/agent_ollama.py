"""
Ollama LLM Backend for Financial Statement Analysis Agent.
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


class OllamaFinancialAnalysisAgent:
    """Financial analysis agent using Ollama for local LLM inference."""

    MODEL = "llama3.1:8b"

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

    def __init__(self, model: str | None = None, base_url: str = "http://localhost:11434") -> None:
        self.model = model or self.MODEL
        self.base_url = base_url
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None and OLLAMA_AVAILABLE:
            self._client = _ollama.Client(host=self.base_url)
        return self._client

    async def chat(self, message: str, context: str = "", history: list[dict] | None = None) -> str:
        """Chat with the financial analysis agent."""
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

    async def analyze_financials(self, company_data: dict) -> str:
        """Analyze financial data using the LLM."""
        prompt = f"""Analyze these financial statements and provide:
1. Key ratio calculations
2. Strengths and weaknesses
3. Industry comparison
4. Risk assessment
5. Recommendation

Data: {company_data}"""
        return await self.chat(prompt)

    def _simulate_response(self, message: str) -> str:
        """Simulate a response when Ollama is not available."""
        lower = message.lower()
        if "ratio" in lower or "liquidity" in lower:
            return "For ratio analysis, I need the balance sheet and income statement data. Please provide: total current assets, total current liabilities, total assets, total liabilities, total equity, revenue, net income, and EBITDA."
        elif "benchmark" in lower or "industry" in lower:
            return "I can compare your company against industry benchmarks. Please specify the industry (technology, manufacturing, retail, financial, healthcare, or energy) and the metrics you'd like to compare."
        elif "z-score" in lower or "bankruptcy" in lower:
            return "For Altman Z-Score calculation, I need: working capital, retained earnings, EBIT, market value of equity, total liabilities, and total assets."
        else:
            return "I'm the Financial Statement Analysis Agent. I can help you analyze financial statements, calculate ratios, compare against benchmarks, and detect trends. What would you like to analyze?"
