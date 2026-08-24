"""
Campaign Management Tool — Manage marketing campaigns and outreach.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── In-memory campaign store ──────────────────────────────────────
CAMPAIGN_DB: dict[str, dict] = {}


async def create_campaign(
    campaign_id: str,
    name: str,
    campaign_type: str,
    target_segment: str,
    offer_id: str | None,
    channels: list[str],
    start_date: str,
    end_date: str,
    budget: float,
) -> dict[str, Any]:
    """Create a new marketing campaign."""
    campaign = {
        "campaign_id": campaign_id,
        "name": name,
        "type": campaign_type,
        "target_segment": target_segment,
        "offer_id": offer_id,
        "channels": channels,
        "start_date": start_date,
        "end_date": end_date,
        "budget": budget,
        "spent": 0,
        "status": "planned",
        "target_audience_size": 0,
        "impressions": 0,
        "clicks": 0,
        "conversions": 0,
        "created_at": datetime.utcnow().isoformat(),
    }
    CAMPAIGN_DB[campaign_id] = campaign

    return {
        "campaign_id": campaign_id,
        "name": name,
        "message": f"Campaign {campaign_id} created successfully.",
    }


async def update_campaign(campaign_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update a campaign."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    campaign.update(updates)
    return {"campaign_id": campaign_id, "message": f"Campaign {campaign_id} updated."}


async def launch_campaign(campaign_id: str) -> dict[str, Any]:
    """Launch a campaign."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    campaign["status"] = "active"
    campaign["launched_at"] = datetime.utcnow().isoformat()

    return {
        "campaign_id": campaign_id,
        "status": "active",
        "message": f"Campaign {campaign_id} launched.",
    }


async def pause_campaign(campaign_id: str, reason: str) -> dict[str, Any]:
    """Pause a campaign."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    campaign["status"] = "paused"
    campaign["pause_reason"] = reason
    return {"campaign_id": campaign_id, "status": "paused", "message": f"Campaign {campaign_id} paused."}


async def close_campaign(campaign_id: str) -> dict[str, Any]:
    """Close a campaign."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    campaign["status"] = "closed"
    campaign["closed_at"] = datetime.utcnow().isoformat()
    return {"campaign_id": campaign_id, "status": "closed", "message": f"Campaign {campaign_id} closed."}


async def get_campaign(campaign_id: str) -> dict[str, Any]:
    """Get campaign details."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}
    return campaign


async def get_campaigns(status: str | None = None) -> dict[str, Any]:
    """Get all campaigns, optionally filtered by status."""
    campaigns = list(CAMPAIGN_DB.values())
    if status:
        campaigns = [c for c in campaigns if c["status"] == status]

    return {
        "total_campaigns": len(campaigns),
        "campaigns": campaigns,
    }


async def record_impression(campaign_id: str, count: int = 1) -> dict[str, Any]:
    """Record campaign impressions."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    campaign["impressions"] = campaign.get("impressions", 0) + count
    return {"campaign_id": campaign_id, "impressions": campaign["impressions"]}


async def record_click(campaign_id: str, count: int = 1) -> dict[str, Any]:
    """Record campaign clicks."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    campaign["clicks"] = campaign.get("clicks", 0) + count
    return {"campaign_id": campaign_id, "clicks": campaign["clicks"]}


async def record_conversion(campaign_id: str, count: int = 1, revenue: float = 0) -> dict[str, Any]:
    """Record campaign conversions."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    campaign["conversions"] = campaign.get("conversions", 0) + count
    campaign["revenue"] = campaign.get("revenue", 0) + revenue
    return {"campaign_id": campaign_id, "conversions": campaign["conversions"], "revenue": campaign.get("revenue", 0)}


async def get_campaign_analytics(campaign_id: str) -> dict[str, Any]:
    """Get campaign performance analytics."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    impressions = campaign.get("impressions", 0)
    clicks = campaign.get("clicks", 0)
    conversions = campaign.get("conversions", 0)
    budget = campaign.get("budget", 0)
    spent = campaign.get("spent", 0)

    return {
        "campaign_id": campaign_id,
        "name": campaign["name"],
        "status": campaign["status"],
        "metrics": {
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "click_through_rate": f"{(clicks/impressions*100):.2f}%" if impressions > 0 else "0%",
            "conversion_rate": f"{(conversions/clicks*100):.2f}%" if clicks > 0 else "0%",
            "cost_per_conversion": f"${(spent/conversions):.2f}" if conversions > 0 else "N/A",
            "budget": budget,
            "spent": spent,
            "remaining_budget": budget - spent,
            "revenue": campaign.get("revenue", 0),
            "roi": f"{((campaign.get('revenue', 0) - spent) / spent * 100):.1f}%" if spent > 0 else "N/A",
        },
    }


async def schedule_outreach(
    campaign_id: str,
    customer_ids: list[str],
    channel: str,
    message_template: str,
    scheduled_date: str,
) -> dict[str, Any]:
    """Schedule outreach for a campaign."""
    campaign = CAMPAIGN_DB.get(campaign_id)
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found"}

    return {
        "campaign_id": campaign_id,
        "customer_count": len(customer_ids),
        "channel": channel,
        "scheduled_date": scheduled_date,
        "message": f"Outreach scheduled for {len(customer_ids)} customers via {channel}.",
    }
