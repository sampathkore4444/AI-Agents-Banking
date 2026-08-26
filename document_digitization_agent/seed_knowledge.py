"""
Seed script: Populate ChromaDB with document digitization & extraction knowledge base data.

Includes:
- Document classification schemas
- Field extraction rules per document type
- Validation rules and business logic
- OCR best practices and quality standards
- Past extraction decisions
- Industry document standards
- Banking document templates

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  DOCUMENT CLASSIFICATION
# ══════════════════════════════════════════════════════════════════

DOCUMENT_CLASSIFICATION = [
    {
        "id": "cls_invoice_001",
        "text": (
            "Invoice classification: Invoices typically contain vendor name, invoice number, "
            "date, line items with quantities and unit prices, subtotal, tax, total amount due, "
            "payment terms, and bank details. Key identifiers: 'Invoice', 'Bill To', 'Amount Due', "
            "'Payment Terms'. Extract: vendor_name, invoice_number, invoice_date, due_date, "
            "line_items, subtotal, tax_amount, total_amount, currency."
        ),
        "metadata": {"doc_type": "invoice", "category": "accounts_payable", "complexity": "medium"},
    },
    {
        "id": "cls_contract_001",
        "text": (
            "Contract classification: Legal agreements between parties. Key sections include "
            "parties, recitals, definitions, terms and conditions, obligations, termination clauses, "
            "governing law, signatures. Key identifiers: 'Agreement', 'Contract', 'Party', 'WHEREAS'. "
            "Extract: contract_type, parties, effective_date, term, key_obligations, termination_clause, "
            "governing_law, total_value."
        ),
        "metadata": {"doc_type": "contract", "category": "legal", "complexity": "high"},
    },
    {
        "id": "cls_bank_statement_001",
        "text": (
            "Bank statement classification: Monthly account statements showing account holder, "
            "account number, statement period, opening/closing balances, and transaction list. "
            "Key identifiers: 'Statement', 'Account Summary', 'Transactions'. "
            "Extract: account_holder, account_number, statement_period, opening_balance, "
            "closing_balance, total_credits, total_debits, transaction_count."
        ),
        "metadata": {"doc_type": "bank_statement", "category": "financial", "complexity": "medium"},
    },
    {
        "id": "cls_tax_return_001",
        "text": (
            "Tax return classification: IRS/state tax filings. Key forms: 1040 (individual), "
            "1120 (corporation), 1065 (partnership), W-2 (wage statement), 1099 (misc income). "
            "Key identifiers: 'Form 1040', 'Adjusted Gross Income', 'Taxable Income'. "
            "Extract: taxpayer_name, ssn_last_four, filing_status, adjusted_gross_income, "
            "taxable_income, total_tax, refund_or_owed, tax_year."
        ),
        "metadata": {"doc_type": "tax_return", "category": "financial", "complexity": "high"},
    },
    {
        "id": "cls_payslip_001",
        "text": (
            "Payslip/pay stub classification: Employee compensation records. "
            "Contains employee name, employer, pay period, gross pay, deductions (tax, insurance, 401k), "
            "net pay, YTD earnings. Key identifiers: 'Pay Stub', 'Gross Pay', 'Net Pay', 'YTD'. "
            "Extract: employee_name, employer_name, pay_period_start, pay_period_end, "
            "gross_pay, deductions, net_pay, ytd_earnings, ytd_tax."
        ),
        "metadata": {"doc_type": "payslip", "category": "financial", "complexity": "low"},
    },
    {
        "id": "cls_proof_address_001",
        "text": (
            "Proof of address classification: Documents verifying residential address. "
            "Accepted types: utility bills, bank statements, council tax, tenancy agreements, NHS letters. "
            "Key identifiers: customer name + address matching. Must be dated within 3 months. "
            "Extract: full_name, address, utility_provider, issue_date."
        ),
        "metadata": {"doc_type": "proof_of_address", "category": "kyc", "complexity": "low"},
    },
    {
        "id": "cls_identity_document_001",
        "text": (
            "Identity document classification: Government-issued photo IDs. "
            "Types: passport, driving licence, national ID, residence permit. "
            "Key features: photo, MRZ code, hologram, security features. "
            "Extract: full_name, date_of_birth, document_number, nationality, expiry_date, "
            "issuing_country, photo_quality_score."
        ),
        "metadata": {"doc_type": "identity_document", "category": "kyc", "complexity": "medium"},
    },
    {
        "id": "cls_financial_statement_001",
        "text": (
            "Financial statement classification: Company financial reports. "
            "Types: balance sheet, income statement, cash flow statement, notes. "
            "Follows IFRS or US GAAP standards. Key identifiers: 'Assets', 'Liabilities', "
            "'Revenue', 'Net Income'. "
            "Extract: company_name, reporting_period, total_assets, total_liabilities, "
            "shareholders_equity, revenue, net_income, operating_cash_flow."
        ),
        "metadata": {"doc_type": "financial_statement", "category": "financial", "complexity": "high"},
    },
    {
        "id": "cls_loan_application_001",
        "text": (
            "Loan application document classification: Documents submitted with loan applications. "
            "Includes: application form, income verification, property appraisal, title search, "
            "insurance documents. Key identifiers: 'Loan Application', 'Mortgage', 'Borrower'. "
            "Extract: borrower_name, loan_type, requested_amount, property_address, "
            "loan_purpose, loan_term, collateral_value."
        ),
        "metadata": {"doc_type": "loan_application", "category": "lending", "complexity": "high"},
    },
    {
        "id": "cls_corporate_resolution_001",
        "text": (
            "Corporate resolution classification: Board/ shareholder resolutions authorizing actions. "
            "Contains: company name, resolution date, authorized actions, signatories. "
            "Key identifiers: 'Resolution', 'Board of Directors', 'Resolved that'. "
            "Extract: company_name, resolution_date, authorized_action, signatories, "
            "resolution_number."
        ),
        "metadata": {"doc_type": "corporate_resolution", "category": "legal", "complexity": "medium"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  EXTRACTION SCHEMAS
# ══════════════════════════════════════════════════════════════════

EXTRACTION_SCHEMAS = [
    {
        "id": "schema_invoice_001",
        "text": (
            "Invoice extraction schema — Required fields: vendor_name (string, non-empty), "
            "invoice_number (alphanumeric, unique), invoice_date (YYYY-MM-DD), due_date (YYYY-MM-DD), "
            "line_items (array of {description, quantity, unit_price, amount}), subtotal (number >= 0), "
            "tax_rate (percentage), tax_amount (number >= 0), total_amount (number > 0), "
            "currency (ISO 4217). Optional: payment_terms, purchase_order_number, vendor_address. "
            "Validation: total_amount = subtotal + tax_amount, all line item amounts = quantity * unit_price."
        ),
        "metadata": {"doc_type": "invoice", "fields": ["vendor_name", "invoice_number", "invoice_date", "due_date", "line_items", "subtotal", "tax_amount", "total_amount", "currency"]},
    },
    {
        "id": "schema_contract_001",
        "text": (
            "Contract extraction schema — Required fields: contract_title (string), "
            "contract_type (service, loan, employment, NDA, lease, other), party_a (string), "
            "party_b (string), effective_date (YYYY-MM-DD), term_months (integer > 0), "
            "total_value (number), payment_terms (string), termination_clause (string), "
            "governing_law (jurisdiction string). Optional: renewal_terms, confidentiality_clause, "
            "non_compete_clause, intellectual_property_clause. "
            "Validation: effective_date must be valid, term_months must be positive, "
            "total_value must be non-negative for commercial contracts."
        ),
        "metadata": {"doc_type": "contract", "fields": ["contract_title", "contract_type", "party_a", "party_b", "effective_date", "term_months", "total_value", "payment_terms", "termination_clause", "governing_law"]},
    },
    {
        "id": "schema_bank_statement_001",
        "text": (
            "Bank statement extraction schema — Required fields: account_holder (string), "
            "account_number (masked or full), statement_period_start (YYYY-MM-DD), "
            "statement_period_end (YYYY-MM-DD), opening_balance (number), closing_balance (number), "
            "total_credits (number >= 0), total_debits (number >= 0), transactions "
            "(array of {date, description, debit, credit, balance}). "
            "Validation: closing_balance = opening_balance + total_credits - total_debits, "
            "each transaction balance is consistent with running total."
        ),
        "metadata": {"doc_type": "bank_statement", "fields": ["account_holder", "account_number", "statement_period_start", "statement_period_end", "opening_balance", "closing_balance", "total_credits", "total_debits", "transactions"]},
    },
    {
        "id": "schema_tax_return_001",
        "text": (
            "Tax return extraction schema — Required fields: taxpayer_name (string), "
            "ssn_last_four (4 digits), filing_status (single, married_joint, married_separate, head_household), "
            "tax_year (YYYY), adjusted_gross_income (number), standard_deduction (number), "
            "taxable_income (number), total_tax (number), total_payments (number), "
            "refund_or_owed (number, positive = refund). Form-specific: employer_name, employer_ein "
            "(W-2). Validation: taxable_income = AGI - deductions, refund_or_owed = total_payments - total_tax."
        ),
        "metadata": {"doc_type": "tax_return", "fields": ["taxpayer_name", "ssn_last_four", "filing_status", "tax_year", "adjusted_gross_income", "taxable_income", "total_tax", "total_payments", "refund_or_owed"]},
    },
    {
        "id": "schema_payslip_001",
        "text": (
            "Payslip extraction schema — Required fields: employee_name (string), "
            "employer_name (string), pay_period_start (YYYY-MM-DD), pay_period_end (YYYY-MM-DD), "
            "gross_pay (number > 0), federal_tax (number >= 0), state_tax (number >= 0), "
            "social_security (number >= 0), medicare (number >= 0), insurance_deductions (number >= 0), "
            "retirement_deductions (number >= 0), net_pay (number > 0), ytd_gross (number), "
            "ytd_net (number). Validation: net_pay = gross_pay - all deductions, "
            "all deductions >= 0."
        ),
        "metadata": {"doc_type": "payslip", "fields": ["employee_name", "employer_name", "pay_period_start", "pay_period_end", "gross_pay", "net_pay", "ytd_gross", "ytd_net"]},
    },
    {
        "id": "schema_financial_statement_001",
        "text": (
            "Financial statement extraction schema — Required fields: company_name (string), "
            "reporting_period (YYYY-MM-DD to YYYY-MM-DD), statement_type (balance_sheet, income_statement, "
            "cash_flow). Balance sheet: total_assets, current_assets, total_liabilities, current_liabilities, "
            "shareholders_equity. Income statement: revenue, cost_of_goods_sold, gross_profit, "
            "operating_expenses, operating_income, net_income. Cash flow: operating_cash_flow, "
            "investing_cash_flow, financing_cash_flow, net_change_in_cash. "
            "Validation: assets = liabilities + equity, gross_profit = revenue - COGS."
        ),
        "metadata": {"doc_type": "financial_statement", "fields": ["company_name", "reporting_period", "total_assets", "total_liabilities", "shareholders_equity", "revenue", "net_income"]},
    },
]


# ══════════════════════════════════════════════════════════════════
#  VALIDATION RULES
# ══════════════════════════════════════════════════════════════════

VALIDATION_RULES = [
    {
        "id": "val_generic_001",
        "text": (
            "Generic document validation rules: "
            "1. All required fields must be present and non-empty. "
            "2. Date fields must be valid YYYY-MM-DD format. "
            "3. Numeric fields must be valid numbers (not text). "
            "4. Currency amounts must be positive for invoices/statements. "
            "5. Document date must not be in the future (except contracts with future effective dates). "
            "6. OCR confidence score must be >= 0.6 for extraction to be accepted. "
            "7. If confidence < 0.7, flag for manual review. "
            "8. Cross-validate totals (sum of line items = invoice total, etc.)."
        ),
        "metadata": {"rule_type": "generic", "priority": "high", "applies_to": "all"},
    },
    {
        "id": "val_invoice_001",
        "text": (
            "Invoice-specific validation rules: "
            "1. Invoice number must be unique within the same vendor. "
            "2. Due date must be after invoice date. "
            "3. Payment terms must be consistent with dates (Net 30 means due = invoice + 30 days). "
            "4. Tax rate must be between 0% and 100%. "
            "5. Line item amounts must equal quantity × unit price. "
            "6. Currency must be ISO 4217 code. "
            "7. Flag invoices > $10,000 for additional review (BSA/CTR threshold). "
            "8. Check for duplicate invoices (same vendor, same amount, same date)."
        ),
        "metadata": {"rule_type": "invoice", "priority": "high", "applies_to": "invoice"},
    },
    {
        "id": "val_contract_001",
        "text": (
            "Contract validation rules: "
            "1. Both parties must be identified. "
            "2. Effective date must be valid. "
            "3. Term must be positive. "
            "4. Total value must be non-negative. "
            "5. Governing law jurisdiction must be valid. "
            "6. Flag contracts > $1M for legal review. "
            "7. Check for missing termination clauses. "
            "8. Verify all required signatures are present."
        ),
        "metadata": {"rule_type": "contract", "priority": "high", "applies_to": "contract"},
    },
    {
        "id": "val_bank_statement_001",
        "text": (
            "Bank statement validation rules: "
            "1. Statement period must be logical (start < end). "
            "2. Opening and closing balances must be numeric. "
            "3. Closing balance = opening balance + credits - debits. "
            "4. All transactions must have valid dates within statement period. "
            "5. Transaction running balance must be consistent. "
            "6. Flag statements with NSF (non-sufficient funds) fees. "
            "7. Check for large cash withdrawals (>$10,000 — BSA threshold). "
            "8. Verify account holder name matches application."
        ),
        "metadata": {"rule_type": "bank_statement", "priority": "high", "applies_to": "bank_statement"},
    },
    {
        "id": "val_tax_return_001",
        "text": (
            "Tax return validation rules: "
            "1. Tax year must be valid (2018-2025). "
            "2. Filing status must be one of: single, married_joint, married_separate, head_household. "
            "3. AGI must be non-negative (unless business loss). "
            "4. Taxable income = AGI - deductions (must be >= 0). "
            "5. Total tax must be >= 0. "
            "6. SSN last four must be exactly 4 digits. "
            "7. Cross-validate with W-2 employer income. "
            "8. Flag significant income changes year-over-year (>30%)."
        ),
        "metadata": {"rule_type": "tax_return", "priority": "high", "applies_to": "tax_return"},
    },
    {
        "id": "val_payslip_001",
        "text": (
            "Payslip validation rules: "
            "1. Gross pay must be > 0. "
            "2. Net pay = gross pay - all deductions (must be > 0). "
            "3. All deductions must be >= 0. "
            "4. Pay period dates must be logical (start < end). "
            "5. YTD amounts must be >= current period amounts. "
            "6. Federal tax should be reasonable relative to gross pay. "
            "7. Check for consistent employer name with application. "
            "8. Flag payslips where net pay < 50% of gross (high deductions)."
        ),
        "metadata": {"rule_type": "payslip", "priority": "high", "applies_to": "payslip"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  OCR BEST PRACTICES
# ══════════════════════════════════════════════════════════════════

OCR_BEST_PRACTICES = [
    {
        "id": "ocr_quality_001",
        "text": (
            "OCR quality assessment: "
            "Confidence thresholds — High (>= 0.85): Direct extraction, minimal review needed. "
            "Medium (0.70-0.84): Extraction accepted, flag for spot-check review. "
            "Low (0.60-0.69): Extraction requires manual verification before acceptance. "
            "Reject (< 0.60): Document must be re-scanned or re-submitted. "
            "Factors affecting quality: scan resolution (min 300 DPI), document condition, "
            "font type (serif vs sans-serif), background noise, skew angle (< 5° acceptable)."
        ),
        "metadata": {"topic": "ocr_quality", "category": "technical", "priority": "high"},
    },
    {
        "id": "ocr_preprocessing_001",
        "text": (
            "Document preprocessing for optimal OCR: "
            "1. Deskew correction (rotate to correct tilt). "
            "2. Noise removal (remove speckles, borders). "
            "3. Contrast enhancement (improve text-background separation). "
            "4. Binarization (convert to black/white for cleaner text). "
            "5. Resolution upscaling if < 300 DPI. "
            "6. Page segmentation (identify text blocks, tables, images). "
            "7. For multi-page docs, process each page separately then merge results."
        ),
        "metadata": {"topic": "preprocessing", "category": "technical", "priority": "medium"},
    },
    {
        "id": "ocr_tables_001",
        "text": (
            "Table extraction from documents: "
            "Tables require special handling beyond standard OCR. "
            "Approaches: 1) Grid-based detection (identify cell boundaries). "
            "2) Rule-based (detect horizontal/vertical lines). "
            "3) ML-based (trained table detection models). "
            "Output: structured data in CSV/JSON format with headers preserved. "
            "Common issues: merged cells, multi-line cells, headers spanning multiple rows."
        ),
        "metadata": {"topic": "table_extraction", "category": "technical", "priority": "medium"},
    },
    {
        "id": "ocr_mrz_001",
        "text": (
            "MRZ (Machine Readable Zone) extraction: "
            "Passports and ID documents contain MRZ codes at the bottom. "
            "Format: 2 lines of 44 characters (passport) or 3 lines of 30 characters (ID card). "
            "MRZ contains: document type, issuing country, name, document number, nationality, "
            "date of birth, sex, expiry date, checksum digits. "
            "Validation: all checksum digits must verify. MRZ data should match visual inspection zone."
        ),
        "metadata": {"topic": "mrz_extraction", "category": "technical", "priority": "high"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  PAST EXTRACTION DECISIONS
# ══════════════════════════════════════════════════════════════════

PAST_EXTRACTION_DECISIONS = [
    {
        "id": "case_success_001",
        "text": (
            "Successful extraction: Vendor invoice from GlobalTech Inc. "
            "OCR confidence: 0.92. All 8 required fields extracted successfully. "
            "Validation passed: line items matched totals, dates valid, currency USD. "
            "Total: $24,500.00. Auto-routed to accounts payable. Processing time: 3.2 seconds."
        ),
        "metadata": {"decision": "auto_processed", "doc_type": "invoice", "confidence": "high", "processing_time_ms": 3200},
    },
    {
        "id": "case_success_002",
        "text": (
            "Successful extraction: Bank statement from Chase for Q3 2024. "
            "OCR confidence: 0.88. All transactions extracted (47 transactions). "
            "Balance reconciliation passed: $45,230.12 opening + $12,400 credits - $8,100.50 debits = $49,529.62 closing. "
            "Auto-routed to credit analysis team."
        ),
        "metadata": {"decision": "auto_processed", "doc_type": "bank_statement", "confidence": "high", "processing_time_ms": 5100},
    },
    {
        "id": "case_review_001",
        "text": (
            "Extracted with manual review: Service contract between Acme Corp and DataFlow LLC. "
            "OCR confidence: 0.71. Contract value: $1,250,000. "
            "Issues: termination clause partially extracted, governing law section unclear. "
            "Routed to legal review queue. Manual reviewer corrected 2 fields."
        ),
        "metadata": {"decision": "manual_review", "doc_type": "contract", "confidence": "medium", "processing_time_ms": 8500},
    },
    {
        "id": "case_rejected_001",
        "text": (
            "Extraction rejected: W-2 tax form — image quality too poor. "
            "OCR confidence: 0.45. Key fields (employer name, wages) unreadable. "
            "Document rejected with reason: 'Image quality below minimum threshold'. "
            "Customer notified to re-upload a clearer scan."
        ),
        "metadata": {"decision": "rejected", "doc_type": "tax_return", "confidence": "low", "processing_time_ms": 1200},
    },
    {
        "id": "case_error_001",
        "text": (
            "Extraction error: Payslip from employer 'Tech Solutions Ltd'. "
            "OCR confidence: 0.82. Validation failed: net_pay calculation mismatch "
            "(gross $5,200 - deductions $1,800 should = $3,400 but extracted $3,100). "
            "Suspected OCR error on net_pay field. Flagged for manual correction."
        ),
        "metadata": {"decision": "validation_failed", "doc_type": "payslip", "confidence": "medium", "processing_time_ms": 4200},
    },
]


# ══════════════════════════════════════════════════════════════════
#  INDUSTRY DOCUMENT STANDARDS
# ══════════════════════════════════════════════════════════════════

INDUSTRY_DOCUMENT_STANDARDS = [
    {
        "id": "std_iso20022_001",
        "text": (
            "ISO 20022 Financial Messaging Standards: "
            "Standard for financial industry messaging including payment instructions, "
            "account management, and trade finance. Documents following ISO 20022 use "
            "structured XML formats with defined field names and data types. "
            "Key message types: pain.001 (payment initiation), camt.053 (bank-to-customer statement), "
            "camt.054 (debit/credit notification). Extraction should map to ISO 20022 field names."
        ),
        "metadata": {"standard": "ISO 20022", "category": "messaging", "applicable_to": ["bank_statement", "payment_document"]},
    },
    {
        "id": "std_ubl_001",
        "text": (
            "UBL (Universal Business Language) Invoice Standard: "
            "OASIS standard for electronic business documents. UBL 2.1 defines structured "
            "invoice, credit note, and order formats. Key elements: InvoiceNumber, IssueDate, "
            "InvoiceLine, TaxTotal, LegalMonetaryTotal. Extraction should map fields to UBL elements "
            "for interoperability with ERP systems."
        ),
        "metadata": {"standard": "UBL 2.1", "category": "e-invoicing", "applicable_to": ["invoice", "credit_note"]},
    },
    {
        "id": "std_ifrs_001",
        "text": (
            "IFRS (International Financial Reporting Standards) Document Requirements: "
            "Financial statements must follow IFRS structure: Statement of Financial Position "
            "(Balance Sheet), Statement of Comprehensive Income, Statement of Changes in Equity, "
            "Statement of Cash Flows, Notes. Key line items are standardized. "
            "Extraction must identify reporting period, entity name, and statement type."
        ),
        "metadata": {"standard": "IFRS", "category": "accounting", "applicable_to": ["financial_statement"]},
    },
    {
        "id": "std_us_gaap_001",
        "text": (
            "US GAAP (Generally Accepted Accounting Principles) Document Standards: "
            "Similar to IFRS but with US-specific requirements. Key differences: LIFO inventory "
            "permitted, development costs expensed (not capitalized), extra items on income statement. "
            "Extraction must identify whether document follows IFRS or US GAAP for proper field mapping."
        ),
        "metadata": {"standard": "US GAAP", "category": "accounting", "applicable_to": ["financial_statement"]},
    },
    {
        "id": "std_bsa_001",
        "text": (
            "BSA/AML Document Retention Requirements: "
            "Bank Secrecy Act requires financial institutions to retain records for 5 years. "
            "CTR (Currency Transaction Report) for transactions > $10,000. "
            "SAR (Suspicious Activity Report) for suspicious transactions > $5,000. "
            "Document extraction must tag documents for BSA retention and flag CTR/SAR thresholds."
        ),
        "metadata": {"standard": "BSA", "category": "compliance", "applicable_to": ["all_financial_documents"]},
    },
]


# ══════════════════════════════════════════════════════════════════
#  BANKING DOCUMENT TEMPLATES
# ══════════════════════════════════════════════════════════════════

BANKING_DOCUMENT_TEMPLATES = [
    {
        "id": "tmpl_loan_app_001",
        "text": (
            "Loan application document package template — Standard documents required: "
            "1. Completed loan application form. 2. Two years of tax returns (1040 + W-2s). "
            "3. Recent pay stubs (2 months). 4. Bank statements (2 months, all pages). "
            "5. Government-issued photo ID. 6. Proof of address (utility bill, < 3 months old). "
            "7. Employment verification letter. 8. Property appraisal (for secured loans). "
            "Each document has specific extraction requirements and validation rules."
        ),
        "metadata": {"template": "loan_application", "category": "lending", "document_count": 8},
    },
    {
        "id": "tmpl_kyc_package_001",
        "text": (
            "KYC document package template — Standard documents for identity verification: "
            "1. Passport or national ID (primary identity). 2. Driving licence (secondary ID + address). "
            "3. Proof of address (utility bill/bank statement, < 3 months). "
            "4. Source of funds documentation. 5. For businesses: Certificate of Incorporation, "
            "Articles of Association, UBO declarations. "
            "Each document has specific extraction and cross-validation requirements."
        ),
        "metadata": {"template": "kyc_package", "category": "compliance", "document_count": 5},
    },
    {
        "id": "tmpl_account_opening_001",
        "text": (
            "Account opening document package template — Documents for new account: "
            "1. Account application form. 2. Photo ID (passport/driving licence). "
            "3. Proof of address (utility bill/bank statement). "
            "4. For business accounts: Company registration, directors' IDs, UBO info. "
            "5. Initial deposit verification. "
            "Standard processing: auto-extract, auto-validate, route for approval."
        ),
        "metadata": {"template": "account_opening", "category": "onboarding", "document_count": 5},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "document_classification": DOCUMENT_CLASSIFICATION,
        "extraction_schemas": EXTRACTION_SCHEMAS,
        "validation_rules": VALIDATION_RULES,
        "ocr_best_practices": OCR_BEST_PRACTICES,
        "past_extraction_decisions": PAST_EXTRACTION_DECISIONS,
        "industry_document_standards": INDUSTRY_DOCUMENT_STANDARDS,
        "banking_document_templates": BANKING_DOCUMENT_TEMPLATES,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  ✓ {collection_name}: {count} documents")

    print("\n✅ Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
