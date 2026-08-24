"""
CRM Tool — Customer relationship management and interaction tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
INTERACTION_DB: list[dict] = []
LEAD_DB: dict[str, dict] = {}


async def log_interaction(
    customer_id: str,
    interaction_type: str,
    channel: str,
    summary: str,
    outcome: str | None = None,
    next_action: str | None = None,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Log a customer interaction."""
    interaction = {
        "interaction_id": f"INT-{int(datetime.utcnow().timestamp())}",
        "customer_id": customer_id,
        "type": interaction_type,
        "channel": channel,
        "summary": summary,
        "outcome": outcome,
        "next_action": next_action,
        "agent_id": agent_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    INTERACTION_DB.append(interaction)

    return {
        "interaction_id": interaction["interaction_id"],
        "customer_id": customer_id,
        "message": "Interaction logged successfully.",
    }


async def get_customer_interactions(
    customer_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    """Get interaction history for a customer."""
    interactions = [i for i in INTERACTION_DB if i["customer_id"] == customer_id]
    interactions.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "customer_id": customer_id,
        "total_interactions": len(interactions),
        "interactions": interactions[:limit],
    }


async def create_lead(
    lead_id: str,
    customer_id: str,
    product_id: str,
    source: str,
    priority: str = "medium",
    notes: str | None = None,
) -> dict[str, Any]:
    """Create a sales lead."""
    lead = {
        "lead_id": lead_id,
        "customer_id": customer_id,
        "product_id": product_id,
        "source": source,
        "priority": priority,
        "status": "open",
        "notes": notes,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    LEAD_DB[lead_id] = lead

    return {
        "lead_id": lead_id,
        "customer_id": customer_id,
        "product_id": product_id,
        "message": f"Lead {lead_id} created.",
    }


async def update_lead(
    lead_id: str,
    status: str | None = None,
    priority: str | None = None,
    notes: str | None = None,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Update a lead."""
    lead = LEAD_DB.get(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    if status:
        lead["status"] = status
    if priority:
        lead["priority"] = priority
    if notes:
        lead["notes"] = notes
    if assigned_to:
        lead["assigned_to"] = assigned_to
    lead["updated_at"] = datetime.utcnow().isoformat()

    return {"lead_id": lead_id, "message": f"Lead {lead_id} updated."}


async def get_lead(lead_id: str) -> dict[str, Any]:
    """Get lead details."""
    lead = LEAD_DB.get(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}
    return lead


async def get_leads(
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Get all leads, optionally filtered."""
    leads = list(LEAD_DB.values())

    if status:
        leads = [l for l in leads if l["status"] == status]
    if priority:
        leads = [l for l in leads if l["priority"] == priority]
    if assigned_to:
        leads = [l for l in leads if l.get("assigned_to") == assigned_to]

    return {
        "total_leads": len(leads),
        "open": sum(1 for l in leads if l["status"] == "open"),
        "converted": sum(1 for l in leads if l["status"] == "converted"),
        "lost": sum(1 for l in leads if l["status"] == "lost"),
        "leads": leads,
    }


async def convert_lead(lead_id: str, revenue: float = 0) -> dict[str, Any]:
    """Convert a lead to a customer (closed-won)."""
    lead = LEAD_DB.get(lead_id)
    if not lead:
        return {"error": f"Lead {lead_id} not found"}

    lead["status"] = "converted"
    lead["revenue"] = revenue
    lead["converted_at"] = datetime.utcnow().isoformat()

    return {
        "lead_id": lead_id,
        "status": "converted",
        "revenue": revenue,
        "message": f"Lead {lead_id} converted. Revenue: ${revenue:.2f}",
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


async def get_crm_stats() -> dict[str, Any]:
    """Get CRM statistics."""
    leads = list(LEAD_DB.values())
    interactions = INTERACTION_DB

    return {
        "total_leads": len(leads),
        "open_leads": sum(1 for l in leads if l["status"] == "open"),
        "converted_leads": sum(1 for l in leads if l["status"] == "converted"),
        "conversion_rate": f"{(sum(1 for l in leads if l['status'] == 'converted') / max(len(leads), 1) * 100):.1f}%",
        "total_revenue": sum(l.get("revenue", 0) for l in leads),
        "total_interactions": len(interactions),
        "interactions_today": sum(1 for i in interactions if i.get("timestamp", "").startswith(datetime.utcnow().strftime("%Y-%m-%d"))),
    }


async def get_pending_follow_ups() -> dict[str, Any]:
    """Get leads requiring follow-up."""
    pending = [l for l in LEAD_DB.values() if l["status"] == "open" and l.get("next_action")]
    pending.sort(key=lambda x: x.get("updated_at", ""))

    return {
        "total_pending": len(pending),
        "leads": pending,
    }
