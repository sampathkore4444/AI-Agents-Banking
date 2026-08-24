"""
Compare LLM Backends for Lead Qualification Agent.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any


SAMPLE_LEADS = [
    {"lead_id": "LEAD-001", "first_name": "John", "last_name": "Smith", "email": "john@email.com", "phone": "+1-555-0101", "source": "website", "product_interest": "mortgage", "demographics": {"age": 35, "income": 95000, "credit_score": 720}},
    {"lead_id": "LEAD-002", "first_name": "Sarah", "last_name": "Johnson", "email": "sarah@email.com", "phone": "+1-555-0102", "source": "referral", "product_interest": "savings", "demographics": {"age": 42, "income": 120000, "credit_score": 780}},
    {"lead_id": "LEAD-003", "first_name": "Michael", "last_name": "Chen", "email": "m.chen@email.com", "phone": "+1-555-0103", "source": "chat", "product_interest": "credit_card", "demographics": {"age": 30, "income": 85000, "credit_score": 705}},
]


async def benchmark_agent(agent_name: str, agent: Any, leads: list[dict]) -> dict[str, Any]:
    """Benchmark a single agent."""
    results = {"agent": agent_name, "latencies": [], "errors": 0}

    for lead in leads:
        start = time.time()
        try:
            await agent.qualify_lead(lead)
            latency = time.time() - start
            results["latencies"].append(latency)
        except Exception:
            results["errors"] += 1

    if results["latencies"]:
        results["avg_latency_ms"] = round(sum(results["latencies"]) / len(results["latencies"]) * 1000, 1)
        results["min_latency_ms"] = round(min(results["latencies"]) * 1000, 1)
        results["max_latency_ms"] = round(max(results["latencies"]) * 1000, 1)
        results["throughput_qps"] = round(len(results["latencies"]) / sum(results["latencies"]), 1)
    del results["latencies"]
    return results


async def run_comparison() -> None:
    """Run comparison across all backends."""
    print("=" * 60)
    print("Lead Qualification Agent — LLM Backend Comparison")
    print("=" * 60)
    print(f"\nLeads to qualify: {len(SAMPLE_LEADS)}\n")

    results = []

    try:
        from llm.agent_ollama import OllamaQualificationAgent
        agent = OllamaQualificationAgent()
        print("Benchmarking Ollama...")
        result = await benchmark_agent("Ollama", agent, SAMPLE_LEADS)
        results.append(result)
        print(f"  Done: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_qps', 'N/A')} QPS")
    except Exception as e:
        print(f"  Ollama: {e}")

    try:
        from llm.agent_vllm import VLLMQualificationAgent
        agent = VLLMQualificationAgent()
        print("Benchmarking vLLM...")
        result = await benchmark_agent("vLLM", agent, SAMPLE_LEADS)
        results.append(result)
        print(f"  Done: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_qps', 'N/A')} QPS")
    except Exception as e:
        print(f"  vLLM: {e}")

    try:
        from llm.agent_sglang import SGLangQualificationAgent
        agent = SGLangQualificationAgent()
        print("Benchmarking SGLang...")
        result = await benchmark_agent("SGLang", agent, SAMPLE_LEADS)
        results.append(result)
        print(f"  Done: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_qps', 'N/A')} QPS")
    except Exception as e:
        print(f"  SGLang: {e}")

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Backend':<12} {'Avg Latency':>15} {'Throughput':>15} {'Errors':>10}")
    print("-" * 60)
    for r in results:
        print(f"{r['agent']:<12} {r.get('avg_latency_ms', 'N/A'):>12}ms {r.get('throughput_qps', 'N/A'):>12} QPS {r.get('errors', 0):>10}")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS FOR LEAD QUALIFICATION")
    print("=" * 60)
    print("""
Use Case Requirements:
- Fast qualification during live conversations
- Accurate intent detection and scoring
- Natural conversation flow

Recommendations:
1. vLLM: Best for production — low latency for live conversations
2. SGLang: Good for structured qualification output
3. Ollama: Best for development/testing — easy local setup

For live qualification conversations, vLLM is recommended.
""")


if __name__ == "__main__":
    asyncio.run(run_comparison())
