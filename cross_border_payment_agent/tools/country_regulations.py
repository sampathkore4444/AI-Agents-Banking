"""
Country Regulations Tool — MCP tool stub for cross-border payments.

Retrieves country-specific regulations, capital controls, and reporting requirements.
"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Country regulation database (simplified)
_COUNTRY_REGULATIONS = {
    "US": {
        "name": "United States",
        "capital_controls": False,
        "reporting_threshold_usd": 10000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": True,
        "travel_rule_threshold": 3000,
        "beneficial_ownership_required": True,
        "tax_reporting": "FBAR > $10K foreign accounts, FATCA > $50K",
        "currency_restrictions": None,
        "notes": "OFAC sanctions apply to all USD transactions globally",
    },
    "GB": {
        "name": "United Kingdom",
        "capital_controls": False,
        "reporting_threshold_usd": 13000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 1000,
        "beneficial_ownership_required": True,
        "tax_reporting": "HMRC reporting for international payments",
        "currency_restrictions": None,
        "notes": "FCA regulated, OFSI sanctions list",
    },
    "EU": {
        "name": "European Union",
        "capital_controls": False,
        "reporting_threshold_usd": 15000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 1000,
        "beneficial_ownership_required": True,
        "tax_reporting": "DAC6/DAC7 cross-border reporting",
        "currency_restrictions": None,
        "notes": "SEPA for EUR payments, PSD2 SCA required",
    },
    "CN": {
        "name": "China",
        "capital_controls": True,
        "reporting_threshold_usd": 50000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 500,
        "beneficial_ownership_required": True,
        "tax_reporting": "SAFE reporting for FX transactions",
        "currency_restrictions": "Individuals: $50K/year FX quota. Corporates: require SAFE approval for capital account transactions.",
        "notes": "Strict capital controls, SAFE (State Administration of Foreign Exchange) oversight",
    },
    "IN": {
        "name": "India",
        "capital_controls": True,
        "reporting_threshold_usd": 10000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 1000,
        "beneficial_ownership_required": True,
        "tax_reporting": "RBI reporting, Form 15CC for remittances",
        "currency_restrictions": "FEMA regulations. Current account: largely free. Capital account: restricted. Liberalized Remittance Scheme: $250K/year for individuals.",
        "notes": "RBI oversight, FEMA compliance required",
    },
    "JP": {
        "name": "Japan",
        "capital_controls": False,
        "reporting_threshold_usd": 30000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 1000,
        "beneficial_ownership_required": True,
        "tax_reporting": "NTA reporting for cross-border payments",
        "currency_restrictions": None,
        "notes": "FSA regulated, BOJ RTGS for JPY",
    },
    "AE": {
        "name": "United Arab Emirates",
        "capital_controls": False,
        "reporting_threshold_usd": 10000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 1000,
        "beneficial_ownership_required": True,
        "tax_reporting": "CBUAE reporting",
        "currency_restrictions": None,
        "notes": "UAE is financial hub, FATF member, strong AML framework",
    },
    "NG": {
        "name": "Nigeria",
        "capital_controls": True,
        "reporting_threshold_usd": 5000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 1000,
        "beneficial_ownership_required": True,
        "tax_reporting": "CBN reporting, NFIU compliance",
        "currency_restrictions": "Multiple exchange rates (official vs parallel). CBN approval needed for large FX transactions.",
        "notes": "High-risk jurisdiction, enhanced due diligence required",
    },
    "BR": {
        "name": "Brazil",
        "capital_controls": False,
        "reporting_threshold_usd": 10000,
        "ctr_required": True,
        "sar_required": True,
        "ofac_screening": False,
        "travel_rule_threshold": 1000,
        "beneficial_ownership_required": True,
        "tax_reporting": "BACEN reporting, CDE declaration",
        "currency_restrictions": "IOF tax on FX transactions (0.38%-6%)",
        "notes": "IOF tax applies to most cross-border FX transactions",
    },
}


async def get_country_regulations(country_code: str) -> dict:
    """Get cross-border payment regulations for a country."""
    logger.info("Getting regulations for: %s", country_code)

    country = country_code.upper()
    regs = _COUNTRY_REGULATIONS.get(country)

    if not regs:
        return {
            "country_code": country,
            "error": f"Regulations not found for {country}",
            "available_countries": list(_COUNTRY_REGULATIONS.keys()),
        }

    return {
        "country_code": country,
        "regulations": regs,
        "retrieved_at": datetime.utcnow().isoformat(),
    }


async def check_capital_controls(
    source_country: str,
    target_country: str,
    amount: float,
    currency: str,
) -> dict:
    """Check if capital controls apply to a cross-border payment."""
    source = source_country.upper()
    target = target_country.upper()

    source_regs = _COUNTRY_REGULATIONS.get(source, {})
    target_regs = _COUNTRY_REGULATIONS.get(target, {})

    controls = []

    if source_regs.get("capital_controls"):
        controls.append({
            "country": source,
            "type": "outflow",
            "restriction": source_regs.get("currency_restrictions", "Capital controls apply"),
            "action_required": "Verify source country FX quota and approval requirements",
        })

    if target_regs.get("capital_controls"):
        controls.append({
            "country": target,
            "type": "inflow",
            "restriction": target_regs.get("currency_restrictions", "Capital controls apply"),
            "action_required": "Verify target country receiving requirements and reporting",
        })

    # Check IOF (Brazil tax)
    if target == "BR" and currency.upper() == "BRL":
        controls.append({
            "country": "BR",
            "type": "tax",
            "restriction": "IOF tax 0.38%-6% on FX transactions",
            "action_required": "IOF tax will be applied — included in final amount",
        })

    return {
        "source_country": source,
        "target_country": target,
        "amount": amount,
        "currency": currency,
        "capital_controls_apply": len(controls) > 0,
        "controls": controls,
        "recommendation": "Proceed with caution" if controls else "No capital control restrictions",
    }
