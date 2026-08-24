"""
Payment Quote Tool — MCP tool stub for cross-border payments.

Generates all-in cost quotes including fees, FX spread, and correspondent costs.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def generate_quote(
    source_currency: str,
    target_currency: str,
    amount: float,
    originator_country: str,
    beneficiary_country: str,
    charges_type: str = "SHA",
    payment_purpose: str | None = None,
    urgency: str = "standard",
) -> dict:
    """
    Generate an all-in cost quote for a cross-border payment.

    charges_type: OUR (sender pays all), BEN (beneficiary pays all), SHA (shared)
    urgency: "standard" (T+2), "express" (T+1), "urgent" (same-day)
    """
    logger.info("Generating quote: %s %s → %s (%s), charges=%s", amount, source_currency, target_currency, beneficiary_country, charges_type)

    quote_id = f"QT-{uuid.uuid4().hex[:8].upper()}"

    # FX rate and spread
    from tools.fx_rates import get_fx_rate
    rate_data = await get_fx_rate(source_currency, target_currency, amount)
    mid_rate = rate_data.get("mid_market_rate", 1.0)
    fx_spread = rate_data.get("fx_cost", round(amount * 0.005, 2))

    # Fee components
    originating_fee = 35.00 if charges_type in ("OUR", "SHA") else 0
    intermediary_fee = 25.00
    beneficiary_fee = 15.00 if charges_type in ("BEN", "SHA") else 0
    swift_message_fee = 8.00

    # Urgency adjustments
    urgency_multiplier = {"standard": 1.0, "express": 1.5, "urgent": 2.0}.get(urgency, 1.0)
    originating_fee *= urgency_multiplier
    intermediary_fee *= urgency_multiplier

    # Total fees
    if charges_type == "OUR":
        total_fees = originating_fee + intermediary_fee + beneficiary_fee + swift_message_fee + fx_spread
    elif charges_type == "BEN":
        total_fees = 0  # Beneficiary pays everything
        total_fees_beneficiary = intermediary_fee + beneficiary_fee + swift_message_fee
    else:  # SHA
        total_fees = originating_fee + swift_message_fee + (fx_spread / 2)
        total_fees_beneficiary = beneficiary_fee + (intermediary_fee) + (fx_spread / 2)

    # Timeline
    timeline = {
        "standard": "2 business days",
        "express": "1 business day",
        "urgent": "Same day (if before cutoff)",
    }

    # Convert amount
    converted = round(amount * mid_rate, 2)

    quote = {
        "quote_id": quote_id,
        "valid_until": f"{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')}Z (30 minutes)",
        "payment_details": {
            "source_currency": source_currency.upper(),
            "target_currency": target_currency.upper(),
            "send_amount": round(amount, 2),
            "converted_amount": converted,
            "mid_market_rate": mid_rate,
            "fx_spread": round(fx_spread, 2),
        },
        "fees": {
            "originating_bank": round(originating_fee, 2),
            "intermediary_correspondent": round(intermediary_fee, 2),
            "beneficiary_bank": round(beneficiary_fee, 2),
            "swift_messages": round(swift_message_fee, 2),
            "fx_spread": round(fx_spread, 2),
            "total_sender_pays": round(total_fees, 2),
            "total_beneficiary_pays": round(total_fees_beneficiary, 2) if charges_type != "OUR" else 0,
        },
        "charges_type": charges_type,
        "charges_explanation": {
            "OUR": "Sender pays all fees — beneficiary receives full converted amount",
            "BEN": "Beneficiary pays all fees — deducted from converted amount",
            "SHA": "Fees shared — sender pays originator fees, beneficiary pays receiving fees",
        }.get(charges_type, ""),
        "timeline": {
            "urgency": urgency,
            "estimated_delivery": timeline.get(urgency, "2 business days"),
            "cutoff_time": "2:00 PM ET for same-day processing",
        },
        "routing": {
            "originator_country": originator_country,
            "beneficiary_country": beneficiary_country,
            "estimated_correspondents": 2,
            "gpi_enabled": True,
        },
        "compliance_notes": [
            "OFAC screening required for USD payments",
            "Travel Rule: Originator/beneficiary info required",
            f"Beneficiary country: {beneficiary_country} — check local regulations",
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }

    return quote


async def compare_options(
    source_currency: str,
    target_currency: str,
    amount: float,
    originator_country: str,
    beneficiary_country: str,
) -> dict:
    """Compare different payment options (wire vs SEPA vs local)."""
    options = []

    # Option 1: SWIFT Wire (standard)
    wire_quote = await generate_quote(source_currency, target_currency, amount, originator_country, beneficiary_country, "SHA", urgency="standard")
    options.append({
        "option": "SWIFT Wire Transfer",
        "total_cost": wire_quote["fees"]["total_sender_pays"] + wire_quote["fees"]["total_beneficiary_pays"],
        "timeline": "2 business days",
        "pros": ["End-to-end tracking (gpi)", "Wide global coverage", "Reliable"],
        "cons": ["Higher fees", "Multiple intermediaries"],
        "quote": wire_quote,
    })

    # Option 2: Express wire
    express_quote = await generate_quote(source_currency, target_currency, amount, originator_country, beneficiary_country, "SHA", urgency="express")
    options.append({
        "option": "SWIFT Express (gpi)",
        "total_cost": express_quote["fees"]["total_sender_pays"] + express_quote["fees"]["total_beneficiary_pays"],
        "timeline": "1 business day",
        "pros": ["Faster delivery", "gpi priority processing"],
        "cons": ["Higher fees than standard"],
        "quote": express_quote,
    })

    # Option 3: FX Broker (e.g., Wise)
    options.append({
        "option": "FX Broker (Wise, Remitly)",
        "total_cost": round(amount * 0.004 + 5, 2),
        "timeline": "1-2 business days",
        "pros": ["Lowest cost", "Transparent pricing", "Good for SME"],
        "cons": ["Limited currencies", "No SWIFT gpi tracking", "May not support large amounts"],
    })

    options.sort(key=lambda x: x["total_cost"])

    return {
        "source_currency": source_currency,
        "target_currency": target_currency,
        "amount": amount,
        "best_option": options[0]["option"],
        "best_cost": options[0]["total_cost"],
        "options": options,
    }
