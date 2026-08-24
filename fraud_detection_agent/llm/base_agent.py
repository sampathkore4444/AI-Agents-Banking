"""
Base Fraud Detection Agent — Common patterns for fraud detection with LLMs.

Includes:
- Guardrails for fraud decisions (block/allow thresholds)
- Human-in-the-loop for high-risk decisions
- Memory for investigation context
- Streaming for real-time alerts
- Observability with OpenTelemetry
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
#  GUARDRAILS — Fraud-specific input/output validation
# ══════════════════════════════════════════════════════════════════

class FraudGuardrails:
    """Fraud-specific guardrails for agent decisions."""

    BLOCK_THRESHOLD = 85
    REVIEW_THRESHOLD = 60
    ALERT_THRESHOLD = 40
    MAX_TRANSACTION_AMOUNT = 1_000_000

    BLOCKED_DECISIONS = {"block_card", "close_account", "file_sar"}
    REQUIRES_APPROVAL = {"block_card", "close_account", "file_sar", "refund"}

    @classmethod
    def validate_transaction(cls, data: dict) -> dict[str, Any]:
        errors = []
        if data.get("amount", 0) > cls.MAX_TRANSACTION_AMOUNT:
            errors.append(f"Amount ${data['amount']:,.2f} exceeds maximum ${cls.MAX_TRANSACTION_AMOUNT:,.2f}")
        if not data.get("customer_id"):
            errors.append("customer_id is required")
        if not data.get("transaction_id"):
            errors.append("transaction_id is required")
        return {"valid": len(errors) == 0, "errors": errors}

    @classmethod
    def validate_decision(cls, decision: str, fraud_score: int) -> dict[str, Any]:
        errors = []
        if decision in cls.BLOCKED_DECISIONS and fraud_score < cls.BLOCK_THRESHOLD:
            errors.append(f"Cannot {decision} with fraud score {fraud_score} (threshold: {cls.BLOCK_THRESHOLD})")
        if decision in cls.REQUIRES_APPROVAL:
            return {"valid": len(errors) == 0, "errors": errors, "requires_approval": True}
        return {"valid": len(errors) == 0, "errors": errors, "requires_approval": False}

    @classmethod
    def check_hours(cls) -> bool:
        now = datetime.utcnow()
        return 6 <= now.hour <= 22


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

    async def request_approval(self, action: str, context: dict, risk_level: str = "high") -> HumanApprovalRequest:
        req = HumanApprovalRequest(action=action, context=context, risk_level=risk_level)
        self._pending[req.request_id] = req
        logger.warning(f"⏳ HUMAN APPROVAL REQUIRED: {action} (risk: {risk_level}) — ID: {req.request_id}")
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

    def get_investigation_context(self) -> str:
        investigation = [e for e in self._entries if e.metadata.get("case_id")]
        return "\n".join(f"[{e.role}] {e.content}" for e in investigation[-20:])


# ══════════════════════════════════════════════════════════════════
#  BASE AGENT
# ══════════════════════════════════════════════════════════════════

class FraudDetectionAgent:
    """Base fraud detection agent with guardrails, HITL, and memory."""

    SYSTEM_PROMPT = """You are a Real-Time Transaction Fraud Detection Agent for a bank.

Your responsibilities:
1. Analyze transactions for fraud indicators in real-time
2. Score transactions using rules and ML-based anomaly detection
3. Take appropriate action (allow, alert, review, block)
4. Manage fraud cases from detection through resolution
5. Ensure compliance with Reg E, Reg Z, and BSA requirements
6. Protect customer accounts from unauthorized access

Key principles:
- False positives are costly but false negatives are worse
- Always err on the side of customer protection
- Document all decisions for audit trail
- Escalate high-risk cases immediately
- Never disclose investigation details to customers (tipping off)

When you detect fraud:
1. Assess the risk level (low/medium/high/critical)
2. Take immediate protective action (block if critical)
3. Notify the customer through appropriate channels
4. Create a case and begin investigation
5. Document all findings

Compliance reminders:
- Reg E: 10-day investigation, 45-day resolution
- Reg Z: 60-day dispute window
- BSA: SAR required for $5,000+ suspicious transactions
- Never disclose SAR filing to the subject
"""

    def __init__(self, llm_client: Any = None, model_name: str = "gpt-4o") -> None:
        self.llm_client = llm_client
        self.model_name = model_name
        self.guardrails = FraudGuardrails()
        self.hitl = HumanInTheLoop()
        self.memory = AgentMemory()
        self._trace_id = str(uuid.uuid4())

    async def analyze_transaction(self, transaction: dict) -> dict[str, Any]:
        """Analyze a transaction with guardrails."""
        validation = self.guardrails.validate_transaction(transaction)
        if not validation["valid"]:
            return {"error": "Validation failed", "errors": validation["errors"]}

        context = self.memory.get_context(last_n=5)
        prompt = f"Analyze this transaction for fraud:\n{json.dumps(transaction, indent=2)}"

        self.memory.add("user", f"Analyze transaction {transaction.get('transaction_id')}", transaction_id=transaction.get("transaction_id"))

        response = await self._call_llm(prompt, context)
        self.memory.add("assistant", response, transaction_id=transaction.get("transaction_id"))

        return {"response": response, "transaction_id": transaction.get("transaction_id"), "trace_id": self._trace_id}

    async def make_decision(self, fraud_score: int, transaction_id: str, customer_id: str) -> dict[str, Any]:
        """Make a fraud decision with guardrails and HITL."""
        if fraud_score >= self.guardrails.BLOCK_THRESHOLD:
            decision = "block"
        elif fraud_score >= self.guardrails.REVIEW_THRESHOLD:
            decision = "review"
        elif fraud_score >= self.guardrails.ALERT_THRESHOLD:
            decision = "alert"
        else:
            decision = "allow"

        validation = self.guardrails.validate_decision(decision, fraud_score)
        if validation.get("requires_approval"):
            approval = await self.hitl.request_approval(decision, {"transaction_id": transaction_id, "customer_id": customer_id, "fraud_score": fraud_score}, "critical")
            return {"decision": decision, "status": "awaiting_approval", "approval_id": approval.request_id}

        self.memory.add("decision", f"Decision: {decision} for {transaction_id}", transaction_id=transaction_id, customer_id=customer_id)
        return {"decision": decision, "status": "executed", "fraud_score": fraud_score}

    async def _call_llm(self, prompt: str, context: str = "") -> str:
        if self.llm_client:
            try:
                messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
                if context:
                    messages.append({"role": "user", "content": f"Context:\n{context}"})
                messages.append({"role": "user", "content": prompt})
                response = await self.llm_client.chat.completions.create(model=self.model_name, messages=messages, max_tokens=1000, temperature=0.1)
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return f"LLM unavailable. Error: {e}"
        return f"[Simulation] Analyzing: {prompt[:200]}..."

    async def stream_analysis(self, transaction: dict) -> AsyncIterator[str]:
        """Stream analysis results."""
        yield f"🔍 Analyzing transaction {transaction.get('transaction_id', 'unknown')}...\n"
        yield f"   Amount: ${transaction.get('amount', 0):,.2f}\n"
        yield f"   Merchant: {transaction.get('merchant_id', 'unknown')}\n"
        yield f"   Channel: {transaction.get('channel', 'unknown')}\n"
        yield "⏳ Running fraud rules...\n"
        await time.sleep(0.1)
        yield "✅ Analysis complete.\n"
