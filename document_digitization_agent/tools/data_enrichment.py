"""
Data Enrichment Tool — MCP tool stub.

Enhances extracted document data with additional context:
- Currency conversion
- Date normalization
- Entity resolution
- Tax calculation
- Document similarity matching
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


async def enrich_invoice_data(
    extracted_fields: dict,
) -> dict:
    """
    Enrich extracted invoice data with additional context.

    Adds: vendor verification, payment terms normalization,
    tax rate calculation, currency conversion, duplicate detection.
    """
    logger.info("Enriching invoice data")

    enriched = dict(extracted_fields)
    enrichment_metadata = {}

    # Vendor verification (simulated)
    vendor = enriched.get("vendor_name", "")
    if vendor:
        vendor_hash = hashlib.md5(vendor.encode()).hexdigest()
        enrichment_metadata["vendor_verified"] = int(vendor_hash[:2], 16) % 100 > 15
        enrichment_metadata["vendor_risk_score"] = round(int(vendor_hash[:2], 16) / 255.0, 2)

    # Payment terms normalization
    terms = enriched.get("payment_terms", "")
    if terms:
        terms_lower = str(terms).lower()
        if "net 30" in terms_lower:
            enrichment_metadata["payment_days"] = 30
        elif "net 60" in terms_lower:
            enrichment_metadata["payment_days"] = 60
        elif "net 90" in terms_lower:
            enrichment_metadata["payment_days"] = 90
        else:
            enrichment_metadata["payment_days"] = 30  # default

    # Tax rate calculation
    subtotal = enriched.get("subtotal")
    tax_amount = enriched.get("tax_amount")
    if isinstance(subtotal, (int, float)) and isinstance(tax_amount, (int, float)) and subtotal > 0:
        enrichment_metadata["calculated_tax_rate"] = round((tax_amount / subtotal) * 100, 2)

    # Currency conversion (simulated rates)
    currency = enriched.get("currency", "USD")
    total = enriched.get("total_amount", 0)
    rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "CAD": 1.36}
    if currency in rates and isinstance(total, (int, float)):
        enrichment_metadata["usd_equivalent"] = round(total / rates[currency], 2)

    # BSA threshold check
    if isinstance(total, (int, float)) and total >= 10000:
        enrichment_metadata["bsa_threshold_exceeded"] = True
        enrichment_metadata["requires_ctr"] = True

    # Duplicate detection hash
    dup_key = f"{vendor}_{total}_{enriched.get('invoice_date', '')}"
    enrichment_metadata["duplicate_hash"] = hashlib.md5(dup_key.encode()).hexdigest()[:12]

    result = {
        "enrichment_id": str(uuid.uuid4()),
        "original_fields": extracted_fields,
        "enriched_fields": enriched,
        "enrichment_metadata": enrichment_metadata,
        "enrichments_applied": list(enrichment_metadata.keys()),
        "enriched_at": datetime.utcnow().isoformat(),
    }

    logger.info("Invoice enrichment complete: %d enrichments applied", len(enrichment_metadata))
    return result


async def enrich_bank_statement_data(
    extracted_fields: dict,
) -> dict:
    """
    Enrich bank statement data with cash flow analysis.

    Adds: savings rate, spending categories, income stability,
    irregularity detection, minimum balance analysis.
    """
    logger.info("Enriching bank statement data")

    enriched = dict(extracted_fields)
    enrichment_metadata = {}

    opening = enriched.get("opening_balance", 0)
    closing = enriched.get("closing_balance", 0)
    credits = enriched.get("total_credits", 0)
    debits = enriched.get("total_debits", 0)
    transactions = enriched.get("transactions", [])

    # Cash flow analysis
    if isinstance(credits, (int, float)) and isinstance(debits, (int, float)):
        net_flow = credits - debits
        enrichment_metadata["net_cash_flow"] = round(net_flow, 2)
        enrichment_metadata["savings_rate"] = round((net_flow / credits * 100), 1) if credits > 0 else 0
        enrichment_metadata["spending_ratio"] = round((debits / credits * 100), 1) if credits > 0 else 0

    # Transaction categorization
    if transactions and isinstance(transactions, list):
        categories = {"income": 0, "housing": 0, "food": 0, "utilities": 0, "other": 0}
        for txn in transactions:
            desc = str(txn.get("description", "")).lower()
            credit = txn.get("credit", 0)
            debit = txn.get("debit", 0)

            if credit > 0:
                categories["income"] += credit
            elif "rent" in desc or "mortgage" in desc:
                categories["housing"] += debit
            elif "grocery" in desc or "food" in desc or "restaurant" in desc:
                categories["food"] += debit
            elif "electric" in desc or "gas" in desc or "water" in desc:
                categories["utilities"] += debit
            else:
                categories["other"] += debit

        enrichment_metadata["spending_categories"] = categories

        # Irregularity detection
        irregularities = []
        for txn in transactions:
            debit = txn.get("debit", 0)
            desc = str(txn.get("description", "")).lower()
            if "nsf" in desc or "overdraft" in desc:
                irregularities.append({"type": "nsf_fee", "description": txn.get("description"), "amount": debit})
            if isinstance(debit, (int, float)) and debit > 5000:
                irregularities.append({"type": "large_withdrawal", "description": txn.get("description"), "amount": debit})

        enrichment_metadata["irregularities"] = irregularities
        enrichment_metadata["irregularity_count"] = len(irregularities)

    # Creditworthiness score (simulated)
    score = 70
    if isinstance(enrichment_metadata.get("savings_rate", 0), (int, float)):
        if enrichment_metadata["savings_rate"] > 20:
            score += 15
        elif enrichment_metadata["savings_rate"] < 0:
            score -= 20
    if enrichment_metadata.get("irregularity_count", 0) > 2:
        score -= 15
    enrichment_metadata["creditworthiness_score"] = min(max(score, 0), 100)

    result = {
        "enrichment_id": str(uuid.uuid4()),
        "original_fields": extracted_fields,
        "enriched_fields": enriched,
        "enrichment_metadata": enrichment_metadata,
        "enrichments_applied": list(enrichment_metadata.keys()),
        "enriched_at": datetime.utcnow().isoformat(),
    }

    logger.info("Bank statement enrichment complete: creditworthiness=%d", enrichment_metadata["creditworthiness_score"])
    return result


async def enrich_contract_data(
    extracted_fields: dict,
) -> dict:
    """
    Enrich contract data with risk analysis.

    Adds: contract risk scoring, missing clause detection,
    renewal reminder dates, value benchmarking.
    """
    logger.info("Enriching contract data")

    enriched = dict(extracted_fields)
    enrichment_metadata = {}

    # Risk scoring
    risk_score = 0
    risk_factors = []

    total_value = enriched.get("total_value", 0)
    if isinstance(total_value, (int, float)) and total_value > 1000000:
        risk_score += 20
        risk_factors.append("high_value_contract")

    termination = enriched.get("termination_clause", "")
    if not termination or termination == "extracted_termination_clause":
        risk_score += 15
        risk_factors.append("missing_termination_clause")

    governing_law = enriched.get("governing_law", "")
    if not governing_law or governing_law == "extracted_governing_law":
        risk_score += 10
        risk_factors.append("missing_governing_law")

    enrichment_metadata["contract_risk_score"] = min(risk_score, 100)
    enrichment_metadata["risk_factors"] = risk_factors
    enrichment_metadata["requires_legal_review"] = risk_score >= 25

    # Renewal tracking
    effective_date = enriched.get("effective_date", "")
    term_months = enriched.get("term_months", 12)
    if isinstance(effective_date, str) and effective_date != "extracted_effective_date":
        try:
            from datetime import timedelta
            eff_dt = datetime.strptime(effective_date, "%Y-%m-%d")
            end_dt = eff_dt + timedelta(days=int(term_months) * 30)
            renewal_reminder = end_dt - timedelta(days=90)
            enrichment_metadata["contract_end_date"] = end_dt.strftime("%Y-%m-%d")
            enrichment_metadata["renewal_reminder_date"] = renewal_reminder.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    result = {
        "enrichment_id": str(uuid.uuid4()),
        "original_fields": extracted_fields,
        "enriched_fields": enriched,
        "enrichment_metadata": enrichment_metadata,
        "enrichments_applied": list(enrichment_metadata.keys()),
        "enriched_at": datetime.utcnow().isoformat(),
    }

    logger.info("Contract enrichment complete: risk_score=%d", enrichment_metadata["contract_risk_score"])
    return result


async def enrich_financial_statement_data(
    extracted_fields: dict,
) -> dict:
    """
    Enrich financial statement data with ratio analysis.

    Adds: liquidity ratios, profitability ratios, leverage ratios,
    industry benchmarking, trend indicators.
    """
    logger.info("Enriching financial statement data")

    enriched = dict(extracted_fields)
    enrichment_metadata = {}

    total_assets = enriched.get("total_assets", 0)
    total_liabilities = enriched.get("total_liabilities", 0)
    shareholders_equity = enriched.get("shareholders_equity", 0)
    revenue = enriched.get("revenue", 0)
    net_income = enriched.get("net_income", 0)

    # Liquidity ratios
    if isinstance(total_assets, (int, float)) and isinstance(total_liabilities, (int, float)) and total_liabilities > 0:
        enrichment_metadata["debt_to_asset_ratio"] = round(total_liabilities / total_assets, 3)
        enrichment_metadata["equity_multiplier"] = round(total_assets / max(shareholders_equity, 1), 3) if isinstance(shareholders_equity, (int, float)) else None

    # Profitability ratios
    if isinstance(revenue, (int, float)) and isinstance(net_income, (int, float)) and revenue > 0:
        enrichment_metadata["net_profit_margin"] = round((net_income / revenue) * 100, 2)
        enrichment_metadata["return_on_assets"] = round((net_income / total_assets) * 100, 2) if isinstance(total_assets, (int, float)) and total_assets > 0 else None
        enrichment_metadata["return_on_equity"] = round((net_income / shareholders_equity) * 100, 2) if isinstance(shareholders_equity, (int, float)) and shareholders_equity > 0 else None

    # Health assessment
    health_score = 50
    if enrichment_metadata.get("net_profit_margin", 0) > 10:
        health_score += 20
    if enrichment_metadata.get("debt_to_asset_ratio", 1) < 0.5:
        health_score += 15
    elif enrichment_metadata.get("debt_to_asset_ratio", 1) > 0.8:
        health_score -= 20
    enrichment_metadata["financial_health_score"] = min(max(health_score, 0), 100)

    result = {
        "enrichment_id": str(uuid.uuid4()),
        "original_fields": extracted_fields,
        "enriched_fields": enriched,
        "enrichment_metadata": enrichment_metadata,
        "enrichments_applied": list(enrichment_metadata.keys()),
        "enriched_at": datetime.utcnow().isoformat(),
    }

    logger.info("Financial statement enrichment complete: health_score=%d", enrichment_metadata["financial_health_score"])
    return result
