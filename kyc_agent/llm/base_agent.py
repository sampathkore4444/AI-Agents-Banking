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

    # Keywords that indicate complexity
    SIMPLE_PATTERNS = [
        r"what (is|are) the (rules|requirements|policies)",
        r"how (do|does|to)",
        r"tell me (about|the)",
        r"what documents (do|are|is) (i|we) need",
        r"explain",
    ]

    COMPLEX_PATTERNS = [
        r"(process|open|create|set up).*(account|application)",
        r"verify|verification|check.*identity",
        r"screen.*sanctions|sanctions.*check",
        r"assess.*risk|risk.*assessment",
        r"compliance|regulatory",
    ]

    CRITICAL_PATTERNS = [
        r"(approve|reject|deny).*(application|account|case)",
        r"(large|high).*(transfer|transaction|amount)",
        r"(block|freeze|close).*(account)",
        r"file.*sar|suspicious activity",
    ]

    @classmethod
    def classify(cls, query: str) -> QueryComplexity:
        """Classify a user query by complexity."""
        query_lower = query.lower()

        # Check critical first (highest priority)
        for pattern in cls.CRITICAL_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.CRITICAL

        # Check complex
        for pattern in cls.COMPLEX_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.COMPLEX

        # Check simple
        for pattern in cls.SIMPLE_PATTERNS:
            if re.search(pattern, query_lower):
                return QueryComplexity.SIMPLE

        # Default to moderate
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

    # Tool risk levels
    TOOL_RISK_MAP: dict[str, ToolRiskLevel] = {
        # Safe — read-only
        "knowledge_search": ToolRiskLevel.SAFE,
        "get_document_schema": ToolRiskLevel.SAFE,
        "get_case": ToolRiskLevel.SAFE,
        "lookup_customer": ToolRiskLevel.SAFE,
        "assess_kyc_risk": ToolRiskLevel.SAFE,
        # Low — minor side effects
        "extract_and_classify_document": ToolRiskLevel.LOW,
        "notify_customer": ToolRiskLevel.LOW,
        # Medium — significant side effects
        "verify_customer_identity": ToolRiskLevel.MEDIUM,
        "screen_customer_sanctions": ToolRiskLevel.MEDIUM,
        "open_compliance_case": ToolRiskLevel.MEDIUM,
        # High — irreversible, requires approval
        "create_bank_account": ToolRiskLevel.HIGH,
        "update_case": ToolRiskLevel.HIGH,
    }

    # Sensitive data patterns to redact from logs
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
        """
        Check if a tool call is allowed.

        Returns: (allowed, reason, risk_level)
        """
        risk = self.get_tool_risk(tool_name)

        if risk == ToolRiskLevel.HIGH or requires_approval:
            return False, f"Tool '{tool_name}' requires human approval (risk={risk.value})", risk

        return True, "OK", risk

    def check_output(self, response: str) -> tuple[bool, str]:
        """Check if the generated response is safe to send."""
        # Check for sensitive data leaks
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            if re.search(pattern, response):
                return False, f"Response may contain sensitive data: {replacement}"

        # Check for prompt injection attempts
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

    def redact敏感数据(self, text: str) -> str:
        """Redact sensitive data from text for logging."""
        redacted = text
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted)
        return redacted


# ══════════════════════════════════════════════════════════════════
#  HUMAN-IN-THE-LOOP
# ══════════════════════════════════════════════════════════════════

class HumanApprovalManager:
    """
    Manages human-in-the-loop approval for high-risk actions.

    Supports:
    - Callback-based approval (production: integrate with Slack, email, UI)
    - Auto-approve for development/testing
    - Approval timeout with configurable behavior
    """

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
        """
        Request human approval for a tool call.

        In production:
        - Send Slack/email notification
        - Wait for approval via webhook
        - Log approval request for audit

        Returns: (approved, reason)
        """
        approval_id = str(uuid.uuid4())

        # Auto-approve in dev mode
        if self.auto_approve:
            logger.info("Auto-approving tool call %s (dev mode)", tool_call.name)
            return True, "Auto-approved (dev mode)"

        # Create approval request
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

        # Notify approver (callback or default behavior)
        if self.on_approval_needed:
            await self.on_approval_needed(request)
        else:
            # Default: log and simulate approval
            logger.warning(
                "APPROVAL REQUIRED: Tool=%s, Risk=%s, Args=%s",
                tool_call.name,
                risk_level.value,
                json.dumps(tool_call.arguments)[:200],
            )
            # In real system, this would block and wait
            # For demo, we auto-approve with a warning
            print(f"\n⚠️  APPROVAL REQUIRED")
            print(f"   Tool: {tool_call.name}")
            print(f"   Risk: {risk_level.value}")
            print(f"   Args: {json.dumps(tool_call.arguments, indent=2)}")
            response = input("   Approve? (yes/no): ").strip().lower()
            approved = response in ("yes", "y", "1", "true")

        if approved:
            request["status"] = "approved"
            return True, f"Approved by human operator"
        else:
            request["status"] = "rejected"
            return False, f"Rejected by human operator"

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
    """
    Manages conversation history with:
    - Token counting (tiktoken or approximation)
    - Sliding window truncation
    - Message summarization
    - Key facts extraction
    """

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
        self._key_facts: list[str] = []  # Extracted facts for long-term memory
        self._total_tokens = 0

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count.
        Rough estimate: 1 token ≈ 4 characters for English.
        For production, use tiktoken or model-specific tokenizer.
        """
        return len(text) // 4

    def add(self, role: str, content: str, is_key_fact: bool = False) -> None:
        """Add a message with automatic token tracking and truncation."""
        tokens = self._estimate_tokens(content)
        msg = Message(role=role, content=content, token_estimate=tokens)
        self.messages.append(msg)
        self._total_tokens += tokens

        # Extract key facts if flagged
        if is_key_fact:
            self._key_facts.append(content[:200])

        # Truncation if over limits
        self._maybe_truncate()

    def _maybe_truncate(self) -> None:
        """Truncate messages if over token or count limits."""
        needs_truncation = (
            self._total_tokens > self.max_tokens
            or len(self.messages) > self.max_messages
        )

        if not needs_truncation:
            return

        # Strategy: Keep system context (first message), summarize middle, keep recent
        while (
            self._total_tokens > self.max_tokens
            and len(self.messages) > 6
        ):
            # Remove oldest non-system message
            removed = self.messages.pop(1)
            self._total_tokens -= removed.token_estimate

        # Also enforce message count
        while len(self.messages) > self.max_messages:
            removed = self.messages.pop(1)
            self._total_tokens -= removed.token_estimate

        logger.debug("Memory truncated: %d messages, ~%d tokens", len(self.messages), self._total_tokens)

    def get_context(self) -> list[dict]:
        """Return messages as LLM-compatible format."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def get_context_with_summary(self) -> list[dict]:
        """
        Return messages with older messages summarized.
        Useful when context window is tight.
        """
        if len(self.messages) <= 6:
            return self.get_context()

        # Summarize older messages
        old_messages = self.messages[1:-4]  # Skip first, keep last 4
        summary = self._summarize_messages(old_messages)

        result = [self.messages[0].__dict__()]  # First message (system)
        result.append({
            "role": "system",
            "content": f"[Conversation summary so far]\n{summary}\n\nKey facts: {self._key_facts}",
        })
        result.extend([{"role": m.role, "content": m.content} for m in self.messages[-4:]])
        return result

    def _summarize_messages(self, messages: list[Message]) -> str:
        """Create a concise summary of messages."""
        if not messages:
            return ""

        summary_parts = []
        for msg in messages:
            if msg.role == "user":
                summary_parts.append(f"User asked: {msg.content[:100]}")
            elif msg.role == "assistant":
                summary_parts.append(f"Agent responded about: {msg.content[:80]}")
            elif msg.role == "tool":
                summary_parts.append(f"Tool returned results")

        return "; ".join(summary_parts)

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
        """Export memory for persistence."""
        return {
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in self.messages
            ],
            "key_facts": self._key_facts,
        }

    def load_session(self, data: dict) -> None:
        """Restore memory from persistence."""
        self.clear()
        for msg in data.get("messages", []):
            self.add(msg["role"], msg["content"])
        self._key_facts = data.get("key_facts", [])


# ══════════════════════════════════════════════════════════════════
#  OBSERVABILITY
# ══════════════════════════════════════════════════════════════════

class AgentTracer:
    """
    Structured observability for agent execution.

    Creates traces with spans for every operation:
    - LLM calls
    - Tool executions
    - Guardrails checks
    - Approval requests
    """

    def __init__(self) -> None:
        self._spans: list[TraceSpan] = []
        self._current_span_id: str | None = None

    def start_span(self, name: str, attributes: dict | None = None) -> str:
        """Start a new trace span. Returns span_id."""
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
        """End a trace span."""
        for span in self._spans:
            if span.span_id == span_id:
                span.end_time = time.time()
                span.status = status
                if attributes:
                    span.attributes.update(attributes)
                break

    def add_event(self, span_id: str, name: str, attributes: dict | None = None) -> None:
        """Add an event to a span."""
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
        """Get a summary of the trace."""
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
            "spans": [
                {
                    "name": s.name,
                    "duration_ms": round(s.duration_ms, 2),
                    "status": s.status,
                }
                for s in self._spans
            ],
        }

    def export_json(self) -> str:
        """Export trace as JSON for logging/monitoring."""
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
        """Return OpenAI-compatible function schemas for all tools."""
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
        """Return formatted tool descriptions for prompt injection."""
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
    """
    Handles errors with retry logic, fallback strategies, and recovery.
    """

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5) -> None:
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._error_counts: dict[str, int] = {}

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if an operation should be retried."""
        if attempt >= self.max_retries:
            return False

        # Don't retry on certain errors
        non_retryable = [
            "authentication",
            "permission",
            "not found",
            "invalid",
        ]
        error_str = str(error).lower()
        for term in non_retryable:
            if term in error_str:
                return False

        return True

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
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
        """Execute an operation with retry logic and tracing."""
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
                logger.warning(
                    "Retry %d/%d for %s after %.1fs: %s",
                    attempt + 1, self.max_retries, operation_name, delay, e,
                )
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

        # Core components
        self.rag = RAGPipeline()
        self.tools = ToolRegistry()
        self.memory = ConversationMemory(max_tokens=8000)
        self.guardrails = Guardrails()
        self.intent_router = IntentRouter()
        self.approval_manager = HumanApprovalManager(auto_approve=auto_approve)
        self.error_handler = ErrorHandler(max_retries=max_retries)
        self.tracer = AgentTracer()

        # Observability counters
        self._total_llm_tokens = {"prompt": 0, "completion": 0}

        # Register built-in RAG tool
        self._register_rag_tools()

    def _register_rag_tools(self) -> None:
        """Register the RAG knowledge search tool."""
        self.tools.register(
            name="knowledge_search",
            description="Search the KYC knowledge base for regulations, policies, and past decisions",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "collection": {
                        "type": "string",
                        "enum": ["all", "kyc_regulations", "product_policies",
                                 "document_schemas", "risk_typologies", "past_kyc_decisions"],
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

    # ── Abstract method ──────────────────────────────────────────
    @abstractmethod
    async def call_llm(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Call the LLM backend. Must return standard format."""
        ...

    # ── Simple RAG response (no tools) ──────────────────────────
    async def _simple_rag_response(self, query: str) -> AgentResponse:
        """Handle simple queries with direct RAG retrieval — no LLM needed."""
        rag_result = self.rag.query(query, top_k=5)

        answer_parts = []
        for i, chunk in enumerate(rag_result.chunks, 1):
            source = chunk.metadata.get("source", "knowledge base")
            answer_parts.append(f"{i}. ({source}) {chunk.text[:200]}")

        answer = f"Based on our knowledge base:\n\n" + "\n\n".join(answer_parts)

        return AgentResponse(
            answer=answer,
            rag_sources=[{"text": c.text[:200], "score": c.score} for c in rag_result.chunks],
            complexity=QueryComplexity.SIMPLE,
            metrics={"route": "simple_rag", "rag_chunks": len(rag_result.chunks)},
        )

    # ── Tool execution with approval ────────────────────────────
    async def execute_tool(self, tool_call: ToolCall) -> ToolCall:
        """Execute a tool call with guardrails, approval, and retry."""
        span_id = self.tracer.start_span(f"tool:{tool_call.name}", {"args": str(tool_call.arguments)[:200]})

        handler = self.tools.get_handler(tool_call.name)
        if not handler:
            tool_call.error = f"Unknown tool: {tool_call.name}"
            tool_call.risk_level = ToolRiskLevel.HIGH
            self.tracer.end_span(span_id, "error", {"error": tool_call.error})
            return tool_call

        # Get risk level
        tool_info = self.tools.get_tool_info(tool_call.name)
        tool_call.risk_level = tool_info.get("risk_level", ToolRiskLevel.MEDIUM) if tool_info else ToolRiskLevel.MEDIUM

        # Guardrails check
        allowed, reason, risk = self.guardrails.check_tool_call(tool_call.name, tool_call.arguments)
        if not allowed:
            # Request human approval
            self.tracer.add_event(span_id, "approval_requested", {"risk": risk.value})
            approved, approval_reason = await self.approval_manager.request_approval(
                tool_call, risk, context=f"Tool: {tool_call.name}"
            )
            tool_call.approved = approved
            tool_call.approval_reason = approval_reason
            self.tracer.add_event(span_id, "approval_result", {"approved": approved})

            if not approved:
                tool_call.error = f"Rejected by human: {approval_reason}"
                self.tracer.end_span(span_id, "error", {"rejected": True})
                return tool_call

        # Execute with retry
        async def _do_execute():
            start = time.time()
            result = await handler(**tool_call.arguments)
            tool_call.result = result
            tool_call.duration_ms = (time.time() - start) * 1000
            return result

        try:
            await self.error_handler.with_retry(
                _do_execute, f"tool:{tool_call.name}", self.tracer
            )
            tool_call.retry_count = self.error_handler._error_counts.get(tool_call.name, 0)
            logger.info("Tool %s executed in %.0fms", tool_call.name, tool_call.duration_ms)
        except Exception as e:
            tool_call.error = f"Failed after retries: {str(e)}"
            logger.error("Tool %s failed: %s", tool_call.name, e)

        self.tracer.end_span(span_id, "ok" if not tool_call.error else "error", {
            "duration_ms": tool_call.duration_ms,
            "retry_count": tool_call.retry_count,
        })
        return tool_call

    # ── Main agent loop ─────────────────────────────────────────
    async def run(self, user_query: str) -> AgentResponse:
        """
        Full agent loop with all production patterns.
        """
        trace_start = time.time()
        self.tracer = AgentTracer()  # Reset trace for new run
        span_id = self.tracer.start_span("agent_run", {"query": user_query[:200]})

        # ── Step 1: Intent routing ──
        complexity = self.intent_router.classify(user_query)
        logger.info("Query classified as: %s", complexity.value)

        # Simple queries → direct RAG, skip LLM
        if complexity == QueryComplexity.SIMPLE:
            self.tracer.end_span(span_id, "ok", {"route": "simple_rag"})
            response = await self._simple_rag_response(user_query)
            response.trace = self.tracer.get_trace()
            return response

        # ── Step 2: Add to memory ──
        self.memory.add("user", user_query)

        # ── Step 3: Build system prompt ──
        system_prompt = self._build_system_prompt(complexity)

        # ── Step 4: ReAct loop ──
        steps: list[AgentStep] = []
        all_tool_calls: list[ToolCall] = []
        rag_sources: list[dict] = []
        final_answer = "I was unable to process your request."

        for step_num in range(1, self.max_steps + 1):
            step_span = self.tracer.start_span(f"step:{step_num}")
            step = AgentStep(step_number=step_num, thought="", complexity=complexity, status=StepStatus.RUNNING)

            # Build messages
            messages = [{"role": "system", "content": system_prompt}] + self.memory.get_context()

            # Call LLM
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

            # Track token usage
            self._total_llm_tokens["prompt"] += usage.get("prompt_tokens", 0)
            self._total_llm_tokens["completion"] += usage.get("completion_tokens", 0)

            step.thought = content

            # If no tool calls → final answer
            if not tool_calls_raw or finish_reason == "stop":
                step.is_final = True
                step.status = StepStatus.COMPLETED
                step.observation = content
                steps.append(step)
                self.memory.add("assistant", content)
                final_answer = content
                self.tracer.end_span(step_span, "ok", {"final": True})
                break

            # Execute tool calls
            for tc_raw in tool_calls_raw:
                tool_call = ToolCall(
                    id=tc_raw.get("id", str(uuid.uuid4())[:8]),
                    name=tc_raw["name"],
                    arguments=tc_raw.get("arguments", {}),
                )
                tool_call = await self.execute_tool(tool_call)
                all_tool_calls.append(tool_call)
                step.tool_calls.append(tool_call)

                # Collect RAG sources
                if tool_call.name == "knowledge_search" and tool_call.result:
                    rag_sources.extend(tool_call.result.get("chunks", []))

            # Build observation
            observations = []
            for tc in step.tool_calls:
                if tc.result:
                    observations.append(f"[{tc.name}] {json.dumps(tc.result)[:500]}")
                elif tc.error:
                    observations.append(f"[{tc.name}] ERROR: {tc.error}")

            step.observation = "\n".join(observations)
            step.status = StepStatus.COMPLETED
            steps.append(step)

            # Update memory
            self.memory.add("assistant", f"Thought: {content}")
            self.memory.add("tool", f"Tool results:\n{step.observation}", is_key_fact=True)

            self.tracer.end_span(step_span, "ok", {
                "tool_calls": len(step.tool_calls),
                "observation_len": len(step.observation),
            })

        # ── Step 5: Output guardrails ──
        allowed, reason = self.guardrails.check_output(final_answer)
        if not allowed:
            final_answer = f"I cannot provide that response due to safety restrictions."

        self.tracer.end_span(span_id, "ok", {"complexity": complexity.value})
        total_duration = (time.time() - trace_start) * 1000

        # Build metrics
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
        """Build system prompt with complexity-aware instructions."""
        base_prompt = f"""You are a KYC Onboarding Agent for a bank. You help process Know Your Customer applications.

You have access to the following tools:
{self.tools.get_tool_descriptions()}

Query complexity: {complexity.value}
"""

        if complexity == QueryComplexity.COMPLEX:
            base_prompt += """
This is a complex query. Plan your approach:
1. Identify what information you need
2. Call tools in the right order
3. Verify results before proceeding
4. If risk is medium/high, open a compliance case
"""
        elif complexity == QueryComplexity.CRITICAL:
            base_prompt += """
This is a critical query involving high-risk actions.
IMPORTANT: You MUST explain your reasoning clearly before calling any tools.
High-risk tools (create_bank_account, update_case) require human approval.
"""
        else:
            base_prompt += """
Be efficient. Minimize tool calls. If you can answer from retrieved context, do so.
"""

        base_prompt += f"""
Rules:
1. Always search knowledge base first if unsure about regulations
2. Explain your reasoning before calling tools
3. Never fabricate information
4. Be professional and concise
5. If a tool fails, explain and suggest alternatives

Current step: {self._step_count}/{self.max_steps}
"""
        return base_prompt
