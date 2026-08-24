"""
Cross-Border Payment Assistant Agent — MCP Server.

Assists customers with international wire transfers — explains fees,
timelines, exchange rates, and compliance requirements.

Covers all 7.3 Cross-Border Payment Assistant Agent capabilities:
- FX rate lookup and comparison
- SWIFT gpi payment tracking
- Correspondent bank discovery
- Sanctions screening (OFAC, EU, UN)
- Compliance checking (Travel Rule, country risk)
- Country-specific regulations
- All-in cost quotes
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.compliance import check_payment_compliance, get_required_information
from tools.correspondent_banks import get_bic_details, get_routing_path, lookup_correspondent
from tools.country_regulations import check_capital_controls, get_country_regulations
from tools.fx_rates import compare_rates, get_fx_rate, get_historical_rate
from tools.notifications import send_xborder_notification
from tools.payment_quotes import compare_options, generate_quote
from tools.sanctions_screening import screen_sanctions
from tools.swift_tracking import get_transaction_history, initiate_payment, track_payment

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Cross-Border Payment Assistant Agent",
    instructions=(
        "Cross-Border Payment Assistant Agent for banking. Use these tools to "
        "help customers with international wire transfers: check FX rates, "
        "generate quotes, track payments, screen sanctions, verify compliance, "
        "and look up correspondent banks and country regulations."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the cross-border payment knowledge base for SWIFT codes, regulations, and correspondent banking details."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  FX RATES
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_rate(source_currency: str, target_currency: str, amount: float | None = None) -> dict[str, Any]:
    """Get current exchange rate for a currency pair."""
    return await get_fx_rate(source_currency, target_currency, amount)


@mcp.tool()
async def compare_fx_rates(source_currency: str, target_currency: str, amount: float) -> dict[str, Any]:
    """Compare FX rates across different channels (online, branch, wire, broker)."""
    return await compare_rates(source_currency, target_currency, amount)


@mcp.tool()
async def get_history_rate(source_currency: str, target_currency: str, date: str) -> dict[str, Any]:
    """Get historical exchange rate for a date."""
    return await get_historical_rate(source_currency, target_currency, date)


# ══════════════════════════════════════════════════════════════════
#  SWIFT GPI TRACKING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def track_wire(uetr: str) -> dict[str, Any]:
    """Track a cross-border payment using SWIFT gpi UETR."""
    return await track_payment(uetr)


@mcp.tool()
async def send_wire(source_currency: str, target_currency: str, amount: float, originator_name: str, originator_account: str, beneficiary_name: str, beneficiary_account: str, beneficiary_bank_bic: str, purpose: str, charges_type: str = "SHA") -> dict[str, Any]:
    """Initiate a cross-border wire transfer."""
    return await initiate_payment(source_currency, target_currency, amount, originator_name, originator_account, beneficiary_name, beneficiary_account, beneficiary_bank_bic, purpose, charges_type)


@mcp.tool()
async def wire_history(originator_account: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Get recent cross-border transaction history."""
    return await get_transaction_history(originator_account, limit)


# ══════════════════════════════════════════════════════════════════
#  CORRESPONDENT BANKS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def find_correspondent(currency: str, source_country: str | None = None, target_country: str | None = None) -> dict[str, Any]:
    """Find correspondent banks for a currency and routing path."""
    return await lookup_correspondent(currency, source_country, target_country)


@mcp.tool()
async def get_route(source_currency: str, target_currency: str, source_country: str, target_country: str) -> dict[str, Any]:
    """Determine optimal routing path for a cross-border payment."""
    return await get_routing_path(source_currency, target_currency, source_country, target_country)


@mcp.tool()
async def lookup_bic(bic: str) -> dict[str, Any]:
    """Get details for a specific BIC/SWIFT code."""
    return await get_bic_details(bic)


# ══════════════════════════════════════════════════════════════════
#  SANCTIONS SCREENING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def screen_entity(entity_name: str, country: str | None = None, entity_type: str = "individual") -> dict[str, Any]:
    """Screen an entity against OFAC, EU, and UN sanctions lists."""
    return await screen_sanctions(entity_name, country, entity_type)


# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def check_compliance(originator_name: str, originator_country: str, beneficiary_name: str, beneficiary_country: str, amount: float, currency: str, purpose: str) -> dict[str, Any]:
    """Run full compliance check on a cross-border payment."""
    return await check_payment_compliance(originator_name, originator_country, beneficiary_name, beneficiary_country, amount, currency, purpose)


@mcp.tool()
async def required_info(originator_country: str, beneficiary_country: str, amount: float, currency: str) -> dict[str, Any]:
    """Determine required information for a cross-border payment."""
    return await get_required_information(originator_country, beneficiary_country, amount, currency)


# ══════════════════════════════════════════════════════════════════
#  COUNTRY REGULATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_regulations(country_code: str) -> dict[str, Any]:
    """Get cross-border payment regulations for a country."""
    return await get_country_regulations(country_code)


@mcp.tool()
async def check_controls(source_country: str, target_country: str, amount: float, currency: str) -> dict[str, Any]:
    """Check if capital controls apply to a cross-border payment."""
    return await check_capital_controls(source_country, target_country, amount, currency)


# ══════════════════════════════════════════════════════════════════
#  PAYMENT QUOTES
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_quote(source_currency: str, target_currency: str, amount: float, originator_country: str, beneficiary_country: str, charges_type: str = "SHA", urgency: str = "standard") -> dict[str, Any]:
    """Generate an all-in cost quote for a cross-border payment."""
    return await generate_quote(source_currency, target_currency, amount, originator_country, beneficiary_country, charges_type, urgency=urgency)


@mcp.tool()
async def compare_payment_options(source_currency: str, target_currency: str, amount: float, originator_country: str, beneficiary_country: str) -> dict[str, Any]:
    """Compare different payment options (wire vs express vs FX broker)."""
    return await compare_options(source_currency, target_currency, amount, originator_country, beneficiary_country)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def notify_customer(recipient_id: str, template_id: str, channel: str = "email", variables: dict | None = None) -> dict[str, Any]:
    """Send a cross-border payment notification."""
    return await send_xborder_notification(recipient_id, template_id, channel, variables)


if __name__ == "__main__":
    logger.info("Starting Cross-Border Payment Assistant Agent MCP Server...")
    mcp.run()
