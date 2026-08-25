"""
Anti-Money Laundering (AML) Alert Agent — MCP Server.

Features:
- Transaction monitoring for AML red flags
- Structuring detection and aggregation analysis
- Sanctions screening (OFAC, EU, UN)
- PEP identification and risk assessment
- SAR creation, filing, and continuing activity management
- CTR filing and exemption management
- Beneficial ownership identification and verification
- AML investigation case management
- Compliance notifications
- RAG-based AML regulation retrieval
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.transaction_monitoring import monitor_transaction, get_transaction, get_transaction_history, block_transaction, get_structuring_analysis, get_aml_alerts, get_aml_stats
from tools.sanctions_screening import screen_name, screen_entity, screen_vessel, screen_transaction, get_screening_history, get_sanctions_lists_info
from tools.pep_screening import screen_for_pep, get_pep_profile, assess_pep_risk, get_rca_links, get_pep_screening_history
from tools.sar_management import create_sar, update_sar, file_sar, create_continuing_sar, get_sar, get_sars_by_status, get_sar_stats
from tools.ctr_management import file_ctr, check_aggregation, create_exemption, get_exemptions, revoke_exemption, get_ctr_stats
from tools.beneficial_ownership import identify_beneficial_owners, verify_beneficial_owner, trace_ultimate_beneficial_owner, update_beneficial_ownership, get_entity_owners, get_pending_verifications
from tools.case_management import create_case, update_case, add_evidence, escalate_case, resolve_case, get_case, get_cases_by_customer, get_open_cases, get_escalated_cases, get_case_stats
from tools.notifications import send_aml_alert, send_sar_filing_confirmation, send_ctr_filing_confirmation, send_escalation_notification, send_deadline_reminder, send_sar_continuing_reminder, get_notification_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Anti-Money Laundering (AML) Alert Agent",
    instructions=(
        "AML Alert Agent for banking. Use these tools to monitor transactions for AML red flags, "
        "screen against sanctions and PEP lists, file SARs and CTRs, manage beneficial ownership, "
        "and handle AML investigation cases. All actions are logged for audit trail."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the AML knowledge base for regulations, typologies, SAR guidelines, and compliance rules."""
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
async def monitor_txn(
    transaction_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    transaction_type: str,
    channel: str,
    country: str,
    counterparty_name: str | None = None,
    counterparty_country: str | None = None,
    account_id: str | None = None,
) -> dict[str, Any]:
    """Monitor a transaction for AML red flags including structuring, layering, and anomalies."""
    return await monitor_transaction(transaction_id, customer_id, amount, currency, transaction_type, channel, country, counterparty_name, counterparty_country, account_id)


@mcp.tool()
async def get_txn_details(transaction_id: str) -> dict[str, Any]:
    """Get transaction details and AML analysis results."""
    return await get_transaction(transaction_id)


@mcp.tool()
async def get_txn_history(customer_id: str, days: int = 90, limit: int = 100) -> dict[str, Any]:
    """Get transaction history for AML analysis."""
    return await get_transaction_history(customer_id, days, limit)


@mcp.tool()
async def block_txn_tool(transaction_id: str, reason: str) -> dict[str, Any]:
    """Block a suspicious transaction."""
    return await block_transaction(transaction_id, reason)


@mcp.tool()
async def analyze_structuring(customer_id: str) -> dict[str, Any]:
    """Analyze a customer's transaction patterns for structuring."""
    return await get_structuring_analysis(customer_id)


@mcp.tool()
async def get_alerts(status: str = "open", limit: int = 50) -> dict[str, Any]:
    """Get AML alerts filtered by status."""
    return await get_aml_alerts(status, limit)


@mcp.tool()
async def aml_statistics(days: int = 30) -> dict[str, Any]:
    """Get AML monitoring statistics."""
    return await get_aml_stats(days)


# ══════════════════════════════════════════════════════════════════
#  SANCTIONS SCREENING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def screen_individual(name: str, name_type: str = "individual", threshold: float = 0.85, lists: list[str] | None = None) -> dict[str, Any]:
    """Screen an individual's name against OFAC SDN, EU, and UN sanctions lists."""
    return await screen_name(name, name_type, threshold, lists)


@mcp.tool()
async def screen_entity_tool(entity_name: str, jurisdiction: str | None = None, threshold: float = 0.85) -> dict[str, Any]:
    """Screen an entity against sanctions lists."""
    return await screen_entity(entity_name, jurisdiction, threshold)


@mcp.tool()
async def screen_vessel_tool(vessel_name: str, imo_number: str | None = None, flag_state: str | None = None) -> dict[str, Any]:
    """Screen a vessel against sanctions lists."""
    return await screen_vessel(vessel_name, imo_number, flag_state)


@mcp.tool()
async def screen_txn(
    transaction_id: str,
    originator_name: str,
    beneficiary_name: str,
    originator_country: str,
    beneficiary_country: str,
    amount: float,
) -> dict[str, Any]:
    """Screen all parties in a transaction against sanctions lists."""
    return await screen_transaction(transaction_id, originator_name, beneficiary_name, originator_country, beneficiary_country, amount)


@mcp.tool()
async def sanctions_screening_history(limit: int = 50) -> dict[str, Any]:
    """Get sanctions screening history."""
    return await get_screening_history(limit)


@mcp.tool()
async def sanctions_lists() -> dict[str, Any]:
    """Get information about loaded sanctions lists."""
    return await get_sanctions_lists_info()


# ══════════════════════════════════════════════════════════════════
#  PEP SCREENING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def screen_pep(name: str, country: str | None = None, threshold: float = 0.85) -> dict[str, Any]:
    """Screen an individual against the PEP database."""
    return await screen_for_pep(name, country, threshold)


@mcp.tool()
async def get_pep_info(pep_id: str) -> dict[str, Any]:
    """Get detailed PEP profile including relatives and close associates."""
    return await get_pep_profile(pep_id)


@mcp.tool()
async def assess_pep_risk_tool(
    pep_id: str,
    country_risk: str = "medium",
    business_type: str = "retail_banking",
    transaction_volume: str = "normal",
) -> dict[str, Any]:
    """Assess risk level for a PEP relationship."""
    return await assess_pep_risk(pep_id, country_risk, business_type, transaction_volume)


@mcp.tool()
async def get_rca(pep_id: str) -> dict[str, Any]:
    """Get relatives and close associates for a PEP."""
    return await get_rca_links(pep_id)


@mcp.tool()
async def pep_screening_history(limit: int = 50) -> dict[str, Any]:
    """Get PEP screening history."""
    return await get_pep_screening_history(limit)


# ══════════════════════════════════════════════════════════════════
#  SAR MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_sar_tool(
    customer_id: str,
    customer_name: str,
    customer_ssn_tin: str,
    customer_dob: str,
    customer_address: str,
    suspicious_activity_type: str,
    activity_description: str,
    first_activity_date: str,
    last_activity_date: str,
    amount_involved: float,
    related_account_numbers: list[str] | None = None,
    related_transactions: list[str] | None = None,
    disposition: str = "file_sar",
) -> dict[str, Any]:
    """Create a SAR with narrative. Deadline: 30 days from detection."""
    return await create_sar(customer_id, customer_name, customer_ssn_tin, customer_dob, customer_address, suspicious_activity_type, activity_description, first_activity_date, last_activity_date, amount_involved, related_account_numbers, related_transactions, disposition)


@mcp.tool()
async def update_sar_tool(
    sar_id: str,
    activity_description: str | None = None,
    amount_involved: float | None = None,
    related_transactions: list[str] | None = None,
    disposition: str | None = None,
) -> dict[str, Any]:
    """Update SAR details before filing."""
    return await update_sar(sar_id, activity_description, amount_involved, related_transactions, disposition)


@mcp.tool()
async def file_sar_tool(sar_id: str) -> dict[str, Any]:
    """File SAR electronically via BSA E-Filing."""
    return await file_sar(sar_id)


@mcp.tool()
async def create_continuing_sar_tool(original_sar_id: str, activity_update: str) -> dict[str, Any]:
    """Create a continuing activity SAR (90-day cycle)."""
    return await create_continuing_sar(original_sar_id, activity_update)


@mcp.tool()
async def get_sar_details(sar_id: str) -> dict[str, Any]:
    """Get SAR details."""
    return await get_sar(sar_id)


@mcp.tool()
async def list_sars(status: str = "all", limit: int = 50) -> dict[str, Any]:
    """Get SARs filtered by status."""
    return await get_sars_by_status(status, limit)


@mcp.tool()
async def sar_statistics() -> dict[str, Any]:
    """Get SAR filing statistics."""
    return await get_sar_stats()


# ══════════════════════════════════════════════════════════════════
#  CTR MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def file_ctr_tool(
    customer_id: str,
    customer_name: str,
    customer_ssn_tin: str,
    customer_address: str,
    customer_occupation: str,
    transaction_date: str,
    total_amount: float,
    transaction_type: str,
    transaction_description: str,
    branch_id: str,
    employee_id: str,
    aggregation_applied: bool = False,
    aggregated_transactions: list[dict] | None = None,
) -> dict[str, Any]:
    """File a Currency Transaction Report for cash transactions ≥ $10,000."""
    return await file_ctr(customer_id, customer_name, customer_ssn_tin, customer_address, customer_occupation, transaction_date, total_amount, transaction_type, transaction_description, branch_id, employee_id, aggregation_applied, aggregated_transactions)


@mcp.tool()
async def check_txn_aggregation(customer_id: str, transactions: list[dict], aggregation_period_days: int = 15) -> dict[str, Any]:
    """Check if multiple transactions should be aggregated for CTR filing."""
    return await check_aggregation(customer_id, transactions, aggregation_period_days)


@mcp.tool()
async def create_ctr_exemption(
    customer_id: str,
    customer_name: str,
    exemption_type: str,
    reason: str,
    approved_by: str,
) -> dict[str, Any]:
    """Create a CTR exemption for a customer."""
    return await create_exemption(customer_id, customer_name, exemption_type, reason, approved_by)


@mcp.tool()
async def list_ctr_exemptions(customer_id: str | None = None) -> dict[str, Any]:
    """Get CTR exemptions."""
    return await get_exemptions(customer_id)


@mcp.tool()
async def revoke_ctr_exemption(exemption_id: str, reason: str) -> dict[str, Any]:
    """Revoke a CTR exemption."""
    return await revoke_exemption(exemption_id, reason)


@mcp.tool()
async def ctr_statistics(days: int = 30) -> dict[str, Any]:
    """Get CTR filing statistics."""
    return await get_ctr_stats(days)


# ══════════════════════════════════════════════════════════════════
#  BENEFICIAL OWNERSHIP
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def identify_bo(
    entity_id: str,
    entity_name: str,
    entity_jurisdiction: str,
    ownership_structure: list[dict],
) -> dict[str, Any]:
    """Identify beneficial owners of a legal entity (25%+ ownership or control)."""
    return await identify_beneficial_owners(entity_id, entity_name, entity_jurisdiction, ownership_structure)


@mcp.tool()
async def verify_bo(bo_id: str, verification_method: str = "documentary", documents_provided: list[str] | None = None) -> dict[str, Any]:
    """Verify a beneficial owner's identity and ownership."""
    return await verify_beneficial_owner(bo_id, verification_method, documents_provided)


@mcp.tool()
async def trace_ubo(entity_id: str) -> dict[str, Any]:
    """Trace through ownership chain to find ultimate beneficial owner."""
    return await trace_ultimate_beneficial_owner(entity_id)


@mcp.tool()
async def update_bo(entity_id: str, changes: list[dict]) -> dict[str, Any]:
    """Update beneficial ownership information."""
    return await update_beneficial_ownership(entity_id, changes)


@mcp.tool()
async def get_bo_owners(entity_id: str) -> dict[str, Any]:
    """Get beneficial owners for an entity."""
    return await get_entity_owners(entity_id)


@mcp.tool()
async def pending_bo_verifications() -> dict[str, Any]:
    """Get all beneficial owners pending verification."""
    return await get_pending_verifications()


# ══════════════════════════════════════════════════════════════════
#  CASE MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_aml_case(
    customer_id: str,
    customer_name: str,
    case_type: str,
    description: str,
    priority: str = "medium",
    related_alerts: list[str] | None = None,
    related_transactions: list[str] | None = None,
    related_accounts: list[str] | None = None,
    risk_score: float = 0.0,
) -> dict[str, Any]:
    """Create an AML investigation case."""
    return await create_case(customer_id, customer_name, case_type, description, priority, related_alerts, related_transactions, related_accounts, risk_score)


@mcp.tool()
async def update_aml_case(
    case_id: str,
    status: str | None = None,
    stage: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Update an AML case."""
    return await update_case(case_id, status, stage, priority, assigned_to, notes)


@mcp.tool()
async def add_case_evidence_tool(case_id: str, evidence_type: str, description: str, data: dict | None = None) -> dict[str, Any]:
    """Add evidence to an AML case."""
    return await add_evidence(case_id, evidence_type, description, data)


@mcp.tool()
async def escalate_aml_case(case_id: str, escalation_reason: str, escalate_to: str = "senior_compliance_officer", escalate_to_law_enforcement: bool = False) -> dict[str, Any]:
    """Escalate an AML case to higher authority or law enforcement."""
    return await escalate_case(case_id, escalation_reason, escalate_to, escalate_to_law_enforcement)


@mcp.tool()
async def resolve_aml_case(case_id: str, resolution: str, outcome: str, sar_id: str | None = None, notes: str | None = None) -> dict[str, Any]:
    """Resolve an AML case."""
    return await resolve_case(case_id, resolution, outcome, sar_id, notes)


@mcp.tool()
async def get_aml_case(case_id: str) -> dict[str, Any]:
    """Get AML case details including evidence."""
    return await get_case(case_id)


@mcp.tool()
async def customer_cases(customer_id: str) -> dict[str, Any]:
    """Get all AML cases for a customer."""
    return await get_cases_by_customer(customer_id)


@mcp.tool()
async def open_cases(priority: str | None = None) -> dict[str, Any]:
    """Get all open AML cases."""
    return await get_open_cases(priority)


@mcp.tool()
async def escalated_cases() -> dict[str, Any]:
    """Get all escalated AML cases."""
    return await get_escalated_cases()


@mcp.tool()
async def case_statistics() -> dict[str, Any]:
    """Get AML case statistics."""
    return await get_case_stats()


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def send_aml_alert_tool(case_id: str, alert_type: str, subject: str, message: str, recipient: str = "compliance_team", priority: str = "high") -> dict[str, Any]:
    """Send an AML alert notification."""
    return await send_aml_alert(case_id, alert_type, subject, message, recipient, priority)


@mcp.tool()
async def sar_filing_notification(sar_id: str, customer_name: str, amount_involved: float, filing_date: str) -> dict[str, Any]:
    """Send SAR filing confirmation."""
    return await send_sar_filing_confirmation(sar_id, customer_name, amount_involved, filing_date)


@mcp.tool()
async def ctr_filing_notification(ctr_id: str, amount: float, customer_name: str) -> dict[str, Any]:
    """Send CTR filing confirmation."""
    return await send_ctr_filing_confirmation(ctr_id, amount, customer_name)


@mcp.tool()
async def escalation_notification(case_id: str, escalation_reason: str, escalate_to: str, law_enforcement_referral: bool = False) -> dict[str, Any]:
    """Send escalation notification."""
    return await send_escalation_notification(case_id, escalation_reason, escalate_to, law_enforcement_referral)


@mcp.tool()
async def deadline_reminder(case_id: str, deadline_type: str, deadline_date: str) -> dict[str, Any]:
    """Send deadline reminder."""
    return await send_deadline_reminder(case_id, deadline_type, deadline_date)


@mcp.tool()
async def continuing_sar_reminder(sar_id: str, next_deadline: str) -> dict[str, Any]:
    """Send continuing SAR 90-day filing reminder."""
    return await send_sar_continuing_reminder(sar_id, next_deadline)


@mcp.tool()
async def notification_history(recipient: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get notification history."""
    return await get_notification_history(recipient, limit)


if __name__ == "__main__":
    logger.info("Starting Anti-Money Laundering (AML) Alert Agent MCP Server...")
    mcp.run()
