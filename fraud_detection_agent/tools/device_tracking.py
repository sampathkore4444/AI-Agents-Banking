"""
Device Tracking Tool — Device fingerprinting and anomaly detection.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import Any


# ── In-memory device store ────────────────────────────────────────
DEVICE_DB: dict[str, dict] = {}
ACCOUNT_DEVICES: dict[str, list[str]] = {}


async def register_device(
    customer_id: str,
    device_id: str,
    device_type: str,
    os: str,
    browser: str,
    ip_address: str,
    screen_resolution: str | None = None,
    language: str | None = None,
    timezone: str | None = None,
) -> dict[str, Any]:
    """Register a device fingerprint for a customer."""
    now = datetime.utcnow()

    device = {
        "device_id": device_id,
        "customer_id": customer_id,
        "device_type": device_type,
        "os": os,
        "browser": browser,
        "ip_address": ip_address,
        "screen_resolution": screen_resolution,
        "language": language,
        "timezone": timezone,
        "first_seen": now.isoformat(),
        "last_seen": now.isoformat(),
        "trust_score": 50,  # Start at neutral
        "is_known": False,
        "flags": [],
    }

    # Check if known device
    if customer_id in ACCOUNT_DEVICES and device_id in ACCOUNT_DEVICES.get(customer_id, []):
        device["is_known"] = True
        device["trust_score"] = 80
        existing = DEVICE_DB.get(device_id, {})
        if existing:
            device["first_seen"] = existing.get("first_seen", now.isoformat())
            # Check for anomalies
            if existing.get("os") != os:
                device["flags"].append("OS changed")
                device["trust_score"] -= 20
            if existing.get("browser") != browser:
                device["flags"].append("Browser changed")
                device["trust_score"] -= 10
    else:
        # New device
        device["flags"].append("New device")
        if customer_id not in ACCOUNT_DEVICES:
            ACCOUNT_DEVICES[customer_id] = []
        ACCOUNT_DEVICES[customer_id].append(device_id)

    DEVICE_DB[device_id] = device

    return {
        "device_id": device_id,
        "customer_id": customer_id,
        "is_known": device["is_known"],
        "trust_score": device["trust_score"],
        "flags": device["flags"],
        "message": f"Device {'recognized' if device['is_known'] else 'registered as new'} — Trust score: {device['trust_score']}/100",
    }


async def check_device(
    customer_id: str,
    device_id: str,
    ip_address: str,
) -> dict[str, Any]:
    """Check device trust and detect anomalies."""
    device = DEVICE_DB.get(device_id)

    if not device:
        return {
            "device_id": device_id,
            "customer_id": customer_id,
            "is_known": False,
            "trust_score": 30,
            "flags": ["Unknown device — never seen before"],
            "risk_level": "high",
            "action": "step_up_auth",
            "message": "Unknown device detected. Step-up authentication recommended.",
        }

    # Check IP change
    if device.get("ip_address") != ip_address:
        device["trust_score"] -= 15
        device["flags"].append(f"IP changed from {device.get('ip_address')} to {ip_address}")

    # Check if too old (device hasn't been seen in 90 days)
    last_seen = datetime.fromisoformat(device["last_seen"])
    days_since = (datetime.utcnow() - last_seen).days
    if days_since > 90:
        device["trust_score"] -= 10
        device["flags"].append(f"Device not seen for {days_since} days")

    # Update last seen
    device["last_seen"] = datetime.utcnow().isoformat()
    device["ip_address"] = ip_address

    trust_score = max(0, min(100, device["trust_score"]))

    if trust_score >= 70:
        risk_level = "low"
        action = "allow"
    elif trust_score >= 40:
        risk_level = "medium"
        action = "step_up_auth"
    else:
        risk_level = "high"
        action = "block_and_verify"

    return {
        "device_id": device_id,
        "customer_id": customer_id,
        "is_known": device["is_known"],
        "trust_score": trust_score,
        "flags": device["flags"],
        "risk_level": risk_level,
        "action": action,
        "device_info": {"type": device["device_type"], "os": device["os"], "browser": device["browser"]},
    }


async def get_device_history(customer_id: str) -> dict[str, Any]:
    """Get device history for a customer."""
    device_ids = ACCOUNT_DEVICES.get(customer_id, [])
    devices = [DEVICE_DB.get(did, {}) for did in device_ids if did in DEVICE_DB]
    return {
        "customer_id": customer_id,
        "total_devices": len(devices),
        "devices": devices,
    }


async def flag_device(
    device_id: str,
    flag_type: str,
    reason: str,
) -> dict[str, Any]:
    """Flag a device as suspicious."""
    device = DEVICE_DB.get(device_id)
    if not device:
        return {"error": f"Device {device_id} not found"}

    device["flags"].append(f"[FLAGGED] {flag_type}: {reason}")
    device["trust_score"] = max(0, device["trust_score"] - 30)
    device["flagged_at"] = datetime.utcnow().isoformat()

    return {
        "device_id": device_id,
        "flag_type": flag_type,
        "reason": reason,
        "trust_score": device["trust_score"],
        "message": f"Device flagged as {flag_type}. Trust score reduced to {device['trust_score']}.",
    }


async def block_device(
    device_id: str,
    reason: str,
) -> dict[str, Any]:
    """Block a device completely."""
    device = DEVICE_DB.get(device_id)
    if not device:
        return {"error": f"Device {device_id} not found"}

    device["status"] = "blocked"
    device["trust_score"] = 0
    device["blocked_at"] = datetime.utcnow().isoformat()
    device["block_reason"] = reason
    device["flags"].append(f"[BLOCKED] {reason}")

    return {
        "device_id": device_id,
        "status": "blocked",
        "reason": reason,
        "message": f"Device {device_id} has been blocked. All future transactions from this device will be rejected.",
    }
