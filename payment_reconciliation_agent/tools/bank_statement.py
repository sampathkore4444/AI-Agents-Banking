"""
Bank Statement Import Tool — MCP tool stub for reconciliation.

Handles importing bank statements in various formats (MT940, BAI2, CSV, ISO 20022).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory bank statement store
_bank_statements: dict[str, dict] = {}
_bank_entries: list[dict] = []

# Seed sample bank entries
def _seed_bank_entries():
    entries = [
        {
            "id": "BNK-001",
            "account_number": "1000-OPERATING",
            "transaction_type": "credit",
            "amount": 25000.00,
            "date": "2026-01-15",
            "value_date": "2026-01-15",
            "reference": "INV-2024-001",
            "counterparty": "ACME CORP",
            "description": "Wire transfer - Invoice 2024-001",
            "transaction_code": "47",
            "source": "wire",
            "status": "settled",
        },
        {
            "id": "BNK-002",
            "account_number": "1000-OPERATING",
            "transaction_type": "debit",
            "amount": 8500.00,
            "date": "2026-01-16",
            "value_date": "2026-01-16",
            "reference": "PO-2024-042",
            "counterparty": "TECH SUPPLIES",
            "description": "ACH Debit - PO 2024-042",
            "transaction_code": "18",
            "source": "ach",
            "status": "settled",
        },
        {
            "id": "BNK-003",
            "account_number": "1000-OPERATING",
            "transaction_type": "credit",
            "amount": 150000.00,
            "date": "2026-01-17",
            "value_date": "2026-01-17",
            "reference": "INV-2024-002",
            "counterparty": "GLOBAL PARTNERS",
            "description": "Wire transfer - Q1 Retainer",
            "transaction_code": "47",
            "source": "wire",
            "status": "settled",
        },
        {
            "id": "BNK-004",
            "account_number": "1000-OPERATING",
            "transaction_type": "debit",
            "amount": 4200.00,
            "date": "2026-01-18",
            "value_date": "2026-01-18",
            "reference": "CLOUD-SUB-001",
            "counterparty": "CLOUD SERVICES CO",
            "description": "ACH Debit - Monthly subscription",
            "transaction_code": "18",
            "source": "ach",
            "status": "settled",
        },
        {
            "id": "BNK-005",
            "account_number": "1000-OPERATING",
            "transaction_type": "credit",
            "amount": 3749.00,
            "date": "2026-01-19",
            "value_date": "2026-01-19",
            "reference": "INV-2024-004",
            "counterparty": "STARTUP VENTURES",
            "description": "ACH Credit - Project milestone",
            "transaction_code": "17",
            "source": "ach",
            "status": "settled",
        },
        {
            "id": "BNK-006",
            "account_number": "1000-OPERATING",
            "transaction_type": "debit",
            "amount": 250.00,
            "date": "2026-01-20",
            "value_date": "2026-01-20",
            "reference": "BANK-FEE-001",
            "counterparty": "BANK OF AMERICA",
            "description": "Monthly service charge",
            "transaction_code": "15",
            "source": "system",
            "status": "settled",
        },
        {
            "id": "BNK-007",
            "account_number": "1000-OPERATING",
            "transaction_type": "debit",
            "amount": 12000.00,
            "date": "2026-01-21",
            "value_date": "2026-01-21",
            "reference": "CHECK-4521",
            "counterparty": "UNKNOWN DEPOSIT",
            "description": "Check deposit - altered amount",
            "transaction_code": "15",
            "source": "check",
            "status": "flagged",
        },
    ]
    _bank_entries.extend(entries)

_seed_bank_entries()


async def import_bank_statement(
    account_number: str,
    format_type: str,
    statement_date: str,
    opening_balance: float,
    closing_balance: float,
    entries: list[dict] | None = None,
) -> dict:
    """
    Import a bank statement in various formats.

    format_type: "MT940", "BAI2", "ISO20022", "CSV"
    """
    logger.info("Importing bank statement: account=%s, format=%s, date=%s", account_number, format_type, statement_date)

    statement_id = f"STMT-{uuid.uuid4().hex[:8].upper()}"

    parsed_entries = entries or []
    imported_count = len(parsed_entries)

    for entry in parsed_entries:
        entry["id"] = f"BNK-{uuid.uuid4().hex[:6].upper()}"
        entry["account_number"] = account_number
        entry["statement_id"] = statement_id
        entry["status"] = "settled"
        _bank_entries.append(entry)

    statement = {
        "statement_id": statement_id,
        "account_number": account_number,
        "format": format_type,
        "statement_date": statement_date,
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(closing_balance, 2),
        "balance_difference": round(closing_balance - opening_balance, 2),
        "entries_imported": imported_count,
        "status": "imported",
        "imported_at": datetime.utcnow().isoformat(),
    }

    _bank_statements[statement_id] = statement

    # Validate balance
    total_credits = sum(e.get("amount", 0) for e in parsed_entries if e.get("transaction_type") == "credit")
    total_debits = sum(e.get("amount", 0) for e in parsed_entries if e.get("transaction_type") == "debit")
    computed_diff = round(total_credits - total_debits, 2)
    expected_diff = round(closing_balance - opening_balance, 2)

    balance_valid = abs(computed_diff - expected_diff) < 0.01

    statement["balance_validation"] = {
        "computed_difference": computed_diff,
        "expected_difference": expected_diff,
        "valid": balance_valid,
        "discrepancy": round(abs(computed_diff - expected_diff), 2),
    }

    if not balance_valid:
        statement["status"] = "imported_with_errors"
        logger.warning("Balance mismatch on statement %s: computed=%s, expected=%s", statement_id, computed_diff, expected_diff)

    return statement


async def get_bank_entries(
    account_number: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    transaction_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict:
    """Retrieve bank statement entries with filters."""
    entries = list(_bank_entries)

    if account_number:
        entries = [e for e in entries if e.get("account_number") == account_number]
    if start_date:
        entries = [e for e in entries if e.get("date", "") >= start_date]
    if end_date:
        entries = [e for e in entries if e.get("date", "") <= end_date]
    if transaction_type:
        entries = [e for e in entries if e.get("transaction_type") == transaction_type]
    if status:
        entries = [e for e in entries if e.get("status") == status]

    entries.sort(key=lambda x: x.get("date", ""), reverse=True)

    total_credits = sum(e["amount"] for e in entries if e.get("transaction_type") == "credit")
    total_debits = sum(e["amount"] for e in entries if e.get("transaction_type") == "debit")

    return {
        "total_entries": len(entries),
        "entries": entries[:limit],
        "summary": {
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "net_amount": round(total_credits - total_debits, 2),
        },
    }


async def parse_statement_format(format_type: str, raw_data: str) -> dict:
    """Parse raw bank statement data into structured entries."""
    logger.info("Parsing %s format statement", format_type)

    if format_type == "MT940":
        return _parse_mt940(raw_data)
    elif format_type == "BAI2":
        return _parse_bai2(raw_data)
    elif format_type == "ISO20022":
        return _parse_iso20022(raw_data)
    elif format_type == "CSV":
        return _parse_csv(raw_data)
    else:
        return {"error": f"Unsupported format: {format_type}"}


def _parse_mt940(raw_data: str) -> dict:
    """Parse MT940 format (simplified)."""
    return {
        "format": "MT940",
        "status": "parsed",
        "entries": [],
        "note": "MT940 parser would extract :61 statement lines and :86 information fields",
    }


def _parse_bai2(raw_data: str) -> dict:
    """Parse BAI2 format (simplified)."""
    return {
        "format": "BAI2",
        "status": "parsed",
        "entries": [],
        "note": "BAI2 parser would extract record type 16 transactions with transaction codes",
    }


def _parse_iso20022(raw_data: str) -> dict:
    """Parse ISO 20022 / CAMT.053 format (simplified)."""
    return {
        "format": "ISO20022",
        "status": "parsed",
        "entries": [],
        "note": "ISO 20022 parser would extract Ntry elements with Amount, CdtDbtInd, RmtInf",
    }


def _parse_csv(raw_data: str) -> dict:
    """Parse CSV format bank statement."""
    return {
        "format": "CSV",
        "status": "parsed",
        "entries": [],
        "note": "CSV parser would extract columns: date, description, debit, credit, balance, reference",
    }
