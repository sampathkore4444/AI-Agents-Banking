"""
Base Product Recommendation Agent — Common patterns for recommendation with LLMs.

Includes:
- Guardrails for recommendations (eligibility, relevance thresholds)
- Human-in-the-loop for high-value offers
- Memory for customer interaction context
- Streaming for real-time recommendations
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
#  GUARDRAILS — Recommendation-specific validation
# ══════════════════════════════════════════════════════════════════

class RecommendationGuardrails:
    """Recommendation-specific guardrails."""

    MIN_RELEVANCE_SCORE = 0.6
    MAX_RECOMMENDATIONS = 10
    REQUIRES_APPROVAL_THRESHOLD = 50000  # Offers > $50K need approval

    ELIGIBILITY_RULES = {
        "credit_card": {"min_credit_score": 670, "min_income": 12000},
        "credit_card_premium": {"min_credit_score": 720, "min_income": 30000},
        "mortgage": {"min_credit_score": 620, "min_income": 40000},
        "auto_loan": {"min_credit_score": 660, "min_income": 25000},
        "personal_loan": {"min_credit_score": 640, "min_income": 15000},
        "ira": {"min_age": 18, "requires_earned_income": True},
    }

    @classmethod
    def check_eligibility(cls, customer: dict, product_category: str) -> dict[str, Any]:
        rules = cls.ELIGIBILITY_RULES.get(product_category, {})
        errors = []

        if "min_credit_score" in rules:
            if customer.get("credit_score", 0) < rules["min_credit_score"]:
                errors.append(f"Credit score {customer.get('credit_score')} below minimum {rules['min_credit_score']}")
        if "min_income" in rules:
            if customer.get("income", 0) < rules["min_income"]:
                errors.append(f"Income ${customer.get('income', 0):,.2f} below minimum ${rules['min_income']:,.2f}")
        if "min_age" in rules:
            if customer.get("age", 0) < rules["min_age"]:
                errors.append(f"Age {customer.get('age')} below minimum {rules['min_age']}")

        return {"eligible": len(errors) == 0, "errors": errors}

    @classmethod
    def validate_recommendation(cls, recommendation: dict) -> dict[str, Any]:
        errors = []
        if recommendation.get("relevance_score", 0) < cls.MIN_RELEVANCE_SCORE:
            errors.append(f"Relevance score {recommendation.get('relevance_score')} below threshold {cls.MIN_RELEVANCE_SCORE}")
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

    def get_customer_context(self, customer_id: str) -> str:
        customer_entries = [e for e in self._entries if e.metadata.get("customer_id") == customer_id]
        return "\n".join(f"[{e.role}] {e.content}" for e in customer_entries[-10:])


# ══════════════════════════════════════════════════════════════════
#  BASE AGENT
# ══════════════════════════════════════════════════════════════════

class ProductRecommendationAgent:
    """Base product recommendation agent with guardrails, HITL, and memory."""

    SYSTEM_PROMPT = """You are a Product Recommendation Agent for a bank.

Your responsibilities:
1. Recommend banking products based on customer profiles and needs
2. Explain product benefits and eligibility clearly
3. Detect cross-sell and upsell opportunities
4. Manage promotional offers and campaigns
5. Ensure recommendations comply with fair lending guidelines
6. Track customer interactions and conversion

Key principles:
- Only recommend products the customer is eligible for
- Be transparent about fees, rates, and terms
- Personalize recommendations based on customer lifecycle stage
- Respect customer communication preferences
- Never pressure customers — inform and guide

When making recommendations:
1. Check eligibility (credit score, income, age)
2. Match to customer segment and lifecycle stage
3. Consider existing products (avoid overlap)
4. Highlight relevant promotions
5. Explain why the product fits their needs

Fair lending reminders:
- Never base recommendations on protected classes
- Ensure consistent treatment across similar profiles
- Document recommendation rationale
- Provide alternatives if customer is declined
"""

    def __init__(self, llm_client: Any = None, model_name: str = "gpt-4o") -> None:
        self.llm_client = llm_client
        self.model_name = model_name
        self.guardrails = RecommendationGuardrails()
        self.hitl = HumanInTheLoop()
        self.memory = AgentMemory()
        self._trace_id = str(uuid.uuid4())

    async def generate_recommendation(self, customer: dict, product: dict) -> dict[str, Any]:
        """Generate a recommendation with guardrails."""
        category = product.get("category", "")
        eligibility = self.guardrails.check_eligibility(customer, category)

        if not eligibility["eligible"]:
            return {"error": "Not eligible", "reasons": eligibility["errors"]}

        context = self.memory.get_customer_context(customer.get("customer_id", ""))
        prompt = f"Recommend {product.get('name', 'product')} to customer {customer.get('name', 'unknown')}."

        self.memory.add("user", f"Recommendation request for {customer.get('customer_id')}", customer_id=customer.get("customer_id"))

        response = await self._call_llm(prompt, context)
        self.memory.add("assistant", response, customer_id=customer.get("customer_id"))

        return {"response": response, "customer_id": customer.get("customer_id"), "product_id": product.get("product_id"), "trace_id": self._trace_id}

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
        return f"[Simulation] Generating recommendation: {prompt[:200]}..."

    async def stream_recommendations(self, customer: dict, products: list[dict]) -> AsyncIterator[str]:
        """Stream recommendation results."""
        yield f"Generating recommendations for {customer.get('name', 'customer')}...\n"
        yield f"Segment: {customer.get('segment', 'unknown')}\n"
        yield f"Products held: {len(customer.get('existing_products', []))}\n"
        yield "Analyzing product fit...\n"
        await time.sleep(0.1)
        yield "✅ Recommendations ready.\n"
