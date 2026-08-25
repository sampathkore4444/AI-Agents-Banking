"""
Trend Analysis Tools — Analyze financial metrics over time.
"""

from __future__ import annotations

from typing import Any


async def analyze_trend(
    metric_name: str,
    values: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze trend for a single metric over multiple periods."""
    if len(values) < 2:
        return {"error": "Need at least 2 data points for trend analysis"}

    periods = sorted(values, key=lambda v: v["period"])
    numeric_values = [v["value"] for v in periods]

    # Calculate changes
    period_changes = []
    for i in range(1, len(periods)):
        prev = periods[i - 1]["value"]
        curr = periods[i]["value"]
        change = curr - prev
        pct_change = round((change / prev * 100), 1) if prev != 0 else None
        period_changes.append({
            "from_period": periods[i - 1]["period"],
            "to_period": periods[i]["period"],
            "from_value": prev,
            "to_value": curr,
            "change": round(change, 2),
            "pct_change": pct_change,
        })

    # Overall trend
    first_val = numeric_values[0]
    last_val = numeric_values[-1]
    total_change = last_val - first_val
    total_pct = round((total_change / first_val * 100), 1) if first_val != 0 else 0

    # CAGR (if periods are annual)
    n_periods = len(periods) - 1
    cagr = round(((last_val / first_val) ** (1 / n_periods) - 1) * 100, 2) if first_val > 0 and n_periods > 0 else None

    # Direction
    if total_pct > 10:
        direction = "strong_upward"
    elif total_pct > 2:
        direction = "upward"
    elif total_pct > -2:
        direction = "stable"
    elif total_pct > -10:
        direction = "downward"
    else:
        direction = "strong_downward"

    # Volatility
    avg_change = sum(abs(c["pct_change"] or 0) for c in period_changes) / len(period_changes)
    max_change = max(abs(c["pct_change"] or 0) for c in period_changes)

    return {
        "metric": metric_name,
        "periods": len(periods),
        "first_period": periods[0]["period"],
        "last_period": periods[-1]["period"],
        "first_value": first_val,
        "last_value": last_val,
        "total_change": round(total_change, 2),
        "total_pct_change": total_pct,
        "cagr_pct": cagr,
        "direction": direction,
        "period_changes": period_changes,
        "volatility": {
            "avg_period_change_pct": round(avg_change, 2),
            "max_period_change_pct": max_change,
        },
    }


async def multi_metric_trend(
    company_id: str,
    statements: list[dict[str, Any]],
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze trends across multiple metrics."""
    if metrics is None:
        metrics = ["revenue", "net_income", "gross_profit", "operating_income", "total_assets", "total_debt"]

    trends = {}
    for metric in metrics:
        values = []
        for stmt in sorted(statements, key=lambda s: s["period"]):
            val = _extract_metric(stmt, metric)
            if val is not None:
                values.append({"period": stmt["period"], "value": val})

        if values:
            trend = await analyze_trend(metric, values)
            trends[metric] = trend

    return {"company_id": company_id, "metrics_analyzed": len(trends), "trends": trends}


async def detect_deterioration(
    company_id: str,
    statements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect early signs of financial deterioration."""
    if len(statements) < 2:
        return {"error": "Need at least 2 periods for deterioration detection"}

    sorted_stmts = sorted(statements, key=lambda s: s["period"])
    warnings = []

    # Check revenue trend
    revenues = [(s["period"], _extract_metric(s, "revenue")) for s in sorted_stmts]
    revenues = [(p, v) for p, v in revenues if v is not None]
    if len(revenues) >= 2:
        rev_change = (revenues[-1][1] - revenues[-2][1]) / revenues[-2][1] * 100 if revenues[-2][1] else 0
        if rev_change < -5:
            warnings.append({"indicator": "revenue_decline", "severity": "high" if rev_change < -15 else "medium", "detail": f"Revenue declined {rev_change:.1f}%"})

    # Check margin compression
    margins = []
    for s in sorted_stmts:
        rev = _extract_metric(s, "revenue")
        ni = _extract_metric(s, "net_income")
        if rev and ni and rev > 0:
            margins.append((s["period"], ni / rev * 100))
    if len(margins) >= 2:
        margin_change = margins[-1][1] - margins[-2][1]
        if margin_change < -2:
            warnings.append({"indicator": "margin_compression", "severity": "high" if margin_change < -5 else "medium", "detail": f"Net margin declined {margin_change:.1f}pp"})

    # Check rising leverage
    leverage = []
    for s in sorted_stmts:
        tl = _extract_metric(s, "total_liabilities")
        te = _extract_metric(s, "total_equity")
        if tl and te and te > 0:
            leverage.append((s["period"], tl / te))
    if len(leverage) >= 2:
        lev_change = (leverage[-1][1] - leverage[-2][1]) / leverage[-2][1] * 100 if leverage[-2][1] else 0
        if lev_change > 10:
            warnings.append({"indicator": "rising_leverage", "severity": "high" if lev_change > 25 else "medium", "detail": f"Debt-to-equity increased {lev_change:.1f}%"})

    # Check declining cash flow
    cashflows = [(s["period"], _extract_metric(s, "cash_from_operations")) for s in sorted_stmts]
    cashflows = [(p, v) for p, v in cashflows if v is not None]
    if len(cashflows) >= 2:
        cf_change = (cashflows[-1][1] - cashflows[-2][1]) / abs(cashflows[-2][1]) * 100 if cashflows[-2][1] else 0
        if cf_change < -10:
            warnings.append({"indicator": "declining_cfo", "severity": "high" if cf_change < -25 else "medium", "detail": f"CFO declined {cf_change:.1f}%"})

    # Check earnings quality (CFO vs NI)
    for s in sorted_stmts[-1:]:
        ni = _extract_metric(s, "net_income")
        cfo = _extract_metric(s, "cash_from_operations")
        if ni and cfo and cfo < ni * 0.7:
            warnings.append({"indicator": "earnings_quality", "severity": "medium", "detail": f"CFO (${cfo/1e6:.0f}M) significantly below NI (${ni/1e6:.0f}M)"})

    severity_order = {"high": 0, "medium": 1, "low": 2}
    warnings.sort(key=lambda w: severity_order.get(w["severity"], 3))

    risk_level = "low"
    if any(w["severity"] == "high" for w in warnings):
        risk_level = "high"
    elif any(w["severity"] == "medium" for w in warnings):
        risk_level = "medium"

    return {
        "company_id": company_id,
        "periods_analyzed": len(sorted_stmts),
        "deterioration_signals": len(warnings),
        "risk_level": risk_level,
        "warnings": warnings,
    }


def _extract_metric(statement: dict, metric_name: str) -> float | None:
    """Extract a metric from a statement, searching nested dicts."""
    for section in ["income_statement", "balance_sheet", "cash_flow_statement"]:
        data = statement.get(section, {})
        if metric_name in data:
            return float(data[metric_name])
    # Handle derived metrics
    if metric_name == "total_debt":
        bs = statement.get("balance_sheet", {})
        return (bs.get("long_term_debt", 0) or 0) + (bs.get("short_term_debt", 0) or 0)
    return None
