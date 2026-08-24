"""
FX Rate Tool — MCP tool stub for cross-border payments.

Handles exchange rate fetching, currency conversion, and rate comparison.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Simulated FX rates (production would call Bloomberg, Reuters, or ECB)
_FX_RATES = {
    ("USD", "EUR"): 0.9200,
    ("USD", "GBP"): 0.7900,
    ("USD", "JPY"): 149.50,
    ("USD", "CHF"): 0.8800,
    ("USD", "CAD"): 1.3600,
    ("USD", "AUD"): 1.5300,
    ("USD", "CNY"): 7.2400,
    ("USD", "INR"): 83.10,
    ("USD", "BRL"): 4.9700,
    ("USD", "MXN"): 17.15,
    ("USD", "NGN"): 1550.00,
    ("USD", "ZAR"): 18.80,
    ("USD", "AED"): 3.6725,
    ("USD", "SAR"): 3.7500,
    ("EUR", "GBP"): 0.8587,
    ("GBP", "USD"): 1.2658,
    ("EUR", "USD"): 1.0870,
}


async def get_fx_rate(
    source_currency: str,
    target_currency: str,
    amount: float | None = None,
) -> dict:
    """Get current exchange rate for a currency pair."""
    logger.info("Fetching FX rate: %s → %s", source_currency, target_currency)

    source = source_currency.upper()
    target = target_currency.upper()

    if source == target:
        return {
            "source_currency": source,
            "target_currency": target,
            "mid_market_rate": 1.0,
            "inverse_rate": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Same currency — no conversion needed",
        }

    # Look up rate (handle inverse)
    rate = _FX_RATES.get((source, target))
    if rate is None:
        # Try inverse
        inv_rate = _FX_RATES.get((target, source))
        if inv_rate:
            rate = round(1.0 / inv_rate, 4)
        else:
            # Try cross-rate via USD
            rate_usd_source = _FX_RATES.get(("USD", source)) or (1.0 / _FX_RATES.get((source, "USD"), 1.0))
            rate_usd_target = _FX_RATES.get(("USD", target)) or (1.0 / _FX_RATES.get((target, "USD"), 1.0))
            if rate_usd_source and rate_usd_target:
                rate = round(rate_usd_target / rate_usd_source, 4)

    if rate is None:
        return {"error": f"Rate not available for {source}/{target}", "available_pairs": list(_FX_RATES.keys())[:10]}

    # Apply typical customer markup (0.5%)
    customer_markup = 0.005
    customer_rate_buy = round(rate * (1 - customer_markup), 4)
    customer_rate_sell = round(rate * (1 + customer_markup), 4)

    result = {
        "source_currency": source,
        "target_currency": target,
        "mid_market_rate": rate,
        "inverse_rate": round(1.0 / rate, 4),
        "customer_buy_rate": customer_rate_buy,
        "customer_sell_rate": customer_rate_sell,
        "spread_pct": round(customer_markup * 100, 2),
        "timestamp": datetime.utcnow().isoformat(),
        "valid_for": "30 seconds",
    }

    if amount:
        result["converted_amount"] = round(amount * customer_rate_buy, 2)
        result["fx_cost"] = round(amount * customer_markup, 2)

    return result


async def compare_rates(
    source_currency: str,
    target_currency: str,
    amount: float,
) -> dict:
    """Compare FX rates across different channels."""
    logger.info("Comparing FX rates: %s %s → %s", amount, source_currency, target_currency)

    base_rate_data = await get_fx_rate(source_currency, target_currency, amount)
    mid_rate = base_rate_data.get("mid_market_rate", 0)

    if mid_rate == 0:
        return base_rate_data

    channels = [
        {"channel": "Online Banking", "markup_pct": 0.50, "processing_fee": 0},
        {"channel": "Branch", "markup_pct": 1.50, "processing_fee": 25},
        {"channel": "Wire Transfer", "markup_pct": 0.75, "processing_fee": 35},
        {"channel": "FX Broker (e.g., Wise)", "markup_pct": 0.35, "processing_fee": 5},
    ]

    comparisons = []
    for ch in channels:
        markup = ch["markup_pct"] / 100
        customer_rate = round(mid_rate * (1 - markup), 4)
        converted = round(amount * customer_rate, 2)
        fx_cost = round(amount * markup, 2)
        total_cost = round(fx_cost + ch["processing_fee"], 2)

        comparisons.append({
            "channel": ch["channel"],
            "rate": customer_rate,
            "converted_amount": converted,
            "fx_spread_cost": round(fx_cost, 2),
            "processing_fee": ch["processing_fee"],
            "total_cost": total_cost,
            "cost_pct": round(total_cost / amount * 100, 2),
        })

    comparisons.sort(key=lambda x: x["total_cost"])

    return {
        "source_currency": source_currency,
        "target_currency": target_currency,
        "amount": amount,
        "mid_market_rate": mid_rate,
        "best_option": comparisons[0]["channel"],
        "best_rate": comparisons[0]["rate"],
        "best_total_cost": comparisons[0]["total_cost"],
        "comparisons": comparisons,
    }


async def get_historical_rate(
    source_currency: str,
    target_currency: str,
    date: str,
) -> dict:
    """Get historical exchange rate for a date."""
    # Simulate historical rate with slight variation
    import hashlib
    h = int(hashlib.md5(f"{source_currency}{target_currency}{date}".encode()).hexdigest()[:8], 16)
    variation = (h % 200 - 100) / 10000  # ±1% variation

    current = await get_fx_rate(source_currency, target_currency)
    mid_rate = current.get("mid_market_rate", 1.0)
    hist_rate = round(mid_rate * (1 + variation), 4)

    return {
        "source_currency": source_currency.upper(),
        "target_currency": target_currency.upper(),
        "date": date,
        "rate": hist_rate,
        "mid_market_rate": mid_rate,
        "variation_from_today": f"{round(variation * 100, 2)}%",
    }
