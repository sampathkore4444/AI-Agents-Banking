"""
Compliance Checker Tool — MCP tool stub.

Validates collections actions against FDCPA, TCPA, FCRA, and state laws.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory compliance log
_compliance_log: list[dict] = []


async def check_contact_compliance(
    account_id: str,
    contact_method: str,
    contact_time: str | None = None,
    borrower_state: str | None = None,
    daily_attempts: int = 0,
    weekly_attempts: int = 0,
    cease_desist_received: bool = False,
    attorney_represented: bool = False,
    validation_notice_sent: bool = False,
) -> dict:
    """
    Check if a proposed contact action complies with FDCPA, TCPA, and state laws.
    """
    logger.info("Checking contact compliance: account=%s, method=%s", account_id, contact_method)

    violations = []
    warnings = []
    compliant = True

    # FDCPA time restrictions
    if contact_time:
        hour = int(contact_time.split(":")[0]) if ":" in contact_time else -1
        if hour < 8 or hour >= 21:
            violations.append({
                "regulation": "FDCPA §1692c(a)(1)",
                "severity": "critical",
                "message": f"Contact at {contact_time} violates FDCPA — contact hours limited to 8:00 AM - 9:00 PM local time",
            })
            compliant = False

    # FDCPA cease and desist
    if cease_desist_received:
        violations.append({
            "regulation": "FDCPA §1692c(c)",
            "severity": "critical",
            "message": "Cease and desist letter received — all communication must stop except to confirm cessation or notify of specific action (e.g., lawsuit)",
        })
        compliant = False

    # FDCPA attorney representation
    if attorney_represented:
        violations.append({
            "regulation": "FDCPA §1692c(a)(2)",
            "severity": "critical",
            "message": "Borrower is represented by attorney — all communication must go through attorney",
        })
        compliant = False

    # FDCPA validation notice
    if not validation_notice_sent and contact_method in ("phone", "letter"):
        warnings.append({
            "regulation": "FDCPA §1692g",
            "severity": "warning",
            "message": "Validation notice must be sent within 5 days of initial communication",
        })

    # FDCPA frequency limits
    if daily_attempts >= 3:
        violations.append({
            "regulation": "FDCPA §1692c(d)",
            "severity": "high",
            "message": f"Daily contact limit reached ({daily_attempts} attempts). FDCPA prohibits repeated calls intended to harass.",
        })
        compliant = False

    # TCPA restrictions
    if contact_method in ("sms", "automated_call"):
        warnings.append({
            "regulation": "TCPA",
            "severity": "warning",
            "message": f"TCPA requires prior express consent for {contact_method} contact. Verify consent is documented.",
        })

    # State-specific checks
    state_restrictions = _get_state_restrictions(borrower_state)
    for restriction in state_restrictions:
        if restriction["check"](daily_attempts, weekly_attempts):
            warnings.append({
                "regulation": f"State Law ({borrower_state})",
                "severity": "warning",
                "message": restriction["message"],
            })

    # Credit reporting timing
    if contact_method == "credit_report":
        warnings.append({
            "regulation": "FCRA",
            "severity": "info",
            "message": "Account must be 30+ days delinquent before reporting to credit bureaus",
        })

    result = {
        "account_id": account_id,
        "contact_method": contact_method,
        "compliant": compliant,
        "violations": violations,
        "warnings": warnings,
        "recommendation": _generate_recommendation(compliant, violations, warnings),
        "checked_at": datetime.utcnow().isoformat(),
    }

    # Log compliance check
    _compliance_log.append({
        "account_id": account_id,
        "action": f"contact_check_{contact_method}",
        "compliant": compliant,
        "violations_count": len(violations),
        "checked_at": datetime.utcnow().isoformat(),
    })

    return result


async def check_disclosure_compliance(
    disclosure_type: str,
    account_id: str,
    amount_owed: float | None = None,
    creditor_name: str | None = None,
) -> dict:
    """Check if required disclosures are being made correctly."""
    logger.info("Checking disclosure compliance: type=%s, account=%s", disclosure_type, account_id)

    required_elements = []
    compliance_status = "compliant"

    if disclosure_type == "validation_notice":
        required_elements = [
            "Amount of debt",
            "Name of creditor",
            "30-day dispute rights statement",
            "Verification rights statement",
            "Original creditor name (upon request)",
        ]
    elif disclosure_type == "settlement_offer":
        required_elements = [
            "Settlement amount",
            "Payment terms",
            "Deadline for acceptance",
            "Tax implications (1099-C notice)",
            "Release of liability language",
            "Credit reporting impact statement",
        ]
    elif disclosure_type == "time_barred_notice":
        required_elements = [
            "Statement that debt is time-barred",
            "Statute of limitations for borrower's state",
            "Warning that payment may restart statute of limitations",
        ]
    elif disclosure_type == "mini_miranda":
        required_elements = [
            "Statement that communication is from a debt collector",
            "Statement that information will be used for collection of debt",
        ]

    return {
        "account_id": account_id,
        "disclosure_type": disclosure_type,
        "required_elements": required_elements,
        "compliance_status": compliance_status,
        "recommendation": f"Ensure all {len(required_elements)} required elements are included in the {disclosure_type}",
        "checked_at": datetime.utcnow().isoformat(),
    }


async def log_collection_action(
    account_id: str,
    action_type: str,
    action_details: dict,
    collector_id: str,
    outcome: str | None = None,
) -> dict:
    """Log a collection action for compliance audit trail."""
    log_entry = {
        "log_id": f"LOG-{len(_compliance_log) + 1:06d}",
        "account_id": account_id,
        "action_type": action_type,
        "action_details": action_details,
        "collector_id": collector_id,
        "outcome": outcome,
        "logged_at": datetime.utcnow().isoformat(),
        "retention_period": "7 years",
    }

    _compliance_log.append(log_entry)
    logger.info("Collection action logged: %s for account %s", action_type, account_id)

    return {
        "logged": True,
        "log_id": log_entry["log_id"],
        "message": f"Action '{action_type}' logged for account {account_id}",
    }


async def get_compliance_report(account_id: str | None = None) -> dict:
    """Generate a compliance report for an account or the full portfolio."""
    logs = _compliance_log
    if account_id:
        logs = [l for l in logs if l.get("account_id") == account_id]

    violations = [l for l in logs if not l.get("compliant", True)]
    total_actions = len(logs)

    return {
        "account_id": account_id or "portfolio_wide",
        "total_actions_logged": total_actions,
        "violations_count": len(violations),
        "compliance_rate": round((1 - len(violations) / max(total_actions, 1)) * 100, 1),
        "recent_violations": violations[-5:] if violations else [],
        "generated_at": datetime.utcnow().isoformat(),
    }


def _get_state_restrictions(state: str | None) -> list[dict]:
    """Get state-specific restrictions."""
    if not state:
        return []

    restrictions = {
        "CA": [
            {"check": lambda d, w: w > 5, "message": "California: Weekly contact limit may apply under Rosenthal Act"},
        ],
        "NY": [
            {"check": lambda d, w: w > 5, "message": "New York: Strict licensing requirements — verify collector license is current"},
        ],
        "TX": [
            {"check": lambda d, w: False, "message": "Texas: 4-year statute of limitations on debt"},
        ],
        "FL": [
            {"check": lambda d, w: w > 6, "message": "Florida: Consider state-specific contact frequency guidelines"},
        ],
    }

    return restrictions.get(state.upper(), [])


def _generate_recommendation(compliant: bool, violations: list, warnings: list) -> str:
    """Generate a compliance recommendation."""
    if not compliant:
        critical = [v for v in violations if v["severity"] in ("critical", "high")]
        if critical:
            return f"STOP — {len(critical)} critical violation(s) found. Do not proceed with this action. Review FDCPA requirements."
        return "Proceed with caution — review warnings before continuing."

    if warnings:
        return f"Action is compliant but {len(warnings)} warning(s) found. Review before proceeding."

    return "Action is fully compliant. Proceed as planned."
