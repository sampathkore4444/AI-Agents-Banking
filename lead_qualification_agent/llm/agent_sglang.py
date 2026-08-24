"""
SGLang Agent Backend — Lead Qualification using SGLang.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from base_agent import LeadQualificationAgent

logger = logging.getLogger(__name__)

SGLANG_BASE_URL = "http://localhost:30000"
SGLANG_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


class SGLangLLMClient:
    def __init__(self, base_url: str = SGLANG_BASE_URL, model: str = SGLANG_MODEL) -> None:
        self.base_url = base_url
        self.model = model

    async def chat_completions_create(self, model: str, messages: list[dict], max_tokens: int = 1000, temperature: float = 0.3) -> Any:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {"model": model or self.model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
            response = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            class Choice:
                def __init__(self, content: str) -> None:
                    self.message = type("Msg", (), {"content": content})()

            class Response:
                def __init__(self, content: str) -> None:
                    self.choices = [Choice(content)]

            return Response(data["choices"][0]["message"]["content"])


class SGLangQualificationAgent(LeadQualificationAgent):
    def __init__(self, model: str = SGLANG_MODEL) -> None:
        llm_client = SGLangLLMClient(model=model)
        super().__init__(llm_client=llm_client, model_name=model)
        self.model_name = model


async def main() -> None:
    agent = SGLangQualificationAgent()
    print("Lead Qualification Agent (SGLang)")
    print(f"Model: {agent.model_name}")
    print("Commands: qualify <lead_json>, history, quit\n")

    loop = asyncio.get_event_loop()
    while True:
        try:
            user_input = await loop.run_in_executor(None, lambda: input("qual> "))
        except (EOFError, KeyboardInterrupt):
            break

        parts = user_input.strip().split(maxsplit=1)
        if not parts:
            continue
        cmd = parts[0].lower()

        if cmd == "quit":
            break
        elif cmd == "qualify" and len(parts) > 1:
            try:
                lead = json.loads(parts[1])
                result = await agent.qualify_lead(lead)
                print(json.dumps(result, indent=2))
            except json.JSONDecodeError:
                print("Invalid JSON")
        elif cmd == "history":
            print(agent.memory.get_context())
        else:
            print("Commands: qualify <lead_json>, history, quit")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
