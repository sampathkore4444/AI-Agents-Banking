"""
Loan Collections Agent — MCP Server.

Manages delinquent accounts with personalized collection strategies,
payment plan negotiation, and regulatory-compliant communications.

Covers all 3.3 Loan Collections Agent capabilities:
- FDCPA-compliant collection workflows
- Personalized strategy recommendation (embedding-based)
- Payment plan creation and management
- Settlement negotiation
- Hardship assessment and program enrollment
- Compliance checking (FDCPA, TCPA, FCRA, UDAAP)
- Debtor profile embedding and clustering
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.account_management import get_portfolio_summary, lookup_account, lookup_account_by_borrower, update_account_status
from tools.collections_strategy import recommend_strategy
from tools.compliance_checker import check_contact_compliance, check_disclosure_compliance, get_compliance_report, log_collection_action
from tools.debtor_embedding import embed_debtor_profile
from tools.notifications import send_demand_letter, send_notification, send_validation_notice
from tools.phone_calls import get_call_history, get_call_stats, get_scheduled_callbacks, initiate_call, leave_voicemail, record_call_outcome, schedule_callback
from tools.payment_gateway import get_payment_history, process_payment, setup_autopay
from tools.payment_scheduling import check_account_eligibility, create_payment_plan, create_settlement_offer, get_payment_plan, modify_payment_plan, record_payment

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Loan Collections Agent",
    instructions=(
        "Loan Collections Agent for banking. Use these tools to manage "
        "delinquent accounts: look up accounts, recommend strategies, "
        "create payment plans, check compliance, process payments, "
        "and send FDCPA-compliant communications."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the collections knowledge base for FDCPA regulations, strategies, and past resolutions."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  ACCOUNT MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_account(account_id: str) -> dict[str, Any]:
    """Look up a delinquent account by ID."""
    return await lookup_account(account_id)


@mcp.tool()
async def search_account_by_borrower(borrower_id: str) -> dict[str, Any]:
    """Look up all accounts for a borrower."""
    return await lookup_account_by_borrower(borrower_id)


@mcp.tool()
async def get_portfolio(collector_id: str | None = None) -> dict[str, Any]:
    """Get summary of the delinquent portfolio."""
    return await get_portfolio_summary(collector_id)


@mcp.tool()
async def update_account(account_id: str, delinquency_status: str | None = None, collection_stage: str | None = None, assigned_collector: str | None = None, hardship_flag: bool | None = None, hardship_type: str | None = None, payment_plan_active: bool | None = None, notes: str | None = None) -> dict[str, Any]:
    """Update a delinquent account's status."""
    return await update_account_status(account_id, delinquency_status, collection_stage, assigned_collector, hardship_flag, hardship_type, payment_plan_active, notes)


# ══════════════════════════════════════════════════════════════════
#  COLLECTIONS STRATEGY
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def recommend_collection_strategy(account_id: str, borrower_name: str, delinquency_days: int, product_type: str, outstanding_balance: float, monthly_payment: float, has_collateral: bool, has_hardship: bool, previous_contact_outcome: str | None = None) -> dict[str, Any]:
    """Recommend optimal collection strategy based on debtor profile."""
    return await recommend_strategy(account_id, borrower_name, delinquency_days, product_type, outstanding_balance, monthly_payment, has_collateral, has_hardship, previous_contact_outcome)


# ══════════════════════════════════════════════════════════════════
#  PAYMENT SCHEDULING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_plan(account_id: str, plan_type: str, monthly_amount: float, total_months: int, start_date: str | None = None, interest_rate: float | None = None) -> dict[str, Any]:
    """Create a payment plan for a delinquent account."""
    return await create_payment_plan(account_id, plan_type, monthly_amount, total_months, start_date, interest_rate)


@mcp.tool()
async def get_plan(plan_id: str) -> dict[str, Any]:
    """Get details of a payment plan."""
    return await get_payment_plan(plan_id)


@mcp.tool()
async def make_payment(plan_id: str, amount: float, payment_date: str | None = None) -> dict[str, Any]:
    """Record a payment against a payment plan."""
    return await record_payment(plan_id, amount, payment_date)


@mcp.tool()
async def restructure_plan(plan_id: str, new_monthly_amount: float | None = None, new_total_months: int | None = None, reason: str | None = None) -> dict[str, Any]:
    """Modify/restructure an existing payment plan."""
    return await modify_payment_plan(plan_id, new_monthly_amount, new_total_months, reason)


@mcp.tool()
async def offer_settlement(account_id: str, settlement_amount: float, settlement_percentage: float, payment_terms: str, deadline_days: int = 30) -> dict[str, Any]:
    """Create a settlement offer for an account."""
    return await create_settlement_offer(account_id, settlement_amount, settlement_percentage, payment_terms, deadline_days)


@mcp.tool()
async def check_program_eligibility(account_id: str, program_type: str) -> dict[str, Any]:
    """Check if an account is eligible for a specific program (forbearance, modification, settlement, payment_plan)."""
    return await check_account_eligibility(account_id, program_type)


# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def check_compliance(account_id: str, contact_method: str, contact_time: str | None = None, borrower_state: str | None = None, daily_attempts: int = 0, weekly_attempts: int = 0, cease_desist_received: bool = False, attorney_represented: bool = False, validation_notice_sent: bool = False) -> dict[str, Any]:
    """Check if a proposed contact action complies with FDCPA, TCPA, and state laws."""
    return await check_contact_compliance(account_id, contact_method, contact_time, borrower_state, daily_attempts, weekly_attempts, cease_desist_received, attorney_represented, validation_notice_sent)


@mcp.tool()
async def check_disclosure(disclosure_type: str, account_id: str, amount_owed: float | None = None, creditor_name: str | None = None) -> dict[str, Any]:
    """Check compliance of required disclosures (validation_notice, settlement_offer, time_barred_notice, mini_miranda)."""
    return await check_disclosure_compliance(disclosure_type, account_id, amount_owed, creditor_name)


@mcp.tool()
async def log_action(account_id: str, action_type: str, action_details: dict, collector_id: str, outcome: str | None = None) -> dict[str, Any]:
    """Log a collection action for compliance audit trail."""
    return await log_collection_action(account_id, action_type, action_details, collector_id, outcome)


@mcp.tool()
async def compliance_report(account_id: str | None = None) -> dict[str, Any]:
    """Generate a compliance report for an account or full portfolio."""
    return await get_compliance_report(account_id)


# ══════════════════════════════════════════════════════════════════
#  DEBTOR EMBEDDING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def embed_profile(account_id: str, borrower_name: str, delinquency_days: int, outstanding_balance: float, monthly_payment: float, annual_income: float | None = None, debt_to_income: float | None = None, has_collateral: bool = False, collateral_value: float | None = None, employment_years: int | None = None, credit_score: int | None = None, num_dependents: int | None = None, previous_delinquencies: int = 0, account_age_months: int = 0) -> dict[str, Any]:
    """Create ML embedding of debtor profile for clustering and strategy matching."""
    return await embed_debtor_profile(account_id, borrower_name, delinquency_days, outstanding_balance, monthly_payment, annual_income, debt_to_income, has_collateral, collateral_value, employment_years, credit_score, num_dependents, previous_delinquencies, account_age_months)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def notify_borrower(recipient_id: str, template_id: str, channel: str = "email", variables: dict | None = None) -> dict[str, Any]:
    """Send a FDCPA-compliant notification to a borrower."""
    return await send_notification("borrower", recipient_id, channel, template_id, variables, fdcpa_compliant=True)


@mcp.tool()
async def send_validation_not(account_id: str, borrower_name: str, amount_owed: float, creditor_name: str, channel: str = "mail") -> dict[str, Any]:
    """Send FDCPA-required validation notice within 5 days of initial communication."""
    return await send_validation_notice(account_id, borrower_name, amount_owed, creditor_name, channel)


@mcp.tool()
async def send_demand(account_id: str, borrower_name: str, product_type: str, balance: float, days_to_respond: int = 30) -> dict[str, Any]:
    """Send formal demand letter for late-stage collections."""
    return await send_demand_letter(account_id, borrower_name, product_type, balance, days_to_respond)


# ══════════════════════════════════════════════════════════════════
#  PHONE CALLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def start_call(account_id: str, borrower_name: str, phone_number: str, collector_name: str, bank_name: str, collection_stage: str, product_type: str, delinquency_days: int, balance: float, past_due_amount: float, daily_attempts: int = 0) -> dict[str, Any]:
    """Initiate an outbound collection call with FDCPA-compliant scripting."""
    return await initiate_call(account_id, borrower_name, phone_number, collector_name, bank_name, collection_stage, product_type, delinquency_days, balance, past_due_amount, daily_attempts)


@mcp.tool()
async def log_call_outcome(call_id: str, outcome: str, call_duration_seconds: int, notes: str | None = None, borrower_promised_amount: float | None = None, borrower_promised_date: str | None = None, recording_consent: bool = False, new_information: dict | None = None) -> dict[str, Any]:
    """Record the outcome of a collection call."""
    return await record_call_outcome(call_id, outcome, call_duration_seconds, notes, borrower_promised_amount, borrower_promised_date, recording_consent, new_information)


@mcp.tool()
async def schedule_call(account_id: str, borrower_name: str, phone_number: str, callback_date: str, callback_time: str, reason: str, collector_id: str, notes: str | None = None) -> dict[str, Any]:
    """Schedule a follow-up call to a borrower."""
    return await schedule_callback(account_id, borrower_name, phone_number, callback_date, callback_time, reason, collector_id, notes)


@mcp.tool()
async def get_call_log(account_id: str, limit: int = 10) -> dict[str, Any]:
    """Get call history for an account."""
    return await get_call_history(account_id, limit)


@mcp.tool()
async def get_callbacks(collector_id: str | None = None, date: str | None = None) -> dict[str, Any]:
    """Get scheduled callbacks."""
    return await get_scheduled_callbacks(collector_id, date)


@mcp.tool()
async def drop_voicemail(account_id: str, borrower_name: str, collector_name: str, bank_name: str, product_type: str, phone_number: str, collection_stage: str) -> dict[str, Any]:
    """Leave a FDCPA-compliant voicemail."""
    return await leave_voicemail(account_id, borrower_name, collector_name, bank_name, product_type, phone_number, collection_stage)


@mcp.tool()
async def call_stats(collector_id: str | None = None) -> dict[str, Any]:
    """Get call statistics for reporting."""
    return await get_call_stats(collector_id)


# ══════════════════════════════════════════════════════════════════
#  PAYMENTS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def process_collections_payment(account_id: str, amount: float, payment_method: str, payment_type: str = "regular", plan_id: str | None = None) -> dict[str, Any]:
    """Process a payment for a collections account."""
    return await process_payment(account_id, amount, payment_method, payment_type, plan_id)


@mcp.tool()
async def enable_autopay(account_id: str, plan_id: str, payment_method: str, payment_day: int = 1, amount: float | None = None) -> dict[str, Any]:
    """Set up automatic payments for a collections account."""
    return await setup_autopay(account_id, plan_id, payment_method, payment_day, amount)


@mcp.tool()
async def get_payments(account_id: str, limit: int = 10) -> dict[str, Any]:
    """Get payment history for a collections account."""
    return await get_payment_history(account_id, limit)


if __name__ == "__main__":
    logger.info("Starting Loan Collections Agent MCP Server...")
    mcp.run()
