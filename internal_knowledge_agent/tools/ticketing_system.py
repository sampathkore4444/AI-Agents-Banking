"""
Ticketing System Tool — MCP tool stub.

In production this would call ServiceNow, Jira, Zendesk, or similar
ticketing system to create, search, and update support tickets.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Simulated ticket store
_tickets: dict[str, dict] = {
    "TKT-001": {
        "id": "TKT-001", "title": "Cannot access VPN", "category": "IT Support",
        "status": "open", "priority": "medium", "assignee": "IT Help Desk",
        "created_at": "2024-09-15T10:30:00", "employee_id": "EMP-1234",
        "description": "Employee unable to connect to VPN after Windows update",
    },
    "TKT-002": {
        "id": "TKT-002", "title": "New laptop request", "category": "Hardware",
        "status": "in_progress", "priority": "low", "assignee": "IT Procurement",
        "created_at": "2024-09-14T14:00:00", "employee_id": "EMP-5678",
        "description": "Requesting replacement laptop due to hardware failure",
    },
}


async def create_ticket(
    title: str,
    description: str,
    category: str,
    priority: str = "medium",
    employee_id: str = "",
) -> dict:
    """
    Create a new support ticket in the ticketing system.
    """
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "status": "open",
        "assignee": "Unassigned",
        "employee_id": employee_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    _tickets[ticket_id] = ticket

    logger.info("Ticket created: %s", ticket_id)
    return ticket


async def search_tickets(
    query: str,
    status: str | None = None,
    category: str | None = None,
    max_results: int = 10,
) -> dict:
    """
    Search tickets by keyword or filters.
    """
    results = []
    query_lower = query.lower()

    for ticket in _tickets.values():
        if status and ticket["status"] != status:
            continue
        if category and ticket["category"] != category:
            continue
        if query_lower in ticket["title"].lower() or query_lower in ticket["description"].lower():
            results.append(ticket)

    return {
        "query": query,
        "results_count": len(results),
        "tickets": results[:max_results],
    }


async def get_ticket(ticket_id: str) -> dict:
    """Retrieve a ticket by its ID."""
    ticket = _tickets.get(ticket_id)
    if not ticket:
        return {"error": f"Ticket {ticket_id} not found"}
    return ticket


async def update_ticket(
    ticket_id: str,
    status: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update a ticket's status, priority, or assignment."""
    ticket = _tickets.get(ticket_id)
    if not ticket:
        return {"error": f"Ticket {ticket_id} not found"}

    if status:
        ticket["status"] = status
    if priority:
        ticket["priority"] = priority
    if assignee:
        ticket["assignee"] = assignee
    if notes:
        ticket["notes"] = notes
    ticket["updated_at"] = datetime.utcnow().isoformat()

    logger.info("Ticket %s updated", ticket_id)
    return ticket


async def get_ticket_stats() -> dict:
    """Get ticket statistics for the support team."""
    open_count = sum(1 for t in _tickets.values() if t["status"] == "open")
    in_progress_count = sum(1 for t in _tickets.values() if t["status"] == "in_progress")
    closed_count = sum(1 for t in _tickets.values() if t["status"] == "closed")

    return {
        "total_tickets": len(_tickets),
        "open": open_count,
        "in_progress": in_progress_count,
        "closed": closed_count,
    }
