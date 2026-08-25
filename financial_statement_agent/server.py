"""
Financial Statement Analysis Agent — MCP Server.

Features:
- Financial data extraction and parsing
- Comprehensive ratio analysis (liquidity, leverage, profitability, efficiency)
- DuPont decomposition of ROE
- Altman Z-Score calculation
- Industry benchmark comparison (6 sectors)
- Peer company comparison and ranking
- Multi-period trend analysis
- Deterioration detection
- GAAP compliance checking
- Audit readiness assessment
- Executive summary generation
- RAG-based accounting standards and analytical frameworks
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.financial_data_extraction import (
    extract_financial_data, get_company_info, list_companies,
    upload_statement, validate_statement_completeness,
)
from tools.ratio_analysis import (
    calculate_liquidity_ratios, calculate_leverage_ratios, calculate_profitability_ratios,
    calculate_efficiency_ratios, calculate_dupont_analysis, calculate_altman_zscore,
    full_ratio_analysis,
)
from tools.industry_benchmarks import (
    get_benchmark, list_benchmarks, compare_to_benchmark, full_benchmark_comparison,
)
from tools.peer_comparison import (
    get_peer_group, compare_company_to_peers, rank_peers, peer_summary_stats,
)
from tools.trend_analysis import (
    analyze_trend, multi_metric_trend, detect_deterioration,
)
from tools.compliance_check import (
    check_gaap_compliance, check_ratio_health, audit_readiness_check,
)
from tools.notifications import (
    send_analysis_complete, send_deterioration_alert, send_benchmark_alert,
    send_compliance_issue, generate_executive_summary, get_notification_log,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Financial Statement Analysis Agent",
    instructions=(
        "Financial Statement Analysis Agent for banking. Use these tools to extract and analyze "
        "financial statements, calculate ratios, compare against industry benchmarks and peers, "
        "detect deterioration trends, check GAAP compliance, and generate executive summaries. "
        "All actions are logged for audit trail."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the financial analysis knowledge base for accounting standards, frameworks, benchmarks, and ratios."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  FINANCIAL DATA EXTRACTION
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def extract_data(company_id: str, period: str | None = None, statement_type: str = "all") -> dict[str, Any]:
    """Extract structured financial data for a company."""
    return await extract_financial_data(company_id, period, statement_type)


@mcp.tool()
async def company_info(company_id: str) -> dict[str, Any]:
    """Get company information."""
    return await get_company_info(company_id)


@mcp.tool()
async def companies(industry: str | None = None, is_public: bool | None = None) -> dict[str, Any]:
    """List available companies."""
    return await list_companies(industry, is_public)


@mcp.tool()
async def upload_stmt(
    company_id: str, period: str, period_type: str,
    balance_sheet: dict | None = None, income_statement: dict | None = None,
    cash_flow_statement: dict | None = None,
) -> dict[str, Any]:
    """Upload a financial statement."""
    return await upload_statement(company_id, period, period_type, balance_sheet, income_statement, cash_flow_statement)


@mcp.tool()
async def validate_completeness(company_id: str, period: str) -> dict[str, Any]:
    """Validate that a financial statement is complete."""
    return await validate_statement_completeness(company_id, period)


# ══════════════════════════════════════════════════════════════════
#  RATIO ANALYSIS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def liquidity_ratios(balance_sheet: dict) -> dict[str, Any]:
    """Calculate liquidity ratios from balance sheet data."""
    return await calculate_liquidity_ratios(balance_sheet)


@mcp.tool()
async def leverage_ratios(balance_sheet: dict, income_statement: dict | None = None) -> dict[str, Any]:
    """Calculate leverage/solvency ratios."""
    return await calculate_leverage_ratios(balance_sheet, income_statement)


@mcp.tool()
async def profitability_ratios(income_statement: dict, total_assets: float = 0, total_equity: float = 0) -> dict[str, Any]:
    """Calculate profitability ratios."""
    return await calculate_profitability_ratios(income_statement, total_assets, total_equity)


@mcp.tool()
async def efficiency_ratios(balance_sheet: dict, income_statement: dict) -> dict[str, Any]:
    """Calculate efficiency/activity ratios."""
    return await calculate_efficiency_ratios(balance_sheet, income_statement)


@mcp.tool()
async def dupont_analysis(income_statement: dict, total_assets: float, total_equity: float) -> dict[str, Any]:
    """Perform DuPont decomposition of ROE."""
    return await calculate_dupont_analysis(income_statement, total_assets, total_equity)


@mcp.tool()
async def altman_zscore(balance_sheet: dict, income_statement: dict, market_cap: float = 0) -> dict[str, Any]:
    """Calculate Altman Z-Score for bankruptcy prediction."""
    return await calculate_altman_zscore(balance_sheet, income_statement, market_cap)


@mcp.tool()
async def full_analysis(
    company_id: str, balance_sheet: dict, income_statement: dict,
    cash_flow_statement: dict | None = None, market_cap: float = 0,
) -> dict[str, Any]:
    """Comprehensive ratio analysis across all categories."""
    return await full_ratio_analysis(company_id, balance_sheet, income_statement, cash_flow_statement, market_cap)


# ══════════════════════════════════════════════════════════════════
#  INDUSTRY BENCHMARKS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def benchmark(industry: str) -> dict[str, Any]:
    """Get benchmark data for an industry."""
    return await get_benchmark(industry)


@mcp.tool()
async def benchmarks_list() -> dict[str, Any]:
    """List all available industry benchmarks."""
    return await list_benchmarks()


@mcp.tool()
async def compare_benchmark(industry: str, metric_name: str, company_value: float) -> dict[str, Any]:
    """Compare a single metric against industry benchmark."""
    return await compare_to_benchmark(industry, metric_name, company_value)


@mcp.tool()
async def full_benchmark(industry: str, company_ratios: dict) -> dict[str, Any]:
    """Compare all ratios against industry benchmarks."""
    return await full_benchmark_comparison(industry, company_ratios)


# ══════════════════════════════════════════════════════════════════
#  PEER COMPARISON
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def peer_group(industry: str) -> dict[str, Any]:
    """Get all peers in an industry."""
    return await get_peer_group(industry)


@mcp.tool()
async def compare_to_peers(company_id: str, industry: str, company_ratios: dict) -> dict[str, Any]:
    """Compare a company against its peer group."""
    return await compare_company_to_peers(company_id, industry, company_ratios)


@mcp.tool()
async def peer_ranking(industry: str, metric: str, ascending: bool = False) -> dict[str, Any]:
    """Rank peers by a specific metric."""
    return await rank_peers(industry, metric, ascending)


@mcp.tool()
async def peer_stats(industry: str) -> dict[str, Any]:
    """Get summary statistics for a peer group."""
    return await peer_summary_stats(industry)


# ══════════════════════════════════════════════════════════════════
#  TREND ANALYSIS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def trend(metric_name: str, values: list[dict]) -> dict[str, Any]:
    """Analyze trend for a single metric over multiple periods."""
    return await analyze_trend(metric_name, values)


@mcp.tool()
async def multi_trend(company_id: str, statements: list[dict], metrics: list[str] | None = None) -> dict[str, Any]:
    """Analyze trends across multiple metrics."""
    return await multi_metric_trend(company_id, statements, metrics)


@mcp.tool()
async def deterioration(company_id: str, statements: list[dict]) -> dict[str, Any]:
    """Detect early signs of financial deterioration."""
    return await detect_deterioration(company_id, statements)


# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE CHECKS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def gaap_compliance(company_id: str, balance_sheet: dict, income_statement: dict, cash_flow_statement: dict) -> dict[str, Any]:
    """Check basic US GAAP compliance of financial statements."""
    return await check_gaap_compliance(company_id, balance_sheet, income_statement, cash_flow_statement)


@mcp.tool()
async def ratio_health(ratios: dict, industry: str = "general") -> dict[str, Any]:
    """Check financial ratios against health thresholds."""
    return await check_ratio_health(ratios, industry)


@mcp.tool()
async def audit_readiness(company_id: str, statements: list[dict]) -> dict[str, Any]:
    """Check if financial statements are audit-ready."""
    return await audit_readiness_check(company_id, statements)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS & REPORTS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def notify_analysis(company_id: str, company_name: str, analysis_type: str, summary: dict) -> dict[str, Any]:
    """Send notification when analysis is complete."""
    return await send_analysis_complete(company_id, company_name, analysis_type, summary)


@mcp.tool()
async def notify_deterioration(company_id: str, company_name: str, risk_level: str, warnings: list[dict]) -> dict[str, Any]:
    """Send alert when financial deterioration is detected."""
    return await send_deterioration_alert(company_id, company_name, risk_level, warnings)


@mcp.tool()
async def notify_benchmark(company_id: str, company_name: str, metric: str, company_value: float, benchmark_median: float, comparison: str) -> dict[str, Any]:
    """Send alert when metric deviates from benchmark."""
    return await send_benchmark_alert(company_id, company_name, metric, company_value, benchmark_median, comparison)


@mcp.tool()
async def notify_compliance(company_id: str, company_name: str, issues: list[dict]) -> dict[str, Any]:
    """Send alert for compliance issues found."""
    return await send_compliance_issue(company_id, company_name, issues)


@mcp.tool()
async def executive_summary(company_id: str, company_name: str, ratio_analysis: dict, benchmark_comparison: dict | None = None, trend_analysis: dict | None = None) -> dict[str, Any]:
    """Generate an executive summary of the financial analysis."""
    return await generate_executive_summary(company_id, company_name, ratio_analysis, benchmark_comparison, trend_analysis)


@mcp.tool()
async def notifications_log(company_id: str | None = None, notification_type: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get notification log."""
    return await get_notification_log(company_id, notification_type, limit)


if __name__ == "__main__":
    logger.info("Starting Financial Statement Analysis Agent MCP Server...")
    mcp.run()
