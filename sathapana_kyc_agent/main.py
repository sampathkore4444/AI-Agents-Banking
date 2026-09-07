"""
Sathapana Bank KYC Onboarding Agent — CLI entrypoint.

Commands:
    python main.py seed                    Populate the NBC/Sathapana knowledge base.
    python main.py demo                    Run the end-to-end onboarding demo (no LLM needed).
    python main.py chat                    Interactive chat via a local Ollama model.
    python main.py serve [--transport stdio|tcp]   Start the (hardened) MCP server.
    python main.py serve-api [--port 8000]         Start the HTTP REST + OpenAPI (Swagger) server.
    python main.py eval-rag                Run the golden-set RAG evaluation.
    python main.py verify-audit            Verify the tamper-evident audit chain.
    python main.py providers               Show configured vendor provider adapters.
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

    transport = "tcp" if "--transport" in sys.argv and sys.argv[sys.argv.index("--transport") + 1] == "tcp" else None
    server.main(transport=transport)


def cmd_serve_api() -> None:
    import api_server

    args = sys.argv[2:]
    host = args[args.index("--host") + 1] if "--host" in args else "127.0.0.1"
    port = int(args[args.index("--port") + 1]) if "--port" in args else 8000
    api_server.serve(host=host, port=port, log_requests="--verbose" in args)


def cmd_eval_rag() -> None:
    import rag_eval

    rag_eval.print_rag_eval()


def cmd_verify_audit() -> None:
    result = db.verify_audit_chain()
    ok = result.get("ok")
    print(f"Audit chain: {'INTACT' if ok else 'TAMPERED'} ({result.get('rows_checked')} rows checked)")
    if not ok:
        print(f"  First bad entry id: {result.get('first_bad_id')}")
    if result.get("legacy_rows"):
        print(f"  Legacy (un-hashed) rows skipped: {result.get('legacy_rows')}")


def cmd_providers() -> None:
    from integrations import get_providers

    for kind, name in get_providers().summary().items():
        print(f"  {kind:12s} -> {name}")


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
    elif cmd == "serve-api":
        cmd_serve_api()
    elif cmd == "eval-rag":
        cmd_eval_rag()
    elif cmd == "verify-audit":
        cmd_verify_audit()
    elif cmd == "providers":
        cmd_providers()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()