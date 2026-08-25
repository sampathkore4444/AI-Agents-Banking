"""
Standing Order & Bill Payment Agent — MCP Server.

Features:
- Standing order CRUD (create, modify, cancel, pause, resume)
- Biller directory search and verification
- Payment scheduling with calendar integration
- Natural language payment intent parsing
- Payment reminders and notifications
- Customer billing profile
- ML-based payment pattern detection
- RAG-based policy and biller knowledge retrieval
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.standing_order_management import (
    create_standing_order, get_standing_order, update_standing_order,
    cancel_standing_order, pause_standing_order, resume_standing_order,
    list_standing_orders, get_upcoming_payments, get_standing_order_stats,
)
from tools.biller_directory import (
    search_billers, get_biller, verify_biller, add_biller,
    list_billers_by_category, get_biller_categories,
)
from tools.payment_scheduling import (
    get_execution_calendar, calculate_payment_dates, process_scheduled_payment,
    retry_failed_payment, get_payment_history, get_holiday_calendar,
)
from tools.calendar_api import (
    create_payment_reminder, get_reminders, create_calendar_event,
    get_calendar_events, send_payment_notification, get_notification_history,
)
from tools.notifications import (
    send_setup_confirmation, send_modification_notice, send_cancellation_notice,
    send_payment_failed_alert, send_suspension_notice, send_amount_change_alert,
    send_daily_summary, get_notification_log,
)
from tools.customer_profile import (
    get_customer_profile, get_customer_accounts, search_customers,
    get_billing_summary, get_account_balance,
)
from tools.payment_embedding import (
    parse_payment_intent, embed_payment_pattern, match_payment_patterns,
    detect_recurring_pattern,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Standing Order & Bill Payment Agent",
    instructions=(
        "Standing Order & Bill Payment Agent for banking. Use these tools to manage recurring "
        "payments, search billers, schedule payments, understand natural language payment requests, "
        "send reminders, and analyze billing patterns. All actions are logged for audit trail."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the standing order knowledge base for policies, billers, schedules, and playbooks."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  STANDING ORDER MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_order(
    account_id: str,
    customer_name: str,
    payee_name: str,
    payee_account_number: str,
    payee_routing: str,
    amount: float,
    frequency: str,
    start_date: str,
    end_date: str | None = None,
    payment_method: str = "ach_debit",
    description: str | None = None,
    max_amount: float | None = None,
) -> dict[str, Any]:
    """Create a new standing order (recurring payment)."""
    return await create_standing_order(account_id, customer_name, payee_name, payee_account_number, payee_routing, amount, frequency, start_date, end_date, payment_method, description, max_amount)


@mcp.tool()
async def get_order(standing_order_id: str) -> dict[str, Any]:
    """Get standing order details."""
    return await get_standing_order(standing_order_id)


@mcp.tool()
async def update_order(
    standing_order_id: str,
    amount: float | None = None,
    frequency: str | None = None,
    payee_name: str | None = None,
    payee_account_number: str | None = None,
    payee_routing: str | None = None,
    end_date: str | None = None,
    description: str | None = None,
    max_amount: float | None = None,
) -> dict[str, Any]:
    """Update an existing standing order."""
    return await update_standing_order(standing_order_id, amount, frequency, payee_name, payee_account_number, payee_routing, end_date, description, max_amount)


@mcp.tool()
async def cancel_order(standing_order_id: str, reason: str = "customer_request") -> dict[str, Any]:
    """Cancel a standing order."""
    return await cancel_standing_order(standing_order_id, reason)


@mcp.tool()
async def pause_order(standing_order_id: str, reason: str = "customer_request") -> dict[str, Any]:
    """Pause a standing order temporarily."""
    return await pause_standing_order(standing_order_id, reason)


@mcp.tool()
async def resume_order(standing_order_id: str) -> dict[str, Any]:
    """Resume a paused standing order."""
    return await resume_standing_order(standing_order_id)


@mcp.tool()
async def list_orders(
    account_id: str | None = None,
    status: str | None = None,
    payee_name: str | None = None,
) -> dict[str, Any]:
    """List standing orders with optional filters."""
    return await list_standing_orders(account_id, status, payee_name)


@mcp.tool()
async def upcoming_payments(account_id: str, days: int = 30) -> dict[str, Any]:
    """Get standing order payments due within N days."""
    return await get_upcoming_payments(account_id, days)


@mcp.tool()
async def order_statistics(account_id: str | None = None) -> dict[str, Any]:
    """Get standing order statistics."""
    return await get_standing_order_stats(account_id)


# ══════════════════════════════════════════════════════════════════
#  BILLER DIRECTORY
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_biller(query: str, category: str | None = None, payment_method: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Search the biller directory by name or category."""
    return await search_billers(query, category, payment_method, limit)


@mcp.tool()
async def get_biller_details(biller_id: str) -> dict[str, Any]:
    """Get biller details by ID."""
    return await get_biller(biller_id)


@mcp.tool()
async def verify_biller_tool(biller_id: str, account_number: str | None = None, customer_name: str | None = None) -> dict[str, Any]:
    """Verify a biller for a specific customer account."""
    return await verify_biller(biller_id, account_number, customer_name)


@mcp.tool()
async def add_biller_tool(
    name: str,
    category: str,
    sub_category: str | None = None,
    payment_methods: list[str] | None = None,
    typical_amount_min: float = 0,
    typical_amount_max: float = 10000,
    billing_cycle: str = "monthly",
    grace_period_days: int = 15,
) -> dict[str, Any]:
    """Add a new biller to the directory."""
    return await add_biller(name, category, sub_category, payment_methods, typical_amount_min, typical_amount_max, billing_cycle, grace_period_days)


@mcp.tool()
async def biller_categories() -> dict[str, Any]:
    """Get all biller categories with counts."""
    return await get_biller_categories()


@mcp.tool()
async def list_billers(category: str) -> dict[str, Any]:
    """List all billers in a category."""
    return await list_billers_by_category(category)


# ══════════════════════════════════════════════════════════════════
#  PAYMENT SCHEDULING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def execution_calendar(account_id: str, start_date: str | None = None, end_date: str | None = None, days_ahead: int = 30) -> dict[str, Any]:
    """Get a calendar view of upcoming scheduled payments."""
    return await get_execution_calendar(account_id, start_date, end_date, days_ahead)


@mcp.tool()
async def payment_dates(start_date: str, frequency: str, count: int = 12, end_date: str | None = None) -> dict[str, Any]:
    """Calculate future payment dates for a given frequency."""
    return await calculate_payment_dates(start_date, frequency, count, end_date)


@mcp.tool()
async def process_payment(
    standing_order_id: str,
    account_id: str,
    payee_name: str,
    payee_account: str,
    payee_routing: str,
    amount: float,
    payment_method: str = "ach_debit",
    scheduled_date: str | None = None,
) -> dict[str, Any]:
    """Process a scheduled payment."""
    return await process_scheduled_payment(standing_order_id, account_id, payee_name, payee_account, payee_routing, amount, payment_method, scheduled_date)


@mcp.tool()
async def retry_payment(payment_id: str, retry_reason: str = "insufficient_funds") -> dict[str, Any]:
    """Retry a failed payment."""
    return await retry_failed_payment(payment_id, retry_reason)


@mcp.tool()
async def payment_history_tool(account_id: str, days: int = 90, limit: int = 100) -> dict[str, Any]:
    """Get payment execution history."""
    return await get_payment_history(account_id, days, limit)


@mcp.tool()
async def holiday_calendar(year: int | None = None) -> dict[str, Any]:
    """Get Federal Reserve holiday calendar."""
    return await get_holiday_calendar(year)


# ══════════════════════════════════════════════════════════════════
#  CALENDAR & REMINDERS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_reminder(standing_order_id: str, account_id: str, payee_name: str, amount: float, scheduled_date: str, reminder_days: list[int] | None = None) -> dict[str, Any]:
    """Create payment reminders for a standing order."""
    return await create_payment_reminder(standing_order_id, account_id, payee_name, amount, scheduled_date, reminder_days)


@mcp.tool()
async def reminders(account_id: str | None = None, status: str | None = None, upcoming_only: bool = True) -> dict[str, Any]:
    """Get payment reminders."""
    return await get_reminders(account_id, status, upcoming_only)


@mcp.tool()
async def calendar_event(standing_order_id: str, title: str, description: str, event_date: str, event_type: str = "payment") -> dict[str, Any]:
    """Create a calendar event for a payment."""
    return await create_calendar_event(standing_order_id, title, description, event_date, event_type)


@mcp.tool()
async def calendar_events(start_date: str | None = None, end_date: str | None = None, event_type: str | None = None) -> dict[str, Any]:
    """Get calendar events within a date range."""
    return await get_calendar_events(start_date, end_date, event_type)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def notify_setup(standing_order_id: str, account_id: str, customer_name: str, payee_name: str, amount: float, frequency: str, next_execution: str) -> dict[str, Any]:
    """Send confirmation when a standing order is created."""
    return await send_setup_confirmation(standing_order_id, account_id, customer_name, payee_name, amount, frequency, next_execution)


@mcp.tool()
async def notify_modification(standing_order_id: str, account_id: str, customer_name: str, changes: list[str]) -> dict[str, Any]:
    """Send notice when a standing order is modified."""
    return await send_modification_notice(standing_order_id, account_id, customer_name, changes)


@mcp.tool()
async def notify_cancellation(standing_order_id: str, account_id: str, customer_name: str, payee_name: str, reason: str) -> dict[str, Any]:
    """Send notice when a standing order is cancelled."""
    return await send_cancellation_notice(standing_order_id, account_id, customer_name, payee_name, reason)


@mcp.tool()
async def notify_payment_failed(standing_order_id: str, account_id: str, customer_name: str, payee_name: str, amount: float, failure_reason: str, retry_date: str | None = None) -> dict[str, Any]:
    """Send alert when a payment fails."""
    return await send_payment_failed_alert(standing_order_id, account_id, customer_name, payee_name, amount, failure_reason, retry_date)


@mcp.tool()
async def notify_suspension(standing_order_id: str, account_id: str, customer_name: str, payee_name: str, reason: str) -> dict[str, Any]:
    """Send notice when a standing order is suspended."""
    return await send_suspension_notice(standing_order_id, account_id, customer_name, payee_name, reason)


@mcp.tool()
async def notify_amount_change(standing_order_id: str, account_id: str, customer_name: str, payee_name: str, old_amount: float, new_amount: float) -> dict[str, Any]:
    """Send alert when a biller changes the payment amount."""
    return await send_amount_change_alert(standing_order_id, account_id, customer_name, payee_name, old_amount, new_amount)


@mcp.tool()
async def daily_summary_tool(account_id: str, customer_name: str, summary: dict[str, Any]) -> dict[str, Any]:
    """Send daily summary of standing order activity."""
    return await send_daily_summary(account_id, customer_name, summary)


@mcp.tool()
async def notification_log(account_id: str | None = None, notification_type: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get notification log."""
    return await get_notification_log(account_id, notification_type, limit)


# ══════════════════════════════════════════════════════════════════
#  CUSTOMER PROFILE
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def customer_profile(customer_id: str) -> dict[str, Any]:
    """Get full customer profile."""
    return await get_customer_profile(customer_id)


@mcp.tool()
async def customer_accounts(customer_id: str) -> dict[str, Any]:
    """Get accounts for a customer."""
    return await get_customer_accounts(customer_id)


@mcp.tool()
async def search_customer(query: str | None = None, min_balance: float | None = None, has_standing_orders: bool | None = None) -> dict[str, Any]:
    """Search customers."""
    return await search_customers(query, min_balance, has_standing_orders)


@mcp.tool()
async def billing_summary(customer_id: str) -> dict[str, Any]:
    """Get billing summary for a customer."""
    return await get_billing_summary(customer_id)


@mcp.tool()
async def account_balance(account_id: str) -> dict[str, Any]:
    """Get account balance for payment validation."""
    return await get_account_balance(account_id)


# ══════════════════════════════════════════════════════════════════
#  PAYMENT EMBEDDINGS (ML)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def parse_intent(natural_language_input: str) -> dict[str, Any]:
    """Parse natural language into a structured payment intent."""
    return await parse_payment_intent(natural_language_input)


@mcp.tool()
async def embed_pattern(pattern_data: dict) -> dict[str, Any]:
    """Create ML embedding of a payment pattern."""
    return await embed_payment_pattern(pattern_data)


@mcp.tool()
async def match_patterns(payment: dict, threshold: float = 0.8) -> dict[str, Any]:
    """Match a payment against known patterns."""
    return await match_payment_patterns(payment, threshold=threshold)


@mcp.tool()
async def detect_patterns(payments: list[dict], min_occurrences: int = 3) -> dict[str, Any]:
    """Detect recurring payment patterns from history."""
    return await detect_recurring_pattern(payments, min_occurrences)


if __name__ == "__main__":
    logger.info("Starting Standing Order & Bill Payment Agent MCP Server...")
    mcp.run()
