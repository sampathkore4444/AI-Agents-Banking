"""
Sathapana Bank KYC Onboarding Agent — CLI entrypoint.

Commands:
    python main.py seed      Populate the NBC/Sathapana knowledge base.
    python main.py demo      Run the end-to-end onboarding demo (no LLM needed).
    python main.py chat      Interactive chat via a local Ollama model.
    python main.py serve     Start the MCP stdio server.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db


def cmd_seed() -> None:
    import seed_knowledge

    seed_knowledge.seed()


def cmd_demo() -> None:
    import runner

    runner.run_demo()


async def cmd_chat(model_name: str = "llama3.1:8b", auto_approve: bool = False) -> None:
    from llm.agent_ollama import OllamaAgent

    agent = OllamaAgent(model_name=model_name, auto_approve=auto_approve)
    ok, info = await agent.health_check()
    print(f"Ollama: {info}")
    if not ok:
        return
    print("Sathapana KYC Agent ready. Type 'quit' to exit.\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        response = await agent.run(query)
        print(f"\nAgent: {response.answer}\n")
        if response.tool_calls:
            print(f"  [tools: {[tc.name for tc in response.tool_calls]} | {response.total_duration_ms:.0f}ms]")


def cmd_serve() -> None:
    import server

    server.main()


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="[%(name)s] %(message)s")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    db.init_db()

    if cmd == "seed":
        cmd_seed()
    elif cmd == "demo":
        cmd_demo()
    elif cmd == "chat":
        model = sys.argv[2] if len(sys.argv) > 2 else "llama3.1:8b"
        auto_approve = "--auto-approve" in sys.argv
        asyncio.run(cmd_chat(model, auto_approve))
    elif cmd == "serve":
        cmd_serve()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()