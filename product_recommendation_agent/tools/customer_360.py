"""
Customer 360 Tool — Complete customer profile and relationship view.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


# ── In-memory customer store ──────────────────────────────────────
CUSTOMER_DB: dict[str, dict] = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "John Smith",
        "date_of_birth": "1985-06-15",
        "age": 41,
        "email": "john.smith@email.com",
        "phone": "+1-555-0101",
        "address": {"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"},
        "segment": "young_professionals",
        "lifecycle_stage": "growth",
        "income": 85000,
        "credit_score": 742,
        "employment": {"status": "employed", "employer": "Tech Corp", "years": 5},
        "existing_products": ["PROD-CHK-001", "PROD-SAV-001", "PROD-CC-001"],
        "total_deposits": 45000,
        "total_loans": 0,
        "credit_utilization": 0.15,
        "account_age_days": 1200,
        "last_transaction": "2026-08-20",
        "customer_lifetime_value": 12500,
        "risk_score": "low",
        "preferences": {"channels": ["mobile", "email"], "communication_frequency": "monthly"},
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Sarah Johnson",
        "date_of_birth": "1978-03-22",
        "age": 48,
        "email": "sarah.j@email.com",
        "phone": "+1-555-0102",
        "address": {"street": "456 Oak Ave", "city": "Chicago", "state": "IL", "zip": "60601"},
        "segment": "families",
        "lifecycle_stage": "accumulation",
        "income": 145000,
        "credit_score": 785,
        "employment": {"status": "employed", "employer": "Finance Inc", "years": 12},
        "existing_products": ["PROD-CHK-001", "PROD-SAV-001", "PROD-CC-002", "PROD-MTG-001"],
        "total_deposits": 125000,
        "total_loans": 350000,
        "credit_utilization": 0.22,
        "account_age_days": 3650,
        "last_transaction": "2026-08-21",
        "customer_lifetime_value": 45000,
        "risk_score": "low",
        "preferences": {"channels": ["branch", "email", "phone"], "communication_frequency": "quarterly"},
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Michael Chen",
        "date_of_birth": "1995-11-08",
        "age": 30,
        "email": "m.chen@email.com",
        "phone": "+1-555-0103",
        "address": {"street": "789 Pine Rd", "city": "San Francisco", "state": "CA", "zip": "94102"},
        "segment": "young_professionals",
        "lifecycle_stage": "growth",
        "income": 95000,
        "credit_score": 710,
        "employment": {"status": "employed", "employer": "StartupXYZ", "years": 2},
        "existing_products": ["PROD-CHK-001", "PROD-SAV-001"],
        "total_deposits": 28000,
        "total_loans": 0,
        "credit_utilization": 0.08,
        "account_age_days": 450,
        "last_transaction": "2026-08-19",
        "customer_lifetime_value": 5500,
        "risk_score": "low",
        "preferences": {"channels": ["mobile"], "communication_frequency": "monthly"},
    },
    "CUST-004": {
        "customer_id": "CUST-004",
        "name": "Emily Davis",
        "date_of_birth": "2003-02-14",
        "age": 23,
        "email": "emily.d@email.com",
        "phone": "+1-555-0104",
        "address": {"street": "321 College Blvd", "city": "Austin", "state": "TX", "zip": "78701"},
        "segment": "students",
        "lifecycle_stage": "entry",
        "income": 18000,
        "credit_score": 650,
        "employment": {"status": "part_time", "employer": "Campus Library", "years": 1},
        "existing_products": ["PROD-CHK-001"],
        "total_deposits": 3500,
        "total_loans": 25000,
        "credit_utilization": 0.45,
        "account_age_days": 180,
        "last_transaction": "2026-08-18",
        "customer_lifetime_value": 1200,
        "risk_score": "medium",
        "preferences": {"channels": ["mobile", "sms"], "communication_frequency": "weekly"},
    },
    "CUST-005": {
        "customer_id": "CUST-005",
        "name": "Robert Wilson",
        "date_of_birth": "1958-07-30",
        "age": 68,
        "email": "r.wilson@email.com",
        "phone": "+1-555-0105",
        "address": {"street": "654 Retirement Ln", "city": "Phoenix", "state": "AZ", "zip": "85001"},
        "segment": "retirees",
        "lifecycle_stage": "distribution",
        "income": 62000,
        "credit_score": 810,
        "employment": {"status": "retired", "employer": None, "years": 0},
        "existing_products": ["PROD-CHK-001", "PROD-SAV-001", "PROD-CD-001", "PROD-IRA-001"],
        "total_deposits": 280000,
        "total_loans": 0,
        "credit_utilization": 0.0,
        "account_age_days": 7300,
        "last_transaction": "2026-08-15",
        "customer_lifetime_value": 85000,
        "risk_score": "low",
        "preferences": {"channels": ["branch", "phone", "mail"], "communication_frequency": "quarterly"},
    },
}


async def get_customer_360(customer_id: str) -> dict[str, Any]:
    """Get complete customer profile."""
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    # Calculate derived metrics
    product_count = len(customer.get("existing_products", []))
    avg_balance = customer.get("total_deposits", 0) / max(product_count, 1)

    return {
        **customer,
        "derived_metrics": {
            "product_count": product_count,
            "avg_balance_per_product": round(avg_balance, 2),
            "years_as_customer": round(customer.get("account_age_days", 0) / 365, 1),
            "deposit_to_loan_ratio": round(customer.get("total_deposits", 0) / max(customer.get("total_loans", 1), 1), 2),
        },
    }


async def search_customers(
    segment: str | None = None,
    lifecycle_stage: str | None = None,
    min_credit_score: int | None = None,
    min_income: float | None = None,
    min_clv: float | None = None,
    has_product: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search customers by criteria."""
    results = list(CUSTOMER_DB.values())

    if segment:
        results = [c for c in results if c.get("segment") == segment]
    if lifecycle_stage:
        results = [c for c in results if c.get("lifecycle_stage") == lifecycle_stage]
    if min_credit_score is not None:
        results = [c for c in results if c.get("credit_score", 0) >= min_credit_score]
    if min_income is not None:
        results = [c for c in results if c.get("income", 0) >= min_income]
    if min_clv is not None:
        results = [c for c in results if c.get("customer_lifetime_value", 0) >= min_clv]
    if has_product:
        results = [c for c in results if has_product in c.get("existing_products", [])]

    return {
        "total_customers": len(results),
        "customers": results[:limit],
    }


async def get_customer_products(customer_id: str) -> dict[str, Any]:
    """Get products held by a customer."""
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    from tools.product_catalog import PRODUCT_DB
    products = []
    for pid in customer.get("existing_products", []):
        product = PRODUCT_DB.get(pid)
        if product:
            products.append(product)

    return {
        "customer_id": customer_id,
        "total_products": len(products),
        "products": products,
    }


async def get_customer_transactions(
    customer_id: str,
    days: int = 30,
) -> dict[str, Any]:
    """Get recent customer transaction summary."""
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    # Simulated transaction summary
    return {
        "customer_id": customer_id,
        "period_days": days,
        "total_transactions": 45,
        "total_amount": 3250.00,
        "avg_transaction": 72.22,
        "top_categories": [
            {"category": "groceries", "count": 12, "amount": 450.00},
            {"category": "dining", "count": 8, "amount": 280.00},
            {"category": "utilities", "count": 4, "amount": 320.00},
            {"category": "entertainment", "count": 6, "amount": 180.00},
        ],
    }


async def update_customer_profile(
    customer_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Update customer profile."""
    customer = CUSTOMER_DB.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    customer.update(updates)
    return {"customer_id": customer_id, "message": f"Customer {customer_id} profile updated."}


async def add_customer(
    customer_id: str,
    name: str,
    date_of_birth: str,
    email: str,
    segment: str,
    income: float,
    credit_score: int,
) -> dict[str, Any]:
    """Add a new customer."""
    customer = {
        "customer_id": customer_id,
        "name": name,
        "date_of_birth": date_of_birth,
        "age": (datetime.utcnow() - datetime.strptime(date_of_birth, "%Y-%m-%d")).days // 365,
        "email": email,
        "segment": segment,
        "income": income,
        "credit_score": credit_score,
        "existing_products": [],
        "total_deposits": 0,
        "total_loans": 0,
        "customer_lifetime_value": 0,
        "account_age_days": 0,
        "last_transaction": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    CUSTOMER_DB[customer_id] = customer

    return {"customer_id": customer_id, "name": name, "message": f"Customer {customer_id} added."}


async def get_customer_segments() -> dict[str, Any]:
    """Get customer distribution by segment."""
    segments: dict[str, int] = {}
    for c in CUSTOMER_DB.values():
        seg = c.get("segment", "unknown")
        segments[seg] = segments.get(seg, 0) + 1

    return {
        "total_customers": len(CUSTOMER_DB),
        "segments": segments,
        "lifecycle_stages": {
            stage: sum(1 for c in CUSTOMER_DB.values() if c.get("lifecycle_stage") == stage)
            for stage in set(c.get("lifecycle_stage") for c in CUSTOMER_DB.values())
        },
    }


async def get_high_value_customers(min_clv: float = 10000) -> dict[str, Any]:
    """Get high-value customers for targeted recommendations."""
    hv_customers = [c for c in CUSTOMER_DB.values() if c.get("customer_lifetime_value", 0) >= min_clv]
    hv_customers.sort(key=lambda x: x.get("customer_lifetime_value", 0), reverse=True)

    return {
        "min_clv": min_clv,
        "count": len(hv_customers),
        "customers": hv_customers,
    }
