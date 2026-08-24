"""
Ledger Management Tool — MCP tool stub for reconciliation.

Manages internal ledger entries, balance tracking, and journal entries.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory ledger store
_ledger_entries: dict[str, dict] = {}
_journal_entries: dict[str, dict] = {}

# Seed sample ledger entries
def _seed_ledger():
    entries = [
        {
            "id": "LED-001",
            "account_number": "1000-OPERATING",
            "transaction_type": "credit",
            "amount": 25000.00,
            "date": "2026-01-15",
            "reference": "INV-2024-001",
            "counterparty": "Acme Corp",
            "description": "Payment received for consulting services",
            "category": "revenue",
            "status": "posted",
        },
        {
            "id": "LED-002",
            "account_number": "1000-OPERATING",
            "transaction_type": "debit",
            "amount": 8500.00,
            "date": "2026-01-16",
            "reference": "PO-2024-042",
            "counterparty": "Tech Supplies Inc",
            "description": "Office equipment purchase",
            "category": "expense",
            "status": "posted",
        },
        {
            "id": "LED-003",
            "account_number": "1000-OPERATING",
            "transaction_type": "credit",
            "amount": 150000.00,
            "date": "2026-01-17",
            "reference": "INV-2024-002",
            "counterparty": "Global Partners LLC",
            "description": "Q1 retainer payment",
            "category": "revenue",
            "status": "posted",
        },
        {
            "id": "LED-004",
            "account_number": "1000-OPERATING",
            "transaction_type": "debit",
            "amount": 4200.00,
            "date": "2026-01-18",
            "reference": "INV-2024-003",
            "counterparty": "Cloud Services Co",
            "description": "Monthly SaaS subscription",
            "category": "expense",
            "status": "posted",
        },
        {
            "id": "LED-005",
            "account_number": "1000-OPERATING",
            "transaction_type": "credit",
            "amount": 3750.00,
            "date": "2026-01-19",
            "reference": "INV-2024-004",
            "counterparty": "Startup Ventures",
            "description": "Project milestone payment",
            "category": "revenue",
            "status": "posted",
        },
    ]
    for e in entries:
        _ledger_entries[e["id"]] = e

_seed_ledger()


async def get_ledger_entries(
    account_number: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    transaction_type: str | None = None,
    limit: int = 50,
) -> dict:
    """Retrieve ledger entries with optional filters."""
    entries = list(_ledger_entries.values())

    if account_number:
        entries = [e for e in entries if e.get("account_number") == account_number]
    if start_date:
        entries = [e for e in entries if e.get("date", "") >= start_date]
    if end_date:
        entries = [e for e in entries if e.get("date", "") <= end_date]
    if transaction_type:
        entries = [e for e in entries if e.get("transaction_type") == transaction_type]

    entries.sort(key=lambda x: x.get("date", ""), reverse=True)

    total_credits = sum(e["amount"] for e in entries if e.get("transaction_type") == "credit")
    total_debits = sum(e["amount"] for e in entries if e.get("transaction_type") == "debit")

    return {
        "total_entries": len(entries),
        "entries": entries[:limit],
        "summary": {
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "net_balance": round(total_credits - total_debits, 2),
        },
    }


async def get_balance(account_number: str) -> dict:
    """Get current balance for an account."""
    entries = [e for e in _ledger_entries.values() if e.get("account_number") == account_number]

    credits = sum(e["amount"] for e in entries if e.get("transaction_type") == "credit")
    debits = sum(e["amount"] for e in entries if e.get("transaction_type") == "debit")

    return {
        "account_number": account_number,
        "total_credits": round(credits, 2),
        "total_debits": round(debits, 2),
        "current_balance": round(credits - debits, 2),
        "entry_count": len(entries),
        "as_of_date": datetime.utcnow().strftime("%Y-%m-%d"),
    }


async def create_journal_entry(
    account_number: str,
    transaction_type: str,
    amount: float,
    reference: str,
    counterparty: str,
    description: str,
    category: str,
    reversal_of: str | None = None,
) -> dict:
    """Create a new journal entry (for adjustments)."""
    entry_id = f"JE-{uuid.uuid4().hex[:8].upper()}"

    entry = {
        "id": entry_id,
        "account_number": account_number,
        "transaction_type": transaction_type,
        "amount": round(amount, 2),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "reference": reference,
        "counterparty": counterparty,
        "description": description,
        "category": category,
        "status": "posted",
        "reversal_of": reversal_of,
        "created_at": datetime.utcnow().isoformat(),
    }

    _journal_entries[entry_id] = entry
    _ledger_entries[entry_id] = entry

    logger.info("Journal entry created: %s", entry_id)
    return entry


async def reverse_entry(entry_id: str, reason: str) -> dict:
    """Reverse an existing ledger entry."""
    original = _ledger_entries.get(entry_id) or _journal_entries.get(entry_id)
    if not original:
        return {"error": f"Entry {entry_id} not found"}

    reversal_type = "debit" if original["transaction_type"] == "credit" else "credit"

    reversal = await create_journal_entry(
        account_number=original["account_number"],
        transaction_type=reversal_type,
        amount=original["amount"],
        reference=f"REV-{original['reference']}",
        counterparty=original["counterparty"],
        description=f"Reversal of {entry_id}: {reason}",
        category=original.get("category", "adjustment"),
        reversal_of=entry_id,
    )

    logger.info("Entry reversed: %s → %s", entry_id, reversal["id"])
    return reversal
