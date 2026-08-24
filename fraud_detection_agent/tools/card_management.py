"""
Card Management Tool — Card freeze/unfreeze, replacement, and status management.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any


# ── In-memory store ───────────────────────────────────────────────
CARD_DB: dict[str, dict] = {}


async def freeze_card(
    card_id: str,
    reason: str,
    fraud_case_id: str | None = None,
) -> dict[str, Any]:
    """Freeze a card immediately to prevent further fraud."""
    card = CARD_DB.get(card_id)
    if not card:
        # Create simulated card
        card = {
            "card_id": card_id,
            "customer_id": f"CUST-{card_id[-6:]}",
            "card_number_last_four": card_id[-4:],
            "card_type": "debit",
            "status": "active",
            "issued_date": "2023-01-15",
            "expiry_date": "2027-01-15",
        }
        CARD_DB[card_id] = card

    previous_status = card["status"]
    card["status"] = "frozen"
    card["frozen_at"] = datetime.utcnow().isoformat()
    card["freeze_reason"] = reason
    card["fraud_case_id"] = fraud_case_id
    card["frozen_by"] = "fraud_agent"

    return {
        "card_id": card_id,
        "previous_status": previous_status,
        "new_status": "frozen",
        "reason": reason,
        "fraud_case_id": fraud_case_id,
        "message": f"Card {card_id[-4:]} has been frozen. No further transactions will be processed.",
        "frozen_at": card["frozen_at"],
    }


async def unfreeze_card(
    card_id: str,
    reason: str,
    verified_by: str = "fraud_agent",
) -> dict[str, Any]:
    """Unfreeze a card after verification."""
    card = CARD_DB.get(card_id)
    if not card:
        return {"error": f"Card {card_id} not found"}

    previous_status = card["status"]
    card["status"] = "active"
    card["unfrozen_at"] = datetime.utcnow().isoformat()
    card["unfreeze_reason"] = reason
    card["unfrozen_by"] = verified_by

    return {
        "card_id": card_id,
        "previous_status": previous_status,
        "new_status": "active",
        "reason": reason,
        "verified_by": verified_by,
        "message": f"Card {card_id[-4:]} has been unfrozen and is now active.",
    }


async def replace_card(
    card_id: str,
    reason: str,
    expedited: bool = True,
) -> dict[str, Any]:
    """Issue a replacement card (e.g., after fraud)."""
    old_card = CARD_DB.get(card_id, {})
    new_card_id = f"CARD-{int(time.time()) % 10**8:08d}"

    new_card = {
        "card_id": new_card_id,
        "customer_id": old_card.get("customer_id", "UNKNOWN"),
        "card_number_last_four": f"{int(time.time()) % 10000:04d}",
        "card_type": old_card.get("card_type", "debit"),
        "status": "active",
        "issued_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "expiry_date": "2029-01-01",
        "replaces_card": card_id,
        "replacement_reason": reason,
        "expedited": expedited,
    }
    CARD_DB[new_card_id] = new_card

    # Deactivate old card
    if card_id in CARD_DB:
        CARD_DB[card_id]["status"] = "replaced"
        CARD_DB[card_id]["replaced_by"] = new_card_id
        CARD_DB[card_id]["replaced_at"] = datetime.utcnow().isoformat()

    return {
        "old_card_id": card_id,
        "new_card_id": new_card_id,
        "new_card_last_four": new_card["card_number_last_four"],
        "status": "active",
        "expedited_shipping": expedited,
        "estimated_delivery": "2-3 business days" if expedited else "7-10 business days",
        "message": f"Replacement card issued. Last four: {new_card['card_number_last_four']}. {'Expedited' if expedited else 'Standard'} shipping.",
    }


async def get_card_status(card_id: str) -> dict[str, Any]:
    """Get current card status."""
    card = CARD_DB.get(card_id)
    if not card:
        return {"error": f"Card {card_id} not found"}
    return card


async def get_cards_by_customer(customer_id: str) -> dict[str, Any]:
    """Get all cards for a customer."""
    cards = [c for c in CARD_DB.values() if c.get("customer_id") == customer_id]
    return {
        "customer_id": customer_id,
        "total_cards": len(cards),
        "active_cards": sum(1 for c in cards if c["status"] == "active"),
        "frozen_cards": sum(1 for c in cards if c["status"] == "frozen"),
        "replaced_cards": sum(1 for c in cards if c["status"] == "replaced"),
        "cards": cards,
    }


async def set_transaction_limits(
    card_id: str,
    daily_limit: float | None = None,
    per_transaction_limit: float | None = None,
    international_enabled: bool | None = None,
) -> dict[str, Any]:
    """Set transaction limits on a card."""
    card = CARD_DB.get(card_id)
    if not card:
        return {"error": f"Card {card_id} not found"}

    if daily_limit is not None:
        card["daily_limit"] = daily_limit
    if per_transaction_limit is not None:
        card["per_transaction_limit"] = per_transaction_limit
    if international_enabled is not None:
        card["international_enabled"] = international_enabled

    return {
        "card_id": card_id,
        "limits_updated": {
            "daily_limit": card.get("daily_limit"),
            "per_transaction_limit": card.get("per_transaction_limit"),
            "international_enabled": card.get("international_enabled"),
        },
        "message": "Transaction limits updated successfully.",
    }
