"""
Peer Comparison Tools — Compare financial metrics across peer companies.
"""

from __future__ import annotations

from typing import Any


# ── Peer company data ─────────────────────────────────────────────
_PEERS: dict[str, dict[str, Any]] = {
    "TECH-A": {
        "company_id": "TECH-A",
        "name": "Acme Technologies",
        "industry": "technology",
        "market_cap": 25000000000,
        "ratios": {
            "current_ratio": 2.77, "debt_to_equity": 0.23,
            "gross_margin_pct": 60.0, "operating_margin_pct": 20.0,
            "net_margin_pct": 15.3, "roa_pct": 11.5, "roe_pct": 17.8,
            "interest_coverage": 20.0, "asset_turnover": 0.75,
        },
    },
    "TECH-B": {
        "company_id": "TECH-B",
        "name": "BetaSoft Inc.",
        "industry": "technology",
        "market_cap": 8000000000,
        "ratios": {
            "current_ratio": 3.20, "debt_to_equity": 0.15,
            "gross_margin_pct": 72.0, "operating_margin_pct": 25.0,
            "net_margin_pct": 20.0, "roa_pct": 18.0, "roe_pct": 22.0,
            "interest_coverage": 35.0, "asset_turnover": 0.60,
        },
    },
    "TECH-C": {
        "company_id": "TECH-C",
        "name": "CloudNine Systems",
        "industry": "technology",
        "market_cap": 3000000000,
        "ratios": {
            "current_ratio": 1.90, "debt_to_equity": 0.65,
            "gross_margin_pct": 48.0, "operating_margin_pct": 12.0,
            "net_margin_pct": 8.0, "roa_pct": 6.0, "roe_pct": 14.0,
            "interest_coverage": 6.0, "asset_turnover": 0.85,
        },
    },
    "MFG-A": {
        "company_id": "MFG-A",
        "name": "Globex Manufacturing",
        "industry": "manufacturing",
        "market_cap": 5000000000,
        "ratios": {
            "current_ratio": 1.75, "debt_to_equity": 0.85,
            "gross_margin_pct": 32.0, "operating_margin_pct": 9.0,
            "net_margin_pct": 5.5, "roa_pct": 6.5, "roe_pct": 13.0,
            "interest_coverage": 5.5, "asset_turnover": 0.82,
        },
    },
    "MFG-B": {
        "company_id": "MFG-B",
        "name": "Precision Parts Corp",
        "industry": "manufacturing",
        "market_cap": 2000000000,
        "ratios": {
            "current_ratio": 1.45, "debt_to_equity": 1.20,
            "gross_margin_pct": 28.0, "operating_margin_pct": 6.0,
            "net_margin_pct": 3.5, "roa_pct": 4.5, "roe_pct": 10.0,
            "interest_coverage": 3.2, "asset_turnover": 0.90,
        },
    },
    "RET-A": {
        "company_id": "RET-A",
        "name": "Springfield Retail",
        "industry": "retail",
        "market_cap": 12000000000,
        "ratios": {
            "current_ratio": 1.35, "debt_to_equity": 1.10,
            "gross_margin_pct": 36.0, "operating_margin_pct": 5.5,
            "net_margin_pct": 3.2, "roa_pct": 7.5, "roe_pct": 16.0,
            "interest_coverage": 4.5, "asset_turnover": 1.60,
        },
    },
}


async def get_peer_group(industry: str) -> dict[str, Any]:
    """Get all peers in an industry."""
    peers = [p for p in _PEERS.values() if p["industry"] == industry]
    return {"industry": industry, "count": len(peers), "peers": peers}


async def compare_company_to_peers(
    company_id: str,
    industry: str,
    company_ratios: dict[str, Any],
) -> dict[str, Any]:
    """Compare a company against its peer group."""
    peers = [p for p in _PEERS.values() if p["industry"] == industry and p["company_id"] != company_id]
    if not peers:
        return {"error": f"No peers found for industry: {industry}"}

    comparisons = {}
    for metric in ["current_ratio", "debt_to_equity", "gross_margin_pct", "operating_margin_pct", "net_margin_pct", "roa_pct", "roe_pct", "interest_coverage", "asset_turnover"]:
        peer_values = [p["ratios"].get(metric) for p in peers if metric in p["ratios"]]
        company_value = _deep_find(company_ratios, metric)

        if peer_values and company_value is not None:
            peer_avg = sum(peer_values) / len(peer_values)
            peer_min = min(peer_values)
            peer_max = max(peer_values)
            rank = sum(1 for v in peer_values if company_value > v) + 1

            comparisons[metric] = {
                "company_value": company_value,
                "peer_average": round(peer_avg, 2),
                "peer_min": peer_min,
                "peer_max": peer_max,
                "peer_count": len(peer_values),
                "rank": f"{rank}/{len(peer_values) + 1}",
                "vs_average_pct": round((company_value - peer_avg) / peer_avg * 100, 1) if peer_avg != 0 else 0,
            }

    return {
        "company_id": company_id,
        "industry": industry,
        "peer_count": len(peers),
        "comparisons": comparisons,
    }


async def rank_peers(
    industry: str,
    metric: str,
    ascending: bool = False,
) -> dict[str, Any]:
    """Rank peers by a specific metric."""
    peers = [p for p in _PEERS.values() if p["industry"] == industry]

    ranked = []
    for p in peers:
        value = p["ratios"].get(metric)
        if value is not None:
            ranked.append({"company_id": p["company_id"], "name": p["name"], "metric_value": value})

    ranked.sort(key=lambda x: x["metric_value"], reverse=not ascending)
    for i, r in enumerate(ranked, 1):
        r["rank"] = i

    return {"industry": industry, "metric": metric, "ranking": ranked}


async def peer_summary_stats(industry: str) -> dict[str, Any]:
    """Get summary statistics for a peer group."""
    peers = [p for p in _PEERS.values() if p["industry"] == industry]
    if not peers:
        return {"error": f"No peers found for industry: {industry}"}

    metrics = ["current_ratio", "debt_to_equity", "gross_margin_pct", "operating_margin_pct", "net_margin_pct", "roa_pct", "roe_pct"]
    stats = {}

    for metric in metrics:
        values = [p["ratios"][metric] for p in peers if metric in p["ratios"]]
        if values:
            stats[metric] = {
                "mean": round(sum(values) / len(values), 2),
                "min": min(values),
                "max": max(values),
                "median": sorted(values)[len(values) // 2],
                "count": len(values),
            }

    return {"industry": industry, "peer_count": len(peers), "metrics": stats}


def _deep_find(d: dict, key: str) -> float | None:
    for k, v in d.items():
        if k == key and isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, dict):
            found = _deep_find(v, key)
            if found is not None:
                return found
    return None
