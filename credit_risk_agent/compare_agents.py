"""
Compare all three LLM backends side by side.

Runs the same KYC query against Ollama, vLLM, and SGLang,
then displays results for comparison.

Usage:
    python compare_agents.py
"""

from __future__ import annotations

import asyncio
import logging
import time

from llm.agent_ollama import OllamaAgent
from llm.agent_vllm import VLLMAgent
from llm.agent_sglang import SGLangAgent

logging.basicConfig(level=logging.WARNING)

# ── Test queries ──────────────────────────────────────────────────
TEST_QUERIES = [
    "I want to open a business account for my UK limited company. What documents do I need?",
    "Check if John Smith is on any sanctions lists. He's a UK national born 1985-03-15.",
    "What's the risk level for a fintech company with complex ownership from a high-risk jurisdiction?",
]


async def run_agent(name: str, agent, query: str) -> dict:
    """Run a single agent with a query and return metrics."""
    start = time.time()
    try:
        response = await agent.run(query)
        duration = (time.time() - start) * 1000
        return {
            "agent": name,
            "status": "success",
            "answer": response.answer,
            "tools_called": [tc.name for tc in response.tool_calls],
            "tool_count": len(response.tool_calls),
            "duration_ms": duration,
            "tokens": response.tokens_used,
        }
    except Exception as e:
        duration = (time.time() - start) * 1000
        return {
            "agent": name,
            "status": "error",
            "error": str(e),
            "duration_ms": duration,
        }


async def compare():
    """Run comparison across all backends."""
    # Initialize agents
    agents = {
        "Ollama (llama3.1:8b)": OllamaAgent(model_name="llama3.1:8b"),
        "vLLM (Llama-3.1-8B)": VLLMAgent(model_name="meta-llama/Llama-3.1-8B-Instruct"),
        "SGLang (Llama-3.1-8B)": SGLangAgent(model_name="meta-llama/Llama-3.1-8B-Instruct"),
    }

    # Health checks
    print("=" * 70)
    print("KYC Agent — LLM Backend Comparison")
    print("=" * 70)
    print("\nChecking backend availability...\n")

    available = {}
    for name, agent in agents.items():
        try:
            health = await agent.health_check()
            status = "✓ Available" if health.get("status") == "healthy" else f"✗ {health.get('status', 'unknown')}"
            print(f"  {name}: {status}")
            if health.get("status") == "healthy":
                available[name] = agent
        except Exception as e:
            print(f"  {name}: ✗ Error: {e}")

    if not available:
        print("\nNo backends available. Start at least one:")
        print("  Ollama: ollama serve")
        print("  vLLM:   vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000")
        print("  SGLang: python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 30000")
        return

    # Run queries
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'=' * 70}")
        print(f"Query {i}: {query}")
        print("=" * 70)

        results = []
        for name, agent in available.items():
            print(f"\n  Running {name}...")
            result = await run_agent(name, agent, query)
            results.append(result)

        # Display results
        for r in results:
            print(f"\n  ┌─ {r['agent']} ({r['status']})")
            if r["status"] == "success":
                print(f"  │  Answer: {r['answer'][:200]}...")
                print(f"  │  Tools:  {r['tools_called']}")
                print(f"  │  Time:   {r['duration_ms']:.0f}ms")
                if r.get("tokens"):
                    print(f"  │  Tokens: prompt={r['tokens'].get('prompt_tokens', 0)}, "
                          f"completion={r['tokens'].get('completion_tokens', 0)}")
            else:
                print(f"  │  Error:  {r.get('error', 'unknown')}")
            print(f"  └{'─' * 50}")

    print(f"\n{'=' * 70}")
    print("Comparison complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(compare())
