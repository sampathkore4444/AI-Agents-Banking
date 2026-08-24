"""
Lead Qualification Agent — MCP Server.

Features:
- Lead management and pipeline tracking
- Multi-model lead scoring (BANT, CHAMP, MEDDIC)
- Conversation intent analysis
- Calendar booking for consultations
- Sales playbook execution
- CRM integration
- Automated notifications and follow-ups
- RAG-based qualification knowledge retrieval
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.lead_management import close_lead, convert_lead, create_lead, get_lead, get_lead_pipeline, get_overdue_follow_ups, search_leads, update_lead
from tools.lead_scoring import get_scoring_model, score_lead, score_leads_batch, update_scoring_weights
from tools.qualification_criteria import evaluate_lead, get_frameworks, get_qualification_checklist
from tools.conversation_analysis import analyze_conversation, get_conversation_history, get_intent_keywords
from tools.calendar_booking import book_appointment, cancel_appointment, get_advisors, get_appointments, get_available_slots, reschedule_appointment
from tools.notifications import get_notification_history, get_templates, send_appointment_reminder, send_follow_up, send_notification, send_qualification_complete, send_welcome
from tools.crm import create_account, get_account, get_activities, get_pipeline, log_activity, search_accounts, update_account
from tools.sales_playbooks import get_conversation_starters, get_objection_handling, get_playbook, get_all_playbooks

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Lead Qualification Agent",
    instructions=(
        "Lead Qualification Agent for banking. Use these tools to qualify inbound leads: "
        "score intent, evaluate against frameworks (BANT/CHAMP/MEDDIC), "
        "book consultations, execute sales playbooks, and track conversions."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the lead qualification knowledge base."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  LEAD MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_new_lead(
    lead_id: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    source: str,
    product_interest: str,
    demographics: dict | None = None,
    behavior: dict | None = None,
) -> dict[str, Any]:
    """Create a new lead."""
    return await create_lead(lead_id, first_name, last_name, email, phone, source, product_interest, demographics, behavior)


@mcp.tool()
async def lead_details(lead_id: str) -> dict[str, Any]:
    """Get lead details."""
    return await get_lead(lead_id)


@mcp.tool()
async def update_lead_status(
    lead_id: str,
    status: str | None = None,
    tier: str | None = None,
    score: int | None = None,
    assigned_to: str | None = None,
    next_follow_up: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Update a lead."""
    return await update_lead(lead_id, status, tier, score, assigned_to, next_follow_up, notes)


@mcp.tool()
async def search_leads_tool(
    status: str | None = None,
    tier: str | None = None,
    source: str | None = None,
    product_interest: str | None = None,
    min_score: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search leads by criteria."""
    return await search_leads(status, tier, source, product_interest, min_score, limit=limit)


@mcp.tool()
async def convert_lead_to_customer(lead_id: str, revenue: float = 0) -> dict[str, Any]:
    """Convert a lead to a customer."""
    return await convert_lead(lead_id, revenue)


@mcp.tool()
async def close_lost_lead(lead_id: str, reason: str) -> dict[str, Any]:
    """Close a lead as lost."""
    return await close_lead(lead_id, reason)


@mcp.tool()
async def lead_pipeline() -> dict[str, Any]:
    """Get lead pipeline summary."""
    return await get_lead_pipeline()


@mcp.tool()
async def overdue_follow_ups() -> dict[str, Any]:
    """Get leads with overdue follow-ups."""
    return await get_overdue_follow_ups()


# ══════════════════════════════════════════════════════════════════
#  LEAD SCORING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def score_lead_tool(lead: dict) -> dict[str, Any]:
    """Score a lead based on demographic, behavioral, and intent signals."""
    return await score_lead(lead)


@mcp.tool()
async def score_leads_batch_tool(leads: list[dict]) -> dict[str, Any]:
    """Score multiple leads at once."""
    return await score_leads_batch(leads)


@mcp.tool()
async def scoring_model() -> dict[str, Any]:
    """Get the current scoring model configuration."""
    return await get_scoring_model()


@mcp.tool()
async def update_scoring_weights_tool(
    demographic: float | None = None,
    behavioral: float | None = None,
    intent: float | None = None,
) -> dict[str, Any]:
    """Update scoring weights."""
    return await update_scoring_weights(demographic, behavioral, intent)


# ══════════════════════════════════════════════════════════════════
#  QUALIFICATION CRITERIA
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def evaluate_lead_qualification(lead: dict, framework: str = "BANT") -> dict[str, Any]:
    """Evaluate a lead against a qualification framework."""
    return await evaluate_lead(lead, framework)


@mcp.tool()
async def qualification_checklist(product_interest: str) -> dict[str, Any]:
    """Get qualification checklist for a product."""
    return await get_qualification_checklist(product_interest)


@mcp.tool()
async def qualification_frameworks() -> dict[str, Any]:
    """Get all available qualification frameworks."""
    return await get_frameworks()


# ══════════════════════════════════════════════════════════════════
#  CONVERSATION ANALYSIS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def analyze_lead_conversation(lead_id: str, messages: list[dict], channel: str) -> dict[str, Any]:
    """Analyze a conversation for intent and qualification signals."""
    return await analyze_conversation(lead_id, messages, channel)


@mcp.tool()
async def conversation_history(lead_id: str) -> dict[str, Any]:
    """Get conversation history for a lead."""
    return await get_conversation_history(lead_id)


@mcp.tool()
async def intent_keywords() -> dict[str, Any]:
    """Get all intent signal keywords."""
    return await get_intent_keywords()


# ══════════════════════════════════════════════════════════════════
#  CALENDAR BOOKING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def book_consultation(
    lead_id: str,
    advisor_id: str | None,
    product_interest: str,
    preferred_date: str,
    preferred_time: str,
    meeting_type: str = "consultation",
    channel: str = "phone",
) -> dict[str, Any]:
    """Book a consultation with an advisor."""
    return await book_appointment(lead_id, advisor_id, product_interest, preferred_date, preferred_time, meeting_type, channel)


@mcp.tool()
async def available_slots(advisor_id: str | None = None, date: str | None = None) -> dict[str, Any]:
    """Get available appointment slots."""
    return await get_available_slots(advisor_id, date)


@mcp.tool()
async def cancel_appointment_tool(appointment_id: str, reason: str) -> dict[str, Any]:
    """Cancel an appointment."""
    return await cancel_appointment(appointment_id, reason)


@mcp.tool()
async def reschedule_appointment_tool(appointment_id: str, new_date: str, new_time: str) -> dict[str, Any]:
    """Reschedule an appointment."""
    return await reschedule_appointment(appointment_id, new_date, new_time)


@mcp.tool()
async def list_appointments(advisor_id: str | None = None, date: str | None = None, status: str | None = None) -> dict[str, Any]:
    """Get appointments."""
    return await get_appointments(advisor_id, date, status)


@mcp.tool()
async def list_advisors() -> dict[str, Any]:
    """Get available advisors."""
    return await get_advisors()


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def send_lead_notification(lead_id: str, template_id: str, channels: list[str], variables: dict | None = None) -> dict[str, Any]:
    """Send a notification to a lead."""
    return await send_notification(lead_id, template_id, channels, variables)


@mcp.tool()
async def send_welcome_email(lead_id: str, name: str, product: str) -> dict[str, Any]:
    """Send welcome notification."""
    return await send_welcome(lead_id, name, product)


@mcp.tool()
async def send_follow_up_email(lead_id: str, name: str, product: str) -> dict[str, Any]:
    """Send follow-up notification."""
    return await send_follow_up(lead_id, name, product)


@mcp.tool()
async def send_qualified_email(lead_id: str, name: str, product: str) -> dict[str, Any]:
    """Send qualification complete notification."""
    return await send_qualification_complete(lead_id, name, product)


@mcp.tool()
async def send_reminder(lead_id: str, name: str, advisor: str, date: str, time: str) -> dict[str, Any]:
    """Send appointment reminder."""
    return await send_appointment_reminder(lead_id, name, advisor, date, time)


@mcp.tool()
async def lead_notification_history(lead_id: str) -> dict[str, Any]:
    """Get notification history for a lead."""
    return await get_notification_history(lead_id)


@mcp.tool()
async def notification_templates() -> dict[str, Any]:
    """Get all notification templates."""
    return await get_templates()


# ══════════════════════════════════════════════════════════════════
#  CRM
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_crm_account(account_id: str, name: str, account_type: str, industry: str | None = None) -> dict[str, Any]:
    """Create a CRM account."""
    return await create_account(account_id, name, account_type, industry)


@mcp.tool()
async def crm_account_details(account_id: str) -> dict[str, Any]:
    """Get CRM account details."""
    return await get_account(account_id)


@mcp.tool()
async def update_crm_account(account_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update a CRM account."""
    return await update_account(account_id, updates)


@mcp.tool()
async def log_crm_activity(who_id: str, activity_type: str, subject: str, description: str, what_id: str | None = None) -> dict[str, Any]:
    """Log a CRM activity."""
    return await log_activity(who_id, what_id, activity_type, subject, description)


@mcp.tool()
async def crm_activities(who_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get CRM activities."""
    return await get_activities(who_id=who_id, limit=limit)


@mcp.tool()
async def crm_pipeline() -> dict[str, Any]:
    """Get sales pipeline summary."""
    return await get_pipeline()


@mcp.tool()
async def crm_search_accounts(account_type: str | None = None, industry: str | None = None) -> dict[str, Any]:
    """Search CRM accounts."""
    return await search_accounts(account_type, industry)


# ══════════════════════════════════════════════════════════════════
#  SALES PLAYBOOKS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_sales_playbook(product_interest: str, tier: str) -> dict[str, Any]:
    """Get the appropriate playbook for a lead."""
    return await get_playbook(product_interest, tier)


@mcp.tool()
async def all_playbooks() -> dict[str, Any]:
    """Get all available playbooks."""
    return await get_all_playbooks()


@mcp.tool()
async def handle_objection(product_interest: str, objection: str) -> dict[str, Any]:
    """Get objection handling response."""
    return await get_objection_handling(product_interest, objection)


@mcp.tool()
async def conversation_starters(product_interest: str) -> dict[str, Any]:
    """Get conversation starters for a product."""
    return await get_conversation_starters(product_interest)


if __name__ == "__main__":
    logger.info("Starting Lead Qualification Agent MCP Server...")
    mcp.run()
