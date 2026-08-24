"""
Lead Management Tool — Create, update, and manage leads through the pipeline.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


# ── In-memory lead store ──────────────────────────────────────────
LEAD_DB: dict[str, dict] = {
    "LEAD-001": {
        "lead_id": "LEAD-001",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@email.com",
        "phone": "+1-555-0101",
        "source": "website",
        "product_interest": "mortgage",
        "status": "new",
        "tier": None,
        "score": 72,
        "qualifier": None,
        "assigned_to": None,
        "created_at": "2026-08-20T10:30:00",
        "updated_at": "2026-08-20T10:30:00",
        "last_contact": None,
        "next_follow_up": None,
        "notes": [],
        "demographics": {"age": 35, "income": 95000, "credit_score": 720, "homeowner": False},
        "behavior": {"pages_visited": 5, "calculator_used": True, "application_started": False},
    },
    "LEAD-002": {
        "lead_id": "LEAD-002",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "email": "sarah.j@email.com",
        "phone": "+1-555-0102",
        "source": "referral",
        "product_interest": "savings",
        "status": "qualified",
        "tier": "hot",
        "score": 85,
        "qualifier": "agent_001",
        "assigned_to": "advisor_001",
        "created_at": "2026-08-18T14:15:00",
        "updated_at": "2026-08-19T09:00:00",
        "last_contact": "2026-08-19T09:00:00",
        "next_follow_up": "2026-08-21T14:00:00",
        "notes": ["Referred by existing customer CUST-001", "Interested in high-yield savings"],
        "demographics": {"age": 42, "income": 120000, "credit_score": 780, "homeowner": True},
        "behavior": {"pages_visited": 3, "calculator_used": False, "application_started": True},
    },
    "LEAD-003": {
        "lead_id": "LEAD-003",
        "first_name": "Michael",
        "last_name": "Chen",
        "email": "m.chen@email.com",
        "phone": "+1-555-0103",
        "source": "chat",
        "product_interest": "credit_card",
        "status": "nurturing",
        "tier": "warm",
        "score": 55,
        "qualifier": "agent_001",
        "assigned_to": None,
        "created_at": "2026-08-17T11:45:00",
        "updated_at": "2026-08-18T16:30:00",
        "last_contact": "2026-08-18T16:30:00",
        "next_follow_up": "2026-08-25T10:00:00",
        "notes": ["Comparing travel rewards cards", "Has existing card with competitor"],
        "demographics": {"age": 30, "income": 85000, "credit_score": 705, "homeowner": False},
        "behavior": {"pages_visited": 8, "calculator_used": True, "application_started": False},
    },
    "LEAD-004": {
        "lead_id": "LEAD-004",
        "first_name": "Emily",
        "last_name": "Davis",
        "email": "emily.d@email.com",
        "phone": "+1-555-0104",
        "source": "webinar",
        "product_interest": "investment",
        "status": "new",
        "tier": None,
        "score": 45,
        "qualifier": None,
        "assigned_to": None,
        "created_at": "2026-08-19T16:00:00",
        "updated_at": "2026-08-19T16:00:00",
        "last_contact": None,
        "next_follow_up": "2026-08-21T10:00:00",
        "notes": ["Attended retirement planning webinar", "Age 25, first-time investor"],
        "demographics": {"age": 25, "income": 55000, "credit_score": 680, "homeowner": False},
        "behavior": {"pages_visited": 2, "calculator_used": False, "application_started": False},
    },
}


async def create_lead(
    lead_id: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    source: str,
    product_interest: str,
    demographics: dict | None = None,
    behavior: dict | None = None,
) -> dict[str, Any]:
    """Create a new lead."""
    now = datetime.utcnow().isoformat()
    lead = {
        "lead_id": lead_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "source": source,
        "product_interest": product_interest,
        "status": "new",
        "tier": None,
        "score": 0,
        "qualifier": None,
        "assigned_to": None,
        "created_at": now,
        "updated_at": now,
        "last_contact": None,
        "next_follow_up": None,
        "notes": [],
        "demographics": demographics or {},
        "behavior": behavior or {},
    }
    LEAD_DB[lead_id] = lead

    return {
        "lead_id": lead_id,
        "name": f"{first_name} {last_name}",
        "source": source,
        "message": f"Lead {lead_id} created successfully.",
    }


async def get_lead(lead_id: str) -> dict[str, Any]:
    """Get lead details."""
    lead = LEAD_DB.get(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}
    return lead


async def update_lead(
    lead_id: str,
    status: str | None = None,
    tier: str | None = None,
    score: int | None = None,
    assigned_to: str | None = None,
    next_follow_up: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Update a lead."""
    lead = LEAD_DB.get(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    if status:
        lead["status"] = status
    if tier:
        lead["tier"] = tier
    if score is not None:
        lead["score"] = score
    if assigned_to:
        lead["assigned_to"] = assigned_to
    if next_follow_up:
        lead["next_follow_up"] = next_follow_up
    if notes:
        lead["notes"].append(notes)
    lead["updated_at"] = datetime.utcnow().isoformat()

    return {"lead_id": lead_id, "message": f"Lead {lead_id} updated."}


async def search_leads(
    status: str | None = None,
    tier: str | None = None,
    source: str | None = None,
    product_interest: str | None = None,
    min_score: int | None = None,
    assigned_to: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search leads by criteria."""
    results = list(LEAD_DB.values())

    if status:
        results = [l for l in results if l["status"] == status]
    if tier:
        results = [l for l in results if l.get("tier") == tier]
    if source:
        results = [l for l in results if l["source"] == source]
    if product_interest:
        results = [l for l in results if l["product_interest"] == product_interest]
    if min_score is not None:
        results = [l for l in results if l.get("score", 0) >= min_score]
    if assigned_to:
        results = [l for l in results if l.get("assigned_to") == assigned_to]

    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "total_leads": len(results),
        "leads": results[:limit],
    }


async def convert_lead(lead_id: str, revenue: float = 0) -> dict[str, Any]:
    """Convert a lead to a customer."""
    lead = LEAD_DB.get(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    lead["status"] = "converted"
    lead["converted_at"] = datetime.utcnow().isoformat()
    lead["revenue"] = revenue

    return {
        "lead_id": lead_id,
        "status": "converted",
        "revenue": revenue,
        "message": f"Lead {lead_id} converted to customer.",
    }


async def close_lead(lead_id: str, reason: str) -> dict[str, Any]:
    """Close a lead as lost."""
    lead = LEAD_DB.get(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    lead["status"] = "lost"
    lead["lost_reason"] = reason
    lead["closed_at"] = datetime.utcnow().isoformat()

    return {"lead_id": lead_id, "status": "lost", "reason": reason}


async def get_lead_pipeline() -> dict[str, Any]:
    """Get lead pipeline summary."""
    leads = list(LEAD_DB.values())
    return {
        "total_leads": len(leads),
        "by_status": {
            "new": sum(1 for l in leads if l["status"] == "new"),
            "qualified": sum(1 for l in leads if l["status"] == "qualified"),
            "nurturing": sum(1 for l in leads if l["status"] == "nurturing"),
            "converted": sum(1 for l in leads if l["status"] == "converted"),
            "lost": sum(1 for l in leads if l["status"] == "lost"),
        },
        "by_tier": {
            "hot": sum(1 for l in leads if l.get("tier") == "hot"),
            "warm": sum(1 for l in leads if l.get("tier") == "warm"),
            "cool": sum(1 for l in leads if l.get("tier") == "cool"),
            "cold": sum(1 for l in leads if l.get("tier") == "cold"),
        },
        "by_source": {
            src: sum(1 for l in leads if l["source"] == src)
            for src in set(l["source"] for l in leads)
        },
        "avg_score": round(sum(l.get("score", 0) for l in leads) / max(len(leads), 1), 1),
    }


async def get_overdue_follow_ups() -> dict[str, Any]:
    """Get leads with overdue follow-ups."""
    now = datetime.utcnow()
    overdue = []
    for lead in LEAD_DB.values():
        next_fu = lead.get("next_follow_up")
        if next_fu:
            fu_time = datetime.fromisoformat(next_fu)
            if fu_time < now:
                overdue.append(lead)

    overdue.sort(key=lambda x: x.get("next_follow_up", ""))

    return {
        "total_overdue": len(overdue),
        "leads": overdue,
    }
