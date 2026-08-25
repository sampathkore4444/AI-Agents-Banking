"""
Base AML Alert Agent — Common patterns for AML detection with LLMs.

Includes:
- Guardrails for AML decisions (SAR/CTR thresholds, filing deadlines)
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
#  GUARDRAILS — AML-specific input/output validation
# ══════════════════════════════════════════════════════════════════

class AMLGuardrails:
    """AML-specific guardrails for agent decisions."""

    SAR_THRESHOLD = 5000.0
    CTR_THRESHOLD = 10000.0
    SAR_FILING_DEADLINE_DAYS = 30
    CTR_FILING_DEADLINE_DAYS = 15
    MAX_CASE_AGE_DAYS = 90

    BLOCKED_DECISIONS = {"file_sar", "escalate_law_enforcement", "block_account"}
    REQUIRES_APPROVAL = {"file_sar", "escalate_law_enforcement", "block_account", "close_account"}

    @classmethod
    def validate_transaction(cls, data: dict) -> dict[str, Any]:
        errors = []
        if not data.get("transaction_id"):
            errors.append("transaction_id is required")
        if not data.get("customer_id"):
            errors.append("customer_id is required")
        if data.get("amount", 0) < 0:
            errors.append("Amount cannot be negative")
        if not data.get("currency"):
            errors.append("Currency is required")
        return {"valid": len(errors) == 0, "errors": errors}

    @classmethod
    def validate_sar_filing(cls, data: dict) -> dict[str, Any]:
        errors = []
        if not data.get("customer_name"):
            errors.append("customer_name is required for SAR")
        if not data.get("suspicious_activity_type"):
            errors.append("suspicious_activity_type is required")
        if not data.get("activity_description"):
            errors.append("activity_description is required (narrative)")
        if data.get("amount_involved", 0) < cls.SAR_THRESHOLD:
            errors.append(f"Amount ${data.get('amount_involved', 0):,.2f} is below SAR threshold ${cls.SAR_THRESHOLD:,.2f}")
        return {"valid": len(errors) == 0, "errors": errors}

    @classmethod
    def check_filing_deadline(cls, detection_date: str, filing_type: str = "sar") -> dict[str, Any]:
        try:
            detected = datetime.fromisoformat(detection_date)
            now = datetime.utcnow()
            days_elapsed = (now - detected).days
            deadline = cls.SAR_FILING_DEADLINE_DAYS if filing_type == "sar" else cls.CTR_FILING_DEADLINE_DAYS
            days_remaining = deadline - days_elapsed
            return {
                "overdue": days_remaining < 0,
                "days_elapsed": days_elapsed,
                "days_remaining": max(days_remaining, 0),
                "deadline_days": deadline,
                "urgency": "critical" if days_remaining <= 5 else "high" if days_remaining <= 10 else "normal",
            }
        except (ValueError, TypeError):
            return {"error": "Invalid date format"}


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

class AMLAlertAgent:
    """Base AML alert agent with guardrails, HITL, and memory."""

    SYSTEM_PROMPT = """You are an Anti-Money Laundering (AML) Alert Agent for a bank.

Your responsibilities:
1. Monitor transactions for AML red flags (structuring, layering, trade-based ML)
2. Screen individuals and entities against sanctions lists (OFAC, EU, UN)
3. Identify and assess PEP risks
4. Create and manage SARs (Suspicious Activity Reports)
5. File CTRs (Currency Transaction Reports) for cash ≥ $10,000
6. Identify and verify beneficial owners of legal entities
7. Manage AML investigation cases from detection through resolution
8. Ensure compliance with BSA, PATRIOT Act, and OFAC regulations

Key principles:
- Never tip off subjects of investigations (federal crime)
- Always document decisions for audit trail
- File SARs within 30 days of detection
- File CTRs within 15 calendar days
- Apply risk-based approach to due diligence
- Escalate high-risk cases immediately

When you detect suspicious activity:
1. Assess the risk level and red flags
2. Screen involved parties against sanctions/PEP lists
3. Determine if SAR/CTR filing is required
4. Create an investigation case if needed
5. Document all findings with evidence
6. Escalate to law enforcement if warranted

Compliance reminders:
- BSA: SAR for $5,000+ suspicious activity
- BSA: CTR for $10,000+ cash transactions
- OFAC: Block SDN-listed persons (strict liability)
- PATRIOT Act: Enhanced due diligence for high-risk accounts
- Corporate Transparency Act: Beneficial ownership reporting
"""

    def __init__(self, llm_client: Any = None, model_name: str = "gpt-4o") -> None:
        self.llm_client = llm_client
        self.model_name = model_name
        self.guardrails = AMLGuardrails()
        self.hitl = HumanInTheLoop()
        self.memory = AgentMemory()
        self._trace_id = str(uuid.uuid4())

    async def analyze_transaction(self, transaction: dict) -> dict[str, Any]:
        """Analyze a transaction with AML guardrails."""
        validation = self.guardrails.validate_transaction(transaction)
        if not validation["valid"]:
            return {"error": "Validation failed", "errors": validation["errors"]}

        context = self.memory.get_context(last_n=5)
        prompt = f"Analyze this transaction for AML red flags:\n{json.dumps(transaction, indent=2)}"

        self.memory.add("user", f"Analyze transaction {transaction.get('transaction_id')}", transaction_id=transaction.get("transaction_id"))

        response = await self._call_llm(prompt, context)
        self.memory.add("assistant", response, transaction_id=transaction.get("transaction_id"))

        return {"response": response, "transaction_id": transaction.get("transaction_id"), "trace_id": self._trace_id}

    async def make_filing_decision(self, activity_type: str, amount: float, customer_id: str) -> dict[str, Any]:
        """Decide on SAR/CTR filing with guardrails and HITL."""
        requires_sar = amount >= self.guardrails.SAR_THRESHOLD and activity_type in ("structuring", "layering", "trade_based_ml", "terrorist_financing", "shell_company")
        requires_ctr = amount >= self.guardrails.CTR_THRESHOLD

        decision = "no_action"
        if requires_sar:
            decision = "file_sar"
        elif requires_ctr:
            decision = "file_ctr"

        if decision in self.guardrails.REQUIRES_APPROVAL:
            approval = await self.hitl.request_approval(
                decision,
                {"customer_id": customer_id, "amount": amount, "activity_type": activity_type},
                "critical" if requires_sar else "high",
            )
            return {"decision": decision, "status": "awaiting_approval", "approval_id": approval.request_id}

        self.memory.add("decision", f"Decision: {decision} for {customer_id}", customer_id=customer_id)
        return {"decision": decision, "status": "auto_approved", "requires_sar": requires_sar, "requires_ctr": requires_ctr}

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

    async def stream_analysis(self, transaction: dict) -> AsyncIterator[str]:
        """Stream analysis results."""
        yield f"🔍 Analyzing transaction {transaction.get('transaction_id', 'unknown')}...\n"
        yield f"   Amount: ${transaction.get('amount', 0):,.2f}\n"
        yield f"   Type: {transaction.get('transaction_type', 'unknown')}\n"
        yield f"   Country: {transaction.get('country', 'unknown')}\n"
        yield "⏳ Running AML rules...\n"
        await time.sleep(0.1)
        yield "✅ Analysis complete.\n"
