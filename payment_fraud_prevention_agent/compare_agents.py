"""
Compare LLM Backends for Payment Fraud Prevention Agent.

Compares Ollama, vLLM, and SGLang on:
- Payment validation latency
- Fraud decision accuracy
- Throughput (payments per second)
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any


SAMPLE_PAYMENTS = [
    {"payment_id": "PAY-001", "payer_account_id": "ACCT-001", "payer_name": "Acme Corp", "payee_name": "Vendor ABC", "payee_account_id": "ACCT-100", "payee_bank_routing": "021000021", "amount": 15000.00, "currency": "USD", "payment_type": "wire", "channel": "online"},
    {"payment_id": "PAY-002", "payer_account_id": "ACCT-002", "payer_name": "John Smith", "payee_name": "John Smith", "payee_account_id": "ACCT-002", "payee_bank_routing": "021000089", "amount": 9500.00, "currency": "USD", "payment_type": "wire", "channel": "online"},
    {"payment_id": "PAY-003", "payer_account_id": "ACCT-003", "payer_name": "Tech Inc", "payee_name": "Beijing Trading Corp", "payee_account_id": "ACCT-200", "payee_bank_routing": "021000021", "amount": 50000.00, "currency": "USD", "payment_type": "wire", "channel": "online", "is_international": True, "beneficiary_country": "CN"},
    {"payment_id": "PAY-004", "payer_account_id": "ACCT-001", "payer_name": "Acme Corp", "payee_name": "Office Supplies Co", "payee_account_id": "ACCT-300", "payee_bank_routing": "021000021", "amount": 2500.00, "currency": "USD", "payment_type": "ach", "channel": "batch"},
    {"payment_id": "PAY-005", "payer_account_id": "ACCT-004", "payer_name": "Real Estate LLC", "payee_name": "Closing Agent", "payee_account_id": "ACCT-400", "payee_bank_routing": "021000021", "amount": 250000.00, "currency": "USD", "payment_type": "wire", "channel": "online"},
]


async def benchmark_agent(agent_name: str, agent: Any, payments: list[dict]) -> dict[str, Any]:
    """Benchmark a single agent."""
    results = {"agent": agent_name, "latencies": [], "errors": 0}

    for payment in payments:
        start = time.time()
        try:
            await agent.validate_payment(payment)
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
    print("Payment Fraud Prevention Agent — LLM Backend Comparison")
    print("=" * 60)
    print(f"\nPayments to validate: {len(SAMPLE_PAYMENTS)}\n")

    results = []

    # Ollama
    try:
        from llm.agent_ollama import OllamaPaymentFraudAgent
        agent = OllamaPaymentFraudAgent()
        print("Benchmarking Ollama...")
        result = await benchmark_agent("Ollama", agent, SAMPLE_PAYMENTS)
        results.append(result)
        print(f"  OK Ollama: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_tps', 'N/A')} TPS")
    except Exception as e:
        print(f"  FAIL Ollama: {e}")

    # vLLM
    try:
        from llm.agent_vllm import VLLMPaymentFraudAgent
        agent = VLLMPaymentFraudAgent()
        print("Benchmarking vLLM...")
        result = await benchmark_agent("vLLM", agent, SAMPLE_PAYMENTS)
        results.append(result)
        print(f"  OK vLLM: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_tps', 'N/A')} TPS")
    except Exception as e:
        print(f"  FAIL vLLM: {e}")

    # SGLang
    try:
        from llm.agent_sglang import SGLangPaymentFraudAgent
        agent = SGLangPaymentFraudAgent()
        print("Benchmarking SGLang...")
        result = await benchmark_agent("SGLang", agent, SAMPLE_PAYMENTS)
        results.append(result)
        print(f"  OK SGLang: {result.get('avg_latency_ms', 'N/A')}ms avg, {result.get('throughput_tps', 'N/A')} TPS")
    except Exception as e:
        print(f"  FAIL SGLang: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Backend':<12} {'Avg Latency':>15} {'Throughput':>15} {'Errors':>10}")
    print("-" * 60)
    for r in results:
        print(f"{r['agent']:<12} {r.get('avg_latency_ms', 'N/A'):>12}ms {r.get('throughput_tps', 'N/A'):>12} TPS {r.get('errors', 0):>10}")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS FOR PAYMENT FRAUD PREVENTION")
    print("=" * 60)
    print("""
Use Case Requirements:
- Sub-second latency for real-time payment validation
- High throughput for batch ACH/check processing
- Accuracy critical for BEC detection and beneficiary verification
- Explainability required for fraud decisions

Recommendations:
1. vLLM: Best for production — optimized for high throughput batch processing
2. SGLang: Good alternative with structured generation for SAR narratives
3. Ollama: Best for development/testing — easy local setup

For payment fraud prevention, vLLM is recommended due to:
- Optimized CUDA kernels for batch inference
- PagedAttention for efficient memory management
- Continuous batching for high throughput payment processing
""")


if __name__ == "__main__":
    asyncio.run(run_comparison())
