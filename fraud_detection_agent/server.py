"""
Real-Time Transaction Fraud Detection Agent — MCP Server.

Features:
- Real-time transaction analysis and fraud scoring
- Card freeze/unfreeze and replacement
- Velocity checks and rate limiting
- Device fingerprinting and tracking
- Account takeover detection
- ML-based anomaly detection using embeddings
- Case management and investigation workflow
- Fraud alerts and notifications
- RAG-based fraud policy retrieval
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.transaction_monitoring import analyze_transaction, block_transaction, get_fraud_stats, get_transaction, get_transaction_history, unblock_transaction
from tools.card_management import freeze_card, get_card_status, get_cards_by_customer, replace_card, set_transaction_limits, unfreeze_card
from tools.velocity_check import check_velocity, get_velocity_summary, update_velocity_limits
from tools.device_tracking import block_device, check_device, flag_device, get_device_history, register_device
from tools.account_takeover import block_ip, get_login_history, monitor_login, revoke_sessions, update_security_settings
from tools.anomaly_detection import add_fraud_pattern, detect_anomaly, embed_customer_behavior, embed_transaction, get_fraud_patterns
from tools.case_management import add_evidence, create_case, escalate_case, get_case, get_case_stats, get_cases_by_customer, get_open_cases, resolve_case, update_case
from tools.notifications import send_card_blocked_notification, send_compliance_notification, send_fraud_alert, send_login_alert, send_transaction_blocked_notification, get_notification_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Real-Time Transaction Fraud Detection Agent",
    instructions=(
        "Real-Time Transaction Fraud Detection Agent for banking. Use these tools to "
        "detect and prevent fraud: analyze transactions, check velocity, track devices, "
        "detect account takeover, manage cards, investigate cases, and send alerts."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the fraud detection knowledge base for regulations, typologies, and investigation playbooks."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  TRANSACTION MONITORING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def monitor_transaction(
    transaction_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    merchant_id: str,
    merchant_category: str,
    channel: str,
    country: str,
    ip_address: str | None = None,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Analyze a transaction in real-time for fraud indicators."""
    return await analyze_transaction(transaction_id, customer_id, amount, currency, merchant_id, merchant_category, channel, country, ip_address, device_id)


@mcp.tool()
async def get_txn_details(transaction_id: str) -> dict[str, Any]:
    """Get transaction details and fraud analysis results."""
    return await get_transaction(transaction_id)


@mcp.tool()
async def get_txn_history(customer_id: str, hours: int = 24, limit: int = 50) -> dict[str, Any]:
    """Get recent transaction history for a customer."""
    return await get_transaction_history(customer_id, hours, limit)


@mcp.tool()
async def block_txn(transaction_id: str, reason: str) -> dict[str, Any]:
    """Block a transaction."""
    return await block_transaction(transaction_id, reason)


@mcp.tool()
async def unblock_txn(transaction_id: str, reason: str) -> dict[str, Any]:
    """Unblock a transaction."""
    return await unblock_transaction(transaction_id, reason)


@mcp.tool()
async def fraud_statistics(hours: int = 24) -> dict[str, Any]:
    """Get fraud statistics for a time period."""
    return await get_fraud_stats(hours)


# ══════════════════════════════════════════════════════════════════
#  CARD MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def freeze_card_tool(card_id: str, reason: str, fraud_case_id: str | None = None) -> dict[str, Any]:
    """Freeze a card to prevent further fraud."""
    return await freeze_card(card_id, reason, fraud_case_id)


@mcp.tool()
async def unfreeze_card_tool(card_id: str, reason: str, verified_by: str = "fraud_agent") -> dict[str, Any]:
    """Unfreeze a card after verification."""
    return await unfreeze_card(card_id, reason, verified_by)


@mcp.tool()
async def replace_card_tool(card_id: str, reason: str, expedited: bool = True) -> dict[str, Any]:
    """Issue a replacement card after fraud."""
    return await replace_card(card_id, reason, expedited)


@mcp.tool()
async def card_status(card_id: str) -> dict[str, Any]:
    """Get current card status."""
    return await get_card_status(card_id)


@mcp.tool()
async def customer_cards(customer_id: str) -> dict[str, Any]:
    """Get all cards for a customer."""
    return await get_cards_by_customer(customer_id)


@mcp.tool()
async def update_card_limits(
    card_id: str,
    daily_limit: float | None = None,
    per_transaction_limit: float | None = None,
    international_enabled: bool | None = None,
) -> dict[str, Any]:
    """Set transaction limits on a card."""
    return await set_transaction_limits(card_id, daily_limit, per_transaction_limit, international_enabled)


# ══════════════════════════════════════════════════════════════════
#  VELOCITY CHECKS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def check_velocity_tool(customer_id: str, amount: float, transaction_id: str) -> dict[str, Any]:
    """Check transaction velocity against rate limits."""
    return await check_velocity(customer_id, amount, transaction_id)


@mcp.tool()
async def velocity_summary(customer_id: str) -> dict[str, Any]:
    """Get velocity summary for a customer."""
    return await get_velocity_summary(customer_id)


@mcp.tool()
async def update_limits(
    hourly_transactions: int | None = None,
    daily_transactions: int | None = None,
    weekly_transactions: int | None = None,
    hourly_amount: float | None = None,
    daily_amount: float | None = None,
    weekly_amount: float | None = None,
) -> dict[str, Any]:
    """Update velocity limits."""
    return await update_velocity_limits(hourly_transactions, daily_transactions, weekly_transactions, hourly_amount, daily_amount, weekly_amount)


# ══════════════════════════════════════════════════════════════════
#  DEVICE TRACKING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def register_device_tool(
    customer_id: str,
    device_id: str,
    device_type: str,
    os: str,
    browser: str,
    ip_address: str,
    screen_resolution: str | None = None,
    language: str | None = None,
    timezone: str | None = None,
) -> dict[str, Any]:
    """Register a device fingerprint."""
    return await register_device(customer_id, device_id, device_type, os, browser, ip_address, screen_resolution, language, timezone)


@mcp.tool()
async def check_device_tool(customer_id: str, device_id: str, ip_address: str) -> dict[str, Any]:
    """Check device trust and detect anomalies."""
    return await check_device(customer_id, device_id, ip_address)


@mcp.tool()
async def device_history(customer_id: str) -> dict[str, Any]:
    """Get device history for a customer."""
    return await get_device_history(customer_id)


@mcp.tool()
async def flag_device_tool(device_id: str, flag_type: str, reason: str) -> dict[str, Any]:
    """Flag a device as suspicious."""
    return await flag_device(device_id, flag_type, reason)


@mcp.tool()
async def block_device_tool(device_id: str, reason: str) -> dict[str, Any]:
    """Block a device completely."""
    return await block_device(device_id, reason)


# ══════════════════════════════════════════════════════════════════
#  ACCOUNT TAKEOVER
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def monitor_login_tool(
    customer_id: str,
    ip_address: str,
    device_id: str,
    user_agent: str,
    geo_location: dict | None = None,
) -> dict[str, Any]:
    """Monitor login attempt for account takeover indicators."""
    return await monitor_login(customer_id, ip_address, device_id, user_agent, geo_location)


@mcp.tool()
async def login_history(customer_id: str, hours: int = 24, limit: int = 50) -> dict[str, Any]:
    """Get login history for a customer."""
    return await get_login_history(customer_id, hours, limit)


@mcp.tool()
async def revoke_all_sessions(customer_id: str, reason: str) -> dict[str, Any]:
    """Revoke all active sessions for a customer."""
    return await revoke_sessions(customer_id, reason)


@mcp.tool()
async def update_account_security(
    customer_id: str,
    mfa_enabled: bool | None = None,
    trusted_devices: list[str] | None = None,
    login_notifications: bool | None = None,
) -> dict[str, Any]:
    """Update account security settings."""
    return await update_security_settings(customer_id, mfa_enabled, trusted_devices, login_notifications)


@mcp.tool()
async def block_ip_address(ip_address: str, reason: str) -> dict[str, Any]:
    """Block an IP address."""
    return await block_ip(ip_address, reason)


# ══════════════════════════════════════════════════════════════════
#  ANOMALY DETECTION (ML)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def embed_txn(
    transaction_id: str,
    customer_id: str,
    amount: float,
    merchant_category: str,
    channel: str,
    country: str,
    hour: int,
    day_of_week: int,
    is_international: bool,
) -> dict[str, Any]:
    """Create ML embedding of transaction pattern."""
    return await embed_transaction(transaction_id, customer_id, amount, merchant_category, channel, country, hour, day_of_week, is_international)


@mcp.tool()
async def embed_behavior(customer_id: str, transactions_last_30_days: list[dict]) -> dict[str, Any]:
    """Create behavioral embedding for a customer."""
    return await embed_customer_behavior(customer_id, transactions_last_30_days)


@mcp.tool()
async def detect_txn_anomaly(
    transaction_id: str,
    customer_id: str,
    amount: float,
    merchant_category: str,
    channel: str,
    country: str,
    hour: int,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Detect if a transaction is anomalous."""
    return await detect_anomaly(transaction_id, customer_id, amount, merchant_category, channel, country, hour, device_id)


@mcp.tool()
async def add_fraud_pattern_tool(pattern_id: str, description: str, features: dict) -> dict[str, Any]:
    """Add a known fraud pattern to the detection database."""
    return await add_fraud_pattern(pattern_id, description, features)


@mcp.tool()
async def fraud_pattern_list() -> dict[str, Any]:
    """Get all known fraud patterns."""
    return await get_fraud_patterns()


# ══════════════════════════════════════════════════════════════════
#  CASE MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_fraud_case(
    customer_id: str,
    case_type: str,
    description: str,
    priority: str = "medium",
    related_transactions: list[str] | None = None,
    related_cards: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new fraud case."""
    return await create_case(customer_id, case_type, description, priority, related_transactions, related_cards)


@mcp.tool()
async def update_fraud_case(
    case_id: str,
    status: str | None = None,
    stage: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Update a fraud case."""
    return await update_case(case_id, status, stage, priority, assigned_to, notes)


@mcp.tool()
async def resolve_fraud_case(
    case_id: str,
    resolution: str,
    outcome: str,
    amount_lost: float = 0,
    amount_recovered: float = 0,
    notes: str | None = None,
) -> dict[str, Any]:
    """Resolve a fraud case."""
    return await resolve_case(case_id, resolution, outcome, amount_lost, amount_recovered, notes)


@mcp.tool()
async def get_fraud_case(case_id: str) -> dict[str, Any]:
    """Get case details."""
    return await get_case(case_id)


@mcp.tool()
async def customer_fraud_cases(customer_id: str) -> dict[str, Any]:
    """Get all cases for a customer."""
    return await get_cases_by_customer(customer_id)


@mcp.tool()
async def open_fraud_cases(priority: str | None = None) -> dict[str, Any]:
    """Get all open cases."""
    return await get_open_cases(priority)


@mcp.tool()
async def add_case_evidence(case_id: str, evidence_type: str, description: str, data: dict | None = None) -> dict[str, Any]:
    """Add evidence to a case."""
    return await add_evidence(case_id, evidence_type, description, data)


@mcp.tool()
async def escalate_fraud_case(case_id: str, escalation_reason: str, escalate_to: str = "senior_investigator") -> dict[str, Any]:
    """Escalate a case to higher authority."""
    return await escalate_case(case_id, escalation_reason, escalate_to)


@mcp.tool()
async def fraud_case_stats() -> dict[str, Any]:
    """Get overall case statistics."""
    return await get_case_stats()


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def alert_customer_fraud(customer_id: str, transaction_id: str, amount: float, merchant: str, channels: list[str] | None = None) -> dict[str, Any]:
    """Send fraud alert to customer."""
    return await send_fraud_alert(customer_id, transaction_id, amount, merchant, channels)


@mcp.tool()
async def alert_card_blocked(customer_id: str, card_last_four: str, reason: str) -> dict[str, Any]:
    """Notify customer that their card has been blocked."""
    return await send_card_blocked_notification(customer_id, card_last_four, reason)


@mcp.tool()
async def alert_txn_blocked(customer_id: str, transaction_id: str, amount: float, merchant: str) -> dict[str, Any]:
    """Notify customer that a transaction was blocked."""
    return await send_transaction_blocked_notification(customer_id, transaction_id, amount, merchant)


@mcp.tool()
async def alert_new_login(customer_id: str, location: str, device: str) -> dict[str, Any]:
    """Notify customer of new login."""
    return await send_login_alert(customer_id, location, device)


@mcp.tool()
async def notification_history(customer_id: str, limit: int = 50) -> dict[str, Any]:
    """Get notification history for a customer."""
    return await get_notification_history(customer_id, limit)


@mcp.tool()
async def compliance_alert(case_id: str, notification_type: str, details: str) -> dict[str, Any]:
    """Send internal compliance notification."""
    return await send_compliance_notification(case_id, notification_type, details)


if __name__ == "__main__":
    logger.info("Starting Real-Time Transaction Fraud Detection Agent MCP Server...")
    mcp.run()
