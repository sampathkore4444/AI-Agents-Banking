"""
Compliance Check Tools — Verify financial statements against accounting standards.
"""

from __future__ import annotations

from typing import Any


async def check_gaap_compliance(
    company_id: str,
    balance_sheet: dict[str, Any],
    income_statement: dict[str, Any],
    cash_flow_statement: dict[str, Any],
) -> dict[str, Any]:
    """Check basic US GAAP compliance of financial statements."""
    issues = []
    warnings = []

    # Balance sheet equation
    assets = balance_sheet.get("total_assets", 0)
    liabilities = balance_sheet.get("total_liabilities", 0)
    equity = balance_sheet.get("total_equity", 0)
    if abs(assets - (liabilities + equity)) > 1:
        issues.append({
            "standard": "GAAP",
            "rule": "Balance Sheet Equation",
            "detail": f"Assets ({assets:,.0f}) ≠ Liabilities + Equity ({liabilities + equity:,.0f})",
            "severity": "critical",
        })

    # Revenue vs COGS sanity
    revenue = income_statement.get("revenue", 0)
    cogs = income_statement.get("cost_of_goods_sold", 0)
    if cogs > revenue and revenue > 0:
        issues.append({
            "standard": "GAAP",
            "rule": "ASC 606",
            "detail": "COGS exceeds Revenue — negative gross margin",
            "severity": "warning",
        })

    # Net income vs revenue
    net_income = income_statement.get("net_income", 0)
    if revenue > 0 and net_income / revenue < -0.3:
        warnings.append({
            "standard": "GAAP",
            "rule": "ASC 225",
            "detail": f"Net margin below -30% — material going concern consideration",
            "severity": "high",
        })

    # Cash flow sanity
    cfo = cash_flow_statement.get("cash_from_operations", 0)
    cfi = cash_flow_statement.get("cash_from_investing", 0)
    cff = cash_flow_statement.get("cash_from_financing", 0)
    net_change = cash_flow_statement.get("net_change_in_cash", 0)
    if abs((cfo + cfi + cff) - net_change) > 1:
        issues.append({
            "standard": "GAAP",
            "rule": "ASC 230",
            "detail": f"CFO + CFI + CFF ({cfo + cfi + cff:,.0f}) ≠ Net Change in Cash ({net_change:,.0f})",
            "severity": "critical",
        })

    # FCF calculation
    capex = cash_flow_statement.get("capital_expenditures", 0)
    fcf = cash_flow_statement.get("free_cash_flow", 0)
    if fcf and cfo and abs(fcf - (cfo + capex)) > 1:
        warnings.append({
            "standard": "GAAP",
            "rule": "FCF Consistency",
            "detail": "Free cash flow doesn't match CFO minus CapEx",
            "severity": "low",
        })

    # Working capital check
    ca = balance_sheet.get("total_current_assets", 0)
    cl = balance_sheet.get("total_current_liabilities", 0)
    if ca < cl:
        warnings.append({
            "standard": "GAAP",
            "rule": "Working Capital",
            "detail": f"Negative working capital: ${ca - cl:,.0f}",
            "severity": "medium",
        })

    return {
        "company_id": company_id,
        "standard": "US GAAP",
        "issues_count": len(issues),
        "warnings_count": len(warnings),
        "issues": issues,
        "warnings": warnings,
        "compliant": len(issues) == 0,
    }


async def check_ratio_health(
    ratios: dict[str, Any],
    industry: str = "general",
) -> dict[str, Any]:
    """Check financial ratios against health thresholds."""
    alerts = []

    # Liquidity
    cr = ratios.get("liquidity", {}).get("current_ratio")
    if cr is not None and cr < 1.0:
        alerts.append({"metric": "current_ratio", "value": cr, "threshold": 1.0, "severity": "high", "message": "Current ratio below 1.0 — liquidity risk"})

    # Leverage
    dte = ratios.get("leverage", {}).get("debt_to_equity")
    if dte is not None and dte > 3.0:
        alerts.append({"metric": "debt_to_equity", "value": dte, "threshold": 3.0, "severity": "high", "message": "Debt-to-equity above 3.0 — high leverage risk"})

    ic = ratios.get("leverage", {}).get("interest_coverage")
    if ic is not None and ic < 1.5:
        alerts.append({"metric": "interest_coverage", "value": ic, "threshold": 1.5, "severity": "critical", "message": "Interest coverage below 1.5 — cannot cover interest payments"})

    # Profitability
    nm = ratios.get("profitability", {}).get("net_margin_pct")
    if nm is not None and nm < 0:
        alerts.append({"metric": "net_margin", "value": nm, "threshold": 0, "severity": "high", "message": "Negative net margin — unprofitable"})

    # Z-Score
    z = ratios.get("altman_zscore", {}).get("z_score")
    if z is not None and z < 1.8:
        alerts.append({"metric": "altman_zscore", "value": z, "threshold": 1.8, "severity": "critical", "message": "Z-Score in distress zone — bankruptcy risk"})

    return {
        "alerts_count": len(alerts),
        "critical_count": sum(1 for a in alerts if a["severity"] == "critical"),
        "alerts": alerts,
    }


async def audit_readiness_check(
    company_id: str,
    statements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check if financial statements are audit-ready."""
    checks = []

    # Completeness check
    for stmt in statements:
        has_bs = "balance_sheet" in stmt
        has_is = "income_statement" in stmt
        has_cf = "cash_flow_statement" in stmt
        completeness = sum([has_bs, has_is, has_cf]) / 3 * 100
        checks.append({
            "period": stmt["period"],
            "balance_sheet": has_bs,
            "income_statement": has_is,
            "cash_flow": has_cf,
            "completeness_pct": completeness,
            "ready": completeness == 100,
        })

    # Multi-period consistency
    periods = sorted(statements, key=lambda s: s["period"])
    consistency_issues = []
    if len(periods) >= 2:
        rev_0 = periods[0].get("income_statement", {}).get("revenue", 0)
        rev_1 = periods[1].get("income_statement", {}).get("revenue", 0)
        if rev_0 and rev_1 and abs(rev_0 - rev_1) / rev_1 > 0.5:
            consistency_issues.append(f"Revenue changed >50% between {periods[0]['period']} and {periods[1]['period']}")

    all_ready = all(c["ready"] for c in checks)
    return {
        "company_id": company_id,
        "periods_checked": len(checks),
        "all_complete": all_ready,
        "period_checks": checks,
        "consistency_issues": consistency_issues,
        "audit_ready": all_ready and len(consistency_issues) == 0,
    }
