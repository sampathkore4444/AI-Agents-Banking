"""
Internal Knowledge Base Agent — MCP Server.

Exposes tools via the Model Context Protocol for searching internal banking
knowledge, managing documents, creating support tickets, querying HR/IT systems,
and sending notifications.

Covers use case 8.1: Internal Knowledge Base Agent (Bank-wide).
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from rag_pipeline import RAGPipeline
from tools.document_management import get_document, get_document_by_version, list_documents, search_documents
from tools.hr_system import get_benefits_info, get_leave_balance, get_org_chart, lookup_employee
from tools.itsm import check_system_status, get_troubleshooting_guide, search_known_issues
from tools.notifications import send_notification
from tools.ticketing_system import create_ticket, get_ticket, get_ticket_stats, search_tickets, update_ticket

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Create MCP server ────────────────────────────────────────────
mcp = FastMCP(
    "Internal Knowledge Base Agent",
    instructions=(
        "Internal Knowledge Base Agent for banking. Use these tools to help employees "
        "find information about bank products, standard operating procedures, IT help, "
        "HR policies, compliance training, process guides, and regulatory updates. "
        "Search the knowledge base first, then use specific tools for tickets, HR, or IT."
    ),
)

rag = RAGPipeline()


# ══════════════════════════════════════════════════════════════════
#  RAG / KNOWLEDGE TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def knowledge_search(query: str, collection: str = "all", top_k: int = 5) -> dict[str, Any]:
    """
    Search the internal knowledge base for products, SOPs, IT help, HR policies,
    compliance training, process guides, regulatory updates, and FAQ.

    Args:
        query: Natural language query (e.g., "How do I reset my password?")
        collection: Collection to search (default: all)
        top_k: Number of results (default: 5)

    Returns:
        Retrieved chunks with scores, sources, and assembled context.
    """
    logger.info("Knowledge search: query='%s', collection=%s", query, collection)
    collections = None if collection == "all" else [collection]
    result = rag.query(query, top_k=top_k, collections=collections)
    return {
        "query": result.query_rewrite,
        "results_count": len(result.chunks),
        "chunks": [
            {"text": c.text, "score": round(c.score, 3), "collection": c.collection, "metadata": c.metadata}
            for c in result.chunks
        ],
        "assembled_context": result.assembled_context,
    }


# ══════════════════════════════════════════════════════════════════
#  DOCUMENT MANAGEMENT TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def search_internal_documents(query: str, category: str | None = None, max_results: int = 10) -> dict[str, Any]:
    """
    Search internal documents by keyword or phrase.

    Args:
        query: Search query
        category: Optional filter (operations, compliance, it, hr)
        max_results: Maximum results (default: 10)

    Returns:
        Matching documents with metadata.
    """
    return await search_documents(query, category, max_results)


@mcp.tool()
async def get_internal_document(document_id: str) -> dict[str, Any]:
    """
    Retrieve a specific internal document by ID.

    Args:
        document_id: Document ID (e.g., DOC-001)

    Returns:
        Full document details and content.
    """
    return await get_document(document_id)


@mcp.tool()
async def list_internal_documents(category: str | None = None, status: str | None = None) -> dict[str, Any]:
    """
    List all internal documents with optional filters.

    Args:
        category: Filter by category
        status: Filter by status (current, archived, draft)

    Returns:
        List of documents.
    """
    return await list_documents(category, status)


# ══════════════════════════════════════════════════════════════════
#  TICKETING TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def create_support_ticket(title: str, description: str, category: str, priority: str = "medium", employee_id: str = "") -> dict[str, Any]:
    """
    Create a new support ticket for IT, HR, or facilities issues.

    Args:
        title: Brief description of the issue
        description: Detailed description
        category: Category (IT Support, Hardware, HR, Facilities, Security)
        priority: Priority level (low, medium, high, critical)
        employee_id: Employee ID of the requester

    Returns:
        Created ticket details.
    """
    return await create_ticket(title, description, category, priority, employee_id)


@mcp.tool()
async def search_support_tickets(query: str, status: str | None = None, category: str | None = None) -> dict[str, Any]:
    """
    Search support tickets by keyword or filters.

    Args:
        query: Search query
        status: Filter by status (open, in_progress, closed)
        category: Filter by category

    Returns:
        Matching tickets.
    """
    return await search_tickets(query, status, category)


@mcp.tool()
async def get_ticket_details(ticket_id: str) -> dict[str, Any]:
    """
    Get details for a specific support ticket.

    Args:
        ticket_id: Ticket ID (e.g., TKT-001)

    Returns:
        Full ticket details.
    """
    return await get_ticket(ticket_id)


@mcp.tool()
async def update_support_ticket(ticket_id: str, status: str | None = None, priority: str | None = None, assignee: str | None = None, notes: str | None = None) -> dict[str, Any]:
    """
    Update a support ticket's status, priority, or assignment.

    Args:
        ticket_id: Ticket ID to update
        status: New status (open, in_progress, closed)
        priority: New priority level
        assignee: New assignee
        notes: Additional notes

    Returns:
        Updated ticket details.
    """
    return await update_ticket(ticket_id, status, priority, assignee, notes)


@mcp.tool()
async def get_ticket_statistics() -> dict[str, Any]:
    """
    Get current ticket statistics for the support team.

    Returns:
        Open, in-progress, and closed ticket counts.
    """
    return await get_ticket_stats()


# ══════════════════════════════════════════════════════════════════
#  HR SYSTEM TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def lookup_employee_info(identifier: str) -> dict[str, Any]:
    """
    Look up an employee by ID, name, or email.

    Args:
        identifier: Employee ID, name, or email

    Returns:
        Employee details (department, position, hire date, location).
    """
    return await lookup_employee(identifier)


@mcp.tool()
async def get_employee_leave_balance(employee_id: str) -> dict[str, Any]:
    """
    Get an employee's current leave balances (annual, sick, personal).

    Args:
        employee_id: Employee ID (e.g., EMP-1234)

    Returns:
        Leave balance breakdown.
    """
    return await get_leave_balance(employee_id)


@mcp.tool()
async def get_employee_benefits(employee_id: str) -> dict[str, Any]:
    """
    Get an employee's benefits enrollment information.

    Args:
        employee_id: Employee ID

    Returns:
        Benefits details (health, dental, 401k, etc.).
    """
    return await get_benefits_info(employee_id)


@mcp.tool()
async def get_organization_chart(department: str | None = None) -> dict[str, Any]:
    """
    Get organizational chart information.

    Args:
        department: Optional department filter

    Returns:
        Org chart with departments and employees.
    """
    return await get_org_chart(department)


# ══════════════════════════════════════════════════════════════════
#  ITSM TOOLS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def check_system_status(system_name: str | None = None) -> dict[str, Any]:
    """
    Check current status of banking systems (online banking, VPN, email, etc.).

    Args:
        system_name: Optional system name filter

    Returns:
        System status and uptime information.
    """
    return await check_system_status(system_name)


@mcp.tool()
async def search_known_issues(query: str, severity: str | None = None) -> dict[str, Any]:
    """
    Search known IT issues and workarounds.

    Args:
        query: Search query (symptom, system name)
        severity: Filter by severity (low, medium, high, critical)

    Returns:
        Matching known issues with workarounds.
    """
    return await search_known_issues(query, severity)


@mcp.tool()
async def get_troubleshooting_steps(issue_id: str) -> dict[str, Any]:
    """
    Get detailed troubleshooting steps for a known IT issue.

    Args:
        issue_id: Issue ID (e.g., ISS-001)

    Returns:
        Step-by-step troubleshooting guide.
    """
    return await get_troubleshooting_guide(issue_id)


# ══════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════


@mcp.tool()
async def send_employee_notification(recipient_id: str, channel: str, template_id: str, variables: dict | None = None) -> dict[str, Any]:
    """
    Send an internal notification to an employee (email, Slack, Teams).

    Args:
        recipient_id: Employee ID or email
        channel: Delivery channel (email, slack, teams)
        template_id: Template to use
        variables: Template variables

    Returns:
        Notification status.
    """
    return await send_notification(recipient_id, channel, template_id, variables)


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("Starting Internal Knowledge Base Agent MCP Server...")
    mcp.run()
