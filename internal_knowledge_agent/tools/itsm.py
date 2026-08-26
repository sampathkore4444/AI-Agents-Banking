"""
ITSM Tool — MCP tool stub.

In production this would call ServiceNow, BMC Remedy, or similar
ITSM system to query known issues, check system status, and
retrieve troubleshooting guides.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Simulated known issues
_KNOWN_ISSUES = {
    "ISS-001": {
        "id": "ISS-001", "title": "Outlook calendar sync delay",
        "status": "investigating", "severity": "medium",
        "affected_systems": ["Outlook", "Exchange"],
        "workaround": "Restart Outlook, wait 5 minutes for sync",
        "estimated_resolution": "2024-09-20",
        "update_count": 3,
    },
    "ISS-002": {
        "id": "ISS-002", "title": "VPN intermittent disconnections",
        "status": "identified", "severity": "high",
        "affected_systems": ["VPN", "Remote Access"],
        "workaround": "Use alternate VPN server (US-WEST-1)",
        "estimated_resolution": "2024-09-18",
        "update_count": 5,
    },
}

# Simulated system status
_SYSTEM_STATUS = {
    "Core Banking System": {"status": "operational", "uptime": "99.98%"},
    "Online Banking Portal": {"status": "operational", "uptime": "99.99%"},
    "Mobile App": {"status": "operational", "uptime": "99.97%"},
    "Email (Exchange)": {"status": "degraded", "uptime": "99.50%", "note": "Calendar sync delays"},
    "VPN": {"status": "degraded", "uptime": "98.90%", "note": "Intermittent disconnections"},
    "ATM Network": {"status": "operational", "uptime": "99.99%"},
    "Wire Transfer System": {"status": "operational", "uptime": "99.99%"},
}


async def check_system_status(system_name: str | None = None) -> dict:
    """
    Check the current status of banking systems.
    """
    if system_name:
        for name, status in _SYSTEM_STATUS.items():
            if system_name.lower() in name.lower():
                return {"system": name, **status}
        return {"error": f"System not found: {system_name}"}

    return {
        "systems": _SYSTEM_STATUS,
        "checked_at": datetime.utcnow().isoformat(),
    }


async def search_known_issues(
    query: str,
    severity: str | None = None,
) -> dict:
    """
    Search known issues and workarounds.
    """
    results = []
    query_lower = query.lower()

    for issue in _KNOWN_ISSUES.values():
        if severity and issue["severity"] != severity:
            continue
        if query_lower in issue["title"].lower() or any(query_lower in s.lower() for s in issue["affected_systems"]):
            results.append(issue)

    return {
        "query": query,
        "results_count": len(results),
        "issues": results,
    }


async def get_troubleshooting_guide(issue_id: str) -> dict:
    """Get detailed troubleshooting steps for a known issue."""
    issue = _KNOWN_ISSUES.get(issue_id)
    if not issue:
        return {"error": f"Issue {issue_id} not found"}

    # Simulated troubleshooting steps
    steps = {
        "ISS-001": [
            "Step 1: Close Outlook completely (check Task Manager for lingering processes)",
            "Step 2: Clear Outlook cache: File > Options > Mail > Store > Clear",
            "Step 3: Restart computer",
            "Step 4: Open Outlook and wait 5 minutes for initial sync",
            "Step 5: If issue persists, recreate Outlook profile (IT Help Desk can assist)",
        ],
        "ISS-002": [
            "Step 1: Disconnect from current VPN server",
            "Step 2: Switch to alternate server: US-WEST-1",
            "Step 3: If still disconnecting, clear VPN client cache",
            "Step 4: Restart VPN client",
            "Step 5: If issue persists, submit ticket to IT Support (Category: VPN)",
        ],
    }

    return {
        "issue": issue,
        "troubleshooting_steps": steps.get(issue_id, ["No specific steps available. Contact IT Help Desk."]),
    }
