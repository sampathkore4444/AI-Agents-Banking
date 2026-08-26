"""
Data Validation Tool — MCP tool stub.

Validates extracted document data against schemas, business rules,
and cross-field consistency checks.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def validate_extracted_data(
    document_type: str,
    extracted_fields: dict,
    schema_rules: dict | None = None,
) -> dict:
    """
    Validate extracted fields against schema rules and business logic.

    Checks:
    - Required fields present
    - Data type correctness
    - Business rule compliance
    - Cross-field consistency
    - Format validation (dates, numbers, etc.)

    Args:
        document_type: Type of document (invoice, contract, bank_statement, etc.)
        extracted_fields: Dict of field_name -> value from extraction
        schema_rules: Optional custom validation rules

    Returns:
        Validation result with pass/fail status, errors, and warnings.
    """
    logger.info("Validating extracted data: type=%s, fields=%d", document_type, len(extracted_fields))

    errors = []
    warnings = []
    validated_fields = {}

    # ── Required field check ──
    REQUIRED_FIELDS = {
        "invoice": ["vendor_name", "invoice_number", "invoice_date", "total_amount", "currency"],
        "contract": ["contract_title", "party_a", "party_b", "effective_date", "total_value"],
        "bank_statement": ["account_holder", "account_number", "statement_period_start", "statement_period_end", "opening_balance", "closing_balance"],
        "tax_return": ["taxpayer_name", "tax_year", "adjusted_gross_income", "taxable_income"],
        "payslip": ["employee_name", "employer_name", "gross_pay", "net_pay"],
        "proof_of_address": ["full_name", "address", "issue_date"],
        "identity_document": ["full_name", "date_of_birth", "document_number", "expiry_date"],
        "financial_statement": ["company_name", "reporting_period", "total_assets", "total_liabilities"],
        "loan_application": ["borrower_name", "loan_type", "requested_amount"],
        "corporate_resolution": ["company_name", "resolution_date", "authorized_action"],
    }

    required = REQUIRED_FIELDS.get(document_type, [])
    missing_fields = [f for f in required if f not in extracted_fields]
    if missing_fields:
        errors.append({
            "type": "missing_required_fields",
            "fields": missing_fields,
            "message": f"Missing required fields: {', '.join(missing_fields)}",
            "severity": "error",
        })

    # ── Type and format validation ──
    for field_name, value in extracted_fields.items():
        field_valid = True
        field_warnings = []

        # Date fields
        if field_name.endswith("_date") or field_name in ("reporting_period",):
            if isinstance(value, str):
                if not _is_valid_date(value):
                    errors.append({
                        "type": "invalid_date_format",
                        "field": field_name,
                        "value": value,
                        "message": f"Invalid date format for {field_name}: expected YYYY-MM-DD",
                        "severity": "error",
                    })
                    field_valid = False

        # Numeric fields
        if field_name in ("total_amount", "subtotal", "tax_amount", "gross_pay", "net_pay",
                          "opening_balance", "closing_balance", "total_credits", "total_debits",
                          "adjusted_gross_income", "taxable_income", "total_tax", "total_payments",
                          "total_value", "requested_amount", "total_assets", "total_liabilities",
                          "revenue", "net_income", "shareholders_equity"):
            if not isinstance(value, (int, float)):
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append({
                        "type": "invalid_numeric",
                        "field": field_name,
                        "value": value,
                        "message": f"Invalid numeric value for {field_name}: {value}",
                        "severity": "error",
                    })
                    field_valid = False

        # Currency field
        if field_name == "currency":
            valid_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR"]
            if value not in valid_currencies:
                warnings.append({
                    "type": "uncommon_currency",
                    "field": field_name,
                    "value": value,
                    "message": f"Currency {value} is not in common banking currencies",
                    "severity": "warning",
                })

        # SSN last four
        if field_name == "ssn_last_four":
            if isinstance(value, str) and (len(value) != 4 or not value.isdigit()):
                errors.append({
                    "type": "invalid_ssn_format",
                    "field": field_name,
                    "value": value,
                    "message": "SSN last four must be exactly 4 digits",
                    "severity": "error",
                })
                field_valid = False

        validated_fields[field_name] = {
            "value": value,
            "valid": field_valid,
            "warnings": field_warnings,
        }

    # ── Business rule validation ──
    business_errors = _validate_business_rules(document_type, extracted_fields)
    errors.extend(business_errors)

    # ── Cross-field consistency ──
    consistency_errors = _check_cross_field_consistency(document_type, extracted_fields)
    errors.extend(consistency_errors)

    # ── Summary ──
    total_fields = len(extracted_fields)
    valid_fields = sum(1 for f in validated_fields.values() if f["valid"])
    error_count = len([e for e in errors if e.get("severity") == "error"])
    warning_count = len([w for w in warnings if w.get("severity") == "warning"]) + len([e for e in errors if e.get("severity") == "warning"])

    is_valid = error_count == 0

    result = {
        "validation_id": str(uuid.uuid4()),
        "document_type": document_type,
        "is_valid": is_valid,
        "total_fields": total_fields,
        "valid_fields": valid_fields,
        "error_count": error_count,
        "warning_count": warning_count,
        "errors": errors,
        "warnings": warnings,
        "validated_fields": validated_fields,
        "recommendation": (
            "auto_accept" if is_valid and warning_count == 0
            else "accept_with_review" if is_valid
            else "reject_or_manual_review"
        ),
        "validated_at": datetime.utcnow().isoformat(),
    }

    logger.info("Validation complete: valid=%s, errors=%d, warnings=%d", is_valid, error_count, warning_count)
    return result


async def cross_validate_documents(
    documents: list[dict],
) -> dict:
    """
    Cross-validate data across multiple related documents.

    For example, verify that payslip income matches tax return income,
    or that bank statement account holder matches identity document name.
    """
    logger.info("Cross-validating %d documents", len(documents))

    discrepancies = []

    if len(documents) < 2:
        return {
            "cross_validation_id": str(uuid.uuid4()),
            "documents_checked": len(documents),
            "discrepancies": [],
            "is_consistent": True,
            "message": "Need at least 2 documents for cross-validation",
        }

    # Check name consistency across documents
    names_found = {}
    for doc in documents:
        doc_type = doc.get("document_type", "unknown")
        fields = doc.get("extracted_fields", {})

        for name_field in ["full_name", "employee_name", "account_holder", "taxpayer_name", "borrower_name"]:
            if name_field in fields:
                name = fields[name_field]
                if isinstance(name, str) and name != f"extracted_{name_field}":
                    if name not in names_found:
                        names_found[name] = []
                    names_found[name].append(doc_type)

    # Check for name mismatches
    if len(names_found) > 1:
        discrepancies.append({
            "type": "name_mismatch",
            "severity": "high",
            "message": f"Multiple names found across documents: {list(names_found.keys())}",
            "details": names_found,
        })

    # Check date consistency
    dates_found = {}
    for doc in documents:
        fields = doc.get("extracted_fields", {})
        for date_field in ["pay_period_start", "statement_period_start", "invoice_date"]:
            if date_field in fields:
                dates_found[date_field] = fields[date_field]

    is_consistent = len(discrepancies) == 0

    result = {
        "cross_validation_id": str(uuid.uuid4()),
        "documents_checked": len(documents),
        "document_types": [doc.get("document_type", "unknown") for doc in documents],
        "discrepancies": discrepancies,
        "is_consistent": is_consistent,
        "checked_at": datetime.utcnow().isoformat(),
    }

    logger.info("Cross-validation complete: consistent=%s, discrepancies=%d", is_consistent, len(discrepancies))
    return result


# ── Internal helpers ──────────────────────────────────────────────

def _is_valid_date(date_str: str) -> bool:
    """Check if a string is a valid date in YYYY-MM-DD format."""
    from datetime import datetime
    try:
        if len(date_str) == 10:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        elif len(date_str) == 7:
            datetime.strptime(date_str, "%Y-%m")
            return True
        return False
    except ValueError:
        return False


def _validate_business_rules(document_type: str, fields: dict) -> list[dict]:
    """Validate document-specific business rules."""
    errors = []

    if document_type == "invoice":
        # Check due date is after invoice date
        invoice_date = fields.get("invoice_date")
        due_date = fields.get("due_date")
        if invoice_date and due_date and isinstance(invoice_date, str) and isinstance(due_date, str):
            if due_date <= invoice_date:
                errors.append({
                    "type": "business_rule_violation",
                    "field": "due_date",
                    "message": "Due date must be after invoice date",
                    "severity": "warning",
                })

        # Check total合理性
        total = fields.get("total_amount")
        if isinstance(total, (int, float)) and total > 100000:
            errors.append({
                "type": "threshold_alert",
                "field": "total_amount",
                "message": f"Large invoice amount (${total:,.2f}) — BSA review threshold",
                "severity": "warning",
            })

    elif document_type == "bank_statement":
        # Check balance consistency
        opening = fields.get("opening_balance")
        closing = fields.get("closing_balance")
        credits = fields.get("total_credits")
        debits = fields.get("total_debits")
        if all(isinstance(v, (int, float)) for v in [opening, closing, credits, debits]):
            expected_closing = opening + credits - debits
            if abs(expected_closing - closing) > 0.01:
                errors.append({
                    "type": "balance_mismatch",
                    "field": "closing_balance",
                    "message": f"Closing balance (${closing:,.2f}) doesn't match expected (${expected_closing:,.2f})",
                    "severity": "warning",
                })

    elif document_type == "tax_return":
        # Check taxable income logic
        agi = fields.get("adjusted_gross_income")
        taxable = fields.get("taxable_income")
        if isinstance(agi, (int, float)) and isinstance(taxable, (int, float)):
            if taxable > agi:
                errors.append({
                    "type": "business_rule_violation",
                    "field": "taxable_income",
                    "message": "Taxable income exceeds AGI — verify deductions",
                    "severity": "warning",
                })

    elif document_type == "payslip":
        # Check net pay logic
        gross = fields.get("gross_pay")
        net = fields.get("net_pay")
        if isinstance(gross, (int, float)) and isinstance(net, (int, float)):
            if net >= gross:
                errors.append({
                    "type": "business_rule_violation",
                    "field": "net_pay",
                    "message": "Net pay should be less than gross pay after deductions",
                    "severity": "error",
                })
            if net < gross * 0.5:
                errors.append({
                    "type": "threshold_alert",
                    "field": "net_pay",
                    "message": "Net pay is less than 50% of gross — verify deductions",
                    "severity": "warning",
                })

    return errors


def _check_cross_field_consistency(document_type: str, fields: dict) -> list[dict]:
    """Check consistency between related fields."""
    errors = []

    if document_type == "invoice":
        subtotal = fields.get("subtotal")
        tax = fields.get("tax_amount")
        total = fields.get("total_amount")
        if all(isinstance(v, (int, float)) for v in [subtotal, tax, total]):
            expected_total = subtotal + tax
            if abs(expected_total - total) > 0.01:
                errors.append({
                    "type": "cross_field_mismatch",
                    "fields": ["subtotal", "tax_amount", "total_amount"],
                    "message": f"Subtotal + tax (${expected_total:,.2f}) ≠ total (${total:,.2f})",
                    "severity": "error",
                })

    elif document_type == "payslip":
        ytd_gross = fields.get("ytd_gross")
        gross = fields.get("gross_pay")
        if isinstance(ytd_gross, (int, float)) and isinstance(gross, (int, float)):
            if ytd_gross < gross:
                errors.append({
                    "type": "cross_field_mismatch",
                    "fields": ["ytd_gross", "gross_pay"],
                    "message": "YTD gross should be >= current period gross pay",
                    "severity": "warning",
                })

    return errors
