"""
Financial Data Extraction Tools — Extract and structure financial statement data.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
_financial_statements: dict[str, dict[str, Any]] = {}


# ── Seeded sample companies ──────────────────────────────────────
_SAMPLE_COMPANIES: dict[str, dict[str, Any]] = {
    "ACME-001": {
        "company_id": "ACME-001",
        "company_name": "Acme Technologies Inc.",
        "industry": "technology",
        "naics_code": "51",
        "fiscal_year_end": "12-31",
        "currency": "USD",
        "is_public": True,
        "tickers": ["ACME"],
    },
    "GLOBEX-001": {
        "company_id": "GLOBEX-001",
        "company_name": "Globex Manufacturing Corp.",
        "industry": "manufacturing",
        "naics_code": "31-33",
        "fiscal_year_end": "12-31",
        "currency": "USD",
        "is_public": True,
        "tickers": ["GLBX"],
    },
    "SPRING-001": {
        "company_id": "SPRING-001",
        "company_name": "Springfield Retail Group",
        "industry": "retail",
        "naics_code": "44-45",
        "fiscal_year_end": "01-31",
        "currency": "USD",
        "is_public": True,
        "tickers": ["SPRG"],
    },
}

# ── Sample financial data (3 years) ──────────────────────────────
_SAMPLE_STATEMENTS: list[dict[str, Any]] = [
    # Acme Technologies — Year 2023
    {
        "statement_id": "STMT-ACME-2023",
        "company_id": "ACME-001",
        "period": "2023",
        "period_type": "annual",
        "balance_sheet": {
            "total_current_assets": 850000000,
            "cash_and_equivalents": 320000000,
            "accounts_receivable": 180000000,
            "inventory": 45000000,
            "total_assets": 2400000000,
            "total_current_liabilities": 310000000,
            "accounts_payable": 95000000,
            "short_term_debt": 50000000,
            "total_liabilities": 850000000,
            "long_term_debt": 350000000,
            "total_equity": 1550000000,
            "total_liabilities_and_equity": 2400000000,
        },
        "income_statement": {
            "revenue": 1800000000,
            "cost_of_goods_sold": 720000000,
            "gross_profit": 1080000000,
            "operating_expenses": 720000000,
            "research_and_development": 270000000,
            "selling_general_admin": 450000000,
            "depreciation_and_amortization": 90000000,
            "operating_income": 360000000,
            "interest_expense": 18000000,
            "interest_income": 5000000,
            "other_income_expense": -3000000,
            "pretax_income": 344000000,
            "income_tax_expense": 68800000,
            "net_income": 275200000,
            "ebitda": 450000000,
            "eps_basic": 5.50,
            "eps_diluted": 5.30,
        },
        "cash_flow_statement": {
            "cash_from_operations": 380000000,
            "cash_from_investing": -180000000,
            "cash_from_financing": -120000000,
            "capital_expenditures": -150000000,
            "free_cash_flow": 230000000,
            "dividends_paid": -50000000,
            "share_repurchases": -80000000,
            "net_change_in_cash": 80000000,
        },
    },
    # Acme Technologies — Year 2022
    {
        "statement_id": "STMT-ACME-2022",
        "company_id": "ACME-001",
        "period": "2022",
        "period_type": "annual",
        "balance_sheet": {
            "total_current_assets": 720000000,
            "cash_and_equivalents": 280000000,
            "accounts_receivable": 155000000,
            "inventory": 40000000,
            "total_assets": 2100000000,
            "total_current_liabilities": 280000000,
            "accounts_payable": 85000000,
            "short_term_debt": 45000000,
            "total_liabilities": 780000000,
            "long_term_debt": 320000000,
            "total_equity": 1320000000,
            "total_liabilities_and_equity": 2100000000,
        },
        "income_statement": {
            "revenue": 1500000000,
            "cost_of_goods_sold": 615000000,
            "gross_profit": 885000000,
            "operating_expenses": 600000000,
            "research_and_development": 225000000,
            "selling_general_admin": 375000000,
            "depreciation_and_amortization": 80000000,
            "operating_income": 285000000,
            "interest_expense": 16000000,
            "interest_income": 3500000,
            "other_income_expense": -2000000,
            "pretax_income": 270500000,
            "income_tax_expense": 54100000,
            "net_income": 216400000,
            "ebitda": 365000000,
            "eps_basic": 4.33,
            "eps_diluted": 4.18,
        },
        "cash_flow_statement": {
            "cash_from_operations": 310000000,
            "cash_from_investing": -160000000,
            "cash_from_financing": -100000000,
            "capital_expenditures": -130000000,
            "free_cash_flow": 180000000,
            "dividends_paid": -45000000,
            "share_repurchases": -60000000,
            "net_change_in_cash": 50000000,
        },
    },
    # Acme Technologies — Year 2021
    {
        "statement_id": "STMT-ACME-2021",
        "company_id": "ACME-001",
        "period": "2021",
        "period_type": "annual",
        "balance_sheet": {
            "total_current_assets": 600000000,
            "cash_and_equivalents": 230000000,
            "accounts_receivable": 130000000,
            "inventory": 35000000,
            "total_assets": 1800000000,
            "total_current_liabilities": 250000000,
            "accounts_payable": 75000000,
            "short_term_debt": 40000000,
            "total_liabilities": 700000000,
            "long_term_debt": 280000000,
            "total_equity": 1100000000,
            "total_liabilities_and_equity": 1800000000,
        },
        "income_statement": {
            "revenue": 1200000000,
            "cost_of_goods_sold": 504000000,
            "gross_profit": 696000000,
            "operating_expenses": 480000000,
            "research_and_development": 180000000,
            "selling_general_admin": 300000000,
            "depreciation_and_amortization": 70000000,
            "operating_income": 216000000,
            "interest_expense": 14000000,
            "interest_income": 2500000,
            "other_income_expense": -1500000,
            "pretax_income": 203000000,
            "income_tax_expense": 40600000,
            "net_income": 162400000,
            "ebitda": 286000000,
            "eps_basic": 3.25,
            "eps_diluted": 3.15,
        },
        "cash_flow_statement": {
            "cash_from_operations": 240000000,
            "cash_from_investing": -140000000,
            "cash_from_financing": -80000000,
            "capital_expenditures": -120000000,
            "free_cash_flow": 120000000,
            "dividends_paid": -40000000,
            "share_repurchases": -40000000,
            "net_change_in_cash": 20000000,
        },
    },
]


async def extract_financial_data(
    company_id: str,
    period: str | None = None,
    statement_type: str = "all",
) -> dict[str, Any]:
    """Extract structured financial data from stored statements."""
    statements = [s for s in _SAMPLE_STATEMENTS if s["company_id"] == company_id]
    if period:
        statements = [s for s in statements if s["period"] == period]

    if not statements:
        return {"error": f"No financial statements found for company {company_id}"}

    statements.sort(key=lambda s: s["period"], reverse=True)

    if statement_type == "all":
        return {"company_id": company_id, "statements": statements}
    elif statement_type in statements[0]:
        return {"company_id": company_id, "period": statements[0]["period"], statement_type: statements[0][statement_type]}
    else:
        return {"error": f"Invalid statement_type: {statement_type}"}


async def get_company_info(company_id: str) -> dict[str, Any]:
    """Get company information."""
    if company_id in _SAMPLE_COMPANIES:
        return _SAMPLE_COMPANIES[company_id]
    # Search by name
    for cid, info in _SAMPLE_COMPANIES.items():
        if company_id.lower() in info["company_name"].lower():
            return info
    return {"error": f"Company {company_id} not found"}


async def list_companies(
    industry: str | None = None,
    is_public: bool | None = None,
) -> dict[str, Any]:
    """List available companies."""
    results = list(_SAMPLE_COMPANIES.values())
    if industry:
        results = [c for c in results if c["industry"] == industry]
    if is_public is not None:
        results = [c for c in results if c["is_public"] == is_public]
    return {"count": len(results), "companies": results}


async def upload_statement(
    company_id: str,
    period: str,
    period_type: str,
    balance_sheet: dict[str, Any] | None = None,
    income_statement: dict[str, Any] | None = None,
    cash_flow_statement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Upload a financial statement."""
    statement_id = f"STMT-{uuid.uuid4().hex[:8].upper()}"
    statement = {
        "statement_id": statement_id,
        "company_id": company_id,
        "period": period,
        "period_type": period_type,
    }
    if balance_sheet:
        statement["balance_sheet"] = balance_sheet
    if income_statement:
        statement["income_statement"] = income_statement
    if cash_flow_statement:
        statement["cash_flow_statement"] = cash_flow_statement

    _financial_statements[statement_id] = statement
    return {"success": True, "statement_id": statement_id, "company_id": company_id, "period": period}


async def validate_statement_completeness(
    company_id: str,
    period: str,
) -> dict[str, Any]:
    """Validate that a financial statement is complete."""
    statements = [s for s in _SAMPLE_STATEMENTS if s["company_id"] == company_id and s["period"] == period]
    if not statements:
        return {"error": f"No statement found for {company_id} period {period}"}

    stmt = statements[0]
    required_sections = {
        "balance_sheet": ["total_current_assets", "total_assets", "total_liabilities", "total_equity"],
        "income_statement": ["revenue", "gross_profit", "operating_income", "net_income"],
        "cash_flow_statement": ["cash_from_operations", "cash_from_investing", "cash_from_financing"],
    }

    completeness = {}
    for section, fields in required_sections.items():
        data = stmt.get(section, {})
        present = sum(1 for f in fields if f in data)
        completeness[section] = {"present": present, "required": len(fields), "pct": round(present / len(fields) * 100, 1)}

    total_pct = sum(c["pct"] for c in completeness.values()) / len(completeness)
    return {
        "company_id": company_id,
        "period": period,
        "completeness": completeness,
        "overall_completeness": round(total_pct, 1),
        "is_complete": total_pct >= 80,
    }
