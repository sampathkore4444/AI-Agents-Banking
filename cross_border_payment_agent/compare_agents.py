"""
Compare all three LLM backends side by side.

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

TEST_QUERIES = [
    "What's the current USD to GBP exchange rate and what fees apply for a wire to the UK?",
    "I need to send $50,000 to Japan. What's the routing, compliance requirements, and total cost?",
    "What are the OFAC sanctions screening requirements for USD payments?",
]


async def run_agent(name: str, agent, query: str) -> dict:
    start = time.time()
    try:
        response = await agent.run(query)
        duration = (time.time() - start) * 1000
        return {"agent": name, "status": "success", "answer": response.answer, "tools_called": [tc.name for tc in response.tool_calls], "tool_count": len(response.tool_calls), "duration_ms": duration, "tokens": response.tokens_used}
    except Exception as e:
        return {"agent": name, "status": "error", "error": str(e), "duration_ms": (time.time() - start) * 1000}


async def compare():
    agents = {
        "Ollama (llama3.1:8b)": OllamaAgent(model_name="llama3.1:8b"),
        "vLLM (Llama-3.1-8B)": VLLMAgent(model_name="meta-llama/Llama-3.1-8B-Instruct"),
        "SGLang (Llama-3.1-8B)": SGLangAgent(model_name="meta-llama/Llama-3.1-8B-Instruct"),
    }
    print("=" * 70)
    print("Cross-Border Payment Agent — LLM Backend Comparison")
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
        print("\nNo backends available. Start at least one.")
        return
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'=' * 70}\nQuery {i}: {query}\n{'=' * 70}")
        results = [await run_agent(name, agent, query) for name, agent in available.items()]
        for r in results:
            print(f"\n  ┌─ {r['agent']} ({r['status']})")
            if r["status"] == "success":
                print(f"  │  Answer: {r['answer'][:200]}...")
                print(f"  │  Tools:  {r['tools_called']}")
                print(f"  │  Time:   {r['duration_ms']:.0f}ms")
            else:
                print(f"  │  Error:  {r.get('error', 'unknown')}")
            print(f"  └{'─' * 50}")
    print(f"\n{'=' * 70}\nComparison complete!\n{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(compare())
