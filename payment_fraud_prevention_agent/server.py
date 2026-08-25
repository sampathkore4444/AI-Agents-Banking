"""
Payment Fraud Prevention Agent — MCP Server.

Features:
- Real-time payment validation (wire, ACH, check, RTP)
- Beneficiary verification
- Sanctions screening (OFAC, EU, UN)
- Velocity checks across all channels
- ML-based payment pattern analysis
- Case management and investigation workflow
- Fraud alerts and notifications
- RAG-based payment fraud policy retrieval
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.payment_validation import validate_payment, get_payment, get_payment_history, block_payment, approve_payment, get_fraud_alerts, get_payment_stats
from tools.beneficiary_verification import verify_beneficiary, add_known_payee, get_known_payees, remove_known_payee, get_beneficiary_risk_profile
from tools.sanctions_screening import screen_payment_parties, get_screening_history, get_sanctions_lists_info
from tools.velocity_check import check_payment_velocity, get_velocity_summary, update_velocity_limits
from tools.payment_embedding import embed_payment, build_customer_payment_profile, detect_payment_anomaly, add_fraud_pattern, match_fraud_pattern, get_fraud_patterns
from tools.notifications import send_payment_blocked_alert, send_payment_review_notification, send_fraud_confirmation, send_operations_alert, get_notification_history
from tools.case_management import create_fraud_case, update_case, add_evidence, escalate_case, resolve_case, get_case, get_cases_by_account, get_open_cases, get_case_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Payment Fraud Prevention Agent",
    instructions=(
        "Payment Fraud Prevention Agent for banking. Use these tools to validate outgoing payments, "
        "verify beneficiaries, screen against sanctions, check velocity, detect anomalies, "
        "and manage fraud investigation cases. All actions are logged for audit trail."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the payment fraud knowledge base for policies, patterns, and investigation playbooks."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  PAYMENT VALIDATION
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def validate_payment_tool(
    payment_id: str,
    payer_account_id: str,
    payer_name: str,
    payee_name: str,
    payee_account_id: str | None,
    payee_bank_routing: str,
    amount: float,
    currency: str,
    payment_type: str,
    channel: str,
    originator_ip: str | None = None,
    device_id: str | None = None,
    description: str | None = None,
    purpose_of_payment: str | None = None,
    is_international: bool = False,
    beneficiary_country: str | None = None,
) -> dict[str, Any]:
    """Validate a payment in real-time for fraud indicators."""
    return await validate_payment(payment_id, payer_account_id, payer_name, payee_name, payee_account_id, payee_bank_routing, amount, currency, payment_type, channel, originator_ip, device_id, description, purpose_of_payment, is_international, beneficiary_country)


@mcp.tool()
async def get_payment_details(payment_id: str) -> dict[str, Any]:
    """Get payment details and fraud analysis."""
    return await get_payment(payment_id)


@mcp.tool()
async def get_payment_history_tool(account_id: str, days: int = 90, limit: int = 100) -> dict[str, Any]:
    """Get payment history for fraud analysis."""
    return await get_payment_history(account_id, days, limit)


@mcp.tool()
async def block_payment_tool(payment_id: str, reason: str) -> dict[str, Any]:
    """Block a suspicious payment."""
    return await block_payment(payment_id, reason)


@mcp.tool()
async def approve_payment_tool(payment_id: str, approved_by: str, notes: str | None = None) -> dict[str, Any]:
    """Approve a payment that was held for review."""
    return await approve_payment(payment_id, approved_by, notes)


@mcp.tool()
async def fraud_alerts(status: str = "open", limit: int = 50) -> dict[str, Any]:
    """Get payment fraud alerts filtered by status."""
    return await get_fraud_alerts(status, limit)


@mcp.tool()
async def payment_statistics(days: int = 30) -> dict[str, Any]:
    """Get payment fraud monitoring statistics."""
    return await get_payment_stats(days)


# ══════════════════════════════════════════════════════════════════
#  BENEFICIARY VERIFICATION
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def verify_beneficiary_tool(
    account_id: str,
    payee_name: str,
    payee_account_number: str,
    payee_routing_number: str,
    payee_bank_name: str | None = None,
    payee_country: str | None = None,
    payment_amount: float = 0.0,
    payment_type: str = "wire",
) -> dict[str, Any]:
    """Verify a beneficiary against known payees and risk indicators."""
    return await verify_beneficiary(account_id, payee_name, payee_account_number, payee_routing_number, payee_bank_name, payee_country, payment_amount, payment_type)


@mcp.tool()
async def add_payee(
    account_id: str,
    name: str,
    account_number: str,
    routing_number: str,
    bank_name: str | None = None,
    payee_type: str = "individual",
    avg_payment_amount: float = 0.0,
    category: str = "general",
) -> dict[str, Any]:
    """Add a known payee to an account's payee database."""
    return await add_known_payee(account_id, name, account_number, routing_number, bank_name, payee_type, avg_payment_amount, category)


@mcp.tool()
async def list_payees(account_id: str) -> dict[str, Any]:
    """Get known payees for an account."""
    return await get_known_payees(account_id)


@mcp.tool()
async def remove_payee(account_id: str, payee_id: str) -> dict[str, Any]:
    """Remove a known payee."""
    return await remove_known_payee(account_id, payee_id)


@mcp.tool()
async def beneficiary_risk(payee_account_number: str, payee_routing_number: str) -> dict[str, Any]:
    """Get risk profile for a beneficiary."""
    return await get_beneficiary_risk_profile(payee_account_number, payee_routing_number)


# ══════════════════════════════════════════════════════════════════
#  SANCTIONS SCREENING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def screen_parties(
    payment_id: str,
    originator_name: str,
    beneficiary_name: str,
    originator_account: str | None = None,
    beneficiary_account: str | None = None,
    beneficiary_bank_country: str | None = None,
    amount: float = 0.0,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Screen all parties in a payment against sanctions lists."""
    return await screen_payment_parties(payment_id, originator_name, beneficiary_name, originator_account, beneficiary_account, beneficiary_bank_country, amount, threshold)


@mcp.tool()
async def sanctions_history(limit: int = 50) -> dict[str, Any]:
    """Get sanctions screening history."""
    return await get_screening_history(limit)


@mcp.tool()
async def sanctions_lists() -> dict[str, Any]:
    """Get information about loaded sanctions lists."""
    return await get_sanctions_lists_info()


# ══════════════════════════════════════════════════════════════════
#  VELOCITY CHECKS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def check_velocity(account_id: str, amount: float, payment_type: str, payment_id: str) -> dict[str, Any]:
    """Check payment velocity against configured limits."""
    return await check_payment_velocity(account_id, amount, payment_type, payment_id)


@mcp.tool()
async def velocity_summary(account_id: str) -> dict[str, Any]:
    """Get current velocity summary for an account."""
    return await get_velocity_summary(account_id)


@mcp.tool()
async def update_limits(
    hourly_payments: int | None = None,
    daily_wires: int | None = None,
    daily_wire_amount: float | None = None,
    daily_ach: int | None = None,
    daily_ach_amount: float | None = None,
) -> dict[str, Any]:
    """Update velocity limits (admin function)."""
    return await update_velocity_limits(hourly_payments, daily_wires, daily_wire_amount, daily_ach, daily_ach_amount)


# ══════════════════════════════════════════════════════════════════
#  PAYMENT EMBEDDINGS (ML)
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def embed_payment_tool(payment: dict) -> dict[str, Any]:
    """Create ML embedding of a payment pattern."""
    return await embed_payment(payment)


@mcp.tool()
async def build_profile(customer_id: str, payments: list[dict]) -> dict[str, Any]:
    """Build a payment behavior profile from historical payments."""
    return await build_customer_payment_profile(customer_id, payments)


@mcp.tool()
async def detect_anomaly(payment_id: str, customer_id: str, payment: dict) -> dict[str, Any]:
    """Detect if a payment is anomalous compared to customer profile."""
    return await detect_payment_anomaly(payment_id, customer_id, payment)


@mcp.tool()
async def add_pattern(pattern_id: str, description: str, payment_features: dict) -> dict[str, Any]:
    """Add a known fraud pattern to the detection database."""
    return await add_fraud_pattern(pattern_id, description, payment_features)


@mcp.tool()
async def match_pattern(payment: dict, threshold: float = 0.8) -> dict[str, Any]:
    """Match a payment against known fraud patterns."""
    return await match_fraud_pattern(payment, threshold)


@mcp.tool()
async def fraud_pattern_list() -> dict[str, Any]:
    """Get all known fraud patterns."""
    return await get_fraud_patterns()


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def alert_payment_blocked(payment_id: str, payer_account_id: str, payer_name: str, amount: float, payee_name: str, reason: str, channels: list[str] | None = None) -> dict[str, Any]:
    """Send alert when payment is blocked."""
    return await send_payment_blocked_alert(payment_id, payer_account_id, payer_name, amount, payee_name, reason, channels)


@mcp.tool()
async def alert_payment_review(payment_id: str, payer_account_id: str, amount: float, payee_name: str, risk_score: float, red_flags: list[str]) -> dict[str, Any]:
    """Send notification when payment is held for review."""
    return await send_payment_review_notification(payment_id, payer_account_id, amount, payee_name, risk_score, red_flags)


@mcp.tool()
async def fraud_confirmation(payment_id: str, payer_account_id: str, is_fraud: bool, action_taken: str) -> dict[str, Any]:
    """Send confirmation after fraud investigation."""
    return await send_fraud_confirmation(payment_id, payer_account_id, is_fraud, action_taken)


@mcp.tool()
async def ops_alert(payment_id: str, alert_type: str, message: str, priority: str = "high") -> dict[str, Any]:
    """Send internal operations alert."""
    return await send_operations_alert(payment_id, alert_type, message, priority)


@mcp.tool()
async def notification_history(account_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get notification history."""
    return await get_notification_history(account_id, limit)


# ══════════════════════════════════════════════════════════════════
#  CASE MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_case(
    account_id: str,
    customer_name: str,
    case_type: str,
    description: str,
    priority: str = "medium",
    related_payments: list[str] | None = None,
    related_alerts: list[str] | None = None,
    estimated_loss: float = 0.0,
) -> dict[str, Any]:
    """Create a payment fraud case."""
    return await create_fraud_case(account_id, customer_name, case_type, description, priority, related_payments, related_alerts, estimated_loss)


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
async def add_case_evidence(case_id: str, evidence_type: str, description: str, data: dict | None = None) -> dict[str, Any]:
    """Add evidence to a fraud case."""
    return await add_evidence(case_id, evidence_type, description, data)


@mcp.tool()
async def escalate_fraud_case(case_id: str, escalation_reason: str, escalate_to: str = "senior_fraud_analyst") -> dict[str, Any]:
    """Escalate a fraud case."""
    return await escalate_case(case_id, escalation_reason, escalate_to)


@mcp.tool()
async def resolve_fraud_case(case_id: str, resolution: str, outcome: str, amount_recovered: float = 0.0, notes: str | None = None) -> dict[str, Any]:
    """Resolve a fraud case."""
    return await resolve_case(case_id, resolution, outcome, amount_recovered, notes)


@mcp.tool()
async def get_fraud_case(case_id: str) -> dict[str, Any]:
    """Get fraud case details."""
    return await get_case(case_id)


@mcp.tool()
async def account_cases(account_id: str) -> dict[str, Any]:
    """Get all fraud cases for an account."""
    return await get_cases_by_account(account_id)


@mcp.tool()
async def open_cases(priority: str | None = None) -> dict[str, Any]:
    """Get all open fraud cases."""
    return await get_open_cases(priority)


@mcp.tool()
async def case_statistics() -> dict[str, Any]:
    """Get fraud case statistics."""
    return await get_case_stats()


if __name__ == "__main__":
    logger.info("Starting Payment Fraud Prevention Agent MCP Server...")
    mcp.run()
