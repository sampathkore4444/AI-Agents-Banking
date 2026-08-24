"""
Loan Application Processing Agent — MCP Server.

Enhanced with 3.2 Credit Scoring & Risk Assessment features:
- Bank statement deep analysis
- Alternative data (rent, utilities, non-traditional credit)
- ML customer embedding and clustering
- Detailed decision explainability
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.alternative_data import check_alternative_data
from tools.application_management import calculate_affordability, create_loan_application, get_application, update_application
from tools.bank_statement_analysis import analyze_bank_statement
from tools.credit_bureau import get_credit_report
from tools.credit_scoring import assess_loan_risk, embed_customer_profile
from tools.document_verification import verify_loan_document
from tools.explainability import explain_decision
from tools.income_verification import verify_income
from tools.notifications import send_notification

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Loan Application Processing Agent",
    instructions=(
        "Loan Application Processing Agent for banking. Use these tools to process "
        "loan applications: check credit, verify income, verify documents, "
        "calculate affordability, assess risk, analyze bank statements, "
        "check alternative data, embed customer profiles, and manage applications."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the loan knowledge base for regulations, policies, and past decisions."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  APPLICATION MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_application(customer_id: str, loan_type: str, loan_amount: float, purpose: str, term_months: int, property_address: dict | None = None) -> dict[str, Any]:
    """Create a new loan application."""
    return await create_loan_application(customer_id, loan_type, loan_amount, purpose, term_months, property_address)


@mcp.tool()
async def get_application_status(application_id: str) -> dict[str, Any]:
    """Get the current status and details of a loan application."""
    return await get_application(application_id)


@mcp.tool()
async def update_application_status(application_id: str, status: str | None = None, substage: str | None = None, documents_received: list[str] | None = None, credit_check_done: bool | None = None, income_verified: bool | None = None, underwriting_decision: str | None = None, notes: str | None = None) -> dict[str, Any]:
    """Update a loan application's status, documents, or decisions."""
    return await update_application(application_id, status, substage, documents_received, credit_check_done, income_verified, underwriting_decision, notes)


# ══════════════════════════════════════════════════════════════════
#  CREDIT & INCOME (3.1 + 3.2)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def check_credit(customer_name: str, date_of_birth: str, ssn_last_four: str, address: dict | None = None) -> dict[str, Any]:
    """Pull a credit report from the credit bureau."""
    return await get_credit_report(customer_name, date_of_birth, ssn_last_four, address)


@mcp.tool()
async def verify_customer_income(customer_id: str, annual_income_claimed: float, employment_type: str = "employed", employer_name: str | None = None, tax_year: int = 2024) -> dict[str, Any]:
    """Verify customer income through multiple sources."""
    return await verify_income(customer_id, annual_income_claimed, employment_type, employer_name, tax_year)


# ══════════════════════════════════════════════════════════════════
#  DOCUMENT VERIFICATION
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def verify_document(document_url: str, document_type: str, expected_values: dict | None = None) -> dict[str, Any]:
    """Extract and verify data from a loan document (payslip, bank statement, tax return, etc.)."""
    return await verify_loan_document(document_url, document_type, expected_values)


# ══════════════════════════════════════════════════════════════════
#  AFFORDABILITY & RISK (3.1 + 3.2)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def calculate_loan_affordability(annual_income: float, monthly_debts: float, loan_amount: float, interest_rate: float, term_months: int) -> dict[str, Any]:
    """Calculate affordability metrics (DTI, monthly payment, total cost)."""
    return await calculate_affordability(annual_income, monthly_debts, loan_amount, interest_rate, term_months)


@mcp.tool()
async def assess_risk(credit_score: int, annual_income: float, loan_amount: float, loan_to_value: float, debt_to_income: float, employment_type: str, loan_type: str) -> dict[str, Any]:
    """Assess loan risk and recommend underwriting decision with explanation."""
    return await assess_loan_risk(credit_score, annual_income, loan_amount, loan_to_value, debt_to_income, employment_type, loan_type)


# ══════════════════════════════════════════════════════════════════
#  NEW: 3.2 CREDIT SCORING & RISK ASSESSMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def analyze_bank_statement(customer_id: str, statement_url: str, statement_months: int = 6) -> dict[str, Any]:
    """Deep analysis of bank statements: transaction categorization, spending patterns, irregularity detection."""
    return await analyze_bank_statement(customer_id, statement_url, statement_months)


@mcp.tool()
async def check_alternative_credit_data(customer_id: str, data_types: list[str] | None = None) -> dict[str, Any]:
    """Check alternative credit data (rent payments, utilities, phone, employment) for customers with thin credit files."""
    return await check_alternative_data(customer_id, data_types)


@mcp.tool()
async def embed_profile(customer_id: str, credit_score: int, annual_income: float, debt_to_income: float, loan_to_value: float, employment_years: int, credit_history_years: int, num_open_accounts: int, derogatory_marks: int) -> dict[str, Any]:
    """Create ML embedding of customer financial profile for clustering and risk prediction."""
    return await embed_customer_profile(customer_id, credit_score, annual_income, debt_to_income, loan_to_value, employment_years, credit_history_years, num_open_accounts, derogatory_marks)


@mcp.tool()
async def explain_loan_decision(application_id: str, decision: str, credit_score: int, dti_ratio: float, ltv_ratio: float, risk_factors: list[str], income_verified: bool, employment_type: str) -> dict[str, Any]:
    """Generate detailed explanation for a credit decision (required by ECOA for adverse action notices)."""
    return await explain_decision(application_id, decision, credit_score, dti_ratio, ltv_ratio, risk_factors, income_verified, employment_type)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def notify_customer(customer_id: str, template_id: str, channel: str = "email", variables: dict | None = None) -> dict[str, Any]:
    """Send a notification to a customer."""
    return await send_notification("customer", customer_id, channel, template_id, variables)


if __name__ == "__main__":
    logger.info("Starting Loan Application Processing Agent MCP Server...")
    mcp.run()
