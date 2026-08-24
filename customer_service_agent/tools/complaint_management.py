"""
Complaint Management Tool — MCP tool stub.

Logs, categorizes, prioritizes, and routes customer complaints.
Suggests resolution steps based on similar past complaints.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

_complaints: dict[str, dict] = {}

COMPLAINT_CATEGORIES = {
    "billing": "Billing errors, incorrect charges, statement issues",
    "service_quality": "Poor service, long wait times, rude staff",
    "fraud": "Fraudulent activity, unauthorized access",
    "product": "Product issues, missing features, broken functionality",
    "technology": "App crashes, login issues, website problems",
    "fees": "Hidden fees, unexpected charges, fee disputes",
    "communication": "Unwanted marketing, missing notifications, unclear messaging",
    "accessibility": "ADA compliance, language barriers, disability access",
}


async def log_complaint(
    customer_id: str,
    description: str,
    channel: str = "chat",
    category_hint: str | None = None,
) -> dict:
    """Log a new customer complaint and auto-categorize."""
    logger.info("Logging complaint from customer %s via %s", customer_id, channel)

    complaint_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"

    # Auto-categorize based on description keywords
    if not category_hint:
        desc_lower = description.lower()
        if any(w in desc_lower for w in ["charge", "bill", "overcharged", "incorrect amount"]):
            category = "billing"
        elif any(w in desc_lower for w in ["rude", "wait", "service", "unhelpful"]):
            category = "service_quality"
        elif any(w in desc_lower for w in ["fraud", "stolen", "unauthorized", "hacked"]):
            category = "fraud"
        elif any(w in desc_lower for w in ["app", "website", "login", "crash", "error"]):
            category = "technology"
        elif any(w in desc_lower for w in ["fee", "hidden", "unexpected charge"]):
            category = "fees"
        elif any(w in desc_lower for w in ["spam", "email", "notification", "marketing"]):
            category = "communication"
        else:
            category = "product"
    else:
        category = category_hint

    # Determine priority
    if category == "fraud":
        priority = "critical"
        escalation_required = True
    elif category in ("billing", "fees") and any(w in description.lower() for w in ["large", "significant", "thousands"]):
        priority = "high"
        escalation_required = True
    elif category in ("service_quality", "communication"):
        priority = "medium"
        escalation_required = False
    else:
        priority = "low"
        escalation_required = False

    complaint = {
        "complaint_id": complaint_id,
        "customer_id": customer_id,
        "description": description,
        "category": category,
        "category_description": COMPLAINT_CATEGORIES.get(category, "Other"),
        "priority": priority,
        "channel": channel,
        "status": "open",
        "escalation_required": escalation_required,
        "assigned_to": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    _complaints[complaint_id] = complaint
    logger.info("Complaint logged: %s (category: %s, priority: %s)", complaint_id, category, priority)
    return complaint


async def get_complaint(complaint_id: str) -> dict:
    """Get complaint details."""
    complaint = _complaints.get(complaint_id)
    if not complaint:
        return {"error": f"Complaint {complaint_id} not found"}
    return complaint


async def update_complaint(
    complaint_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    resolution: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update complaint status or assignment."""
    complaint = _complaints.get(complaint_id)
    if not complaint:
        return {"error": f"Complaint {complaint_id} not found"}
    if status:
        complaint["status"] = status
    if assigned_to:
        complaint["assigned_to"] = assigned_to
    if resolution:
        complaint["resolution"] = resolution
        complaint["resolved_at"] = datetime.utcnow().isoformat()
    if notes:
        complaint["notes"] = notes
    complaint["updated_at"] = datetime.utcnow().isoformat()
    return complaint


async def get_complaint_categories() -> dict:
    """Get available complaint categories."""
    return {"categories": [{"type": k, "description": v} for k, v in COMPLAINT_CATEGORIES.items()]}
