"""
Industry Benchmark Tools — Compare financial metrics against industry peers.
"""

from __future__ import annotations

from typing import Any


# ── Industry benchmark data ───────────────────────────────────────
_BENCHMARKS: dict[str, dict[str, Any]] = {
    "technology": {
        "industry": "Technology",
        "naics": "51",
        "metrics": {
            "current_ratio": {"median": 2.8, "p25": 1.8, "p75": 4.0},
            "debt_to_equity": {"median": 0.4, "p25": 0.1, "p75": 0.8},
            "gross_margin_pct": {"median": 55.0, "p25": 40.0, "p75": 68.0},
            "operating_margin_pct": {"median": 18.0, "p25": 8.0, "p75": 28.0},
            "net_margin_pct": {"median": 15.0, "p25": 5.0, "p75": 25.0},
            "roa_pct": {"median": 12.0, "p25": 5.0, "p75": 20.0},
            "roe_pct": {"median": 18.0, "p25": 8.0, "p75": 30.0},
            "interest_coverage": {"median": 15.0, "p25": 5.0, "p75": 30.0},
            "asset_turnover": {"median": 0.7, "p25": 0.4, "p75": 1.0},
            "days_sales_outstanding": {"median": 45, "p25": 30, "p75": 60},
            "days_inventory_outstanding": {"median": 15, "p25": 5, "p75": 30},
        },
    },
    "manufacturing": {
        "industry": "Manufacturing",
        "naics": "31-33",
        "metrics": {
            "current_ratio": {"median": 1.8, "p25": 1.2, "p75": 2.5},
            "debt_to_equity": {"median": 0.8, "p25": 0.3, "p75": 1.5},
            "gross_margin_pct": {"median": 30.0, "p25": 20.0, "p75": 40.0},
            "operating_margin_pct": {"median": 8.0, "p25": 3.0, "p75": 15.0},
            "net_margin_pct": {"median": 5.0, "p25": 1.0, "p75": 10.0},
            "roa_pct": {"median": 6.0, "p25": 2.0, "p75": 10.0},
            "roe_pct": {"median": 12.0, "p25": 5.0, "p75": 20.0},
            "interest_coverage": {"median": 5.0, "p25": 2.0, "p75": 10.0},
            "asset_turnover": {"median": 0.8, "p25": 0.5, "p75": 1.2},
            "days_sales_outstanding": {"median": 50, "p25": 35, "p75": 65},
            "days_inventory_outstanding": {"median": 60, "p25": 35, "p75": 90},
        },
    },
    "retail": {
        "industry": "Retail",
        "naics": "44-45",
        "metrics": {
            "current_ratio": {"median": 1.3, "p25": 0.9, "p75": 1.8},
            "debt_to_equity": {"median": 1.2, "p25": 0.5, "p75": 2.0},
            "gross_margin_pct": {"median": 35.0, "p25": 25.0, "p75": 45.0},
            "operating_margin_pct": {"median": 5.0, "p25": 2.0, "p75": 10.0},
            "net_margin_pct": {"median": 3.0, "p25": 0.5, "p75": 6.0},
            "roa_pct": {"median": 7.0, "p25": 3.0, "p75": 12.0},
            "roe_pct": {"median": 15.0, "p25": 5.0, "p75": 25.0},
            "interest_coverage": {"median": 4.0, "p25": 1.5, "p75": 8.0},
            "asset_turnover": {"median": 1.5, "p25": 1.0, "p75": 2.2},
            "days_sales_outstanding": {"median": 10, "p25": 5, "p75": 20},
            "days_inventory_outstanding": {"median": 70, "p25": 40, "p75": 100},
        },
    },
    "financial": {
        "industry": "Financial Services",
        "naics": "52",
        "metrics": {
            "current_ratio": {"median": 1.0, "p25": 0.8, "p75": 1.3},
            "debt_to_equity": {"median": 5.0, "p25": 3.0, "p75": 8.0},
            "gross_margin_pct": {"median": 100.0, "p25": 100.0, "p75": 100.0},
            "operating_margin_pct": {"median": 25.0, "p25": 15.0, "p75": 35.0},
            "net_margin_pct": {"median": 20.0, "p25": 10.0, "p75": 30.0},
            "roa_pct": {"median": 1.2, "p25": 0.5, "p75": 2.0},
            "roe_pct": {"median": 12.0, "p25": 6.0, "p75": 18.0},
            "interest_coverage": {"median": 3.0, "p25": 1.5, "p75": 5.0},
            "asset_turnover": {"median": 0.05, "p25": 0.03, "p75": 0.08},
            "days_sales_outstanding": {"median": 0, "p25": 0, "p75": 0},
            "days_inventory_outstanding": {"median": 0, "p25": 0, "p75": 0},
        },
    },
    "healthcare": {
        "industry": "Healthcare",
        "naics": "62",
        "metrics": {
            "current_ratio": {"median": 1.6, "p25": 1.1, "p75": 2.2},
            "debt_to_equity": {"median": 0.9, "p25": 0.4, "p75": 1.5},
            "gross_margin_pct": {"median": 40.0, "p25": 28.0, "p75": 55.0},
            "operating_margin_pct": {"median": 10.0, "p25": 4.0, "p75": 18.0},
            "net_margin_pct": {"median": 7.0, "p25": 2.0, "p75": 14.0},
            "roa_pct": {"median": 6.0, "p25": 2.0, "p75": 10.0},
            "roe_pct": {"median": 13.0, "p25": 5.0, "p75": 22.0},
            "interest_coverage": {"median": 4.5, "p25": 2.0, "p75": 8.0},
            "asset_turnover": {"median": 0.7, "p25": 0.4, "p75": 1.0},
            "days_sales_outstanding": {"median": 50, "p25": 35, "p75": 65},
            "days_inventory_outstanding": {"median": 30, "p25": 15, "p75": 50},
        },
    },
    "energy": {
        "industry": "Energy",
        "naics": "21",
        "metrics": {
            "current_ratio": {"median": 1.4, "p25": 1.0, "p75": 1.9},
            "debt_to_equity": {"median": 0.7, "p25": 0.3, "p75": 1.2},
            "gross_margin_pct": {"median": 40.0, "p25": 25.0, "p75": 55.0},
            "operating_margin_pct": {"median": 15.0, "p25": 5.0, "p75": 25.0},
            "net_margin_pct": {"median": 8.0, "p25": 1.0, "p75": 15.0},
            "roa_pct": {"median": 5.0, "p25": 1.0, "p75": 9.0},
            "roe_pct": {"median": 10.0, "p25": 2.0, "p75": 18.0},
            "interest_coverage": {"median": 6.0, "p25": 2.5, "p75": 12.0},
            "asset_turnover": {"median": 0.5, "p25": 0.3, "p75": 0.8},
            "days_sales_outstanding": {"median": 30, "p25": 15, "p75": 45},
            "days_inventory_outstanding": {"median": 25, "p25": 10, "p75": 45},
        },
    },
}


async def get_benchmark(industry: str) -> dict[str, Any]:
    """Get benchmark data for an industry."""
    if industry in _BENCHMARKS:
        return _BENCHMARKS[industry]
    return {"error": f"No benchmark data for industry: {industry}"}


async def list_benchmarks() -> dict[str, Any]:
    """List all available industry benchmarks."""
    return {
        "industries": list(_BENCHMARKS.keys()),
        "count": len(_BENCHMARKS),
    }


async def compare_to_benchmark(
    industry: str,
    metric_name: str,
    company_value: float,
) -> dict[str, Any]:
    """Compare a single metric against industry benchmark."""
    if industry not in _BENCHMARKS:
        return {"error": f"No benchmark data for industry: {industry}"}

    benchmark = _BENCHMARKS[industry]["metrics"].get(metric_name)
    if not benchmark:
        return {"error": f"Metric '{metric_name}' not found in benchmarks"}

    median = benchmark["median"]
    p25 = benchmark["p25"]
    p75 = benchmark["p75"]

    if company_value >= p75:
        percentile_label = "top quartile (above 75th)"
        comparison = "strong"
    elif company_value >= median:
        percentile_label = "above median (50th-75th)"
        comparison = "above_average"
    elif company_value >= p25:
        percentile_label = "below median (25th-50th)"
        comparison = "below_average"
    else:
        percentile_label = "bottom quartile (below 25th)"
        comparison = "weak"

    # For lower-is-better metrics, invert
    lower_is_better = {"debt_to_equity", "days_sales_outstanding", "days_inventory_outstanding", "cash_conversion_cycle"}
    if metric_name in lower_is_better:
        if company_value <= p25:
            percentile_label = "top quartile (below 25th — best)"
            comparison = "strong"
        elif company_value <= median:
            percentile_label = "above median (25th-50th)"
            comparison = "above_average"
        elif company_value <= p75:
            percentile_label = "below median (50th-75th)"
            comparison = "below_average"
        else:
            percentile_label = "bottom quartile (above 75th — worst)"
            comparison = "weak"

    return {
        "metric": metric_name,
        "industry": _BENCHMARKS[industry]["industry"],
        "company_value": company_value,
        "benchmark_median": median,
        "benchmark_p25": p25,
        "benchmark_p75": p75,
        "percentile_label": percentile_label,
        "comparison": comparison,
    }


async def full_benchmark_comparison(
    industry: str,
    company_ratios: dict[str, Any],
) -> dict[str, Any]:
    """Compare all available ratios against industry benchmarks."""
    if industry not in _BENCHMARKS:
        return {"error": f"No benchmark data for industry: {industry}"}

    benchmark = _BENCHMARKS[industry]
    comparisons = []

    for metric_name, benchmark_data in benchmark["metrics"].items():
        # Try to find matching value in company ratios (flatten nested dicts)
        company_value = _find_metric_value(company_ratios, metric_name)
        if company_value is not None:
            comp = await compare_to_benchmark(industry, metric_name, company_value)
            comparisons.append(comp)

    strong = sum(1 for c in comparisons if c["comparison"] == "strong")
    weak = sum(1 for c in comparisons if c["comparison"] == "weak")

    return {
        "industry": benchmark["industry"],
        "metrics_compared": len(comparisons),
        "strong_count": strong,
        "weak_count": weak,
        "comparisons": comparisons,
        "summary": f"{strong} strong, {len(comparisons) - strong - weak} average, {weak} weak vs industry peers",
    }


def _find_metric_value(ratios: dict, metric_name: str) -> float | None:
    """Recursively search nested dict for a metric value."""
    for key, value in ratios.items():
        if key == metric_name and isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            found = _find_metric_value(value, metric_name)
            if found is not None:
                return found
    return None
