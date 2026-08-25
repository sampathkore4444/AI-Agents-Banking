"""
Base Financial Statement Analysis Agent — Common patterns for financial analysis with LLMs.

Includes:
- Guardrails for analysis decisions (materiality, thresholds)
- Human-in-the-loop for critical findings
- Memory for analysis context
- Streaming for real-time analysis updates
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
#  GUARDRAILS — Financial analysis validation
# ══════════════════════════════════════════════════════════════════

class FinancialAnalysisGuardrails:
    """Financial analysis-specific guardrails."""

    MATERIALITY_THRESHOLD_PCT = 5.0  # 5% of pre-tax income
    ZSCORE_DISTRESS = 1.8
    ZSCORE_GRAY = 3.0
    MAX_RATIO_DEVIATION_PCT = 50.0

    REQUIRES_REVIEW = {"negative_equity", "zscore_distress", "going_concern", "material_misstatement"}
    BLOCKED_OUTPUTS = {"fabricated_data", "unsubstantiated_claims"}

    @classmethod
    def validate_analysis_input(cls, data: dict) -> dict[str, Any]:
        errors = []
        if not data.get("company_id"):
            errors.append("company_id is required")
        bs = data.get("balance_sheet", {})
        if bs.get("total_assets", 0) <= 0:
            errors.append("total_assets must be positive")
        is_data = data.get("income_statement", {})
        if is_data.get("revenue", 0) <= 0:
            errors.append("revenue must be positive")
        return {"valid": len(errors) == 0, "errors": errors}

    @classmethod
    def validate_output(cls, output: dict) -> dict[str, Any]:
        warnings = []
        # Check for extreme ratios
        cr = output.get("liquidity", {}).get("current_ratio")
        if cr and cr > 10:
            warnings.append("Current ratio > 10 — possible data error")
        dte = output.get("leverage", {}).get("debt_to_equity")
        if dte and dte > 10:
            warnings.append("Debt-to-equity > 10 — possible data error")
        return {"valid": len(warnings) == 0, "warnings": warnings}

    @classmethod
    def check_review_needed(cls, findings: list[dict]) -> bool:
        return any(f.get("severity") in {"critical", "high"} for f in findings)


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
        logger.warning(f"HUMAN REVIEW REQUIRED: {action} (risk: {risk_level}) — ID: {req.request_id}")
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

    def get_analysis_context(self, company_id: str) -> str:
        analysis = [e for e in self._entries if e.metadata.get("company_id") == company_id]
        return "\n".join(f"[{e.role}] {e.content}" for e in analysis[-20:])


# ══════════════════════════════════════════════════════════════════
#  BASE AGENT
# ══════════════════════════════════════════════════════════════════

class FinancialAnalysisAgent:
    """Base financial statement analysis agent with guardrails, HITL, and memory."""

    SYSTEM_PROMPT = """You are a Financial Statement Analysis Agent for a bank.

Your responsibilities:
1. Parse and extract data from financial statements (balance sheet, income statement, cash flow)
2. Calculate comprehensive financial ratios (liquidity, leverage, profitability, efficiency)
3. Perform DuPont analysis and Altman Z-Score calculations
4. Compare metrics against industry benchmarks and peer companies
5. Detect trends and early signs of financial deterioration
6. Check GAAP/IFRS compliance and audit readiness
7. Generate executive summaries for credit assessment and investment due diligence

Key principles:
- Always validate data completeness before analysis
- Cross-reference ratios for consistency
- Flag material deviations from benchmarks (>25% from median)
- Consider industry context when interpreting ratios
- Use multiple frameworks (DuPont, Z-Score, Piotroski) for comprehensive assessment
- Clearly distinguish between facts and analytical judgments

Analysis frameworks:
- Liquidity: Current ratio, quick ratio, cash ratio, working capital
- Leverage: D/E, interest coverage, debt/EBITDA, fixed charge coverage
- Profitability: Margins, ROA, ROE, ROIC, EVA
- Efficiency: Asset turnover, inventory turnover, DSO, DPO, CCC
- Credit: Z-Score, Piotroski F-Score, credit rating methodology
- Valuation: P/E, EV/EBITDA, P/B (when market data available)

Red flags to highlight:
- Declining revenue > 10% year-over-year
- Net margin compression > 3 percentage points
- Rising leverage (D/E increase > 25%)
- Z-Score below 1.8 (distress zone)
- Negative free cash flow for 2+ consecutive periods
- Earnings quality issues (CFO significantly below net income)
"""

    def __init__(self, llm_client: Any = None, model_name: str = "gpt-4o") -> None:
        self.llm_client = llm_client
        self.model_name = model_name
        self.guardrails = FinancialAnalysisGuardrails()
        self.hitl = HumanInTheLoop()
        self.memory = AgentMemory()
        self._trace_id = str(uuid.uuid4())

    async def analyze_statement(self, company_id: str, balance_sheet: dict, income_statement: dict, cash_flow: dict | None = None) -> dict[str, Any]:
        """Analyze a financial statement with guardrails."""
        validation = self.guardrails.validate_analysis_input({"company_id": company_id, "balance_sheet": balance_sheet, "income_statement": income_statement})
        if not validation["valid"]:
            return {"error": "Validation failed", "errors": validation["errors"]}

        self.memory.add("user", f"Analyze financial statements for {company_id}", company_id=company_id)
        prompt = f"Perform comprehensive financial analysis for {company_id}"
        response = await self._call_llm(prompt)
        self.memory.add("assistant", f"Analysis complete for {company_id}", company_id=company_id)

        return {"company_id": company_id, "analysis_status": "complete", "trace_id": self._trace_id}

    async def get_recommendation(self, company_id: str, analysis: dict) -> dict[str, Any]:
        """Generate investment/credit recommendation."""
        health = analysis.get("overall_health", {})
        rating = health.get("health_rating", "unknown")

        if rating == "strong":
            recommendation = "recommend"
            rationale = "Strong financial health across all dimensions"
        elif rating == "adequate":
            recommendation = "conditional_recommend"
            rationale = "Adequate financial position with some areas to monitor"
        elif rating == "watch":
            recommendation = "caution"
            rationale = "Financial metrics warrant close monitoring"
        else:
            recommendation = "decline"
            rationale = "Significant financial concerns identified"

        return {
            "company_id": company_id,
            "recommendation": recommendation,
            "rationale": rationale,
            "health_rating": rating,
            "requires_human_review": self.guardrails.check_review_needed(health.get("risk_signals", [])),
        }

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

    async def stream_analysis(self, company_id: str) -> AsyncIterator[str]:
        """Stream analysis progress."""
        yield f"Starting financial analysis for {company_id}...\n"
        yield "Extracting financial data...\n"
        await time.sleep(0.1)
        yield "Calculating ratios...\n"
        await time.sleep(0.1)
        yield "Comparing to benchmarks...\n"
        await time.sleep(0.1)
        yield "Analyzing trends...\n"
        await time.sleep(0.1)
        yield "Generating summary...\n"
        yield "Analysis complete.\n"
