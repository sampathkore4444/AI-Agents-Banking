"""
Base Agent — orchestration for the Sathapana KYC agent.

Implements the agent loop: intent routing, RAG-backed answers, tool
execution with guardrails, human-in-the-loop approval for high-risk
actions, conversation memory, audit logging, and tracing.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import db
from tools import get_rag, get_registry

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    result: dict | None = None
    error: str | None = None
    duration_ms: float = 0.0
    risk_level: str = "safe"
    approved: bool = False
    approval_reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AgentStep:
    step_number: int
    thought: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    observation: str = ""
    is_final: bool = False
    duration_ms: float = 0.0


@dataclass
class AgentResponse:
    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    total_duration_ms: float = 0.0
    rag_sources: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════
#  GUARDRAILS & APPROVALS
# ══════════════════════════════════════════════════════════════════

class Guardrails:
    """Tool risk gating and output sanitisation."""

    SENSITIVE_PATTERNS = [
        (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[CARD_REDACTED]"),
        (re.compile(r"(?i)\b(phone|mobile|tel|mob)\b\s*[:=]?\s*\+?\d[\d\s]{6,}\b"), "[PHONE_REDACTED]"),
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
        (re.compile(r"\b\d{9,10}\b"), "[ID_REDACTED]"),
    ]

    HIGH_RISK_TOOLS = {"create_customer_profile", "open_account", "update_case"}

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.HIGH_RISK_TOOLS

    def check_output(self, text: str) -> tuple[bool, str]:
        for pattern, label in self.SENSITIVE_PATTERNS:
            if pattern.search(text):
                return False, f"Output may contain sensitive data: {label}"
        return True, "OK"

    def redact(self, text: str) -> str:
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


class ApprovalManager:
    """Human-in-the-loop approval for high-risk tool calls."""

    def __init__(self, auto_approve: bool = False) -> None:
        self.auto_approve = auto_approve
        self.pending: dict[str, dict] = {}
        self.decisions: dict[str, bool] = {}

    def request_approval(self, tool_call: ToolCall) -> tuple[bool, str]:
        approval_id = str(uuid.uuid4())[:8]
        if self.auto_approve:
            tool_call.approved = True
            return True, "Auto-approved (dev mode)"
        print(f"\n  [AUDIT] Approval required for '{tool_call.name}': {json.dumps(tool_call.arguments)[:200]}")
        choice = input("  Approve? (yes/no) [yes]: ").strip().lower()
        approved = choice in ("", "yes", "y", "1")
        self.decisions[approval_id] = approved
        self.pending.pop(approval_id, None)
        tool_call.approved = approved
        tool_call.approval_reason = "Approved by officer" if approved else "Rejected by officer"
        return approved, tool_call.approval_reason


# ══════════════════════════════════════════════════════════════════
#  MEMORY
# ══════════════════════════════════════════════════════════════════

class ConversationMemory:
    """Sliding-window conversation history with token estimates."""

    def __init__(self, max_tokens: int = 8000, max_messages: int = 40) -> None:
        self.messages: list[dict] = []
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.total_tokens = 0

    @staticmethod
    def _estimate(text: str) -> int:
        return len(text) // 4

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.total_tokens += self._estimate(content)
        self._trim()

    def _trim(self) -> None:
        while (self.total_tokens > self.max_tokens or len(self.messages) > self.max_messages) and len(self.messages) > 6:
            removed = self.messages.pop(1)
            self.total_tokens -= self._estimate(removed["content"])

    def context(self) -> list[dict]:
        return list(self.messages)

    def usage(self) -> dict:
        return {"messages": len(self.messages), "tokens": self.total_tokens, "max_tokens": self.max_tokens}


# ══════════════════════════════════════════════════════════════════
#  BASE AGENT
# ══════════════════════════════════════════════════════════════════

class BaseAgent(ABC):
    """ReAct agent loop with guardrails, approvals, memory, and audit."""

    def __init__(
        self,
        model_name: str = "",
        max_steps: int = 10,
        auto_approve: bool = False,
        run_id: str = "runner",
    ) -> None:
        self.model_name = model_name
        self.max_steps = max_steps
        self.run_id = run_id
        self.registry = get_registry()
        self.memory = ConversationMemory()
        self.guardrails = Guardrails()
        self.approvals = ApprovalManager(auto_approve=auto_approve)

    # ── LLM backend ───────────────────────────────────────────────
    @abstractmethod
    async def call_llm(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Call the LLM backend. Returns standard dict with content/tool_calls."""

    # ── tool execution ────────────────────────────────────────────
    async def execute_tool(self, tool_call: ToolCall) -> ToolCall:
        start = time.time()
        risk = self.registry.risk(tool_call.name)
        tool_call.risk_level = risk

        if self.guardrails.requires_approval(tool_call.name):
            approved, reason = self.approvals.request_approval(tool_call)
            if not approved:
                tool_call.error = f"Rejected by officer: {reason}"
                db.log_action(self.run_id, f"tool:{tool_call.name}", {"arguments": tool_call.arguments, "error": tool_call.error}, "rejected")
                return tool_call
            db.log_action(self.run_id, f"approval:{tool_call.name}", {"decision": "approved"}, "ok")

        result = self.registry.invoke(tool_call.name, tool_call.arguments)
        tool_call.duration_ms = (time.time() - start) * 1000
        if "error" in result:
            tool_call.error = str(result["error"])
        else:
            tool_call.result = result
        db.log_action(self.run_id, f"tool:{tool_call.name}", {"arguments": tool_call.arguments, "result": result, "risk": risk}, "error" if tool_call.error else "ok")
        return tool_call

    # ── simple RAG route (no LLM) ─────────────────────────────────
    def _simple_rag_response(self, query: str) -> AgentResponse:
        rag = get_rag()
        result = rag.query(query, top_k=5)
        parts = []
        for i, chunk in enumerate(result.chunks, 1):
            source = chunk.metadata.get("source", chunk.metadata.get("product", chunk.collection))
            parts.append(f"{i}. ({source}) {chunk.text}")
        return AgentResponse(
            answer="Based on the Sathapana/NBC knowledge base:\n\n" + "\n\n".join(parts),
            rag_sources=[{"text": c.text[:200], "score": round(c.score, 3), "source": c.metadata.get("source", "nbc")} for c in result.chunks],
            metrics={"route": "simple_rag", "chunks": len(result.chunks)},
        )

    # ── main loop ─────────────────────────────────────────────────
    async def run(self, user_query: str) -> AgentResponse:
        trace_start = time.time()
        self.memory = ConversationMemory()
        self.memory.add("user", user_query)

        if re.search(r"(?i)(what|how|rules|requirements|documents|policy|regulation)", user_query) and "process" not in user_query.lower():
            resp = self._simple_rag_response(user_query)
            resp.total_duration_ms = (time.time() - trace_start) * 1000
            return resp

        system_prompt = (
            "You are the Sathapana Bank KYC Onboarding Agent operating under NBC "
            "regulations and the Cambodia AML/CFT Law 2020. Available tools:\n"
            + self.registry.descriptions()
            + "\n\nRules:\n"
            "1. Retrieve NBC knowledge (knowledge_search) before making decisions.\n"
            "2. Screen sanctions and PEPs for every customer before onboarding.\n"
            "3. Screen beneficial owners for legal persons (default 25%, risk-based 10%).\n"
            "4. Medium/high risk -> open a compliance case; escalating gambling/cash-intensive sectors and PEPs to EDD.\n"
            "5. Sanctions hit -> onboarding prohibited, notify CAMFIU.\n"
            "6. High-risk tools (create_customer_profile, open_account, update_case) require officer approval.\n"
            "7. Never fabricate; cite the knowledge source. Responses must pass audit."
        )

        steps: list[AgentStep] = []
        all_calls: list[ToolCall] = []
        rag_sources: list[dict] = []
        final_answer = "I was unable to complete the request."

        for step_num in range(1, self.max_steps + 1):
            step = AgentStep(step_number=step_num, thought="")
            messages = [{"role": "system", "content": system_prompt}] + self.memory.context()
            llm_output = await self.call_llm(messages, tools=self.registry.schemas_for_llm())

            content = llm_output.get("content", "")
            tool_calls_raw = llm_output.get("tool_calls", [])
            step.thought = content

            if not tool_calls_raw:
                step.is_final = True
                step.observation = content
                final_answer = content
                self.memory.add("assistant", content)
                steps.append(step)
                break

            observations = []
            for raw in tool_calls_raw:
                tc = ToolCall(id=raw.get("id", str(uuid.uuid4())[:8]), name=raw["name"], arguments=raw.get("arguments", {}))
                await self.execute_tool(tc)
                if tc.name == "knowledge_search" and tc.result:
                    rag_sources.extend(tc.result.get("chunks", []))
                all_calls.append(tc)
                step.tool_calls.append(tc)
                if tc.result:
                    observations.append(f"[{tc.name}] {json.dumps(tc.result)[:500]}")
                elif tc.error:
                    observations.append(f"[{tc.name}] ERROR: {tc.error}")

            step.observation = "\n".join(observations)
            steps.append(step)
            self.memory.add("assistant", f"Thought: {content}")
            self.memory.add("tool", f"Tool results:\n{step.observation}")

        ok, reason = self.guardrails.check_output(final_answer)
        if not ok:
            final_answer = "I cannot provide that response (sensitive content detected)."

        total = (time.time() - trace_start) * 1000
        return AgentResponse(
            answer=final_answer,
            steps=steps,
            tool_calls=all_calls,
            total_duration_ms=total,
            rag_sources=rag_sources,
            metrics={"steps": len(steps), "tools": len(all_calls), "model": self.model_name, "duration_ms": round(total, 2)},
        )