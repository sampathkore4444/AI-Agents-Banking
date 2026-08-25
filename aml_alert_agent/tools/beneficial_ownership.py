"""
Beneficial Ownership — Identification, Verification, Ongoing Monitoring.

Manages:
- Beneficial owner identification (25%+ ownership)
- Verification workflows
- UBO (Ultimate Beneficial Owner) tracing
- Ongoing monitoring and updates
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

# ── In-memory store ───────────────────────────────────────────────
_BENEFICIAL_OWNERS: dict[str, dict] = {}
_ENTITY_BO: dict[str, list[dict]] = {}


async def identify_beneficial_owners(
    entity_id: str,
    entity_name: str,
    entity_jurisdiction: str,
    ownership_structure: list[dict],
) -> dict[str, Any]:
    """Identify beneficial owners of a legal entity."""
    owners: list[dict] = []

    for owner in ownership_structure:
        name = owner.get("name", "")
        ownership_pct = owner.get("ownership_percentage", 0)
        control_type = owner.get("control_type", "ownership")
        is_individual = owner.get("is_individual", True)

        # Identify BO: 25%+ ownership or significant control
        is_beneficial_owner = ownership_pct >= 25 or control_type == "control"

        if is_beneficial_owner:
            bo_id = f"BO-{hashlib.md5(f'{entity_id}{name}'.encode()).hexdigest()[:10].upper()}"
            bo = {
                "bo_id": bo_id,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "name": name,
                "ownership_percentage": ownership_pct,
                "control_type": control_type,
                "is_individual": is_individual,
                "entity_jurisdiction": entity_jurisdiction,
                "status": "identified",
                "identified_at": datetime.utcnow().isoformat(),
                "verification_status": "pending",
            }
            owners.append(bo)
            _BENEFICIAL_OWNERS[bo_id] = bo

    # If no individual met the 25% threshold, identify senior managing official
    if not owners and ownership_structure:
        smo = ownership_structure[0]
        bo_id = f"BO-SMO-{hashlib.md5(entity_id.encode()).hexdigest()[:8].upper()}"
        bo = {
            "bo_id": bo_id,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "name": smo.get("name", "Senior Managing Official"),
            "ownership_percentage": smo.get("ownership_percentage", 0),
            "control_type": "senior_managing_official",
            "is_individual": True,
            "entity_jurisdiction": entity_jurisdiction,
            "status": "identified",
            "identified_at": datetime.utcnow().isoformat(),
            "verification_status": "pending",
            "note": "No individual met 25% ownership threshold — SMO identified",
        }
        owners.append(bo)
        _BENEFICIAL_OWNERS[bo_id] = bo

    _ENTITY_BO[entity_id] = owners

    return {
        "entity_id": entity_id,
        "entity_name": entity_name,
        "beneficial_owners_identified": len(owners),
        "owners": owners,
        "requires_verification": True,
    }


async def verify_beneficial_owner(
    bo_id: str,
    verification_method: str = "documentary",
    documents_provided: list[str] | None = None,
) -> dict[str, Any]:
    """Verify a beneficial owner's identity and ownership."""
    bo = _BENEFICIAL_OWNERS.get(bo_id)
    if not bo:
        return {"error": "Beneficial owner not found"}

    # Simulate verification
    bo["verification_status"] = "verified"
    bo["verification_method"] = verification_method
    bo["documents_provided"] = documents_provided or []
    bo["verified_at"] = datetime.utcnow().isoformat()

    return {
        "bo_id": bo_id,
        "name": bo["name"],
        "verification_status": "verified",
        "verification_method": verification_method,
        "documents_provided": documents_provided or [],
    }


async def trace_ultimate_beneficial_owner(
    entity_id: str,
    chain: list[dict] | None = None,
) -> dict[str, Any]:
    """Trace through ownership chain to find ultimate beneficial owner."""
    if chain is None:
        chain = []

    entity_owners = _ENTITY_BO.get(entity_id, [])
    if not entity_owners:
        return {
            "entity_id": entity_id,
            "ubo_found": False,
            "traversal_chain": chain,
            "reason": "No beneficial owners identified",
        }

    # Find the individual with highest ownership
    individual_owners = [o for o in entity_owners if o.get("is_individual")]
    if individual_owners:
        ubo = max(individual_owners, key=lambda x: x.get("ownership_percentage", 0))
        chain.append({
            "level": len(chain) + 1,
            "entity": entity_id,
            "owner": ubo["name"],
            "ownership_pct": ubo["ownership_percentage"],
            "is_individual": True,
        })
        return {
            "entity_id": entity_id,
            "ubo_found": True,
            "ubo_name": ubo["name"],
            "ubo_ownership_pct": ubo["ownership_percentage"],
            "traversal_chain": chain,
            "total_levels": len(chain),
        }

    # If owner is another entity, recurse
    entity_owners_entities = [o for o in entity_owners if not o.get("is_individual")]
    if entity_owners_entities:
        parent = entity_owners_entities[0]
        chain.append({
            "level": len(chain) + 1,
            "entity": entity_id,
            "owner_entity": parent.get("entity_name", "unknown"),
            "ownership_pct": parent.get("ownership_percentage", 0),
            "is_individual": False,
        })
        return await trace_ultimate_beneficial_owner(parent.get("entity_id", ""), chain)

    return {
        "entity_id": entity_id,
        "ubo_found": False,
        "traversal_chain": chain,
    }


async def update_beneficial_ownership(
    entity_id: str,
    changes: list[dict],
) -> dict[str, Any]:
    """Update beneficial ownership information."""
    current = _ENTITY_BO.get(entity_id, [])
    updates: list[dict] = []

    for change in changes:
        action = change.get("action", "add")
        if action == "add":
            bo_id = f"BO-{hashlib.md5(f'{entity_id}{change.get('name', '')}'.encode()).hexdigest()[:10].upper()}"
            bo = {
                "bo_id": bo_id,
                "entity_id": entity_id,
                "name": change.get("name", ""),
                "ownership_percentage": change.get("ownership_percentage", 0),
                "control_type": change.get("control_type", "ownership"),
                "is_individual": change.get("is_individual", True),
                "status": "identified",
                "identified_at": datetime.utcnow().isoformat(),
                "verification_status": "pending",
            }
            _BENEFICIAL_OWNERS[bo_id] = bo
            current.append(bo)
            updates.append({"bo_id": bo_id, "action": "added"})
        elif action == "remove":
            bo_id = change.get("bo_id", "")
            current = [o for o in current if o.get("bo_id") != bo_id]
            updates.append({"bo_id": bo_id, "action": "removed"})

    _ENTITY_BO[entity_id] = current
    return {
        "entity_id": entity_id,
        "updates": updates,
        "current_bos": len(current),
    }


async def get_entity_owners(entity_id: str) -> dict[str, Any]:
    """Get beneficial owners for an entity."""
    owners = _ENTITY_BO.get(entity_id, [])
    return {
        "entity_id": entity_id,
        "beneficial_owners": owners,
        "total": len(owners),
        "verified": len([o for o in owners if o.get("verification_status") == "verified"]),
        "pending_verification": len([o for o in owners if o.get("verification_status") == "pending"]),
    }


async def get_pending_verifications() -> dict[str, Any]:
    """Get all beneficial owners pending verification."""
    pending = [bo for bo in _BENEFICIAL_OWNERS.values() if bo.get("verification_status") == "pending"]
    return {
        "total_pending": len(pending),
        "owners": pending,
    }
