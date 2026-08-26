"""
Base Agent — Shared orchestration logic for all LLM backends.

Implements full production patterns:
- Intent routing (simple vs complex query classification)
- Guardrails with approval workflow
- Human-in-the-loop pause/resume
- Memory management with token counting and summarization
- Error handling with LLM fallback and recovery
- Structured observability with traces and metrics

Adapted for Document Digitization & Extraction Agent.
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


# ══════════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ══════════════════════════════════════════════════════════════════

class QueryComplexity(Enum):
    """Intent classification for query routing."""
    SIMPLE = "simple"       # Direct RAG response, no tools needed
    MODERATE = "moderate"   # 1-2 tool calls, straightforward
    COMPLEX = "complex"     # Multi-step, multiple tools, may need approval
    CRITICAL = "critical"   # High-risk action, requires human approval


class StepStatus(Enum):
    """Status of an agent step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    SKIPPED = "skipped"


class ToolRiskLevel(Enum):
    """Risk level of a tool call."""
    SAFE = "safe"           # Read-only, auto-execute
    LOW = "low"             # Minor side effects
    MEDIUM = "medium"       # Significant side effects
    HIGH = "high"           # Irreversible, requires approval


# ══════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════

@dataclass
class ToolCall:
    """A single tool call made by the agent."""
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
    """A single reasoning step in the agent loop."""
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
    """A single span in the observability trace."""
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
    """Final agent response with full trace."""
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
    """A single message in conversation history."""
    role: str
    content: str
    token_estimate: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ══════════════════════════════════════════════════════════════════
#  INTENT ROUTER
# ══════════════════════════════════════════════════════════════════

class IntentRouter:
    """
    Classifies queries as simple, moderate, complex, or critical.

    Simple queries → direct RAG response (no tools)
    Moderate → 1-2 tool calls
    Complex → multi-step agent loop
    Critical → requires human approval
    """

    SIMPLE_PATTERNS = [
        r"what (is|are) the (rules|requirements|policies|standards)",
        r"how (do|does|to)",
        r"tell me (about|the)",
        r"what documents (do|are|is) (i|we|needed)",
        r"explain",
        r"what is the (schema|format|template)",
    ]

    COMPLEX_PATTERNS = [
        r"(process|extract|digitize|convert).*(document|invoice|contract|statement)",
        r"classify.*document|document.*classification",
        r"ocr|optical character",
        r"validate.*data|data.*validation",
        r"batch.*process|process.*batch",
        r"enrich.*data|data.*enrichment",
    ]

    CRITICAL_PATTERNS = [
        r"(approve|reject|accept|decline).*(document|extraction|batch)",
        r"(delete|remove|purge).*(document|data)",
        r"(export|download|send).*(all|everything|bulk)",
        r"(override|force|bypass).*(validation|check|rule)",
    ]

    @classmethod
    def classify(cls, query: str) -> QueryComplexity:
        """Classify a user query by complexity."""
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

    @classmethod
    def should_use_tools(cls, complexity: QueryComplexity) -> bool:
        """Determine if tools are needed based on complexity."""
        return complexity in (QueryComplexity.MODERATE, QueryComplexity.COMPLEX, QueryComplexity.CRITICAL)


# ══════════════════════════════════════════════════════════════════
#  GUARDRAILS
# ══════════════════════════════════════════════════════════════════

class Guardrails:
    """Safety checks and guardrails for tool calls and outputs."""

    TOOL_RISK_MAP: dict[str, ToolRiskLevel] = {
        # Safe — read-only
        "knowledge_search": ToolRiskLevel.SAFE,
        "get_document_schema": ToolRiskLevel.SAFE,
        "get_supported_document_types": ToolRiskLevel.SAFE,
        "get_extraction_status": ToolRiskLevel.SAFE,
        # Low — minor side effects
        "classify_document": ToolRiskLevel.LOW,
        "extract_document": ToolRiskLevel.LOW,
        "validate_extracted_data": ToolRiskLevel.LOW,
        "extract_table_data": ToolRiskLevel.LOW,
        "extract_mrz": ToolRiskLevel.LOW,
        "enrich_invoice_data": ToolRiskLevel.LOW,
        "enrich_bank_statement_data": ToolRiskLevel.LOW,
        "enrich_contract_data": ToolRiskLevel.LOW,
        "enrich_financial_statement_data": ToolRiskLevel.LOW,
        "notify_customer": ToolRiskLevel.LOW,
        # Medium — significant side effects
        "batch_classify": ToolRiskLevel.MEDIUM,
        "batch_process_documents": ToolRiskLevel.MEDIUM,
        "cross_validate_documents": ToolRiskLevel.MEDIUM,
        # High — irreversible, requires approval
        "store_extracted_data": ToolRiskLevel.HIGH,
        "delete_document_data": ToolRiskLevel.HIGH,
        "export_batch_results": ToolRiskLevel.HIGH,
    }

    SENSITIVE_PATTERNS = [
        (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARD_REDACTED]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
    ]

    def __init__(self, auto_approve_up_to: ToolRiskLevel = ToolRiskLevel.LOW) -> None:
        self.auto_approve_up_to = auto_approve_up_to
        self._risk_order = [ToolRiskLevel.SAFE, ToolRiskLevel.LOW, ToolRiskLevel.MEDIUM, ToolRiskLevel.HIGH]

    def get_tool_risk(self, tool_name: str) -> ToolRiskLevel:
        return self.TOOL_RISK_MAP.get(tool_name, ToolRiskLevel.MEDIUM)

    def check_tool_call(
        self,
        tool_name: str,
        arguments: dict,
        requires_approval: bool = False,
    ) -> tuple[bool, str, ToolRiskLevel]:
        """Check if a tool call is allowed."""
        risk = self.get_tool_risk(tool_name)

        if risk == ToolRiskLevel.HIGH or requires_approval:
            return False, f"Tool '{tool_name}' requires human approval (risk={risk.value})", risk

        return True, "OK", risk

    def check_output(self, response: str) -> tuple[bool, str]:
        """Check if the generated response is safe to send."""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            if re.search(pattern, response):
                return False, f"Response may contain sensitive data: {replacement}"

        injection_patterns = [
            r"ignore (previous|all|above) instructions",
            r"you are now",
            r"system prompt",
            r"jailbreak",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, response.lower()):
                return False, "Response may contain prompt injection content"

        return True, "OK"


# ══════════════════════════════════════════════════════════════════
#  HUMAN-IN-THE-LOOP
# ══════════════════════════════════════════════════════════════════

class HumanApprovalManager:
    """Manages human-in-the-loop approval for high-risk actions."""

    def __init__(
        self,
        auto_approve: bool = False,
        approval_timeout_seconds: int = 300,
        on_approval_needed: Callable | None = None,
    ) -> None:
        self.auto_approve = auto_approve
        self.approval_timeout = approval_timeout_seconds
        self.on_approval_needed = on_approval_needed
        self._pending_approvals: dict[str, dict] = {}

    async def request_approval(
        self,
        tool_call: ToolCall,
        risk_level: ToolRiskLevel,
        context: str = "",
    ) -> tuple[bool, str]:
        """Request human approval for a tool call."""
        approval_id = str(uuid.uuid4())

        if self.auto_approve:
            logger.info("Auto-approving tool call %s (dev mode)", tool_call.name)
            return True, "Auto-approved (dev mode)"

        request = {
            "id": approval_id,
            "tool_name": tool_call.name,
            "arguments": tool_call.arguments,
            "risk_level": risk_level.value,
            "context": context,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }
        self._pending_approvals[approval_id] = request

        if self.on_approval_needed:
            await self.on_approval_needed(request)
        else:
            logger.warning(
                "APPROVAL REQUIRED: Tool=%s, Risk=%s, Args=%s",
                tool_call.name,
                risk_level.value,
                json.dumps(tool_call.arguments)[:200],
            )
            print(f"\n⚠️  APPROVAL REQUIRED")
            print(f"   Tool: {tool_call.name}")
            print(f"   Risk: {risk_level.value}")
            print(f"   Args: {json.dumps(tool_call.arguments, indent=2)}")
            response = input("   Approve? (yes/no): ").strip().lower()
            approved = response in ("yes", "y", "1", "true")

        if approved:
            request["status"] = "approved"
            return True, "Approved by human operator"
        else:
            request["status"] = "rejected"
            return False, "Rejected by human operator"

    def get_pending_approvals(self) -> list[dict]:
        return [r for r in self._pending_approvals.values() if r["status"] == "pending"]

    def approve(self, approval_id: str, reason: str = "Manual approval") -> bool:
        if approval_id in self._pending_approvals:
            self._pending_approvals[approval_id]["status"] = "approved"
            self._pending_approvals[approval_id]["reason"] = reason
            return True
        return False

    def reject(self, approval_id: str, reason: str = "Manual rejection") -> bool:
        if approval_id in self._pending_approvals:
            self._pending_approvals[approval_id]["status"] = "rejected"
            self._pending_approvals[approval_id]["reason"] = reason
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  MEMORY MANAGEMENT
# ══════════════════════════════════════════════════════════════════

class ConversationMemory:
    """Manages conversation history with token counting and summarization."""

    def __init__(
        self,
        max_tokens: int = 8000,
        max_messages: int = 50,
        summarize_threshold: float = 0.7,
    ) -> None:
        self.messages: list[Message] = []
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.summarize_threshold = summarize_threshold
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
        needs_truncation = (
            self._total_tokens > self.max_tokens
            or len(self.messages) > self.max_messages
        )
        if not needs_truncation:
            return
        while self._total_tokens > self.max_tokens and len(self.messages) > 6:
            removed = self.messages.pop(1)
            self._total_tokens -= removed.token_estimate
        while len(self.messages) > self.max_messages:
            removed = self.messages.pop(1)
            self._total_tokens -= removed.token_estimate

    def get_context(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def get_token_usage(self) -> dict:
        return {
            "total_tokens": self._total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": round(self._total_tokens / self.max_tokens, 2),
            "message_count": len(self.messages),
        }

    def clear(self) -> None:
        self.messages.clear()
        self._total_tokens = 0
        self._key_facts.clear()

    def save_session(self) -> dict:
        return {
            "messages": [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in self.messages],
            "key_facts": self._key_facts,
        }

    def load_session(self, data: dict) -> None:
        self.clear()
        for msg in data.get("messages", []):
            self.add(msg["role"], msg["content"])
        self._key_facts = data.get("key_facts", [])


# ══════════════════════════════════════════════════════════════════
#  OBSERVABILITY
# ══════════════════════════════════════════════════════════════════

class AgentTracer:
    """Structured observability for agent execution."""

    def __init__(self) -> None:
        self._spans: list[TraceSpan] = []
        self._current_span_id: str | None = None

    def start_span(self, name: str, attributes: dict | None = None) -> str:
        span_id = str(uuid.uuid4())[:8]
        span = TraceSpan(
            span_id=span_id,
            parent_span_id=self._current_span_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )
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
                span.events.append({
                    "name": name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "attributes": attributes or {},
                })
                break

    def get_trace(self) -> list[TraceSpan]:
        return self._spans

    def get_trace_summary(self) -> dict:
        total_duration = sum(s.duration_ms for s in self._spans if s.end_time)
        llm_calls = sum(1 for s in self._spans if "llm" in s.name.lower())
        tool_calls = sum(1 for s in self._spans if "tool" in s.name.lower())
        errors = sum(1 for s in self._spans if s.status == "error")
        return {
            "total_spans": len(self._spans),
            "total_duration_ms": round(total_duration, 2),
            "llm_calls": llm_calls,
            "tool_calls": tool_calls,
            "errors": errors,
            "spans": [{"name": s.name, "duration_ms": round(s.duration_ms, 2), "status": s.status} for s in self._spans],
        }

    def export_json(self) -> str:
        return json.dumps(self.get_trace_summary(), indent=2)


# ══════════════════════════════════════════════════════════════════
#  TOOL REGISTRY
# ══════════════════════════════════════════════════════════════════

class ToolRegistry:
    """Registry of available tools with their schemas and metadata."""

    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
        risk_level: ToolRiskLevel = ToolRiskLevel.SAFE,
    ) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
            "risk_level": risk_level,
        }

    def get_schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for tool in self._tools.values()
        ]

    def get_handler(self, name: str) -> Callable | None:
        tool = self._tools.get(name)
        return tool["handler"] if tool else None

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def get_tool_info(self, name: str) -> dict | None:
        return self._tools.get(name)

    def get_tool_descriptions(self) -> str:
        lines = []
        for tool in self._tools.values():
            risk = tool.get("risk_level", ToolRiskLevel.SAFE).value
            params = ", ".join(tool["parameters"].get("properties", {}).keys())
            lines.append(f"- {tool['name']} [{risk}]: {tool['description']} (params: {params})")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ══════════════════════════════════════════════════════════════════

class ErrorHandler:
    """Handles errors with retry logic, fallback strategies, and recovery."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5) -> None:
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._error_counts: dict[str, int] = {}

    def should_retry(self, error: Exception, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False
        non_retryable = ["authentication", "permission", "not found", "invalid"]
        error_str = str(error).lower()
        for term in non_retryable:
            if term in error_str:
                return False
        return True

    def get_retry_delay(self, attempt: int) -> float:
        return self.backoff_factor ** attempt

    def record_error(self, error_type: str) -> None:
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def get_error_summary(self) -> dict:
        return dict(self._error_counts)

    async def with_retry(
        self,
        operation: Callable,
        operation_name: str,
        tracer: AgentTracer | None = None,
        *args,
        **kwargs,
    ) -> Any:
        last_error = None
        span_id = None
        if tracer:
            span_id = tracer.start_span(f"retry:{operation_name}")

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
                if span_id and tracer:
                    tracer.add_event(span_id, "retry", {"attempt": attempt + 1, "error": str(e)})
                time.sleep(delay)

        if span_id and tracer:
            tracer.end_span(span_id, "error", {"attempts": self.max_retries + 1, "final_error": str(last_error)})
        raise last_error


# ══════════════════════════════════════════════════════════════════
#  BASE AGENT
# ══════════════════════════════════════════════════════════════════

class BaseAgent(ABC):
    """
    Base agent class with full production-ready orchestration.

    Subclasses implement `call_llm()` for their specific backend.
    """

    def __init__(
        self,
        model_name: str = "",
        max_steps: int = 10,
        max_retries: int = 3,
        auto_approve: bool = False,
    ) -> None:
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
        """Register the RAG knowledge search tool."""
        self.tools.register(
            name="knowledge_search",
            description="Search the document processing knowledge base for schemas, rules, and best practices",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "collection": {
                        "type": "string",
                        "enum": ["all", "document_classification", "extraction_schemas",
                                 "validation_rules", "ocr_best_practices", "past_extraction_decisions",
                                 "industry_document_standards", "banking_document_templates"],
                        "description": "Collection to search (default: all)",
                    },
                    "top_k": {"type": "integer", "description": "Number of results (default: 5)"},
                },
                "required": ["query"],
            },
            handler=self._handle_knowledge_search,
            risk_level=ToolRiskLevel.SAFE,
        )

    async def _handle_knowledge_search(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        collection = kwargs.get("collection", "all")
        top_k = kwargs.get("top_k", 5)
        collections = None if collection == "all" else [collection]
        result = self.rag.query(query, top_k=top_k, collections=collections)
        return {
            "results_count": len(result.chunks),
            "chunks": [
                {"text": c.text[:300], "score": round(c.score, 3), "source": c.metadata.get("source", "unknown")}
                for c in result.chunks
            ],
            "context": result.assembled_context[:1000],
        }

    @abstractmethod
    async def call_llm(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Call the LLM backend. Must return standard format."""
        ...

    async def _simple_rag_response(self, query: str) -> AgentResponse:
        """Handle simple queries with direct RAG retrieval — no LLM needed."""
        rag_result = self.rag.query(query, top_k=5)
        answer_parts = []
        for i, chunk in enumerate(rag_result.chunks, 1):
            source = chunk.metadata.get("source", "knowledge base")
            answer_parts.append(f"{i}. ({source}) {chunk.text[:200]}")
        answer = f"Based on our document processing knowledge base:\n\n" + "\n\n".join(answer_parts)
        return AgentResponse(
            answer=answer,
            rag_sources=[{"text": c.text[:200], "score": c.score} for c in rag_result.chunks],
            complexity=QueryComplexity.SIMPLE,
            metrics={"route": "simple_rag", "rag_chunks": len(rag_result.chunks)},
        )

    async def execute_tool(self, tool_call: ToolCall) -> ToolCall:
        """Execute a tool call with guardrails, approval, and retry."""
        span_id = self.tracer.start_span(f"tool:{tool_call.name}", {"args": str(tool_call.arguments)[:200]})

        handler = self.tools.get_handler(tool_call.name)
        if not handler:
            tool_call.error = f"Unknown tool: {tool_call.name}"
            tool_call.risk_level = ToolRiskLevel.HIGH
            self.tracer.end_span(span_id, "error", {"error": tool_call.error})
            return tool_call

        tool_info = self.tools.get_tool_info(tool_call.name)
        tool_call.risk_level = tool_info.get("risk_level", ToolRiskLevel.MEDIUM) if tool_info else ToolRiskLevel.MEDIUM

        allowed, reason, risk = self.guardrails.check_tool_call(tool_call.name, tool_call.arguments)
        if not allowed:
            self.tracer.add_event(span_id, "approval_requested", {"risk": risk.value})
            approved, approval_reason = await self.approval_manager.request_approval(tool_call, risk, context=f"Tool: {tool_call.name}")
            tool_call.approved = approved
            tool_call.approval_reason = approval_reason
            self.tracer.add_event(span_id, "approval_result", {"approved": approved})
            if not approved:
                tool_call.error = f"Rejected by human: {approval_reason}"
                self.tracer.end_span(span_id, "error", {"rejected": True})
                return tool_call

        async def _do_execute():
            start = time.time()
            result = await handler(**tool_call.arguments)
            tool_call.result = result
            tool_call.duration_ms = (time.time() - start) * 1000
            return result

        try:
            await self.error_handler.with_retry(_do_execute, f"tool:{tool_call.name}", self.tracer)
            logger.info("Tool %s executed in %.0fms", tool_call.name, tool_call.duration_ms)
        except Exception as e:
            tool_call.error = f"Failed after retries: {str(e)}"
            logger.error("Tool %s failed: %s", tool_call.name, e)

        self.tracer.end_span(span_id, "ok" if not tool_call.error else "error", {
            "duration_ms": tool_call.duration_ms,
        })
        return tool_call

    async def run(self, user_query: str) -> AgentResponse:
        """Full agent loop with all production patterns."""
        trace_start = time.time()
        self.tracer = AgentTracer()
        self._step_count = 0
        span_id = self.tracer.start_span("agent_run", {"query": user_query[:200]})

        complexity = self.intent_router.classify(user_query)
        logger.info("Query classified as: %s", complexity.value)

        if complexity == QueryComplexity.SIMPLE:
            self.tracer.end_span(span_id, "ok", {"route": "simple_rag"})
            response = await self._simple_rag_response(user_query)
            response.trace = self.tracer.get_trace()
            return response

        self.memory.add("user", user_query)
        system_prompt = self._build_system_prompt(complexity)

        steps: list[AgentStep] = []
        all_tool_calls: list[ToolCall] = []
        rag_sources: list[dict] = []
        final_answer = "I was unable to process your request."
        usage = {}

        for step_num in range(1, self.max_steps + 1):
            self._step_count = step_num
            step_span = self.tracer.start_span(f"step:{step_num}")
            step = AgentStep(step_number=step_num, thought="", complexity=complexity, status=StepStatus.RUNNING)

            messages = [{"role": "system", "content": system_prompt}] + self.memory.get_context()

            llm_span = self.tracer.start_span("llm_call")
            try:
                llm_response = await self.error_handler.with_retry(
                    lambda: self.call_llm(messages=messages, tools=self.tools.get_schemas()),
                    "llm_call",
                    self.tracer,
                )
            except Exception as e:
                logger.error("LLM call failed at step %d: %s", step_num, e)
                step.status = StepStatus.FAILED
                step.observation = f"LLM error: {str(e)}"
                steps.append(step)
                self.tracer.end_span(llm_span, "error")
                self.tracer.end_span(step_span, "error")
                break
            self.tracer.end_span(llm_span, "ok", llm_response.get("usage", {}))

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
                step.observation = content
                steps.append(step)
                self.memory.add("assistant", content)
                final_answer = content
                self.tracer.end_span(step_span, "ok", {"final": True})
                break

            for tc_raw in tool_calls_raw:
                tool_call = ToolCall(
                    id=tc_raw.get("id", str(uuid.uuid4())[:8]),
                    name=tc_raw["name"],
                    arguments=tc_raw.get("arguments", {}),
                )
                tool_call = await self.execute_tool(tool_call)
                all_tool_calls.append(tool_call)
                step.tool_calls.append(tool_call)
                if tool_call.name == "knowledge_search" and tool_call.result:
                    rag_sources.extend(tool_call.result.get("chunks", []))

            observations = []
            for tc in step.tool_calls:
                if tc.result:
                    observations.append(f"[{tc.name}] {json.dumps(tc.result)[:500]}")
                elif tc.error:
                    observations.append(f"[{tc.name}] ERROR: {tc.error}")

            step.observation = "\n".join(observations)
            step.status = StepStatus.COMPLETED
            steps.append(step)

            self.memory.add("assistant", f"Thought: {content}")
            self.memory.add("tool", f"Tool results:\n{step.observation}", is_key_fact=True)

            self.tracer.end_span(step_span, "ok", {
                "tool_calls": len(step.tool_calls),
                "observation_len": len(step.observation),
            })

        allowed, reason = self.guardrails.check_output(final_answer)
        if not allowed:
            final_answer = "I cannot provide that response due to safety restrictions."

        self.tracer.end_span(span_id, "ok", {"complexity": complexity.value})
        total_duration = (time.time() - trace_start) * 1000

        metrics = {
            "complexity": complexity.value,
            "total_steps": len(steps),
            "total_tool_calls": len(all_tool_calls),
            "total_duration_ms": round(total_duration, 2),
            "tokens": self._total_llm_tokens,
            "memory_usage": self.memory.get_token_usage(),
            "trace_summary": self.tracer.get_trace_summary(),
            "errors": self.error_handler.get_error_summary(),
        }

        return AgentResponse(
            answer=final_answer,
            steps=steps,
            tool_calls=all_tool_calls,
            total_duration_ms=total_duration,
            tokens_used=usage,
            rag_sources=rag_sources,
            trace=self.tracer.get_trace(),
            complexity=complexity,
            metrics=metrics,
        )

    def _build_system_prompt(self, complexity: QueryComplexity) -> str:
        base_prompt = f"""You are a Document Digitization & Extraction Agent for a bank. You help process banking documents by classifying, extracting, validating, and enriching structured data from unstructured documents.

You have access to the following tools:
{self.tools.get_tool_descriptions()}

Query complexity: {complexity.value}
"""

        if complexity == QueryComplexity.COMPLEX:
            base_prompt += """
This is a complex query. Plan your approach:
1. Classify the document type first
2. Use the appropriate extraction schema
3. Extract data using OCR tools
4. Validate extracted data against rules
5. Enrich with additional context
6. Report results with confidence scores
"""
        elif complexity == QueryComplexity.CRITICAL:
            base_prompt += """
This is a critical query involving high-risk actions.
IMPORTANT: You MUST explain your reasoning clearly before calling any tools.
High-risk tools (store_extracted_data, delete_document_data, export_batch_results) require human approval.
"""
        else:
            base_prompt += """
Be efficient. Minimize tool calls. If you can answer from retrieved context, do so.
"""

        base_prompt += f"""
Rules:
1. Always search knowledge base first if unsure about document schemas or extraction rules
2. Explain your reasoning before calling tools
3. Never fabricate extracted data — only report what tools return
4. Be professional and concise
5. If a tool fails, explain and suggest alternatives
6. Always provide confidence scores for extracted data
7. Flag low-confidence extractions for manual review

Current step: {self._step_count}/{self.max_steps}
"""
        return base_prompt
