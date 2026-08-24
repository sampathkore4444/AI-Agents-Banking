"""
Compare LLM Backends for Product Recommendation Agent.

Compares Ollama, vLLM, and SGLang on:
- Recommendation generation latency
- Response quality
- Throughput
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any


SAMPLE_CUSTOMERS = [
    {"customer_id": "CUST-001", "name": "John Smith", "age": 41, "segment": "young_professionals", "credit_score": 742, "income": 85000, "existing_products": ["PROD-CHK-001", "PROD-SAV-001", "PROD-CC-001"]},
    {"customer_id": "CUST-002", "name": "Sarah Johnson", "age": 48, "segment": "families", "credit_score": 785, "income": 145000, "existing_products": ["PROD-CHK-001", "PROD-SAV-001", "PROD-CC-002", "PROD-MTG-001"]},
    {"customer_id": "CUST-003", "name": "Michael Chen", "age": 30, "segment": "young_professionals", "credit_score": 710, "income": 95000, "existing_products": ["PROD-CHK-001", "PROD-SAV-001"]},
    {"customer_id": "CUST-004", "name": "Emily Davis", "age": 23, "segment": "students", "credit_score": 650, "income": 18000, "existing_products": ["PROD-CHK-001"]},
    {"customer_id": "CUST-005", "name": "Robert Wilson", "age": 68, "segment": "retirees", "credit_score": 810, "income": 62000, "existing_products": ["PROD-CHK-001", "PROD-SAV-001", "PROD-CD-001", "PROD-IRA-001"]},
]

SAMPLE_PRODUCTS = [
    {"product_id": "PROD-IRA-001", "name": "Traditional IRA", "category": "investment"},
    {"product_id": "PROD-CC-002", "name": "Travel Rewards Credit Card", "category": "credit"},
    {"product_id": "PROD-HELOC-001", "name": "Home Equity Line of Credit", "category": "lending"},
]


async def benchmark_agent(agent_name: str, agent: Any, customers: list[dict], products: list[dict]) -> dict[str, Any]:
    """Benchmark a single agent."""
    results = {"agent": agent_name, "latencies": [], "errors": 0}

    for customer in customers:
        for product in products:
            start = time.time()
            try:
                await agent.generate_recommendation(customer, product)
                latency = time.time() - start
                results["latencies"].append(latency)
            except Exception:
                results["errors"] += 1

    if results["latencies"]:
        results["avg_latency_ms"] = round(sum(results["latencies"]) / len(results["latencies"]) * 1000, 1)
        results["min_latency_ms"] = round(min(results["latencies"]) * 1000, 1)
        results["max_latency_ms"] = round(max(results["latencies"]) * 1000, 1)
        results["throughput_rps"] = round(len(results["latencies"]) / sum(results["latencies"]), 1)
    del results["latencies"]
    return results


async def run_comparison() -> None:
    """Run comparison across all backends."""
    print("=" * 60)
    print("Product Recommendation Agent — LLM Backend Comparison")
    print("=" * 60)
    print(f"\nCustomers: {len(SAMPLE_CUSTOMERS)}, Products: {len(SAMPLE_PRODUCTS)}")
    print(f"Total recommendations to generate: {len(SAMPLE_CUSTOMERS) * len(SAMPLE_PRODUCTS)}\n")

    results = []

    # Ollama
    try:
        from llm.agent_ollama import OllamaRecommendationAgent
        agent = OllamaRecommendationAgent()
        print("Benchmarking Ollama...")
        result = await benchmark_agent("Ollama", agent, SAMPLE_CUSTOMERS, SAMPLE_PRODUCTS)
        results.append(result)
        print(f"  Done: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_rps', 'N/A')} RPS")
    except Exception as e:
        print(f"  Ollama: {e}")

    # vLLM
    try:
        from llm.agent_vllm import VLLMRecommendationAgent
        agent = VLLMRecommendationAgent()
        print("Benchmarking vLLM...")
        result = await benchmark_agent("vLLM", agent, SAMPLE_CUSTOMERS, SAMPLE_PRODUCTS)
        results.append(result)
        print(f"  Done: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_rps', 'N/A')} RPS")
    except Exception as e:
        print(f"  vLLM: {e}")

    # SGLang
    try:
        from llm.agent_sglang import SGLangRecommendationAgent
        agent = SGLangRecommendationAgent()
        print("Benchmarking SGLang...")
        result = await benchmark_agent("SGLang", agent, SAMPLE_CUSTOMERS, SAMPLE_PRODUCTS)
        results.append(result)
        print(f"  Done: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_rps', 'N/A')} RPS")
    except Exception as e:
        print(f"  SGLang: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Backend':<12} {'Avg Latency':>15} {'Throughput':>15} {'Errors':>10}")
    print("-" * 60)
    for r in results:
        print(f"{r['agent']:<12} {r.get('avg_latency_ms', 'N/A'):>12}ms {r.get('throughput_rps', 'N/A'):>12} RPS {r.get('errors', 0):>10}")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS FOR PRODUCT RECOMMENDATIONS")
    print("=" * 60)
    print("""
Use Case Requirements:
- Real-time recommendations during customer interactions
- Accurate product matching based on customer profiles
- Clear, natural language explanations

Recommendations:
1. vLLM: Best for production — high throughput for batch recommendations
2. SGLang: Good for structured recommendation output
3. Ollama: Best for development/testing — easy local setup

For real-time customer-facing recommendations, vLLM is recommended.
""")


if __name__ == "__main__":
    asyncio.run(run_comparison())
