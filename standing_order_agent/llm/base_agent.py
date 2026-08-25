"""
Base Standing Order & Bill Payment Agent — Common patterns for recurring payment management with LLMs.

Includes:
- Guardrails for standing order decisions (amount limits, approval thresholds)
- Human-in-the-loop for high-value changes
- Memory for billing context
- Streaming for real-time status updates
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  GUARDRAILS — Standing order input/output validation
# ══════════════════════════════════════════════════════════════════

class StandingOrderGuardrails:
    """Standing order-specific guardrails for agent decisions."""

    MAX_SINGLE_AMOUNT = 50_000
    MAX_DAILY_AGGREGATE = 100_000
    REVIEW_THRESHOLD = 10_000
    APPROVAL_THRESHOLD = 25_000
    MAX_ACTIVE_ORDERS = 50
    AMOUNT_CHANGE_REVIEW_PCT = 20

    REQUIRES_APPROVAL = {"create_high_value", "modify_amount_increase", "cancel_all", "change_payee"}
    BLOCKED_ACTIONS = {"create_over_limit", "exceed_daily_aggregate"}

    @classmethod
    def validate_creation(cls, data: dict) -> dict[str, Any]:
        errors = []
        if not data.get("account_id"):
            errors.append("account_id is required")
        if not data.get("payee_name"):
            errors.append("payee_name is required")
        if not data.get("payee_account_number"):
            errors.append("payee_account_number is required")
        if not data.get("payee_routing"):
            errors.append("payee_routing is required")
        amount = data.get("amount", 0)
        if amount <= 0:
            errors.append("Amount must be positive")
        if amount > cls.MAX_SINGLE_AMOUNT:
            errors.append(f"Amount ${amount:,.2f} exceeds single payment limit ${cls.MAX_SINGLE_AMOUNT:,.2f}")
        frequency = data.get("frequency")
        valid_freq = {"once", "daily", "weekly", "biweekly", "monthly", "quarterly", "semi-annual", "annual", "custom"}
        if frequency and frequency not in valid_freq:
            errors.append(f"Invalid frequency: {frequency}")
        if not data.get("start_date"):
            errors.append("start_date is required")
        return {"valid": len(errors) == 0, "errors": errors}

    @classmethod
    def validate_modification(cls, data: dict, current: dict) -> dict[str, Any]:
        errors = []
        new_amount = data.get("amount")
        if new_amount is not None:
            if new_amount <= 0 or new_amount > cls.MAX_SINGLE_AMOUNT:
                errors.append(f"Invalid amount: {new_amount}")
            old_amount = current.get("amount", 0)
            if old_amount > 0:
                pct_change = abs(new_amount - old_amount) / old_amount * 100
                if pct_change > cls.AMOUNT_CHANGE_REVIEW_PCT:
                    return {"valid": len(errors) == 0, "errors": errors, "requires_approval": True}
        return {"valid": len(errors) == 0, "errors": errors, "requires_approval": False}

    @classmethod
    def check_approval_needed(cls, action: str, amount: float = 0) -> bool:
        if action in cls.REQUIRES_APPROVAL:
            return True
        if amount >= cls.APPROVAL_THRESHOLD:
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  HUMAN-IN-THE-LOOP
# ══════════════════════════════════════════════════════════════════

@dataclass
class HumanApprovalRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    context: dict = field(default_factory=dict)
    risk_level: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"
    approved_by: str | None = None


class HumanInTheLoop:
    def __init__(self) -> None:
        self._pending: dict[str, HumanApprovalRequest] = {}

    async def request_approval(self, action: str, context: dict, risk_level: str = "medium") -> HumanApprovalRequest:
        req = HumanApprovalRequest(action=action, context=context, risk_level=risk_level)
        self._pending[req.request_id] = req
        logger.warning(f"HUMAN APPROVAL REQUIRED: {action} (risk: {risk_level}) — ID: {req.request_id}")
        return req

    async def approve(self, request_id: str, approver: str = "system") -> bool:
        if request_id in self._pending:
            self._pending[request_id].status = "approved"
            self._pending[request_id].approved_by = approver
            return True
        return False


# ══════════════════════════════════════════════════════════════════
#  MEMORY
# ══════════════════════════════════════════════════════════════════

@dataclass
class MemoryEntry:
    role: str = ""
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class AgentMemory:
    def __init__(self, max_entries: int = 50) -> None:
        self.max_entries = max_entries
        self._entries: list[MemoryEntry] = []

    def add(self, role: str, content: str, **metadata: Any) -> None:
        self._entries.append(MemoryEntry(role=role, content=content, metadata=metadata))
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

    def get_context(self, last_n: int = 10) -> str:
        recent = self._entries[-last_n:]
        return "\n".join(f"[{e.role}] {e.content}" for e in recent)

    def get_billing_context(self, account_id: str) -> str:
        billing = [e for e in self._entries if e.metadata.get("account_id") == account_id]
        return "\n".join(f"[{e.role}] {e.content}" for e in billing[-20:])


# ══════════════════════════════════════════════════════════════════
#  BASE AGENT
# ══════════════════════════════════════════════════════════════════

class StandingOrderAgent:
    """Base standing order agent with guardrails, HITL, and memory."""

    SYSTEM_PROMPT = """You are a Standing Order & Bill Payment Agent for a bank.

Your responsibilities:
1. Help customers set up, modify, or cancel recurring payments
2. Search and verify billers in the directory
3. Parse natural language payment requests into structured intents
4. Manage payment schedules and calendars
5. Send payment reminders and notifications
6. Detect recurring payment patterns
7. Ensure compliance with Reg E, NACHA, and UDAAP requirements

Key principles:
- Always verify payee/biller information before creating standing orders
- Respect payment limits and approval thresholds
- Provide clear confirmations for all customer actions
- Handle payment failures gracefully with retry logic
- Protect customers from unauthorized recurring payment changes
- Log all actions for audit trail

Standing order lifecycle:
1. Customer requests → Intent parsing → Validation → Creation → Confirmation
2. Scheduled execution → Payment processing → Status update → Notification
3. Modification request → Change validation → Approval (if needed) → Update → Notice
4. Cancellation request → Validation → Cancellation → Confirmation
5. Payment failure → Retry logic → Suspension (if needed) → Customer alert

Common scenarios:
- 'Pay my rent on the 1st of every month' → Monthly standing order to landlord
- 'Set up auto-pay for my electric bill' → Monthly variable amount to utility
- 'Transfer $500 to savings every payday' → Biweekly transfer to savings
- 'Cancel my Netflix standing order' → Cancel subscription payment
"""

    def __init__(self, llm_client: Any = None, model_name: str = "gpt-4o") -> None:
        self.llm_client = llm_client
        self.model_name = model_name
        self.guardrails = StandingOrderGuardrails()
        self.hitl = HumanInTheLoop()
        self.memory = AgentMemory()
        self._trace_id = str(uuid.uuid4())

    async def handle_request(self, request: str, account_id: str | None = None) -> dict[str, Any]:
        """Handle a customer request for standing order management."""
        context = self.memory.get_context(last_n=5)
        prompt = f"Handle this standing order request:\n{request}"

        if account_id:
            billing_ctx = self.memory.get_billing_context(account_id)
            prompt += f"\n\nBilling context for account {account_id}:\n{billing_ctx}"

        self.memory.add("user", request, account_id=account_id or "")
        response = await self._call_llm(prompt, context)
        self.memory.add("assistant", response, account_id=account_id or "")

        return {"response": response, "trace_id": self._trace_id}

    async def validate_and_create(self, order_data: dict) -> dict[str, Any]:
        """Validate and create a standing order with guardrails."""
        validation = self.guardrails.validate_creation(order_data)
        if not validation["valid"]:
            return {"error": "Validation failed", "errors": validation["errors"]}

        amount = order_data.get("amount", 0)
        if self.guardrails.check_approval_needed("create_high_value", amount):
            approval = await self.hitl.request_approval(
                "create_standing_order", order_data,
                "high" if amount >= self.guardrails.APPROVAL_THRESHOLD else "medium",
            )
            return {"status": "awaiting_approval", "approval_id": approval.request_id, "order_data": order_data}

        self.memory.add("order_created", f"Created standing order: ${amount} to {order_data.get('payee_name')}", account_id=order_data.get("account_id"))
        return {"status": "created", "order_data": order_data}

    async def validate_and_modify(self, order_id: str, changes: dict, current: dict) -> dict[str, Any]:
        """Validate and modify a standing order with guardrails."""
        validation = self.guardrails.validate_modification(changes, current)
        if not validation["valid"]:
            return {"error": "Validation failed", "errors": validation["errors"]}

        if validation.get("requires_approval"):
            approval = await self.hitl.request_approval(
                "modify_standing_order", {"order_id": order_id, "changes": changes}, "high",
            )
            return {"status": "awaiting_approval", "approval_id": approval.request_id}

        self.memory.add("order_modified", f"Modified standing order {order_id}: {changes}", account_id=current.get("account_id"))
        return {"status": "modified", "order_id": order_id, "changes": changes}

    async def _call_llm(self, prompt: str, context: str = "") -> str:
        if self.llm_client:
            try:
                messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
                if context:
                    messages.append({"role": "user", "content": f"Context:\n{context}"})
                messages.append({"role": "user", "content": prompt})
                response = await self.llm_client.chat_completions_create(model=self.model_name, messages=messages, max_tokens=1000, temperature=0.1)
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return f"LLM unavailable. Error: {e}"
        return f"[Simulation] Analyzing: {prompt[:200]}..."

    async def stream_status(self, standing_order_id: str, status: str) -> AsyncIterator[str]:
        """Stream standing order status updates."""
        yield f"Standing Order {standing_order_id}...\n"
        yield f"   Status: {status}\n"
        yield "Processing...\n"
        await time.sleep(0.1)
        yield "Complete.\n"
