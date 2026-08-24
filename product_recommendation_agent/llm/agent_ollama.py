"""
Ollama Agent Backend — Product Recommendations using Ollama.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from base_agent import ProductRecommendationAgent

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"


class OllamaLLMClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL) -> None:
        self.base_url = base_url
        self.model = model

    async def chat_completions_create(self, model: str, messages: list[dict], max_tokens: int = 1000, temperature: float = 0.3) -> Any:
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


class OllamaRecommendationAgent(ProductRecommendationAgent):
    def __init__(self, model: str = OLLAMA_MODEL) -> None:
        llm_client = OllamaLLMClient(model=model)
        super().__init__(llm_client=llm_client, model_name=model)
        self.model_name = model


async def main() -> None:
    agent = OllamaRecommendationAgent()
    print("Product Recommendation Agent (Ollama)")
    print(f"Model: {agent.model_name}")
    print("Commands: recommend <customer_json> <product_json>, history, quit\n")

    loop = asyncio.get_event_loop()
    while True:
        try:
            user_input = await loop.run_in_executor(None, lambda: input("rec> "))
        except (EOFError, KeyboardInterrupt):
            break

        parts = user_input.strip().split(maxsplit=1)
        if not parts:
            continue
        cmd = parts[0].lower()

        if cmd == "quit":
            break
        elif cmd == "recommend" and len(parts) > 1:
            try:
                args = parts[1].split("} ", 1)
                if len(args) == 2:
                    customer = json.loads(args[0] + "}")
                    product = json.loads(args[1])
                    result = await agent.generate_recommendation(customer, product)
                    print(json.dumps(result, indent=2))
                else:
                    print("Usage: recommend {customer_json} {product_json}")
            except json.JSONDecodeError:
                print("Invalid JSON")
        elif cmd == "history":
            print(agent.memory.get_context())
        else:
            print("Commands: recommend <customer> <product>, history, quit")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
