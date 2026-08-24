"""
Product Recommendation Agent — MCP Server.

Features:
- Personalized product recommendations
- Cross-sell and upsell detection
- ML-based customer-product matching using embeddings
- Promotional offer management
- Campaign management and analytics
- Customer 360 view
- CRM integration
- RAG-based product knowledge retrieval
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.product_catalog import add_product, compare_products, deactivate_product, get_product, get_product_recommendations, search_products, update_product
from tools.customer_360 import add_customer, get_customer_360, get_customer_products, get_customer_segments, get_customer_transactions, get_high_value_customers, search_customers, update_customer_profile
from tools.recommendation_engine import generate_recommendations, get_recommendation_explanation, get_upsell_opportunities, get_win_back_recommendations
from tools.offer_management import create_offer, deactivate_offer, get_active_offers, get_offer, get_offer_analytics, get_personalized_offers, redeem_offer, update_offer
from tools.campaign_management import close_campaign, create_campaign, get_campaign, get_campaign_analytics, get_campaigns, launch_campaign, pause_campaign, record_click, record_conversion, record_impression, schedule_outreach, update_campaign
from tools.product_embedding import cluster_customers, embed_customer_preferences, embed_product, find_similar_products, get_embedding_stats, match_customer_to_products
from tools.notifications import get_notification_history, get_notification_stats, send_cross_sell_notification, send_offer_notification, send_product_recommendation
from tools.crm import close_lead, convert_lead, create_lead, get_crm_stats, get_customer_interactions, get_lead, get_leads, get_pending_follow_ups, log_interaction, update_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Product Recommendation Agent",
    instructions=(
        "Product Recommendation Agent for banking. Use these tools to recommend "
        "banking products: search catalog, match customer profiles, manage offers, "
        "run campaigns, and track conversions."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the product knowledge base for catalog, eligibility, and offers."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  PRODUCT CATALOG
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_products_tool(
    category: str | None = None,
    subcategory: str | None = None,
    target_segment: str | None = None,
    min_credit_score: int | None = None,
    max_annual_fee: float | None = None,
) -> dict[str, Any]:
    """Search products by category, segment, credit score, and fees."""
    return await search_products(category, subcategory, target_segment, min_credit_score, max_annual_fee)


@mcp.tool()
async def get_product_details(product_id: str) -> dict[str, Any]:
    """Get detailed product information."""
    return await get_product(product_id)


@mcp.tool()
async def compare_products_tool(product_ids: list[str]) -> dict[str, Any]:
    """Compare multiple products side by side."""
    return await compare_products(product_ids)


@mcp.tool()
async def get_related_products(product_id: str, limit: int = 5) -> dict[str, Any]:
    """Get related product recommendations."""
    return await get_product_recommendations(product_id, limit)


@mcp.tool()
async def add_new_product(
    product_id: str,
    name: str,
    category: str,
    subcategory: str,
    description: str,
    features: list[str],
    target_segments: list[str],
    **kwargs: Any,
) -> dict[str, Any]:
    """Add a new product to the catalog."""
    return await add_product(product_id, name, category, subcategory, description, features, target_segments, **kwargs)


@mcp.tool()
async def update_product_details(product_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update product details."""
    return await update_product(product_id, updates)


@mcp.tool()
async def deactivate_product_tool(product_id: str, reason: str) -> dict[str, Any]:
    """Deactivate a product from the catalog."""
    return await deactivate_product(product_id, reason)


# ══════════════════════════════════════════════════════════════════
#  CUSTOMER 360
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_customer_profile(customer_id: str) -> dict[str, Any]:
    """Get complete customer 360 view."""
    return await get_customer_360(customer_id)


@mcp.tool()
async def search_customers_tool(
    segment: str | None = None,
    lifecycle_stage: str | None = None,
    min_credit_score: int | None = None,
    min_income: float | None = None,
    min_clv: float | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search customers by segment, lifecycle, credit score, income."""
    return await search_customers(segment, lifecycle_stage, min_credit_score, min_income, min_clv, limit=limit)


@mcp.tool()
async def customer_products(customer_id: str) -> dict[str, Any]:
    """Get products held by a customer."""
    return await get_customer_products(customer_id)


@mcp.tool()
async def customer_transactions(customer_id: str, days: int = 30) -> dict[str, Any]:
    """Get customer transaction summary."""
    return await get_customer_transactions(customer_id, days)


@mcp.tool()
async def update_customer(customer_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update customer profile."""
    return await update_customer_profile(customer_id, updates)


@mcp.tool()
async def add_new_customer(
    customer_id: str,
    name: str,
    date_of_birth: str,
    email: str,
    segment: str,
    income: float,
    credit_score: int,
) -> dict[str, Any]:
    """Add a new customer."""
    return await add_customer(customer_id, name, date_of_birth, email, segment, income, credit_score)


@mcp.tool()
async def customer_segments() -> dict[str, Any]:
    """Get customer distribution by segment."""
    return await get_customer_segments()


@mcp.tool()
async def high_value_customers(min_clv: float = 10000) -> dict[str, Any]:
    """Get high-value customers for targeted recommendations."""
    return await get_high_value_customers(min_clv)


# ══════════════════════════════════════════════════════════════════
#  RECOMMENDATION ENGINE
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_recommendations(customer_id: str, max_recommendations: int = 10, strategy: str = "balanced") -> dict[str, Any]:
    """Generate personalized product recommendations."""
    return await generate_recommendations(customer_id, max_recommendations, strategy)


@mcp.tool()
async def explain_recommendation(customer_id: str, product_id: str) -> dict[str, Any]:
    """Get detailed explanation for a recommendation."""
    return await get_recommendation_explanation(customer_id, product_id)


@mcp.tool()
async def upsell_opportunities(customer_id: str) -> dict[str, Any]:
    """Identify upsell opportunities for existing products."""
    return await get_upsell_opportunities(customer_id)


@mcp.tool()
async def win_back_recommendations(customer_id: str) -> dict[str, Any]:
    """Generate win-back recommendations for at-risk customers."""
    return await get_win_back_recommendations(customer_id)


# ══════════════════════════════════════════════════════════════════
#  OFFER MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def active_offers(product_id: str | None = None, target_segment: str | None = None, offer_type: str | None = None) -> dict[str, Any]:
    """Get active promotional offers."""
    return await get_active_offers(product_id, target_segment, offer_type)


@mcp.tool()
async def offer_details(offer_id: str) -> dict[str, Any]:
    """Get offer details."""
    return await get_offer(offer_id)


@mcp.tool()
async def create_new_offer(
    offer_id: str,
    name: str,
    offer_type: str,
    product_id: str | None,
    description: str,
    target_segments: list[str],
    start_date: str,
    end_date: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a new promotional offer."""
    return await create_offer(offer_id, name, offer_type, product_id, description, target_segments, start_date, end_date, **kwargs)


@mcp.tool()
async def update_offer_details(offer_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update an offer."""
    return await update_offer(offer_id, updates)


@mcp.tool()
async def deactivate_offer_tool(offer_id: str, reason: str) -> dict[str, Any]:
    """Deactivate an offer."""
    return await deactivate_offer(offer_id, reason)


@mcp.tool()
async def redeem_offer_tool(offer_id: str, customer_id: str) -> dict[str, Any]:
    """Record offer redemption."""
    return await redeem_offer(offer_id, customer_id)


@mcp.tool()
async def offer_analytics(offer_id: str | None = None) -> dict[str, Any]:
    """Get offer performance analytics."""
    return await get_offer_analytics(offer_id)


@mcp.tool()
async def personalized_offers(customer_id: str) -> dict[str, Any]:
    """Get offers personalized for a customer."""
    return await get_personalized_offers(customer_id)


# ══════════════════════════════════════════════════════════════════
#  CAMPAIGN MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_new_campaign(
    campaign_id: str,
    name: str,
    campaign_type: str,
    target_segment: str,
    offer_id: str | None,
    channels: list[str],
    start_date: str,
    end_date: str,
    budget: float,
) -> dict[str, Any]:
    """Create a new marketing campaign."""
    return await create_campaign(campaign_id, name, campaign_type, target_segment, offer_id, channels, start_date, end_date, budget)


@mcp.tool()
async def launch_campaign_tool(campaign_id: str) -> dict[str, Any]:
    """Launch a campaign."""
    return await launch_campaign(campaign_id)


@mcp.tool()
async def pause_campaign_tool(campaign_id: str, reason: str) -> dict[str, Any]:
    """Pause a campaign."""
    return await pause_campaign(campaign_id, reason)


@mcp.tool()
async def close_campaign_tool(campaign_id: str) -> dict[str, Any]:
    """Close a campaign."""
    return await close_campaign(campaign_id)


@mcp.tool()
async def campaign_details(campaign_id: str) -> dict[str, Any]:
    """Get campaign details."""
    return await get_campaign(campaign_id)


@mcp.tool()
async def list_campaigns(status: str | None = None) -> dict[str, Any]:
    """Get all campaigns."""
    return await get_campaigns(status)


@mcp.tool()
async def campaign_analytics(campaign_id: str) -> dict[str, Any]:
    """Get campaign performance analytics."""
    return await get_campaign_analytics(campaign_id)


@mcp.tool()
async def record_campaign_impression(campaign_id: str, count: int = 1) -> dict[str, Any]:
    """Record campaign impressions."""
    return await record_impression(campaign_id, count)


@mcp.tool()
async def record_campaign_click(campaign_id: str, count: int = 1) -> dict[str, Any]:
    """Record campaign clicks."""
    return await record_click(campaign_id, count)


@mcp.tool()
async def record_campaign_conversion(campaign_id: str, count: int = 1, revenue: float = 0) -> dict[str, Any]:
    """Record campaign conversions."""
    return await record_conversion(campaign_id, count, revenue)


@mcp.tool()
async def schedule_campaign_outreach(campaign_id: str, customer_ids: list[str], channel: str, message_template: str, scheduled_date: str) -> dict[str, Any]:
    """Schedule outreach for a campaign."""
    return await schedule_outreach(campaign_id, customer_ids, channel, message_template, scheduled_date)


# ══════════════════════════════════════════════════════════════════
#  PRODUCT EMBEDDINGS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def embed_product_tool(product_id: str, name: str, category: str, features: dict[str, Any]) -> dict[str, Any]:
    """Create ML embedding of a product."""
    return await embed_product(product_id, name, category, features)


@mcp.tool()
async def embed_customer_prefs(
    customer_id: str,
    risk_tolerance: str,
    investment_horizon_years: int,
    income_level: str,
    age_group: str,
    existing_products: list[str],
    preferences: dict[str, Any],
) -> dict[str, Any]:
    """Create ML embedding of customer preferences."""
    return await embed_customer_preferences(customer_id, risk_tolerance, investment_horizon_years, income_level, age_group, existing_products, preferences)


@mcp.tool()
async def match_customer_products(customer_id: str, top_k: int = 5) -> dict[str, Any]:
    """Match customer to products using embeddings."""
    return await match_customer_to_products(customer_id, top_k)


@mcp.tool()
async def similar_products(product_id: str, top_k: int = 5) -> dict[str, Any]:
    """Find similar products using embeddings."""
    return await find_similar_products(product_id, top_k)


@mcp.tool()
async def cluster_customer_base(customer_ids: list[str], n_clusters: int = 3) -> dict[str, Any]:
    """Cluster customers based on preferences."""
    return await cluster_customers(customer_ids, n_clusters)


@mcp.tool()
async def embedding_stats() -> dict[str, Any]:
    """Get embedding database statistics."""
    return await get_embedding_stats()


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def send_product_rec(customer_id: str, product_id: str, product_name: str, description: str, channels: list[str] | None = None) -> dict[str, Any]:
    """Send product recommendation notification."""
    return await send_product_recommendation(customer_id, product_id, product_name, description, channels)


@mcp.tool()
async def send_offer(customer_id: str, customer_name: str, offer_id: str, offer_description: str, end_date: str, channels: list[str] | None = None) -> dict[str, Any]:
    """Send promotional offer notification."""
    return await send_offer_notification(customer_id, customer_name, offer_id, offer_description, end_date, channels)


@mcp.tool()
async def send_cross_sell(customer_id: str, customer_name: str, product_name: str, benefit: str, channels: list[str] | None = None) -> dict[str, Any]:
    """Send cross-sell notification."""
    return await send_cross_sell_notification(customer_id, customer_name, product_name, benefit, channels)


@mcp.tool()
async def notification_history(customer_id: str, limit: int = 50) -> dict[str, Any]:
    """Get notification history for a customer."""
    return await get_notification_history(customer_id, limit)


@mcp.tool()
async def notification_stats() -> dict[str, Any]:
    """Get notification statistics."""
    return await get_notification_stats()


# ══════════════════════════════════════════════════════════════════
#  CRM
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def log_customer_interaction(customer_id: str, interaction_type: str, channel: str, summary: str, outcome: str | None = None, next_action: str | None = None) -> dict[str, Any]:
    """Log a customer interaction."""
    return await log_interaction(customer_id, interaction_type, channel, summary, outcome, next_action)


@mcp.tool()
async def customer_interaction_history(customer_id: str, limit: int = 50) -> dict[str, Any]:
    """Get interaction history for a customer."""
    return await get_customer_interactions(customer_id, limit)


@mcp.tool()
async def create_sales_lead(lead_id: str, customer_id: str, product_id: str, source: str, priority: str = "medium") -> dict[str, Any]:
    """Create a sales lead."""
    return await create_lead(lead_id, customer_id, product_id, source, priority)


@mcp.tool()
async def update_sales_lead(lead_id: str, status: str | None = None, priority: str | None = None, notes: str | None = None, assigned_to: str | None = None) -> dict[str, Any]:
    """Update a lead."""
    return await update_lead(lead_id, status, priority, notes, assigned_to)


@mcp.tool()
async def lead_details(lead_id: str) -> dict[str, Any]:
    """Get lead details."""
    return await get_lead(lead_id)


@mcp.tool()
async def list_leads(status: str | None = None, priority: str | None = None) -> dict[str, Any]:
    """Get all leads."""
    return await get_leads(status, priority)


@mcp.tool()
async def convert_sales_lead(lead_id: str, revenue: float = 0) -> dict[str, Any]:
    """Convert a lead to a customer."""
    return await convert_lead(lead_id, revenue)


@mcp.tool()
async def close_sales_lead(lead_id: str, reason: str) -> dict[str, Any]:
    """Close a lead as lost."""
    return await close_lead(lead_id, reason)


@mcp.tool()
async def crm_stats() -> dict[str, Any]:
    """Get CRM statistics."""
    return await get_crm_stats()


@mcp.tool()
async def pending_follow_ups() -> dict[str, Any]:
    """Get leads requiring follow-up."""
    return await get_pending_follow_ups()


if __name__ == "__main__":
    logger.info("Starting Product Recommendation Agent MCP Server...")
    mcp.run()
