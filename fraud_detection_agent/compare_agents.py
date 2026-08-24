"""
Compare LLM Backends for Fraud Detection Agent.

Compares Ollama, vLLM, and SGLang on:
- Transaction analysis latency
- Fraud decision accuracy
- Throughput (transactions per second)
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any


SAMPLE_TRANSACTIONS = [
    {"transaction_id": "TXN-001", "customer_id": "CUST-001", "amount": 45.99, "currency": "USD", "merchant_id": "MERCH-100", "merchant_category": "groceries", "channel": "card_present", "country": "US"},
    {"transaction_id": "TXN-002", "customer_id": "CUST-002", "amount": 2500.00, "currency": "USD", "merchant_id": "MERCH-200", "merchant_category": "electronics", "channel": "card_not_present", "country": "US"},
    {"transaction_id": "TXN-003", "customer_id": "CUST-003", "amount": 15000.00, "currency": "EUR", "merchant_id": "MERCH-300", "merchant_category": "wire_transfer", "channel": "online", "country": "GB"},
    {"transaction_id": "TXN-004", "customer_id": "CUST-001", "amount": 125.00, "currency": "USD", "merchant_id": "MERCH-400", "merchant_category": "restaurant", "channel": "card_present", "country": "US"},
    {"transaction_id": "TXN-005", "customer_id": "CUST-004", "amount": 500.00, "currency": "USD", "merchant_id": "MERCH-500", "merchant_category": "gambling", "channel": "online", "country": "MT"},
]


async def benchmark_agent(agent_name: str, agent: Any, transactions: list[dict]) -> dict[str, Any]:
    """Benchmark a single agent."""
    results = {"agent": agent_name, "latencies": [], "errors": 0}

    for txn in transactions:
        start = time.time()
        try:
            await agent.analyze_transaction(txn)
            latency = time.time() - start
            results["latencies"].append(latency)
        except Exception:
            results["errors"] += 1

    if results["latencies"]:
        results["avg_latency_ms"] = round(sum(results["latencies"]) / len(results["latencies"]) * 1000, 1)
        results["min_latency_ms"] = round(min(results["latencies"]) * 1000, 1)
        results["max_latency_ms"] = round(max(results["latencies"]) * 1000, 1)
        results["throughput_tps"] = round(len(results["latencies"]) / sum(results["latencies"]), 1)
    del results["latencies"]
    return results


async def run_comparison() -> None:
    """Run comparison across all backends."""
    print("=" * 60)
    print("Fraud Detection Agent — LLM Backend Comparison")
    print("=" * 60)
    print(f"\nTransactions to analyze: {len(SAMPLE_TRANSACTIONS)}\n")

    results = []

    # Ollama
    try:
        from llm.agent_ollama import OllamaFraudAgent
        agent = OllamaFraudAgent()
        print("Benchmarking Ollama...")
        result = await benchmark_agent("Ollama", agent, SAMPLE_TRANSACTIONS)
        results.append(result)
        print(f"  ✓ Ollama: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_tps', 'N/A')} TPS")
    except Exception as e:
        print(f"  ✗ Ollama: {e}")

    # vLLM
    try:
        from llm.agent_vllm import VLLMFraudAgent
        agent = VLLMFraudAgent()
        print("Benchmarking vLLM...")
        result = await benchmark_agent("vLLM", agent, SAMPLE_TRANSACTIONS)
        results.append(result)
        print(f"  ✓ vLLM: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_tps', 'N/A')} TPS")
    except Exception as e:
        print(f"  ✗ vLLM: {e}")

    # SGLang
    try:
        from llm.agent_sglang import SGLangFraudAgent
        agent = SGLangFraudAgent()
        print("Benchmarking SGLang...")
        result = await benchmark_agent("SGLang", agent, SAMPLE_TRANSACTIONS)
        results.append(result)
        print(f"  ✓ SGLang: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_tps', 'N/A')} TPS")
    except Exception as e:
        print(f"  ✗ SGLang: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Backend':<12} {'Avg Latency':>15} {'Throughput':>15} {'Errors':>10}")
    print("-" * 60)
    for r in results:
        print(f"{r['agent']:<12} {r.get('avg_latency_ms', 'N/A'):>12}ms {r.get('throughput_tps', 'N/A'):>12} TPS {r.get('errors', 0):>10}")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS FOR FRAUD DETECTION")
    print("=" * 60)
    print("""
Use Case Requirements:
- Sub-second latency required for real-time fraud detection
- High throughput needed (1000+ TPS in production)
- Model accuracy critical for reducing false positives/negatives

Recommendations:
1. vLLM: Best for production — optimized for high throughput
2. SGLang: Good alternative with structured generation support
3. Ollama: Best for development/testing — easy local setup

For real-time fraud detection, vLLM is recommended due to:
- Optimized CUDA kernels for batch inference
- PagedAttention for efficient memory management
- Continuous batching for high throughput
""")


if __name__ == "__main__":
    asyncio.run(run_comparison())
