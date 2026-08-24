"""
Base Lead Qualification Agent — Common patterns for lead qualification with LLMs.

Includes:
- Guardrails for qualification (eligibility, scoring thresholds)
- Human-in-the-loop for high-value leads
- Memory for conversation context
- Streaming for real-time qualification
- Observability with trace IDs
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
#  GUARDRAILS — Qualification-specific validation
# ══════════════════════════════════════════════════════════════════

class QualificationGuardrails:
    """Qualification-specific guardrails."""

    MIN_LEAD_SCORE = 30
    AUTO_QUALIFY_SCORE = 80
    ROUTING_THRESHOLD = 60
    MAX_QUALIFICATION_ATTEMPTS = 3

    PRODUCT_REQUIREMENTS = {
        "checking": {"min_age": 18, "requires_ssn": True},
        "savings": {"min_age": 18, "requires_ssn": True},
        "credit_card": {"min_age": 18, "min_credit_score": 670, "min_income": 12000},
        "mortgage": {"min_age": 18, "min_credit_score": 620, "min_income": 40000},
        "auto_loan": {"min_age": 18, "min_credit_score": 660, "min_income": 25000},
        "investment": {"min_age": 18, "requires_earned_income": True},
    }

    @classmethod
    def check_product_eligibility(cls, lead: dict, product: str) -> dict[str, Any]:
        requirements = cls.PRODUCT_REQUIREMENTS.get(product, {})
        errors = []

        if "min_age" in requirements:
            age = lead.get("demographics", {}).get("age", 0)
            if age < requirements["min_age"]:
                errors.append(f"Age {age} below minimum {requirements['min_age']}")
        if "min_credit_score" in requirements:
            credit = lead.get("demographics", {}).get("credit_score", 0)
            if credit < requirements["min_credit_score"]:
                errors.append(f"Credit score {credit} below minimum {requirements['min_credit_score']}")
        if "min_income" in requirements:
            income = lead.get("demographics", {}).get("income", 0)
            if income < requirements["min_income"]:
                errors.append(f"Income ${income:,.0f} below minimum ${requirements['min_income']:,.0f}")

        return {"eligible": len(errors) == 0, "errors": errors}

    @classmethod
    def validate_qualification(cls, lead: dict, score: int) -> dict[str, Any]:
        errors = []
        if score < cls.MIN_LEAD_SCORE:
            errors.append(f"Lead score {score} below minimum {cls.MIN_LEAD_SCORE}")
        if not lead.get("email"):
            errors.append("Email is required")
        if not lead.get("phone"):
            errors.append("Phone is required")
        return {"valid": len(errors) == 0, "errors": errors}


# ══════════════════════════════════════════════════════════════════
#  HUMAN-IN-THE-LOOP
# ══════════════════════════════════════════════════════════════════

@dataclass
class HumanApprovalRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    context: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"
    approved_by: str | None = None


class HumanInTheLoop:
    def __init__(self) -> None:
        self._pending: dict[str, HumanApprovalRequest] = {}

    async def request_approval(self, action: str, context: dict) -> HumanApprovalRequest:
        req = HumanApprovalRequest(action=action, context=context)
        self._pending[req.request_id] = req
        logger.warning(f"⏳ HUMAN APPROVAL REQUIRED: {action} — ID: {req.request_id}")
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

    def get_lead_context(self, lead_id: str) -> str:
        lead_entries = [e for e in self._entries if e.metadata.get("lead_id") == lead_id]
        return "\n".join(f"[{e.role}] {e.content}" for e in lead_entries[-10:])


# ══════════════════════════════════════════════════════════════════
#  BASE AGENT
# ══════════════════════════════════════════════════════════════════

class LeadQualificationAgent:
    """Base lead qualification agent with guardrails, HITL, and memory."""

    SYSTEM_PROMPT = """You are a Lead Qualification Agent for a bank.

Your responsibilities:
1. Qualify inbound leads from web, chat, referrals
2. Score lead intent and urgency
3. Evaluate against qualification frameworks (BANT, CHAMP, MEDDIC)
4. Route qualified leads to appropriate sales teams
5. Book consultations with advisors
6. Execute sales playbooks for different products
7. Ensure TCPA/DNC compliance for outreach

Key principles:
- Speed to lead: respond within 5 minutes
- Be helpful, not pushy
- Gather qualification data naturally in conversation
- Respect customer time and preferences
- Document all interactions in CRM
- Never make promises about rates or terms without approval

Qualification frameworks:
- BANT: Budget, Authority, Need, Timeline
- CHAMP: Challenges, Authority, Money, Prioritization
- MEDDIC: Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion

When qualifying a lead:
1. Identify their primary product interest
2. Assess their timeline and urgency
3. Verify eligibility (credit score, income)
4. Score their intent level
5. Route to appropriate team/booking
6. Send follow-up materials

Compliance reminders:
- TCPA: Check DNC before calling, 8am-9pm only
- Record consent for all outreach
- Fair lending: same criteria for all leads
"""


    def __init__(self, llm_client: Any = None, model_name: str = "gpt-4o") -> None:
        self.llm_client = llm_client
        self.model_name = model_name
        self.guardrails = QualificationGuardrails()
        self.hitl = HumanInTheLoop()
        self.memory = AgentMemory()
        self._trace_id = str(uuid.uuid4())

    async def qualify_lead(self, lead: dict) -> dict[str, Any]:
        """Qualify a lead with guardrails."""
        product = lead.get("product_interest", "")
        eligibility = self.guardrails.check_product_eligibility(lead, product)

        context = self.memory.get_lead_context(lead.get("lead_id", ""))
        prompt = f"Qualify lead {lead.get('first_name', '')} {lead.get('last_name', '')} for {product}."

        self.memory.add("user", f"Qualification request for {lead.get('lead_id')}", lead_id=lead.get("lead_id"))

        response = await self._call_llm(prompt, context)
        self.memory.add("assistant", response, lead_id=lead.get("lead_id"))

        return {"response": response, "lead_id": lead.get("lead_id"), "product": product, "eligible": eligibility["eligible"], "trace_id": self._trace_id}

    async def _call_llm(self, prompt: str, context: str = "") -> str:
        if self.llm_client:
            try:
                messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
                if context:
                    messages.append({"role": "user", "content": f"Context:\n{context}"})
                messages.append({"role": "user", "content": prompt})
                response = await self.llm_client.chat.completions.create(model=self.model_name, messages=messages, max_tokens=1000, temperature=0.3)
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return f"LLM unavailable. Error: {e}"
        return f"[Simulation] Qualifying lead: {prompt[:200]}..."

    async def stream_qualification(self, lead: dict) -> AsyncIterator[str]:
        """Stream qualification results."""
        yield f"Qualifying lead {lead.get('first_name', '')} {lead.get('last_name', '')}...\n"
        yield f"Product interest: {lead.get('product_interest', 'unknown')}\n"
        yield f"Source: {lead.get('source', 'unknown')}\n"
        yield "Checking eligibility...\n"
        await time.sleep(0.1)
        yield "✅ Qualification complete.\n"
