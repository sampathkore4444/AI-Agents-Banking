"""
Account Takeover Detection Tool — Login monitoring and credential protection.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
LOGIN_DB: dict[str, list[dict]] = {}
ACCOUNT_SECURITY: dict[str, dict] = {}


async def monitor_login(
    customer_id: str,
    ip_address: str,
    device_id: str,
    user_agent: str,
    geo_location: dict | None = None,
) -> dict[str, Any]:
    """Monitor login attempt for account takeover indicators."""
    now = datetime.utcnow()

    if customer_id not in LOGIN_DB:
        LOGIN_DB[customer_id] = []

    logins = LOGIN_DB[customer_id]
    recent_logins = [l for l in logins if (now - datetime.fromisoformat(l["timestamp"])).total_seconds() < 86400]

    # Check for ATO indicators
    indicators: list[dict] = []
    risk_score = 0

    # 1. New device
    known_devices = [l["device_id"] for l in logins]
    if device_id not in known_devices:
        indicators.append({"type": "new_device", "severity": "medium", "detail": f"Device {device_id} not previously used"})
        risk_score += 20

    # 2. New IP / location
    known_ips = [l["ip_address"] for l in logins]
    if ip_address not in known_ips:
        indicators.append({"type": "new_ip", "severity": "medium", "detail": f"IP {ip_address} not previously used"})
        risk_score += 15

    # 3. Impossible travel
    if recent_logins and geo_location:
        last_login = recent_logins[-1]
        last_geo = last_login.get("geo_location", {})
        if last_geo and last_geo.get("lat") and geo_location.get("lat"):
            # Simplified distance check
            lat_diff = abs(last_geo["lat"] - geo_location.get("lat", 0))
            lon_diff = abs(last_geo.get("lon", 0) - geo_location.get("lon", 0))
            time_diff_hours = (now - datetime.fromisoformat(last_login["timestamp"])).total_seconds() / 3600
            estimated_distance_km = ((lat_diff + lon_diff) * 111)  # rough approx
            if time_diff_hours > 0 and estimated_distance_km / time_diff_hours > 800:
                indicators.append({"type": "impossible_travel", "severity": "critical", "detail": f"Travel speed {estimated_distance_km/time_diff_hours:.0f} km/h — physically impossible"})
                risk_score += 40

    # 4. Multiple failed attempts
    failed_recent = [l for l in recent_logins if not l.get("success", True)]
    if len(failed_recent) >= 3:
        indicators.append({"type": "multiple_failures", "severity": "high", "detail": f"{len(failed_recent)} failed attempts in last 24 hours"})
        risk_score += 30

    # 5. Login at unusual time
    if 2 <= now.hour <= 5:
        indicators.append({"type": "unusual_time", "severity": "low", "detail": f"Login at {now.hour}:00 (unusual hours)"})
        risk_score += 10

    # 6. VPN/Proxy detected
    if geo_location and geo_location.get("is_vpn"):
        indicators.append({"type": "vpn_detected", "severity": "medium", "detail": "Login from VPN/proxy"})
        risk_score += 15

    risk_score = min(risk_score, 100)

    # Determine action
    if risk_score >= 70:
        action = "block_and_notify"
        risk_level = "critical"
    elif risk_score >= 40:
        action = "step_up_auth"
        risk_level = "high"
    elif risk_score >= 20:
        action = "monitor"
        risk_level = "medium"
    else:
        action = "allow"
        risk_level = "low"

    # Record login
    login_record = {
        "customer_id": customer_id,
        "ip_address": ip_address,
        "device_id": device_id,
        "user_agent": user_agent,
        "geo_location": geo_location,
        "timestamp": now.isoformat(),
        "success": action != "block_and_notify",
        "risk_score": risk_score,
        "indicators": [i["type"] for i in indicators],
    }
    LOGIN_DB[customer_id].append(login_record)

    return {
        "customer_id": customer_id,
        "login_analysis": {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "action": action,
            "indicators": indicators,
        },
        "message": f"Login {'blocked' if action == 'block_and_notify' else 'flagged' if action != 'allow' else 'allowed'} — Risk score: {risk_score}/100",
    }


async def get_login_history(
    customer_id: str,
    hours: int = 24,
    limit: int = 50,
) -> dict[str, Any]:
    """Get login history for a customer."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    logins = [l for l in LOGIN_DB.get(customer_id, []) if l["timestamp"] >= cutoff]
    logins.sort(key=lambda x: x["timestamp"], reverse=True)
    return {
        "customer_id": customer_id,
        "time_range_hours": hours,
        "total_logins": len(logins),
        "failed_logins": sum(1 for l in logins if not l.get("success", True)),
        "high_risk_logins": sum(1 for l in logins if l.get("risk_score", 0) >= 40),
        "logins": logins[:limit],
    }


async def revoke_sessions(customer_id: str, reason: str) -> dict[str, Any]:
    """Revoke all active sessions for a customer."""
    sessions_revoked = len(LOGIN_DB.get(customer_id, []))
    LOGIN_DB[customer_id] = []
    return {
        "customer_id": customer_id,
        "sessions_revoked": sessions_revoked,
        "reason": reason,
        "message": f"All {sessions_revoked} sessions revoked for customer {customer_id}.",
    }


async def update_security_settings(
    customer_id: str,
    mfa_enabled: bool | None = None,
    trusted_devices: list[str] | None = None,
    login_notifications: bool | None = None,
) -> dict[str, Any]:
    """Update account security settings."""
    if customer_id not in ACCOUNT_SECURITY:
        ACCOUNT_SECURITY[customer_id] = {
            "mfa_enabled": True,
            "trusted_devices": [],
            "login_notifications": True,
        }

    settings = ACCOUNT_SECURITY[customer_id]
    if mfa_enabled is not None:
        settings["mfa_enabled"] = mfa_enabled
    if trusted_devices is not None:
        settings["trusted_devices"] = trusted_devices
    if login_notifications is not None:
        settings["login_notifications"] = login_notifications

    return {
        "customer_id": customer_id,
        "security_settings": settings,
        "message": "Security settings updated successfully.",
    }


async def block_ip(ip_address: str, reason: str) -> dict[str, Any]:
    """Block an IP address."""
    return {
        "ip_address": ip_address,
        "status": "blocked",
        "reason": reason,
        "message": f"IP {ip_address} has been blocked.",
    }
