"""
Payment Reconciliation Agent — MCP Server.

Automates reconciliation of incoming/outgoing payments, identifies
mismatches, and suggests resolutions using RAG and MCP tools.

Covers all 7.2 Payment Reconciliation Agent capabilities:
- Payment matching (auto, fuzzy, semantic)
- Bank statement import (MT940, BAI2, ISO 20022, CSV)
- Ledger management and adjusting entries
- Exception handling and escalation
- Discrepancy investigation and resolution
- Payment reference embedding for semantic matching
- Reconciliation reporting
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.accounting_system import check_gl_sync_status, generate_reconciliation_report, get_adjustments, post_adjusting_entry
from tools.bank_statement import get_bank_entries, import_bank_statement, parse_statement_format
from tools.discrepancy_resolution import get_discrepancy_report, identify_discrepancies, investigate_discrepancy, resolve_amount_discrepancy
from tools.exception_handling import create_exception, escalate_exception, get_exception, get_exception_aging_report, get_exception_queue, resolve_exception
from tools.ledger_management import create_journal_entry, get_balance, get_ledger_entries, reverse_entry
from tools.notifications import send_exception_alert, send_recon_notification
from tools.payment_embedding import embed_counterparty, embed_invoice, embed_payment, find_similar_invoices
from tools.payment_matching import auto_match_payments, embed_payment_reference, match_single_payment

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Payment Reconciliation Agent",
    instructions=(
        "Payment Reconciliation Agent for banking. Use these tools to "
        "reconcile payments: import bank statements, match payments to "
        "ledger entries, investigate discrepancies, resolve exceptions, "
        "and generate reconciliation reports."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """Search the reconciliation knowledge base for rules, standards, and past discrepancies."""
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "results_count": len(result.chunks),
        "chunks": [{"text": c.text[:300], "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata} for c in result.chunks],
        "assembled_context": result.assembled_context[:1000],
    }


# ══════════════════════════════════════════════════════════════════
#  PAYMENT MATCHING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def run_auto_match(bank_entries: list[dict], ledger_entries: list[dict], match_threshold: float = 0.95, amount_tolerance_pct: float = 0.01, date_tolerance_days: int = 2) -> dict[str, Any]:
    """Auto-match bank statement entries to ledger entries using rules and embeddings."""
    return await auto_match_payments(bank_entries, ledger_entries, match_threshold, amount_tolerance_pct, date_tolerance_days)


@mcp.tool()
async def match_payment(bank_entry: dict, ledger_entries: list[dict]) -> dict[str, Any]:
    """Match a single bank entry against all ledger entries and return ranked candidates."""
    return await match_single_payment(bank_entry, ledger_entries)


# ══════════════════════════════════════════════════════════════════
#  BANK STATEMENT IMPORT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def import_statement(account_number: str, format_type: str, statement_date: str, opening_balance: float, closing_balance: float, entries: list[dict] | None = None) -> dict[str, Any]:
    """Import a bank statement (MT940, BAI2, ISO 20022, CSV)."""
    return await import_bank_statement(account_number, format_type, statement_date, opening_balance, closing_balance, entries)


@mcp.tool()
async def get_bank_data(account_number: str | None = None, start_date: str | None = None, end_date: str | None = None, transaction_type: str | None = None, status: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Retrieve bank statement entries with optional filters."""
    return await get_bank_entries(account_number, start_date, end_date, transaction_type, status, limit)


@mcp.tool()
async def parse_statement(format_type: str, raw_data: str) -> dict[str, Any]:
    """Parse raw bank statement data into structured entries."""
    return await parse_statement_format(format_type, raw_data)


# ══════════════════════════════════════════════════════════════════
#  LEDGER MANAGEMENT
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_ledger(account_number: str | None = None, start_date: str | None = None, end_date: str | None = None, transaction_type: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Retrieve ledger entries with optional filters."""
    return await get_ledger_entries(account_number, start_date, end_date, transaction_type, limit)


@mcp.tool()
async def get_account_balance(account_number: str) -> dict[str, Any]:
    """Get current balance for an account."""
    return await get_balance(account_number)


@mcp.tool()
async def create_journal(account_number: str, transaction_type: str, amount: float, reference: str, counterparty: str, description: str, category: str, reversal_of: str | None = None) -> dict[str, Any]:
    """Create a new journal entry for adjustments."""
    return await create_journal_entry(account_number, transaction_type, amount, reference, counterparty, description, category, reversal_of)


@mcp.tool()
async def reverse_ledger_entry(entry_id: str, reason: str) -> dict[str, Any]:
    """Reverse an existing ledger entry."""
    return await reverse_entry(entry_id, reason)


# ══════════════════════════════════════════════════════════════════
#  EXCEPTION HANDLING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_recon_exception(exception_type: str, severity: str, amount: float, date: str, description: str, bank_entry_id: str | None = None, ledger_entry_id: str | None = None, assigned_to: str | None = None) -> dict[str, Any]:
    """Create a new reconciliation exception item."""
    return await create_exception(exception_type, severity, amount, date, description, bank_entry_id, ledger_entry_id, assigned_to)


@mcp.tool()
async def get_exception(exception_id: str) -> dict[str, Any]:
    """Get details of an exception item."""
    return await get_exception(exception_id)


@mcp.tool()
async def get_exceptions(status: str | None = None, severity: str | None = None, exception_type: str | None = None, assigned_to: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get exception queue with optional filters."""
    return await get_exception_queue(status, severity, exception_type, assigned_to, limit)


@mcp.tool()
async def resolve_recon_exception(exception_id: str, resolution: str, root_cause: str, adjusting_entry_id: str | None = None, notes: str | None = None) -> dict[str, Any]:
    """Resolve an exception item."""
    return await resolve_exception(exception_id, resolution, root_cause, adjusting_entry_id, notes)


@mcp.tool()
async def escalate_recon_exception(exception_id: str, escalate_to: str, reason: str) -> dict[str, Any]:
    """Escalate an exception to a higher authority."""
    return await escalate_exception(exception_id, escalate_to, reason)


@mcp.tool()
async def exception_aging() -> dict[str, Any]:
    """Generate aging report for all open exceptions."""
    return await get_exception_aging_report()


# ══════════════════════════════════════════════════════════════════
#  DISCREPANCY RESOLUTION
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def find_discrepancies(matched_pairs: list[dict], amount_tolerance_pct: float = 0.01) -> dict[str, Any]:
    """Analyze matched pairs to identify amount discrepancies."""
    return await identify_discrepancies(matched_pairs, amount_tolerance_pct)


@mcp.tool()
async def investigate_disc(discrepancy_id: str) -> dict[str, Any]:
    """Investigate a discrepancy and suggest possible causes."""
    return await investigate_discrepancy(discrepancy_id)


@mcp.tool()
async def resolve_disc(discrepancy_id: str, resolution_type: str, adjusting_amount: float | None = None, description: str | None = None, approved_by: str | None = None) -> dict[str, Any]:
    """Resolve an amount discrepancy (adjust_ledger, write_off, bank_notification, no_action)."""
    return await resolve_amount_discrepancy(discrepancy_id, resolution_type, adjusting_amount, description, approved_by)


@mcp.tool()
async def discrepancy_report(start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    """Generate a discrepancy report."""
    return await get_discrepancy_report(start_date, end_date)


# ══════════════════════════════════════════════════════════════════
#  PAYMENT EMBEDDING
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def embed_inv(invoice_id: str, vendor_name: str, amount: float, invoice_date: str, description: str, po_number: str | None = None) -> dict[str, Any]:
    """Create embedding of an invoice for semantic matching."""
    return await embed_invoice(invoice_id, vendor_name, amount, invoice_date, description, po_number)


@mcp.tool()
async def embed_pay(payment_id: str, payer_name: str, amount: float, payment_date: str, reference: str, payment_method: str) -> dict[str, Any]:
    """Create embedding of a payment for semantic matching."""
    return await embed_payment(payment_id, payer_name, amount, payment_date, reference, payment_method)


@mcp.tool()
async def find_similar(payment_id: str, top_k: int = 5) -> dict[str, Any]:
    """Find invoices similar to a payment using embedding similarity."""
    return await find_similar_invoices(payment_id, top_k)


@mcp.tool()
async def embed_cp(counterparty_id: str, name: str, aliases: list[str] | None = None) -> dict[str, Any]:
    """Create embedding of a counterparty name with aliases."""
    return await embed_counterparty(counterparty_id, name, aliases)


# ══════════════════════════════════════════════════════════════════
#  ACCOUNTING SYSTEM
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def post_adjustment(account_number: str, amount: float, adjustment_type: str, description: str, reference: str, supporting_document: str | None = None, approved_by: str | None = None) -> dict[str, Any]:
    """Post an adjusting journal entry to the GL."""
    return await post_adjusting_entry(account_number, amount, adjustment_type, description, reference, supporting_document, approved_by)


@mcp.tool()
async def get_adjustments(account_number: str | None = None, period: str | None = None, adjustment_type: str | None = None) -> dict[str, Any]:
    """Get posted adjusting entries."""
    return await get_adjustments(account_number, period, adjustment_type)


@mcp.tool()
async def gen_recon_report(account_number: str, period: str) -> dict[str, Any]:
    """Generate a formal reconciliation report for a period."""
    return await generate_reconciliation_report(account_number, period)


@mcp.tool()
async def check_gl_sync(account_number: str) -> dict[str, Any]:
    """Check if GL is in sync with reconciliation."""
    return await check_gl_sync_status(account_number)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════

@mcp.tool()
async def notify_recon(recipient_id: str, template_id: str, channel: str = "email", variables: dict | None = None) -> dict[str, Any]:
    """Send a reconciliation notification."""
    return await send_recon_notification(recipient_id, template_id, channel, variables)


@mcp.tool()
async def alert_exception(exception_id: str, exception_type: str, amount: float, account_number: str, assigned_to: str, aging_days: int) -> dict[str, Any]:
    """Send an exception escalation alert."""
    return await send_exception_alert(exception_id, exception_type, amount, account_number, assigned_to, aging_days)


if __name__ == "__main__":
    logger.info("Starting Payment Reconciliation Agent MCP Server...")
    mcp.run()
