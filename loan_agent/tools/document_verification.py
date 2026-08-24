"""
Document Verification Tool — MCP tool stub.

Handles OCR and verification of loan-related documents:
payslips, bank statements, tax returns, employment letters, etc.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Document schemas for loan documents
LOAN_DOC_SCHEMAS = {
    "payslip": ["employee_name", "employer_name", "gross_pay", "net_pay", "pay_period", "ytd_earnings"],
    "bank_statement": ["account_holder", "account_number", "statement_period", "opening_balance", "closing_balance", "transactions"],
    "tax_return": ["taxpayer_name", "ssn_last_four", "tax_year", "adjusted_gross_income", "taxable_income", "total_income"],
    "employment_letter": ["employee_name", "employer_name", "position", "start_date", "annual_salary", "employment_status"],
    "id_document": ["full_name", "date_of_birth", "document_number", "expiry_date", "nationality"],
    "proof_of_address": ["full_name", "address", "utility_provider", "issue_date"],
}


async def verify_loan_document(
    document_url: str,
    document_type: str,
    expected_values: dict | None = None,
) -> dict:
    """
    Extract and verify data from a loan document.

    Returns extracted fields, verification status, and anomalies detected.
    """
    logger.info("Verifying document type=%s from %s", document_type, document_url)

    # Stub: extract plausible data
    url_hash = hashlib.md5(document_url.encode()).hexdigest()
    confidence = round(min(max(int(url_hash[:4], 16) / 1000.0, 0.70), 0.99), 2)
    quality = "high" if confidence > 0.85 else "medium" if confidence > 0.70 else "low"

    schema = LOAN_DOC_SCHEMAS.get(document_type, ["text_content"])
    extracted_fields = {}
    for field_name in schema:
        if field_name in ("gross_pay", "net_pay", "ytd_earnings", "opening_balance", "closing_balance", "annual_salary", "adjusted_gross_income", "taxable_income", "total_income"):
            extracted_fields[field_name] = round(30000 + (int(url_hash[:4], 16) % 120000), 2)
        elif field_name == "pay_period":
            extracted_fields[field_name] = "monthly"
        elif field_name == "tax_year":
            extracted_fields[field_name] = 2024
        else:
            extracted_fields[field_name] = f"extracted_{field_name}"

    # Cross-validate with expected values if provided
    anomalies = []
    if expected_values:
        for key, expected in expected_values.items():
            if key in extracted_fields:
                extracted_val = extracted_fields[key]
                if isinstance(expected, (int, float)) and isinstance(extracted_val, (int, float)):
                    diff_pct = abs(expected - extracted_val) / max(expected, 1)
                    if diff_pct > 0.1:  # >10% discrepancy
                        anomalies.append({
                            "field": key,
                            "expected": expected,
                            "extracted": extracted_val,
                            "discrepancy_pct": round(diff_pct * 100, 1),
                            "severity": "high" if diff_pct > 0.25 else "medium",
                        })

    result = {
        "verification_id": str(uuid.uuid4()),
        "document_url": document_url,
        "document_type": document_type,
        "extracted_fields": extracted_fields,
        "confidence_score": confidence,
        "ocr_quality": quality,
        "anomalies": anomalies,
        "has_anomalies": len(anomalies) > 0,
        "verified_at": datetime.utcnow().isoformat(),
    }

    logger.info("Document verification complete: confidence=%s, anomalies=%d", confidence, len(anomalies))
    return result
