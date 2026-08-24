"""
Ollama Agent Backend — Real-Time Fraud Detection using Ollama.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

import httpx

from base_agent import FraudDetectionAgent

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"


class OllamaLLMClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL) -> None:
        self.base_url = base_url
        self.model = model

    async def chat_completions_create(self, model: str, messages: list[dict], max_tokens: int = 1000, temperature: float = 0.1) -> Any:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {"model": model or self.model, "messages": messages, "stream": False, "options": {"temperature": temperature, "num_predict": max_tokens}}
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            class Choice:
                def __init__(self, content: str) -> None:
                    self.message = type("Msg", (), {"content": content})()

            class Response:
                def __init__(self, content: str) -> None:
                    self.choices = [Choice(content)]

            return Response(data["message"]["content"])


class OllamaFraudAgent(FraudDetectionAgent):
    def __init__(self, model: str = OLLAMA_MODEL) -> None:
        llm_client = OllamaLLMClient(model=model)
        super().__init__(llm_client=llm_client, model_name=model)
        self.model_name = model


async def main() -> None:
    agent = OllamaFraudAgent()
    print("Real-Time Fraud Detection Agent (Ollama)")
    print(f"Model: {agent.model_name}")
    print("Commands: analyze <json>, decision <score> <txn_id> <cust_id>, history, quit\n")

    loop = asyncio.get_event_loop()
    while True:
        try:
            user_input = await loop.run_in_executor(None, lambda: input("fraud> "))
        except (EOFError, KeyboardInterrupt):
            break

        parts = user_input.strip().split(maxsplit=1)
        if not parts:
            continue
        cmd = parts[0].lower()

        if cmd == "quit":
            break
        elif cmd == "analyze" and len(parts) > 1:
            try:
                txn = json.loads(parts[1])
                result = await agent.analyze_transaction(txn)
                print(json.dumps(result, indent=2))
            except json.JSONDecodeError:
                print("Invalid JSON. Usage: analyze {\"transaction_id\": \"TXN-001\", ...}")
        elif cmd == "decision" and len(parts) > 1:
            args = parts[1].split()
            if len(args) >= 3:
                result = await agent.make_decision(int(args[0]), args[1], args[2])
                print(json.dumps(result, indent=2))
            else:
                print("Usage: decision <score> <txn_id> <customer_id>")
        elif cmd == "history":
            print(agent.memory.get_context())
        else:
            print("Commands: analyze <json>, decision <score> <txn_id> <cust_id>, history, quit")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
