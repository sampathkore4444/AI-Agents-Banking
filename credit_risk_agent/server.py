"""
Credit Risk Monitoring Agent — MCP Server.

Continuously monitors portfolio credit risk, identifies deteriorating
accounts, and triggers early warning alerts.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.alerts import acknowledge_alert, generate_alert, generate_daily_risk_report, get_active_alerts
from tools.early_warning import check_borrower_signals, get_watchlist, run_early_warning_scan
from tools.financial_analysis import analyze_financial_statements
from tools.market_data import get_default_probability_curve, get_market_indicators, get_sector_risk
from tools.portfolio_monitor import check_concentration, get_borrower_exposure, get_portfolio_summary
from tools.rating_agency import check_rating_transition, get_credit_rating
from tools.risk_assessment import assess_borrower_risk, calculate_expected_loss

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Credit Risk Monitoring Agent",
    instructions=(
        "Credit Risk Monitoring Agent for banking. Use these tools to monitor "
        "portfolio credit risk, detect early warning signals, analyze financial "
        "statements, track market data, manage alerts, and assess borrower risk."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_risk_knowledge(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search risk policies, Basel requirements, and credit review procedures using RAG."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  PORTFOLIO MONITORING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_portfolio(portfolio_id: str = "main") -> dict[str, Any]:
    """Get overall portfolio summary with key risk metrics."""
    return await get_portfolio_summary(portfolio_id)


@mcp.tool()
async def get_exposure(borrower_id: str) -> dict[str, Any]:
    """Get detailed exposure for a specific borrower."""
    return await get_borrower_exposure(borrower_id)


@mcp.tool()
async def check_portfolio_concentration(portfolio_id: str = "main") -> dict[str, Any]:
    """Check portfolio concentration against limits."""
    return await check_concentration(portfolio_id)


# ══════════════════════════════════════════════════════════════════
#  EARLY WARNING SYSTEM
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def run_early_warning(portfolio_id: str = "main") -> dict[str, Any]:
    """Scan entire portfolio for early warning signals."""
    return await run_early_warning_scan(portfolio_id)


@mcp.tool()
async def check_borrower(borrower_id: str) -> dict[str, Any]:
    """Check early warning signals for a specific borrower."""
    return await check_borrower_signals(borrower_id)


@mcp.tool()
async def get_watchlist_borrowers() -> dict[str, Any]:
    """Get current watchlist of deteriorating borrowers."""
    return await get_watchlist()


# ══════════════════════════════════════════════════════════════════
#  FINANCIAL ANALYSIS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def analyze_financials(borrower_id: str, financial_data: dict | None = None) -> dict[str, Any]:
    """Analyze financial statements: ratios, Z-Score, credit health."""
    return await analyze_financial_statements(borrower_id, financial_data)


# ══════════════════════════════════════════════════════════════════
#  MARKET DATA
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_market() -> dict[str, Any]:
    """Get current market indicators (credit spreads, yields, VIX)."""
    return await get_market_indicators()


@mcp.tool()
async def get_sector(sector: str) -> dict[str, Any]:
    """Get sector-specific risk indicators."""
    return await get_sector_risk(sector)


@mcp.tool()
async def get_pd_curve(borrower_id: str) -> dict[str, Any]:
    """Get term structure of default probability for a borrower."""
    return await get_default_probability_curve(borrower_id)


# ══════════════════════════════════════════════════════════════════
#  RATING AGENCY
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_rating(borrower_id: str) -> dict[str, Any]:
    """Get current credit rating from major agencies."""
    return await get_credit_rating(borrower_id)


@mcp.tool()
async def check_rating(borrower_id: str) -> dict[str, Any]:
    """Check rating transition probability."""
    return await check_rating_transition(borrower_id)


# ══════════════════════════════════════════════════════════════════
#  ALERT MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_alert(borrower_id: str, alert_type: str, severity: str, message: str, recommended_action: str | None = None) -> dict[str, Any]:
    """Generate a new risk alert."""
    return await generate_alert(borrower_id, alert_type, severity, message, recommended_action)


@mcp.tool()
async def acknowledge(alert_id: str, analyst_id: str, notes: str | None = None) -> dict[str, Any]:
    """Acknowledge an active alert."""
    return await acknowledge_alert(alert_id, analyst_id, notes)


@mcp.tool()
async def get_alerts(severity_filter: str | None = None) -> dict[str, Any]:
    """Get all active risk alerts."""
    return await get_active_alerts(severity_filter)


@mcp.tool()
async def daily_report(portfolio_id: str = "main") -> dict[str, Any]:
    """Generate daily risk summary report."""
    return await generate_daily_risk_report(portfolio_id)


# ══════════════════════════════════════════════════════════════════
#  RISK ASSESSMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def assess_risk(borrower_id: str) -> dict[str, Any]:
    """Comprehensive risk assessment combining all data sources."""
    return await assess_borrower_risk(borrower_id)


@mcp.tool()
async def calculate_el(exposure: float, probability_of_default: float, loss_given_default: float) -> dict[str, Any]:
    """Calculate Expected Loss (EL = PD × LGD × EAD)."""
    return await calculate_expected_loss(exposure, probability_of_default, loss_given_default)


if __name__ == "__main__":
    logger.info("Starting Credit Risk Monitoring Agent MCP Server...")
    mcp.run()
