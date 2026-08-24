"""
Compliance Tool — MCP tool stub for cross-border payments.

Handles compliance checks, Travel Rule validation, and regulatory checks.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_payment_compliance(
    originator_name: str,
    originator_country: str,
    beneficiary_name: str,
    beneficiary_country: str,
    amount: float,
    currency: str,
    purpose: str,
    originator_address: str | None = None,
    beneficiary_address: str | None = None,
) -> dict:
    """Run full compliance check on a cross-border payment."""
    logger.info("Running compliance check: %s → %s, $%s %s", originator_country, beneficiary_country, amount, currency)

    checks = []

    # Travel Rule check
    travel_rule = _check_travel_rule(originator_name, originator_country, beneficiary_name, beneficiary_country, amount)
    checks.append(travel_rule)

    # OFAC/sanctions check (simplified)
    sanctions = _check_sanctions_country(beneficiary_country)
    checks.append(sanctions)

    # Amount thresholds
    amount_check = _check_amount_thresholds(amount, currency)
    checks.append(amount_check)

    # Country risk
    country_risk = _check_country_risk(beneficiary_country)
    checks.append(country_risk)

    # Purpose check
    purpose_check = _check_purpose(purpose, amount)
    checks.append(purpose_check)

    # Overall decision
    blocking = [c for c in checks if c["status"] == "BLOCK"]
    holding = [c for c in checks if c["status"] == "HOLD"]
    warnings = [c for c in checks if c["status"] == "WARNING"]

    if blocking:
        decision = "BLOCKED"
        reason = f"Blocking compliance issue: {blocking[0]['check']}"
    elif holding:
        decision = "HELD_FOR_REVIEW"
        reason = f"Requires compliance review: {holding[0]['check']}"
    elif warnings:
        decision = "PROCEED_WITH_WARNINGS"
        reason = f"{len(warnings)} warning(s) — proceed with caution"
    else:
        decision = "APPROVED"
        reason = "All compliance checks passed"

    return {
        "decision": decision,
        "reason": reason,
        "checks": checks,
        "total_checks": len(checks),
        "passed": len([c for c in checks if c["status"] == "PASS"]),
        "warnings": len(warnings),
        "holds": len(holding),
        "blocks": len(blocking),
        "checked_at": datetime.utcnow().isoformat(),
        "compliance_id": str(uuid.uuid4())[:12],
    }


async def get_required_information(
    originator_country: str,
    beneficiary_country: str,
    amount: float,
    currency: str,
) -> dict:
    """Determine required information for a cross-border payment."""
    required = []
    recommended = []

    # Always required
    required.extend([
        "Originator full legal name",
        "Originator account number (IBAN or local)",
        "Beneficiary full legal name",
        "Beneficiary account number (IBAN or local)",
        "Beneficiary bank BIC/SWIFT code",
        "Purpose of payment",
    ])

    # Travel Rule thresholds
    if amount > 1000:
        required.append("Originator address")
        required.append("Beneficiary address")

    # Country-specific
    high_risk_countries = ["IR", "KP", "SY", "CU", "VE", "MM"]
    if beneficiary_country in high_risk_countries:
        required.extend([
            "Source of funds documentation",
            "Detailed business justification",
            "Beneficiary identification documents",
        ])

    # Large amounts
    if amount > 100000:
        required.extend([
            "Source of funds declaration",
            "Beneficial ownership information",
        ])
        recommended.append("Compliance officer pre-approval")

    # EU-specific
    if beneficiary_country == "EU" or originator_country == "EU":
        required.append("Originator/Beneficiary LEI (if entity)")

    return {
        "originator_country": originator_country,
        "beneficiary_country": beneficiary_country,
        "amount": amount,
        "currency": currency,
        "required_information": required,
        "recommended_information": recommended,
        "travel_rule_threshold": 1000,
    }


def _check_travel_rule(originator: str, originator_country: str, beneficiary: str, beneficiary_country: str, amount: float) -> dict:
    """Check FATF Travel Rule compliance."""
    if amount < 1000:
        return {"check": "Travel Rule", "status": "PASS", "detail": "Below $1,000 threshold (FATF recommended)"}

    has_originator = bool(originator and originator_country)
    has_beneficiary = bool(beneficiary and beneficiary_country)

    if has_originator and has_beneficiary:
        return {"check": "Travel Rule", "status": "PASS", "detail": f"Originator and beneficiary info present for ${amount:,.2f} transfer"}
    else:
        return {"check": "Travel Rule", "status": "BLOCK", "detail": "Missing required originator/beneficiary information"}


def _check_sanctions_country(country: str) -> dict:
    """Check if destination country is sanctioned."""
    fully_sanctioned = {"IR", "KP", "SY", "CU"}
    partially_sanctioned = {"RU", "BY", "MM", "VE"}

    if country in fully_sanctioned:
        return {"check": "Sanctions Country", "status": "BLOCK", "detail": f"{country} is under comprehensive sanctions — payment prohibited"}
    elif country in partially_sanctioned:
        return {"check": "Sanctions Country", "status": "HOLD", "detail": f"{country} has targeted sanctions — enhanced screening required"}
    else:
        return {"check": "Sanctions Country", "status": "PASS", "detail": f"{country} not under sanctions"}


def _check_amount_thresholds(amount: float, currency: str) -> dict:
    """Check amount-based compliance thresholds."""
    if amount > 1000000:
        return {"check": "Large Transfer", "status": "HOLD", "detail": "Transfers > $1M require enhanced due diligence"}
    elif amount > 100000:
        return {"check": "Large Transfer", "status": "WARNING", "detail": "Transfers > $100K flagged for monitoring"}
    else:
        return {"check": "Large Transfer", "status": "PASS", "detail": "Within normal limits"}


def _check_country_risk(country: str) -> dict:
    """Check beneficiary country risk level."""
    high_risk = {"IR", "KP", "SY", "CU", "VE", "MM", "AF", "YE", "SO"}
    medium_risk = {"RU", "BY", "PK", "NG", "IQ", "LY", "SD"}

    if country in high_risk:
        return {"check": "Country Risk", "status": "HOLD", "detail": f"{country} classified as high-risk — enhanced due diligence required"}
    elif country in medium_risk:
        return {"check": "Country Risk", "status": "WARNING", "detail": f"{country} classified as medium-risk — additional monitoring recommended"}
    else:
        return {"check": "Country Risk", "status": "PASS", "detail": f"{country} classified as standard risk"}


def _check_purpose(purpose: str, amount: float) -> dict:
    """Check payment purpose合理性."""
    if not purpose:
        return {"check": "Purpose", "status": "WARNING", "detail": "No purpose specified — required for Travel Rule"}

    suspicious_keywords = ["gift", "donation", "loan", "investment"]
    if any(kw in purpose.lower() for kw in suspicious_keywords) and amount > 50000:
        return {"check": "Purpose", "status": "WARNING", "detail": f"Large {purpose.lower()} payment — enhanced documentation recommended"}

    return {"check": "Purpose", "status": "PASS", "detail": f"Purpose: {purpose}"}
