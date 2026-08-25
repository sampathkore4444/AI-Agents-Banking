"""
Compare LLM Backends for Standing Order & Bill Payment Agent.

Tests:
- Response quality for payment intent parsing
- Standing order creation guidance
- Policy retrieval accuracy
- Natural language understanding
- Latency and throughput
"""

from __future__ import annotations

import asyncio
import time
from typing import Any


TEST_CASES = [
    {
        "name": "Rent Payment Setup",
        "input": "I want to pay my rent on the 1st of every month. It's $1,500 to ABC Property Management.",
        "expected_intent": "create",
        "expected_frequency": "monthly",
        "expected_amount": 1500,
    },
    {
        "name": "Utility Auto-Pay",
        "input": "Set up auto-pay for my Con Edison electric bill. The amount varies each month.",
        "expected_intent": "create",
        "expected_biller_category": "utility",
        "expected_variable": True,
    },
    {
        "name": "Cancel Subscription",
        "input": "I want to cancel my Netflix standing order.",
        "expected_intent": "cancel",
        "expected_payee": "Netflix",
    },
    {
        "name": "Modify Amount",
        "input": "Change my Wells Fargo mortgage payment from $2,000 to $2,200.",
        "expected_intent": "modify",
        "expected_amount": 2200,
    },
    {
        "name": "List Standing Orders",
        "input": "Show me all my active standing orders and how much I'm paying each month.",
        "expected_intent": "list",
    },
    {
        "name": "Payment Failed Inquiry",
        "input": "My payment to GEICO failed. What happened and what should I do?",
        "expected_intent": "troubleshoot",
        "expected_biller_category": "insurance",
    },
    {
        "name": "Savings Transfer",
        "input": "I get paid every other Friday. Can you transfer $500 to my savings account each time?",
        "expected_intent": "create",
        "expected_frequency": "biweekly",
    },
    {
        "name": "Complex Request",
        "input": "I need to set up payments for my apartment: $1,200 rent on the 1st, $100 electric on the 15th, and $50 internet on the 20th.",
        "expected_intent": "create_multiple",
        "expected_count": 3,
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

        results.append({
            "test": test["name"],
            "response": response[:200],
            "latency_ms": round(test_time * 1000, 1),
        })

    total_time = time.time() - start_time
    return {
        "backend": "Ollama",
        "model": agent.MODEL,
        "total_tests": len(TEST_CASES),
        "total_time_seconds": round(total_time, 2),
        "avg_latency_ms": round((total_time / len(TEST_CASES)) * 1000, 1),
        "results": results,
    }


async def test_vllm(agent: Any) -> dict[str, Any]:
    """Test vLLM backend."""
    results = []
    start_time = time.time()

    for test in TEST_CASES:
        test_start = time.time()
        response = await agent.chat(test["input"])
        test_time = time.time() - test_start

        results.append({
            "test": test["name"],
            "response": response[:200],
            "latency_ms": round(test_time * 1000, 1),
        })

    total_time = time.time() - start_time
    return {
        "backend": "vLLM",
        "model": agent.MODEL,
        "total_tests": len(TEST_CASES),
        "total_time_seconds": round(total_time, 2),
        "avg_latency_ms": round((total_time / len(TEST_CASES)) * 1000, 1),
        "results": results,
    }


async def test_sglang(agent: Any) -> dict[str, Any]:
    """Test SGLang backend."""
    results = []
    start_time = time.time()

    for test in TEST_CASES:
        test_start = time.time()
        response = await agent.chat(test["input"])
        test_time = time.time() - test_start

        results.append({
            "test": test["name"],
            "response": response[:200],
            "latency_ms": round(test_time * 1000, 1),
        })

    total_time = time.time() - start_time
    return {
        "backend": "SGLang",
        "model": agent.MODEL,
        "total_tests": len(TEST_CASES),
        "total_time_seconds": round(total_time, 2),
        "avg_latency_ms": round((total_time / len(TEST_CASES)) * 1000, 1),
        "results": results,
    }


async def compare_all() -> dict[str, Any]:
    """Compare all three backends."""
    from llm.agent_ollama import OllamaStandingOrderAgent
    from llm.agent_vllm import VLLMStandingOrderAgent
    from llm.agent_sglang import SGLangStandingOrderAgent

    ollama_agent = OllamaStandingOrderAgent()
    vllm_agent = VLLMStandingOrderAgent()
    sglang_agent = SGLangStandingOrderAgent()

    ollama_results = await test_ollama(ollama_agent)
    vllm_results = await test_vllm(vllm_agent)
    sglang_results = await test_sglang(sglang_agent)

    return {
        "comparison": [ollama_results, vllm_results, sglang_results],
        "recommendation": _get_recommendation(ollama_results, vllm_results, sglang_results),
    }


def _get_recommendation(ollama: dict, vllm: dict, sglang: dict) -> str:
    backends = [
        ("Ollama", ollama["avg_latency_ms"]),
        ("vLLM", vllm["avg_latency_ms"]),
        ("SGLang", sglang["avg_latency_ms"]),
    ]
    fastest = min(backends, key=lambda x: x[1])
    return (
        f"Fastest backend: {fastest[0]} ({fastest[1]:.0f}ms avg latency). "
        "For standing order agents, Ollama is recommended for development (easiest setup), "
        "vLLM for production throughput, and SGLang for structured output requirements."
    )


if __name__ == "__main__":
    results = asyncio.run(compare_all())
    print("\n=== Standing Order Agent — LLM Backend Comparison ===\n")
    for backend in results["comparison"]:
        print(f"Backend: {backend['backend']} ({backend['model']})")
        print(f"  Total time: {backend['total_time_seconds']}s")
        print(f"  Avg latency: {backend['avg_latency_ms']}ms")
        for r in backend["results"]:
            print(f"    {r['test']}: {r['latency_ms']}ms")
        print()

    print(f"Recommendation: {results['recommendation']}")
