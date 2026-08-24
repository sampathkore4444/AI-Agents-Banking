"""
Customer Service & Support Agent — MCP Server.

Covers all 5 use cases from BANKING_USE_CASES.md:
1.1 Intelligent Banking FAQ Agent
1.2 Account Information Agent
1.3 Dispute Resolution Agent
1.4 Multilingual Banking Support Agent
1.5 Complaint Management Agent
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.account_info import get_account_balance, get_account_statements, get_transaction_history
from tools.complaint_management import get_complaint, get_complaint_categories, log_complaint, update_complaint
from tools.dispute_management import file_dispute, get_dispute_status, get_dispute_types, update_dispute
from tools.escalation import create_support_ticket, escalate_to_human, get_available_agents
from tools.notifications import send_notification
from tools.translation import detect_language, get_supported_languages, translate_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Customer Service & Support Agent",
    instructions=(
        "Customer Service & Support Agent for banking. Use these tools to help customers "
        "with account inquiries, disputes, complaints, and general banking questions. "
        "Supports multilingual conversations and can escalate to human agents."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  1.1 INTELLIGENT BANKING FAQ
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_knowledge_base(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search banking FAQ, product info, and policies using RAG."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  1.2 ACCOUNT INFORMATION
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_balance(customer_id: str, account_number: str | None = None) -> dict[str, Any]:
    """Get current account balance and status."""
    return await get_account_balance(customer_id, account_number)


@mcp.tool()
async def get_transactions(customer_id: str, account_number: str | None = None, days: int = 30, category_filter: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Get recent transactions with optional filtering by category."""
    return await get_transaction_history(customer_id, account_number, days, category_filter, limit)


@mcp.tool()
async def get_statements(customer_id: str, months: int = 6) -> dict[str, Any]:
    """Get available account statements."""
    return await get_account_statements(customer_id, months)


# ══════════════════════════════════════════════════════════════════
#  1.3 DISPUTE RESOLUTION
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def file_new_dispute(customer_id: str, account_number: str, transaction_date: str, transaction_amount: float, dispute_type: str, description: str, merchant_name: str | None = None) -> dict[str, Any]:
    """File a new dispute for an unauthorized or incorrect transaction."""
    return await file_dispute(customer_id, account_number, transaction_date, transaction_amount, dispute_type, description, merchant_name)


@mcp.tool()
async def check_dispute_status(dispute_id: str) -> dict[str, Any]:
    """Get current status of a dispute."""
    return await get_dispute_status(dispute_id)


@mcp.tool()
async def update_dispute_status(dispute_id: str, status: str | None = None, notes: str | None = None, resolution: str | None = None) -> dict[str, Any]:
    """Update dispute status or add notes."""
    return await update_dispute(dispute_id, status, notes, resolution)


@mcp.tool()
async def get_dispute_types_list() -> dict[str, Any]:
    """Get available dispute types and descriptions."""
    return await get_dispute_types()


# ══════════════════════════════════════════════════════════════════
#  1.4 MULTILINGUAL SUPPORT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def detect_language_tool(text: str) -> dict[str, Any]:
    """Detect the language of customer input."""
    return await detect_language(text)


@mcp.tool()
async def translate(text: str, source_language: str, target_language: str) -> dict[str, Any]:
    """Translate text between languages."""
    return await translate_text(text, source_language, target_language)


@mcp.tool()
async def get_languages() -> dict[str, Any]:
    """Get list of supported languages."""
    return await get_supported_languages()


# ══════════════════════════════════════════════════════════════════
#  1.5 COMPLAINT MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def log_new_complaint(customer_id: str, description: str, channel: str = "chat", category_hint: str | None = None) -> dict[str, Any]:
    """Log a new customer complaint and auto-categorize."""
    return await log_complaint(customer_id, description, channel, category_hint)


@mcp.tool()
async def check_complaint(complaint_id: str) -> dict[str, Any]:
    """Get complaint details."""
    return await get_complaint(complaint_id)


@mcp.tool()
async def update_complaint_status(complaint_id: str, status: str | None = None, assigned_to: str | None = None, resolution: str | None = None, notes: str | None = None) -> dict[str, Any]:
    """Update complaint status or assignment."""
    return await update_complaint(complaint_id, status, assigned_to, resolution, notes)


@mcp.tool()
async def get_complaint_types() -> dict[str, Any]:
    """Get available complaint categories."""
    return await get_complaint_categories()


# ══════════════════════════════════════════════════════════════════
#  ESCALATION & NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def escalate_to_agent(customer_id: str, reason: str, channel: str = "chat", priority: str = "medium", context_summary: str | None = None, customer_sentiment: str = "neutral") -> dict[str, Any]:
    """Escalate conversation to a human agent."""
    return await escalate_to_human(customer_id, reason, channel, priority, context_summary, customer_sentiment)


@mcp.tool()
async def create_ticket(customer_id: str, subject: str, description: str, category: str, priority: str = "medium") -> dict[str, Any]:
    """Create a support ticket for follow-up."""
    return await create_support_ticket(customer_id, subject, description, category, priority)


@mcp.tool()
async def check_agent_availability(channel: str = "chat") -> dict[str, Any]:
    """Check available human agents for escalation."""
    return await get_available_agents(channel)


@mcp.tool()
async def notify(recipient_id: str, template_id: str, channel: str = "email", variables: dict | None = None) -> dict[str, Any]:
    """Send a notification to a customer."""
    return await send_notification(recipient_id, template_id, channel, variables)


if __name__ == "__main__":
    logger.info("Starting Customer Service & Support Agent MCP Server...")
    mcp.run()
