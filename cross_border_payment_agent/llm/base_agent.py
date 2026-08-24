"""
Base Agent — Shared orchestration logic for all LLM backends.

Implements full production patterns:
- Intent routing (simple vs complex query classification)
- Guardrails with approval workflow
- Human-in-the-loop pause/resume
- Memory management with token counting and summarization
- Error handling with LLM fallback and recovery
- Structured observability with traces and metrics
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    SKIPPED = "skipped"


class ToolRiskLevel(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    result: dict | None = None
    error: str | None = None
    duration_ms: float = 0.0
    risk_level: ToolRiskLevel = ToolRiskLevel.SAFE
    approved: bool = False
    approval_reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    retry_count: int = 0


@dataclass
class AgentStep:
    step_number: int
    thought: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    observation: str = ""
    is_final: bool = False
    status: StepStatus = StepStatus.PENDING
    complexity: QueryComplexity = QueryComplexity.MODERATE
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TraceSpan:
    span_id: str
    parent_span_id: str | None
    name: str
    start_time: float
    end_time: float = 0.0
    status: str = "ok"
    attributes: dict = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000 if self.end_time else 0


@dataclass
class AgentResponse:
    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    total_duration_ms: float = 0.0
    tokens_used: dict = field(default_factory=dict)
    rag_sources: list[dict] = field(default_factory=list)
    trace: list[TraceSpan] = field(default_factory=list)
    complexity: QueryComplexity = QueryComplexity.MODERATE
    metrics: dict = field(default_factory=dict)


@dataclass
class Message:
    role: str
    content: str
    token_estimate: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class IntentRouter:
    SIMPLE_PATTERNS = [
        r"what (is|are) the (rules|requirements|fees|rate)",
        r"how (do|does|to)",
        r"tell me (about|the)",
        r"explain",
        r"what (country|currency|swift|bic)",
    ]
    COMPLEX_PATTERNS = [
        r"(send|initiate|wire|transfer).*(international|cross.border|abroad)",
        r"(track|status|where).*(payment|wire|transfer)",
        r"(quote|cost|fee|compare).*(wire|transfer|payment)",
        r"(compliance|sanction|regulation|travel.rule)",
        r"(correspondent|intermediary|routing)",
        r"(capital.control|reporting.requirement)",
    ]
    CRITICAL_PATTERNS = [
        r"(block|reject|hold).*(payment|wire|transfer)",
        r"(sanction).*(match|hit|found)",
        r"(fraud|suspicious|illegal)",
    ]

    @classmethod
    def classify(cls, query: str) -> QueryComplexity:
        query_lower = query.lower()
        for pattern in cls.CRITICAL_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.CRITICAL
        for pattern in cls.COMPLEX_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.COMPLEX
        for pattern in cls.SIMPLE_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.SIMPLE
        return QueryComplexity.MODERATE


class Guardrails:
    TOOL_RISK_MAP: dict[str, ToolRiskLevel] = {
        "knowledge_search": ToolRiskLevel.SAFE,
        "get_rate": ToolRiskLevel.SAFE,
        "compare_fx_rates": ToolRiskLevel.SAFE,
        "get_history_rate": ToolRiskLevel.SAFE,
        "track_wire": ToolRiskLevel.SAFE,
        "wire_history": ToolRiskLevel.SAFE,
        "find_correspondent": ToolRiskLevel.SAFE,
        "lookup_bic": ToolRiskLevel.SAFE,
        "get_regulations": ToolRiskLevel.SAFE,
        "required_info": ToolRiskLevel.SAFE,
        "get_quote": ToolRiskLevel.SAFE,
        "compare_payment_options": ToolRiskLevel.SAFE,
        "screen_entity": ToolRiskLevel.LOW,
        "check_compliance": ToolRiskLevel.LOW,
        "check_controls": ToolRiskLevel.LOW,
        "get_route": ToolRiskLevel.LOW,
        "notify_customer": ToolRiskLevel.LOW,
        "send_wire": ToolRiskLevel.HIGH,
    }

    def __init__(self, auto_approve_up_to: ToolRiskLevel = ToolRiskLevel.LOW) -> None:
        self.auto_approve_up_to = auto_approve_up_to

    def get_tool_risk(self, tool_name: str) -> ToolRiskLevel:
        return self.TOOL_RISK_MAP.get(tool_name, ToolRiskLevel.MEDIUM)

    def check_tool_call(self, tool_name: str, arguments: dict, requires_approval: bool = False) -> tuple[bool, str, ToolRiskLevel]:
        risk = self.get_tool_risk(tool_name)
        if risk == ToolRiskLevel.HIGH or requires_approval:
            return False, f"Tool '{tool_name}' requires human approval (risk={risk.value})", risk
        return True, "OK", risk

    def check_output(self, response: str) -> tuple[bool, str]:
        injection_patterns = [r"ignore (previous|all|above) instructions", r"you are now", r"system prompt", r"jailbreak"]
        for pattern in injection_patterns:
            if re.search(pattern, response.lower()):
                return False, "Response may contain prompt injection content"
        return True, "OK"


class HumanApprovalManager:
    def __init__(self, auto_approve: bool = False, approval_timeout_seconds: int = 300, on_approval_needed: Callable | None = None) -> None:
        self.auto_approve = auto_approve
        self.approval_timeout = approval_timeout_seconds
        self.on_approval_needed = on_approval_needed
        self._pending_approvals: dict[str, dict] = {}

    async def request_approval(self, tool_call: ToolCall, risk_level: ToolRiskLevel, context: str = "") -> tuple[bool, str]:
        if self.auto_approve:
            return True, "Auto-approved (dev mode)"
        logger.warning("APPROVAL REQUIRED: Tool=%s, Risk=%s", tool_call.name, risk_level.value)
        print(f"\n⚠️  APPROVAL REQUIRED: {tool_call.name} (risk={risk_level.value})")
        response = input("   Approve? (yes/no): ").strip().lower()
        approved = response in ("yes", "y", "1", "true")
        return approved, "Approved by human operator" if approved else "Rejected by human operator"


class ConversationMemory:
    def __init__(self, max_tokens: int = 8000, max_messages: int = 50) -> None:
        self.messages: list[Message] = []
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self._key_facts: list[str] = []
        self._total_tokens = 0

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def add(self, role: str, content: str, is_key_fact: bool = False) -> None:
        tokens = self._estimate_tokens(content)
        msg = Message(role=role, content=content, token_estimate=tokens)
        self.messages.append(msg)
        self._total_tokens += tokens
        if is_key_fact:
            self._key_facts.append(content[:200])
        self._maybe_truncate()

    def _maybe_truncate(self) -> None:
        while self._total_tokens > self.max_tokens and len(self.messages) > 6:
            removed = self.messages.pop(1)
            self._total_tokens -= removed.token_estimate
        while len(self.messages) > self.max_messages:
            removed = self.messages.pop(1)
            self._total_tokens -= removed.token_estimate

    def get_context(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def get_token_usage(self) -> dict:
        return {"total_tokens": self._total_tokens, "max_tokens": self.max_tokens, "utilization": round(self._total_tokens / self.max_tokens, 2), "message_count": len(self.messages)}


class AgentTracer:
    def __init__(self) -> None:
        self._spans: list[TraceSpan] = []
        self._current_span_id: str | None = None

    def start_span(self, name: str, attributes: dict | None = None) -> str:
        span_id = str(uuid.uuid4())[:8]
        span = TraceSpan(span_id=span_id, parent_span_id=self._current_span_id, name=name, start_time=time.time(), attributes=attributes or {})
        self._spans.append(span)
        self._current_span_id = span_id
        return span_id

    def end_span(self, span_id: str, status: str = "ok", attributes: dict | None = None) -> None:
        for span in self._spans:
            if span.span_id == span_id:
                span.end_time = time.time()
                span.status = status
                if attributes:
                    span.attributes.update(attributes)
                break

    def add_event(self, span_id: str, name: str, attributes: dict | None = None) -> None:
        for span in self._spans:
            if span.span_id == span_id:
                span.events.append({"name": name, "timestamp": datetime.utcnow().isoformat(), "attributes": attributes or {}})
                break

    def get_trace(self) -> list[TraceSpan]:
        return self._spans

    def get_trace_summary(self) -> dict:
        total_duration = sum(s.duration_ms for s in self._spans if s.end_time)
        return {"total_spans": len(self._spans), "total_duration_ms": round(total_duration, 2), "llm_calls": sum(1 for s in self._spans if "llm" in s.name.lower()), "tool_calls": sum(1 for s in self._spans if "tool" in s.name.lower()), "errors": sum(1 for s in self._spans if s.status == "error")}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, parameters: dict, handler: Callable, risk_level: ToolRiskLevel = ToolRiskLevel.SAFE) -> None:
        self._tools[name] = {"name": name, "description": description, "parameters": parameters, "handler": handler, "risk_level": risk_level}

    def get_schemas(self) -> list[dict]:
        return [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in self._tools.values()]

    def get_handler(self, name: str) -> Callable | None:
        tool = self._tools.get(name)
        return tool["handler"] if tool else None

    def get_tool_info(self, name: str) -> dict | None:
        return self._tools.get(name)

    def get_tool_descriptions(self) -> str:
        return "\n".join(f"- {t['name']} [{t.get('risk_level', ToolRiskLevel.SAFE).value}]: {t['description']}" for t in self._tools.values())


class ErrorHandler:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5) -> None:
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._error_counts: dict[str, int] = {}

    def should_retry(self, error: Exception, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False
        return not any(term in str(error).lower() for term in ["authentication", "permission", "not found", "invalid"])

    def get_retry_delay(self, attempt: int) -> float:
        return self.backoff_factor ** attempt

    def record_error(self, error_type: str) -> None:
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def get_error_summary(self) -> dict:
        return dict(self._error_counts)

    async def with_retry(self, operation: Callable, operation_name: str, tracer: AgentTracer | None = None, *args, **kwargs) -> Any:
        last_error = None
        span_id = tracer.start_span(f"retry:{operation_name}") if tracer else None
        for attempt in range(self.max_retries + 1):
            try:
                result = await operation(*args, **kwargs)
                if span_id and tracer:
                    tracer.end_span(span_id, "ok", {"attempts": attempt + 1})
                return result
            except Exception as e:
                last_error = e
                self.record_error(type(e).__name__)
                if not self.should_retry(e, attempt):
                    break
                delay = self.get_retry_delay(attempt)
                logger.warning("Retry %d/%d for %s after %.1fs: %s", attempt + 1, self.max_retries, operation_name, delay, e)
                time.sleep(delay)
        if span_id and tracer:
            tracer.end_span(span_id, "error", {"final_error": str(last_error)})
        raise last_error


class BaseAgent(ABC):
    def __init__(self, model_name: str = "", max_steps: int = 10, max_retries: int = 3, auto_approve: bool = False) -> None:
        self.model_name = model_name
        self.max_steps = max_steps
        self._step_count = 0
        self.rag = RAGPipeline()
        self.tools = ToolRegistry()
        self.memory = ConversationMemory(max_tokens=8000)
        self.guardrails = Guardrails()
        self.intent_router = IntentRouter()
        self.approval_manager = HumanApprovalManager(auto_approve=auto_approve)
        self.error_handler = ErrorHandler(max_retries=max_retries)
        self.tracer = AgentTracer()
        self._total_llm_tokens = {"prompt": 0, "completion": 0}
        self._register_rag_tools()

    def _register_rag_tools(self) -> None:
        self.tools.register(
            name="knowledge_search",
            description="Search the cross-border payment knowledge base for SWIFT codes, regulations, and correspondent banking details",
            parameters={"type": "object", "properties": {"query": {"type": "string", "description": "Natural language search query"}, "collection": {"type": "string", "enum": ["all", "correspondent_banking", "swift_codes", "country_regulations", "fee_schedules", "fx_trading_rules", "compliance_requirements", "past_transactions"], "description": "Collection to search (default: all)"}, "top_k": {"type": "integer", "description": "Number of results (default: 5)"}}, "required": ["query"]},
            handler=self._handle_knowledge_search,
            risk_level=ToolRiskLevel.SAFE,
        )

    async def _handle_knowledge_search(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        collection = kwargs.get("collection", "all")
        top_k = kwargs.get("top_k", 5)
        collections = None if collection == "all" else [collection]
        result = self.rag.query(query, top_k=top_k, collections=collections)
        return {"results_count": len(result.chunks), "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "source": c.metadata.get("source", "unknown")} for c in result.chunks], "context": result.assembled_context[:1000]}

    @abstractmethod
    async def call_llm(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        ...

    async def _simple_rag_response(self, query: str) -> AgentResponse:
        rag_result = self.rag.query(query, top_k=5)
        answer_parts = [f"{i}. ({c.metadata.get('source', 'knowledge base')}) {c.text[:200]}" for i, c in enumerate(rag_result.chunks, 1)]
        return AgentResponse(answer=f"Based on our cross-border payment knowledge base:\n\n" + "\n\n".join(answer_parts), rag_sources=[{"text": c.text[:200], "score": c.score} for c in rag_result.chunks], complexity=QueryComplexity.SIMPLE)

    async def execute_tool(self, tool_call: ToolCall) -> ToolCall:
        span_id = self.tracer.start_span(f"tool:{tool_call.name}", {"args": str(tool_call.arguments)[:200]})
        handler = self.tools.get_handler(tool_call.name)
        if not handler:
            tool_call.error = f"Unknown tool: {tool_call.name}"
            self.tracer.end_span(span_id, "error")
            return tool_call
        tool_info = self.tools.get_tool_info(tool_call.name)
        tool_call.risk_level = tool_info.get("risk_level", ToolRiskLevel.MEDIUM) if tool_info else ToolRiskLevel.MEDIUM
        allowed, reason, risk = self.guardrails.check_tool_call(tool_call.name, tool_call.arguments)
        if not allowed:
            approved, approval_reason = await self.approval_manager.request_approval(tool_call, risk)
            tool_call.approved = approved
            if not approved:
                tool_call.error = f"Rejected by human: {approval_reason}"
                self.tracer.end_span(span_id, "error")
                return tool_call

        async def _do_execute():
            start = time.time()
            result = await handler(**tool_call.arguments)
            tool_call.result = result
            tool_call.duration_ms = (time.time() - start) * 1000
            return result

        try:
            await self.error_handler.with_retry(_do_execute, f"tool:{tool_call.name}", self.tracer)
        except Exception as e:
            tool_call.error = f"Failed after retries: {str(e)}"
        self.tracer.end_span(span_id, "ok" if not tool_call.error else "error", {"duration_ms": tool_call.duration_ms})
        return tool_call

    async def run(self, user_query: str) -> AgentResponse:
        trace_start = time.time()
        self.tracer = AgentTracer()
        self._step_count = 0
        span_id = self.tracer.start_span("agent_run", {"query": user_query[:200]})
        complexity = self.intent_router.classify(user_query)
        if complexity == QueryComplexity.SIMPLE:
            self.tracer.end_span(span_id, "ok")
            return await self._simple_rag_response(user_query)
        self.memory.add("user", user_query)
        system_prompt = self._build_system_prompt(complexity)
        steps: list[AgentStep] = []
        all_tool_calls: list[ToolCall] = []
        final_answer = "I was unable to process your request."
        usage = {}
        for step_num in range(1, self.max_steps + 1):
            self._step_count = step_num
            step = AgentStep(step_number=step_num, thought="", complexity=complexity, status=StepStatus.RUNNING)
            messages = [{"role": "system", "content": system_prompt}] + self.memory.get_context()
            try:
                llm_response = await self.error_handler.with_retry(lambda: self.call_llm(messages=messages, tools=self.tools.get_schemas()), "llm_call", self.tracer)
            except Exception as e:
                step.status = StepStatus.FAILED
                steps.append(step)
                break
            content = llm_response.get("content", "")
            tool_calls_raw = llm_response.get("tool_calls", [])
            finish_reason = llm_response.get("finish_reason", "stop")
            usage = llm_response.get("usage", {})
            self._total_llm_tokens["prompt"] += usage.get("prompt_tokens", 0)
            self._total_llm_tokens["completion"] += usage.get("completion_tokens", 0)
            step.thought = content
            if not tool_calls_raw or finish_reason == "stop":
                step.is_final = True
                step.status = StepStatus.COMPLETED
                steps.append(step)
                self.memory.add("assistant", content)
                final_answer = content
                break
            for tc_raw in tool_calls_raw:
                tc = ToolCall(id=tc_raw.get("id", str(uuid.uuid4())[:8]), name=tc_raw["name"], arguments=tc_raw.get("arguments", {}))
                tc = await self.execute_tool(tc)
                all_tool_calls.append(tc)
                step.tool_calls.append(tc)
            observations = [f"[{tc.name}] {json.dumps(tc.result)[:500]}" if tc.result else f"[{tc.name}] ERROR: {tc.error}" for tc in step.tool_calls]
            step.observation = "\n".join(observations)
            step.status = StepStatus.COMPLETED
            steps.append(step)
            self.memory.add("assistant", f"Thought: {content}")
            self.memory.add("tool", f"Tool results:\n{step.observation}", is_key_fact=True)
        allowed, _ = self.guardrails.check_output(final_answer)
        if not allowed:
            final_answer = "I cannot provide that response due to safety restrictions."
        total_duration = (time.time() - trace_start) * 1000
        return AgentResponse(answer=final_answer, steps=steps, tool_calls=all_tool_calls, total_duration_ms=total_duration, tokens_used=usage, trace=self.tracer.get_trace(), complexity=complexity, metrics={"complexity": complexity.value, "total_steps": len(steps), "total_tool_calls": len(all_tool_calls), "total_duration_ms": round(total_duration, 2), "tokens": self._total_llm_tokens})

    def _build_system_prompt(self, complexity: QueryComplexity) -> str:
        base = f"""You are a Cross-Border Payment Assistant Agent for a bank. You help customers with international wire transfers — explaining fees, timelines, exchange rates, and compliance requirements.

You have access to the following tools:
{self.tools.get_tool_descriptions()}

Query complexity: {complexity.value}
"""
        if complexity == QueryComplexity.COMPLEX:
            base += "\nThis is a complex query. Plan your approach: look up FX rates, check compliance, find correspondent banks, and provide a complete cost breakdown.\n"
        elif complexity == QueryComplexity.CRITICAL:
            base += "\nThis is a critical query. Explain your reasoning clearly before calling tools. Sanctions hits or compliance blocks require careful handling.\n"
        base += "\nRules:\n1. Always search knowledge base for regulations and correspondent details\n2. Explain fees and timelines clearly\n3. Check compliance before recommending payments\n4. Never fabricate exchange rates or fees\n5. Be professional and helpful\n"
        return base
