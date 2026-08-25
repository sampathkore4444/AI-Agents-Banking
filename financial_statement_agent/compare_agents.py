"""
Compare LLM Backends for Financial Statement Analysis Agent.

Tests:
- Financial ratio interpretation
- Industry benchmark analysis
- GAAP compliance assessment
- Credit risk evaluation
- Latency and throughput
"""

from __future__ import annotations

import asyncio
import time
from typing import Any


TEST_CASES = [
    {
        "name": "Liquidity Assessment",
        "input": "Company has current ratio 0.8, quick ratio 0.5, and negative working capital of $2M. Assess liquidity.",
        "expected_quality": "Should identify liquidity risk and recommend actions",
    },
    {
        "name": "Leverage Analysis",
        "input": "Debt-to-equity is 3.5, interest coverage is 1.2x, and debt/EBITDA is 4.5x. Evaluate solvency.",
        "expected_quality": "Should flag high leverage and potential covenant concerns",
    },
    {
        "name": "Profitability Trend",
        "input": "Gross margin declined from 45% to 32% over 3 years while revenue grew 20%. What does this indicate?",
        "expected_quality": "Should identify margin compression and competitive pressure",
    },
    {
        "name": "Z-Score Interpretation",
        "input": "Altman Z-Score is 1.6. What is the credit risk assessment?",
        "expected_quality": "Should identify distress zone and recommend enhanced monitoring",
    },
    {
        "name": "DuPont Decomposition",
        "input": "ROE is 25% but driven primarily by 4.0x equity multiplier. Analyze quality of returns.",
        "expected_quality": "Should note leverage-driven ROE vs organic profitability",
    },
    {
        "name": "GAAP Compliance",
        "input": "Balance sheet shows assets $500M, liabilities $300M, equity $180M. Is this GAAP compliant?",
        "expected_quality": "Should identify $20M imbalance and flag potential misstatement",
    },
    {
        "name": "Industry Comparison",
        "input": "Tech company has 55% gross margin vs industry median 48%. How does this compare?",
        "expected_quality": "Should note above-average gross margin and potential competitive advantage",
    },
    {
        "name": "Earnings Quality",
        "input": "Net income is $50M but CFO is $20M. What concerns should an analyst raise?",
        "expected_quality": "Should flag earnings quality issue and potential accrual manipulation",
    },
]


async def test_ollama(agent: Any) -> dict[str, Any]:
    """Test Ollama backend."""
    results = []
    start_time = time.time()
    for test in TEST_CASES:
        test_start = time.time()
        response = await agent.chat(test["input"])
        test_time = time.time() - test_start
        results.append({"test": test["name"], "response": response[:200], "latency_ms": round(test_time * 1000, 1)})
    total_time = time.time() - start_time
    return {"backend": "Ollama", "model": agent.MODEL, "total_tests": len(TEST_CASES), "total_time_seconds": round(total_time, 2), "avg_latency_ms": round((total_time / len(TEST_CASES)) * 1000, 1), "results": results}


async def test_vllm(agent: Any) -> dict[str, Any]:
    """Test vLLM backend."""
    results = []
    start_time = time.time()
    for test in TEST_CASES:
        test_start = time.time()
        response = await agent.chat(test["input"])
        test_time = time.time() - test_start
        results.append({"test": test["name"], "response": response[:200], "latency_ms": round(test_time * 1000, 1)})
    total_time = time.time() - start_time
    return {"backend": "vLLM", "model": agent.MODEL, "total_tests": len(TEST_CASES), "total_time_seconds": round(total_time, 2), "avg_latency_ms": round((total_time / len(TEST_CASES)) * 1000, 1), "results": results}


async def test_sglang(agent: Any) -> dict[str, Any]:
    """Test SGLang backend."""
    results = []
    start_time = time.time()
    for test in TEST_CASES:
        test_start = time.time()
        response = await agent.chat(test["input"])
        test_time = time.time() - test_start
        results.append({"test": test["name"], "response": response[:200], "latency_ms": round(test_time * 1000, 1)})
    total_time = time.time() - start_time
    return {"backend": "SGLang", "model": agent.MODEL, "total_tests": len(TEST_CASES), "total_time_seconds": round(total_time, 2), "avg_latency_ms": round((total_time / len(TEST_CASES)) * 1000, 1), "results": results}


async def compare_all() -> dict[str, Any]:
    """Compare all three backends."""
    from llm.agent_ollama import OllamaFinancialAnalysisAgent
    from llm.agent_vllm import VLLMFinancialAnalysisAgent
    from llm.agent_sglang import SGLangFinancialAnalysisAgent

    results = await asyncio.gather(
        test_ollama(OllamaFinancialAnalysisAgent()),
        test_vllm(VLLMFinancialAnalysisAgent()),
        test_sglang(SGLangFinancialAnalysisAgent()),
    )

    return {
        "comparison": list(results),
        "recommendation": "Ollama for development, vLLM for production throughput, SGLang for structured financial output (ratio tables, Z-Score components).",
    }


if __name__ == "__main__":
    results = asyncio.run(compare_all())
    print("\n=== Financial Statement Analysis Agent — LLM Backend Comparison ===\n")
    for backend in results["comparison"]:
        print(f"Backend: {backend['backend']} ({backend['model']})")
        print(f"  Avg latency: {backend['avg_latency_ms']}ms")
        print()
    print(f"Recommendation: {results['recommendation']}")
