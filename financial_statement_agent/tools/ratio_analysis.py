"""
Ratio Analysis Tools — Calculate and analyze financial ratios.
"""

from __future__ import annotations

from typing import Any


async def calculate_liquidity_ratios(balance_sheet: dict[str, Any]) -> dict[str, Any]:
    """Calculate liquidity ratios from balance sheet data."""
    ca = balance_sheet.get("total_current_assets", 0)
    cl = balance_sheet.get("total_current_liabilities", 0)
    cash = balance_sheet.get("cash_and_equivalents", 0)
    ar = balance_sheet.get("accounts_receivable", 0)
    inv = balance_sheet.get("inventory", 0)

    current_ratio = round(ca / cl, 2) if cl > 0 else None
    quick_ratio = round((cash + ar) / cl, 2) if cl > 0 else None
    cash_ratio = round(cash / cl, 2) if cl > 0 else None
    working_capital = ca - cl

    return {
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "cash_ratio": cash_ratio,
        "working_capital": working_capital,
        "assessment": _assess_liquidity(current_ratio, quick_ratio, cash_ratio),
    }


async def calculate_leverage_ratios(balance_sheet: dict[str, Any], income_statement: dict[str, Any] | None = None) -> dict[str, Any]:
    """Calculate leverage/solvency ratios."""
    total_liabilities = balance_sheet.get("total_liabilities", 0)
    total_equity = balance_sheet.get("total_equity", 0)
    long_term_debt = balance_sheet.get("long_term_debt", 0)
    short_term_debt = balance_sheet.get("short_term_debt", 0)
    total_debt = long_term_debt + short_term_debt

    dte = round(total_liabilities / total_equity, 2) if total_equity > 0 else None
    debt_to_capital = round(total_debt / (total_debt + total_equity), 2) if (total_debt + total_equity) > 0 else None

    result = {
        "debt_to_equity": dte,
        "debt_to_capital": debt_to_capital,
        "total_debt": total_debt,
    }

    if income_statement:
        ebit = income_statement.get("operating_income", 0)
        interest = income_statement.get("interest_expense", 0)
        ebitda = income_statement.get("ebitda", 0)

        result["interest_coverage"] = round(ebit / interest, 2) if interest > 0 else None
        result["debt_to_ebitda"] = round(total_debt / ebitda, 2) if ebitda > 0 else None

    result["assessment"] = _assess_leverage(dte, result.get("interest_coverage"))
    return result


async def calculate_profitability_ratios(income_statement: dict[str, Any], total_assets: float = 0, total_equity: float = 0) -> dict[str, Any]:
    """Calculate profitability ratios from income statement."""
    revenue = income_statement.get("revenue", 0)
    cogs = income_statement.get("cost_of_goods_sold", 0)
    operating_income = income_statement.get("operating_income", 0)
    net_income = income_statement.get("net_income", 0)
    ebitda = income_statement.get("ebitda", 0)

    gross_margin = round((revenue - cogs) / revenue * 100, 1) if revenue > 0 else None
    operating_margin = round(operating_income / revenue * 100, 1) if revenue > 0 else None
    net_margin = round(net_income / revenue * 100, 1) if revenue > 0 else None
    ebitda_margin = round(ebitda / revenue * 100, 1) if revenue > 0 else None

    roa = round(net_income / total_assets * 100, 1) if total_assets > 0 else None
    roe = round(net_income / total_equity * 100, 1) if total_equity > 0 else None

    return {
        "gross_margin_pct": gross_margin,
        "operating_margin_pct": operating_margin,
        "net_margin_pct": net_margin,
        "ebitda_margin_pct": ebitda_margin,
        "roa_pct": roa,
        "roe_pct": roe,
        "assessment": _assess_profitability(gross_margin, operating_margin, net_margin, roe),
    }


async def calculate_efficiency_ratios(balance_sheet: dict[str, Any], income_statement: dict[str, Any]) -> dict[str, Any]:
    """Calculate efficiency/activity ratios."""
    revenue = income_statement.get("revenue", 0)
    cogs = income_statement.get("cost_of_goods_sold", 0)
    total_assets = balance_sheet.get("total_assets", 0)
    inventory = balance_sheet.get("inventory", 0)
    ar = balance_sheet.get("accounts_receivable", 0)
    ap = balance_sheet.get("accounts_payable", 0)
    pp_e = total_assets - balance_sheet.get("total_current_assets", 0) + balance_sheet.get("total_current_assets", 0) * 0.3  # Approximate

    inv_turnover = round(cogs / inventory, 2) if inventory > 0 else None
    dio = round(365 / inv_turnover, 0) if inv_turnover and inv_turnover > 0 else None

    ar_turnover = round(revenue / ar, 2) if ar > 0 else None
    dso = round(365 / ar_turnover, 0) if ar_turnover and ar_turnover > 0 else None

    ap_turnover = round(cogs / ap, 2) if ap > 0 else None
    dpo = round(365 / ap_turnover, 0) if ap_turnover and ap_turnover > 0 else None

    ccc = round((dio or 0) + (dso or 0) - (dpo or 0), 0)
    asset_turnover = round(revenue / total_assets, 2) if total_assets > 0 else None

    return {
        "asset_turnover": asset_turnover,
        "inventory_turnover": inv_turnover,
        "days_inventory_outstanding": dio,
        "receivables_turnover": ar_turnover,
        "days_sales_outstanding": dso,
        "payables_turnover": ap_turnover,
        "days_payable_outstanding": dpo,
        "cash_conversion_cycle": ccc,
        "assessment": _assess_efficiency(inv_turnover, dso, dpo, ccc),
    }


async def calculate_dupont_analysis(income_statement: dict[str, Any], total_assets: float, total_equity: float) -> dict[str, Any]:
    """Perform DuPont decomposition of ROE."""
    revenue = income_statement.get("revenue", 0)
    net_income = income_statement.get("net_income", 0)
    ebit = income_statement.get("operating_income", 0)
    pretax = income_statement.get("pretax_income", 0)
    tax = income_statement.get("income_tax_expense", 0)

    net_margin = net_income / revenue if revenue > 0 else 0
    asset_turnover = revenue / total_assets if total_assets > 0 else 0
    equity_multiplier = total_assets / total_equity if total_equity > 0 else 0

    tax_burden = net_income / pretax if pretax > 0 else 0
    interest_burden = pretax / ebit if ebit > 0 else 0
    operating_margin = ebit / revenue if revenue > 0 else 0

    roe_3 = net_margin * asset_turnover * equity_multiplier
    roe_5 = tax_burden * interest_burden * operating_margin * asset_turnover * equity_multiplier

    return {
        "roe_three_component": round(roe_3 * 100, 2),
        "roe_five_component": round(roe_5 * 100, 2),
        "net_profit_margin": round(net_margin * 100, 2),
        "asset_turnover": round(asset_turnover, 2),
        "equity_multiplier": round(equity_multiplier, 2),
        "tax_burden": round(tax_burden, 3),
        "interest_burden": round(interest_burden, 3),
        "operating_margin": round(operating_margin * 100, 2),
        "drivers": _identify_dupont_drivers(net_margin, asset_turnover, equity_multiplier),
    }


async def calculate_altman_zscore(balance_sheet: dict[str, Any], income_statement: dict[str, Any], market_cap: float = 0) -> dict[str, Any]:
    """Calculate Altman Z-Score."""
    total_assets = balance_sheet.get("total_assets", 0)
    total_liabilities = balance_sheet.get("total_liabilities", 0)
    current_assets = balance_sheet.get("total_current_assets", 0)
    current_liabilities = balance_sheet.get("total_current_liabilities", 0)
    retained_earnings = balance_sheet.get("total_equity", 0) * 0.4  # Approximate
    ebit = income_statement.get("operating_income", 0)
    revenue = income_statement.get("revenue", 0)

    if total_assets == 0:
        return {"error": "Total assets required for Z-Score calculation"}

    x1 = (current_assets - current_liabilities) / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_liabilities if total_liabilities > 0 and market_cap > 0 else 0
    x5 = revenue / total_assets

    z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    if z_score > 3.0:
        zone = "safe"
    elif z_score > 1.8:
        zone = "gray"
    else:
        zone = "distress"

    return {
        "z_score": round(z_score, 2),
        "zone": zone,
        "components": {
            "x1_working_capital": round(x1, 4),
            "x2_retained_earnings": round(x2, 4),
            "x3_ebit": round(x3, 4),
            "x4_market_equity": round(x4, 4),
            "x5_asset_turnover": round(x5, 4),
        },
    }


async def full_ratio_analysis(
    company_id: str,
    balance_sheet: dict[str, Any],
    income_statement: dict[str, Any],
    cash_flow_statement: dict[str, Any] | None = None,
    market_cap: float = 0,
) -> dict[str, Any]:
    """Comprehensive ratio analysis."""
    total_assets = balance_sheet.get("total_assets", 0)
    total_equity = balance_sheet.get("total_equity", 0)

    liquidity = await calculate_liquidity_ratios(balance_sheet)
    leverage = await calculate_leverage_ratios(balance_sheet, income_statement)
    profitability = await calculate_profitability_ratios(income_statement, total_assets, total_equity)
    efficiency = await calculate_efficiency_ratios(balance_sheet, income_statement)
    dupont = await calculate_dupont_analysis(income_statement, total_assets, total_equity)
    zscore = await calculate_altman_zscore(balance_sheet, income_statement, market_cap)

    return {
        "company_id": company_id,
        "liquidity": liquidity,
        "leverage": leverage,
        "profitability": profitability,
        "efficiency": efficiency,
        "dupont": dupont,
        "altman_zscore": zscore,
        "overall_health": _overall_health_assessment(liquidity, leverage, profitability, zscore),
    }


def _assess_liquidity(current_ratio, quick_ratio, cash_ratio) -> str:
    if current_ratio and current_ratio >= 1.5:
        return "Strong liquidity position"
    elif current_ratio and current_ratio >= 1.0:
        return "Adequate liquidity, monitor closely"
    elif current_ratio:
        return "Weak liquidity — potential short-term solvency risk"
    return "Insufficient data for assessment"


def _assess_leverage(dte, interest_coverage) -> str:
    issues = []
    if dte and dte > 2.0:
        issues.append("high debt-to-equity")
    if interest_coverage and interest_coverage < 2.0:
        issues.append("weak interest coverage")
    if issues:
        return f"Elevated leverage: {', '.join(issues)}"
    return "Leverage within acceptable range"


def _assess_profitability(gross_margin, operating_margin, net_margin, roe) -> str:
    if gross_margin and gross_margin > 50:
        return "Strong profitability with high gross margins"
    elif operating_margin and operating_margin > 10:
        return "Healthy operating profitability"
    elif net_margin and net_margin > 5:
        return "Moderate profitability"
    elif net_margin:
        return "Thin margins — profitability under pressure"
    return "Insufficient data"


def _assess_efficiency(inv_turnover, dso, dpo, ccc) -> str:
    parts = []
    if dso and dso > 60:
        parts.append("slow collections")
    if inv_turnover and inv_turnover < 4:
        parts.append("slow inventory turnover")
    if ccc and ccc > 90:
        parts.append("long cash conversion cycle")
    if parts:
        return f"Efficiency concerns: {', '.join(parts)}"
    return "Efficiency metrics within normal range"


def _identify_dupont_drivers(net_margin, asset_turnover, equity_multiplier) -> list[str]:
    drivers = []
    if net_margin > 0.10:
        drivers.append("Strong profit margins drive ROE")
    elif net_margin < 0.05:
        drivers.append("Low profit margins drag ROE")
    if asset_turnover > 0.8:
        drivers.append("Efficient asset utilization"
        )
    elif asset_turnover < 0.4:
        drivers.append("Low asset turnover drags ROE")
    if equity_multiplier > 2.5:
        drivers.append("High leverage amplifies ROE (and risk)")
    return drivers


def _overall_health_assessment(liquidity, leverage, profitability, zscore) -> dict[str, Any]:
    score = 0
    signals = []

    cr = liquidity.get("current_ratio")
    if cr and cr >= 1.5:
        score += 2
    elif cr and cr >= 1.0:
        score += 1
    else:
        score -= 1
        signals.append("liquidity_risk")

    dte = leverage.get("debt_to_equity")
    if dte and dte < 1.0:
        score += 2
    elif dte and dte < 2.0:
        score += 1
    else:
        score -= 1
        signals.append("high_leverage")

    nm = profitability.get("net_margin_pct")
    if nm and nm > 10:
        score += 2
    elif nm and nm > 5:
        score += 1

    z = zscore.get("z_score", 0)
    if z > 3.0:
        score += 2
    elif z > 1.8:
        score += 1
    else:
        score -= 2
        signals.append("bankruptcy_risk")

    if score >= 6:
        health = "strong"
    elif score >= 3:
        health = "adequate"
    elif score >= 0:
        health = "watch"
    else:
        health = "concern"

    return {"health_rating": health, "score": score, "risk_signals": signals}
