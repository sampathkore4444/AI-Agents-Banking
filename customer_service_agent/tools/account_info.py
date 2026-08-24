"""
Account Information Tool — MCP tool stub.

Provides real-time account balance, recent transactions, account status,
and statement details via core banking API.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def get_account_balance(customer_id: str, account_number: str | None = None) -> dict:
    """Get current account balance and status."""
    logger.info("Fetching balance for customer %s", customer_id)
    cust_hash = hashlib.md5(customer_id.encode()).hexdigest()
    hash_val = int(cust_hash[:8], 16)

    balance = round(1000 + hash_val % 50000, 2)
    available = round(balance * 0.9, 2)

    return {
        "customer_id": customer_id,
        "account_number": f"ACC-{hash_val % 1000000:06d}",
        "account_type": ["checking", "savings", "business"][hash_val % 3],
        "balance": balance,
        "available_balance": available,
        "hold_amount": round(balance - available, 2),
        "currency": "USD",
        "status": "active",
        "as_of": datetime.utcnow().isoformat(),
    }


async def get_transaction_history(
    customer_id: str,
    account_number: str | None = None,
    days: int = 30,
    category_filter: str | None = None,
    limit: int = 20,
) -> dict:
    """Get recent transactions with optional filtering."""
    logger.info("Fetching transactions for customer %s (last %d days)", customer_id, days)
    cust_hash = hashlib.md5(customer_id.encode()).hexdigest()
    hash_val = int(cust_hash[:8], 16)

    categories = ["groceries", "restaurants", "utilities", "transportation", "entertainment", "shopping", "income", "transfer"]
    transactions = []
    for i in range(min(limit, 20)):
        days_ago = i * (days // limit)
        date = datetime.utcnow() - timedelta(days=days_ago)
        cat = categories[hash_val % len(categories)]
        amount = round(-50 - hash_val % 500, 2) if hash_val % 4 != 0 else round(1000 + hash_val % 5000, 2)
        transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "description": f"Transaction {i+1}",
            "amount": amount,
            "category": cat,
            "balance_after": round(5000 + hash_val % 20000 - (i * 100), 2),
        })

    if category_filter:
        transactions = [t for t in transactions if t["category"] == category_filter]

    total_spent = round(sum(abs(t["amount"]) for t in transactions if t["amount"] < 0), 2)
    total_received = round(sum(t["amount"] for t in transactions if t["amount"] > 0), 2)

    return {
        "customer_id": customer_id,
        "transaction_count": len(transactions),
        "transactions": transactions,
        "summary": {
            "total_spent": total_spent,
            "total_received": total_received,
            "net_flow": round(total_received - total_spent, 2),
        },
        "period_days": days,
    }


async def get_account_statements(customer_id: str, months: int = 6) -> dict:
    """Get available account statements."""
    logger.info("Fetching statements for customer %s", customer_id)
    statements = []
    for i in range(months):
        date = datetime.utcnow() - timedelta(days=30 * i)
        statements.append({
            "month": date.strftime("%Y-%m"),
            "url": f"https://statements.bank.com/{customer_id}/{date.strftime('%Y-%m')}.pdf",
            "generated_date": date.strftime("%Y-%m-%d"),
        })
    return {"customer_id": customer_id, "statements": statements, "count": len(statements)}
