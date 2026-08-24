"""
Seed script: Populate ChromaDB with payment reconciliation knowledge base data.

Includes:
- Reconciliation rules (matching criteria, tolerances, workflows)
- Payment standards (BAI2, ISO 20022, NACHA, SWIFT MT940)
- Exception handling procedures (unmatched, discrepancies, duplicates)
- Accounting standards (GAAP, IFRS, ASC 842)
- Past discrepancy cases (resolution patterns)
- Matching patterns (reference matching, amount matching, date matching)
- Regulatory requirements (SOX, Basel III, AML reporting)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

RECONCILIATION_RULES = [
    {
        "id": "rule_001",
        "text": "Payment Reconciliation Overview: Payment reconciliation is the process of matching internal financial records (ledger entries) against external bank statements to ensure all transactions are accounted for, accurately recorded, and properly categorized. Three-way reconciliation matches: 1) Bank statement entry, 2) Internal ledger entry, 3) Source document (invoice, receipt, or approval). Two-way reconciliation matches bank statement to ledger only. Daily reconciliation is required for high-volume accounts; weekly for standard accounts; monthly for low-activity accounts.",
        "metadata": {"source": "Internal Policy", "section": "Reconciliation Overview", "type": "overview"},
    },
    {
        "id": "rule_002",
        "text": "Matching Criteria for Payment Reconciliation: Exact Match: Amount, date, and reference number all match within tolerance. Fuzzy Match: Amount matches within tolerance (±1%), date within ±2 business days, reference partially matches. Partial Match: Only amount or reference matches — requires manual review. No Match: No corresponding entry found — creates exception item. Amount Tolerance: Standard tolerance is ±$0.01 for exact matches, ±1% for fuzzy matches. Date Tolerance: ±2 business days for standard transactions, ±5 for international wires.",
        "metadata": {"source": "Internal Policy", "section": "Matching Criteria", "type": "rules"},
    },
    {
        "id": "rule_003",
        "text": "Reconciliation Workflow: Step 1: Import bank statement data (MT940, BAI2, CSV). Step 2: Import internal ledger entries. Step 3: Run auto-matching engine (exact matches first, then fuzzy). Step 4: Review auto-matched items for accuracy. Step 5: Investigate unmatched items (exceptions). Step 6: Resolve discrepancies with supporting documentation. Step 7: Post adjusting entries if needed. Step 8: Generate reconciliation report. Step 9: Manager review and sign-off. Step 10: Archive reconciliation package.",
        "metadata": {"source": "Internal Policy", "section": "Workflow", "type": "process"},
    },
    {
        "id": "rule_004",
        "text": "Three-Way Matching Rules: For payments to vendors: Match purchase order (PO), goods receipt (GR), and invoice before payment approval. Tolerance levels: Amount: ±$50 or ±0.5% (whichever is less). Quantity: ±2% of ordered quantity. Date: Invoice date must be within 30 days of receipt date. If tolerance exceeded, route to exception queue for manual review. Auto-approval threshold: All three documents match within tolerance AND amount < $10,000.",
        "metadata": {"source": "Internal Policy", "section": "Three-Way Match", "type": "rules"},
    },
]

PAYMENT_STANDARDS = [
    {
        "id": "std_bai2_001",
        "text": "BAI2 Format (Bank Administration Institute): Standard for cash management reporting. File structure: Group Header (record type 01) → Account Identifier (record type 02) → Transaction Details (record type 16, 49) → Group Trailer (record type 98) → File Trailer (record type 99). Key fields: Transaction code (credits, debits, ACH, wires), amount, value date, account number, reference. Common transaction codes: 10 (credit/deposit), 15 (debit/withdrawal), 17 (ACH credit), 18 (ACH debit), 47 (wire credit), 48 (wire debit), 61 (SCD/tax).",
        "metadata": {"source": "BAI", "standard": "BAI2", "type": "format_spec"},
    },
    {
        "id": "std_iso20022_001",
        "text": "ISO 20022 (CAMT.053): Bank-to-Customer Statement. XML-based standard replacing MT940. Key elements: Document root <Document> → BkToCstmrStmt → Stmt (Statement) → Acct (Account) → Ntry (Entry) → Amount, CdtDbtInd (Credit/Debit Indicator), BookgDt (Booking Date), ValDt (Value Date), AcctSvcrRef (Account Servicer Reference). Statement line includes: RmtInf (Remittance Information) with structured (Strd) or unstructured (Ustrd) references. Supports multiple currencies and very long reference fields.",
        "metadata": {"source": "ISO", "standard": "ISO 20022", "type": "format_spec"},
    },
    {
        "id": "std_mt940_001",
        "text": "SWIFT MT940 Format: Customer Statement Message. Tag structure: :20 (Transaction Reference), :25 (Account Identification), :28C (Statement Number), :60F (Opening Balance), :61 (Statement Line — contains value date, debit/credit, amount, reference), :86 (Information to Account Owner), :62F (Closing Balance). Statement line (:61) format: YYMMDD[MMDD][C/D]amount[//reference][/ordering customer]. Debit/Credit indicator: C = Credit, D = Debit. Matching uses reference field (:86 or appended to :61) against internal payment references.",
        "metadata": {"source": "SWIFT", "standard": "MT940", "type": "format_spec"},
    },
    {
        "id": "std_nacha_001",
        "text": "NACHA Format (ACH Payments): Automated Clearing House file format. File structure: File Header (9 characters) → Batch Header (6) → Entry Detail (7 entries per batch) → Batch Control → File Control. Entry Detail record: Transaction code (22=PPD credit, 27=PPD debit, 22=CCD credit, 27=CCD debit), routing number, account number, amount, individual name, trace number. Addenda records provide remittance information. Same-day ACH: settlement windows at 1:00 PM, 4:00 PM, and 6:00 PM ET.",
        "metadata": {"source": "NACHA", "standard": "NACHA", "type": "format_spec"},
    },
]

EXCEPTION_HANDLING = [
    {
        "id": "exc_001",
        "text": "Exception Item Categories: Type 1 — Unmatched Bank Entry: Bank statement shows a transaction with no corresponding ledger entry. Possible causes: Timing difference, recording error, fraudulent transaction, intercompany transfer not booked. Resolution: Trace to source document, post missing entry, or flag for investigation. Type 2 — Unmatched Ledger Entry: Ledger shows a transaction with no corresponding bank statement entry. Possible causes: Check not yet cleared, ACH pending, recording error. Resolution: Check outstanding items aging, void stale entries. Type 3 — Amount Discrepancy: Matched entries have different amounts. Possible causes: Bank fees, currency conversion, partial payments, data entry error. Resolution: Investigate difference, post adjusting entry. Type 4 — Duplicate Entry: Same transaction appears twice in one system. Possible causes: Double posting, file import error. Resolution: Reverse duplicate entry.",
        "metadata": {"source": "Internal Policy", "section": "Exception Handling", "type": "categories"},
    },
    {
        "id": "exc_002",
        "text": "Exception Aging and Escalation: 0-3 days: Auto-notification to analyst assigned. 4-7 days: Supervisor notification, daily follow-up required. 8-14 days: Manager escalation, formal investigation initiated. 15-30 days: Director review, root cause analysis required. 31+ days: VP/CFO notification, may require write-off approval. Materiality threshold: Exceptions > $10,000 escalate immediately to supervisor. Exceptions > $50,000 escalate to manager. Exceptions > $100,000 escalate to director. Exceptions > $500,000 escalate to CFO.",
        "metadata": {"source": "Internal Policy", "section": "Escalation", "type": "escalation"},
    },
    {
        "id": "exc_003",
        "text": "Timing Difference Procedures: Outstanding Checks: Checks issued but not yet cleared. Aging: 0-30 days normal, 31-60 days investigate, 61+ days consider voiding. ACH/Wire Pending: Initiated but not yet settled. Same-day ACH: Expected same business day. Next-day ACH: Expected next business day. Wire: Domestic same-day, international 1-3 business days. Deposits in Transit: Received but not yet credited by bank. Normally clears next business day. Month-end cutoff: Deposits received before 5:00 PM on last business day included in current month.",
        "metadata": {"source": "Internal Policy", "section": "Timing Differences", "type": "procedures"},
    },
]

ACCOUNTING_STANDARDS = [
    {
        "id": "acct_gaap_001",
        "text": "GAAP Reconciliation Requirements: ASC 210 (Balance Sheet): Requires reconciliation of cash and cash equivalents. ASC 230 (Cash Flow): Statement of cash flows must reconcile beginning and ending cash balances. ASC 850 (Related Party): Disclose related party transactions in reconciliation. Materiality: Errors < 5% of pre-tax income are generally immaterial. Quantitative threshold: Misstatements > $50,000 individually or > $200,000 in aggregate require investigation. Qualitative: Even small errors must be investigated if they could influence user decisions.",
        "metadata": {"source": "FASB", "standard": "GAAP", "type": "requirements"},
    },
    {
        "id": "acct_sox_001",
        "text": "SOX Compliance for Reconciliation: Sarbanes-Oxley Act Section 302: CEO/CFO must certify accuracy of financial reports including reconciliations. Section 404: Internal controls over financial reporting (ICFR) must include reconciliation controls. Key controls: 1) Segregation of duties (preparer ≠ reviewer), 2) Management review of reconciliations, 3) Timely completion (within 5 business days of period end), 4) Documentation of exceptions and resolutions. Audit trail: All reconciliation actions must be logged with timestamps and user IDs. Retention: Reconciliation records must be retained for 7 years minimum.",
        "metadata": {"source": "SEC", "standard": "SOX", "type": "compliance"},
    },
]

PAST_DISCREPANCIES = [
    {
        "id": "disc_001",
        "text": "Discrepancy Case — Duplicate ACH Entry: Scenario: Company ABC shows two identical ACH debits of $15,000 on the same day to vendor XYZ. Root Cause: File import error — same ACH file was uploaded twice to the accounting system. Resolution: Identified duplicate via trace number matching. Reversed one entry in ledger. Implemented file hash check to prevent duplicate imports. Recovery: No financial impact — internal correction only. Prevention: Added duplicate detection rule based on trace number + amount + date combination.",
        "metadata": {"resolution": "duplicate_reversal", "product": "ach", "outcome": "success", "impact": "none"},
    },
    {
        "id": "disc_002",
        "text": "Discrepancy Case — Currency Conversion Mismatch: Scenario: International wire of €50,000 received, but bank credited $54,200 while ledger recorded $54,500. Root Cause: Bank used spot rate at settlement time (1.084), but accounting recorded at rate from payment initiation date (1.090). Resolution: GAAP requires recording at spot rate on settlement date. Adjusted ledger entry to match bank's rate. Posted FX gain of $300. Impact: $300 adjustment (materiality threshold not met). Prevention: Updated policy to use settlement-date spot rate for all FX transactions.",
        "metadata": {"resolution": "fx_adjustment", "product": "wire", "outcome": "success", "impact": "minor"},
    },
    {
        "id": "disc_003",
        "text": "Discrepancy Case — Check Fraudulent Alteration: Scenario: Paper check #4521 for $1,200 to vendor DEF was altered to $12,000 and deposited to unknown account. Root Cause: Check was intercepted in mail and amount was chemically altered. Detection: Reconciliation flagged amount mismatch — check image showed alteration. Resolution: Filed fraud report with bank. Bank provisional credit within 10 business days. Stopped payment on original check. Issued replacement payment via wire. Impact: $10,800 temporarily out of account, fully recovered via bank claim. Prevention: Switched to electronic payments for all vendor disbursements > $1,000.",
        "metadata": {"resolution": "fraud_claim", "product": "check", "outcome": "success", "impact": "significant"},
    },
]

MATCHING_PATTERNS = [
    {
        "id": "match_001",
        "text": "Reference Number Matching Patterns: Exact reference match: Bank statement reference = Ledger reference (confidence: 99%). Truncated reference: Bank shows last 8 chars of 12-char reference (confidence: 95%). Reference with prefix/suffix: Bank adds date or batch code to reference (confidence: 90%). Structured remittance: ISO 20022 Strd element contains invoice number (confidence: 98%). Unstructured remittance: Free-text field contains invoice number somewhere (confidence: 85%). No reference: Must rely on amount + date matching (confidence: 60%).",
        "metadata": {"pattern": "reference_matching", "type": "algorithm"},
    },
    {
        "id": "match_002",
        "text": "Amount-Based Matching Rules: Exact amount: Bank = Ledger (±$0.01) → auto-match. Rounded amount: Bank = $1,000.00, Ledger = $999.99 → flag for review. Split payments: One bank entry matches multiple ledger entries (sum within tolerance) → auto-match. Partial payment: Bank amount < Ledger amount → exception (possible short payment). Overpayment: Bank amount > Ledger amount → exception (possible duplicate or error). Multi-currency: Convert to common currency using settlement-date rate → compare.",
        "metadata": {"pattern": "amount_matching", "type": "algorithm"},
    },
]

REGULATORY_REQUIREMENTS = [
    {
        "id": "reg_aml_001",
        "text": "AML/BSA Reconciliation Requirements: Bank Secrecy Act (BSA): Currency Transaction Reports (CTRs) must be filed for cash transactions > $10,000. Reconciliation must identify: 1) Structuring (multiple transactions just under $10,000), 2) Unusual patterns (rapid movement of funds), 3) Geographic risk (high-risk jurisdictions). Suspicious Activity Reports (SARs): Filed when transactions are suspicious regardless of amount. Reconciliation flag: Any transaction > $5,000 with no clear business purpose. Record retention: 5 years for CTRs, 5 years for SARs. FinCEN reporting: Quarterly reconciliation of CTR filings.",
        "metadata": {"source": "FinCEN", "regulation": "BSA/AML", "type": "compliance"},
    },
    {
        "id": "reg_basel_001",
        "text": "Basel III Operational Risk: Reconciliation failures are operational risk events. Key Risk Indicators (KRIs): 1) Reconciliation breaks > $10,000 per day, 2) Unresolved items > 30 days old, 3) Manual overrides to auto-matching, 4) Late reconciliation completion. Operational risk capital: Banks must hold capital for operational risk including reconciliation failures. Loss event data: Reconciliation errors that result in financial loss must be logged in the operational risk database. Scenario analysis: Include reconciliation failure scenarios in annual stress testing.",
        "metadata": {"source": "BIS", "regulation": "Basel III", "type": "risk"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "reconciliation_rules": RECONCILIATION_RULES,
        "payment_standards": PAYMENT_STANDARDS,
        "exception_handling": EXCEPTION_HANDLING,
        "accounting_standards": ACCOUNTING_STANDARDS,
        "past_discrepancies": PAST_DISCREPANCIES,
        "matching_patterns": MATCHING_PATTERNS,
        "regulatory_requirements": REGULATORY_REQUIREMENTS,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        if documents:
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
