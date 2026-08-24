"""
Seed script: Populate ChromaDB with cross-border payment knowledge base data.

Includes:
- Correspondent banking details (routing, nostro/vostro accounts)
- SWIFT/BIC codes (format, lookup, gpi tracking)
- Country regulations (capital controls, reporting, tax)
- Fee schedules (wire fees, intermediary fees, FX spreads)
- FX trading rules (spot, forward, spread, RBI)
- Compliance requirements (OFAC, EU sanctions, AML, CTR)
- Past transaction patterns

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

CORRESPONDENT_BANKING = [
    {
        "id": "corr_001",
        "text": "Correspondent Banking Overview: Correspondent banking enables banks to provide international payment services by maintaining relationships with foreign banks (correspondents). The originating bank (ordering bank) sends instructions through a chain of correspondents to reach the beneficiary bank. Nostro account: 'Our account' — account held by our bank at a foreign correspondent. Vostro account: 'Your account' — account held by a foreign correspondent at our bank. The correspondent chain typically involves: Originating Bank → Intermediary Bank (USD correspondent) → Beneficiary Bank.",
        "metadata": {"source": "SWIFT", "topic": "overview", "type": "correspondent_banking"},
    },
    {
        "id": "corr_002",
        "text": "USD Correspondent Banking: Most international USD payments clear through US-based correspondents (JPMorgan Chase, Citibank, Bank of New York Mellon, Wells Fargo). CLS (Continuous Linked Settlement) settles FX trades to eliminate principal risk. Fedwire processes high-value USD transfers. CHIPS (Clearing House Interbank Payments System) processes large-value USD payments. Key routing: Non-US bank → USD Correspondent (JPM/Citi) → Fedwire/CHIPS → Beneficiary Bank.",
        "metadata": {"source": "Federal Reserve", "topic": "usd_clearing", "type": "correspondent_banking"},
    },
]

SWIFT_CODES = [
    {
        "id": "swift_001",
        "text": "SWIFT Code Structure (BIC - Bank Identifier Code): 8-character code: AAAA BB CC (AAAA=Bank code, BB=Country code, CC=Location code). 11-character code: AAAA BB CC DDD (DDD=Branch code, optional). Example: BOFAUS3N = Bank of America, US, New York. Country codes follow ISO 3166-1 alpha-2 (US=United States, GB=United Kingdom, DE=Germany, JP=Japan). SWIFT gpi (Global Payments Innovation): End-to-end tracking of cross-border payments. UETR (Unique End-to-End Transaction Reference) is a UUID v4 assigned to each gpi payment. Bank Reference Number (BRN) enables tracking through the correspondent chain.",
        "metadata": {"source": "SWIFT", "standard": "BIC", "type": "codes"},
    },
    {
        "id": "swift_002",
        "text": "SWIFT Message Types for Payments: MT103: Single Customer Credit Transfer — standard international wire instruction. Contains ordering customer, beneficiary, amount, charges, and bank-to-bank instructions. MT202: General Financial Institution Transfer — bank-to-bank payment. Used for correspondent banking settlement. MT202COV: Cover payment — follows an MT103, carries the underlying payment info. MT199: Free-format message — used for queries, amendments, or notifications. ISO 20022 Migration: SWIFT is migrating from MT to ISO 20022 XML messages (pacs.008 for customer credit, pacs.009 for bank transfer). Migration deadline: November 2025.",
        "metadata": {"source": "SWIFT", "standard": "MT", "type": "message_types"},
    },
    {
        "id": "swift_003",
        "text": "SWIFT gpi Tracking: SWIFT gpi provides end-to-end payment tracking across the correspondent chain. Key features: 1) UETR tracking — unique reference follows payment through all banks, 2) Faster processing — gpi banks commit to same-day processing, 3) Fee transparency — all fees disclosed before payment, 4) Confirmation — beneficiary bank confirms credit. Tracking states: Initiated → Sent → In Progress (at intermediary) → Completed. Approximately 90% of SWIFT cross-border payments are gpi-enabled. Bank can track payment status via SWIFT API or FINcopy service.",
        "metadata": {"source": "SWIFT", "standard": "gpi", "type": "tracking"},
    },
]

COUNTRY_REGULATIONS = [
    {
        "id": "reg_us_001",
        "text": "United States — Cross-Border Payment Requirements: OFAC Sanctions: All USD transactions screened against SDN (Specially Designated Nationals) list. Transactions with OFAC-sanctioned countries/entities are prohibited (Cuba, Iran, North Korea, Syria, Crimea). CTR (Currency Transaction Report): Required for cash transactions > $10,000. SAR (Suspicious Activity Report): Required for suspicious transactions > $5,000 (or any amount if structured). FinCEN Beneficial Ownership: Accounts must identify ultimate beneficial owners (25%+ ownership threshold). Dodd-Frank: Derivatives and certain cross-border swaps require CFTC reporting.",
        "metadata": {"source": "US Treasury", "country": "US", "type": "regulations"},
    },
    {
        "id": "reg_eu_001",
        "text": "European Union — Cross-Border Payment Requirements: SEPA (Single Euro Payments Area): Euro transfers within EU/EEA settle in 1 business day (SCT Inst: instant). PSD2 (Payment Services Directive 2): Requires Strong Customer Authentication (SCA) for electronic payments. EU Sanctions: Aligned with UN sanctions, additional EU-specific listings. Transfers > €15,000 require enhanced due diligence. MiFID II: Reporting requirements for FX forwards and swaps. GDPR: Cross-border data transfers require Standard Contractual Clauses (SCCs) or adequacy decisions. Anti-Money Laundering Directives (AMLD6): Beneficial ownership registers, crypto-asset transfer rules (TFR).",
        "metadata": {"source": "EC", "country": "EU", "type": "regulations"},
    },
    {
        "id": "reg_uk_001",
        "text": "United Kingdom — Cross-Border Payment Requirements: FCA Regulation: Payment institutions must be authorized. Strong Customer Authentication (SCA) required. HMRC: All international payments require Originator/Beneficiary information. Sanctions: UK maintains its own sanctions list (OFSI — Office of Financial Sanctions Implementation). Post-Brexit: No longer follows EU PSD2 directly, but FCA maintains equivalent rules. CHAPS: Same-day GBP settlement via Bank of England RTGS. BACS: 3-day processing for GBP direct debits/standing orders. Faster Payments: Real-time GBP transfers (up to £1M).",
        "metadata": {"source": "FCA", "country": "UK", "type": "regulations"},
    },
    {
        "id": "reg_jp_001",
        "text": "Japan — Cross-Border Payment Requirements: FSA (Financial Services Agency) regulates cross-border payments. Foreign Exchange and Foreign Trade Act: Requires reporting for overseas remittances > ¥30 million. Anti-Money Laundering: Act on Prevention of Transfer of Criminal Proceeds requires customer identification. BOJ (Bank of Japan): RTGS system for high-value JPY settlements. Zengin System: Electronic payment system for domestic JPY. Cross-border JPY payments typically route through Citibank Tokyo or JPMorgan Tokyo as USD correspondent.",
        "metadata": {"source": "FSA Japan", "country": "JP", "type": "regulations"},
    },
]

FEE_SCHEDULES = [
    {
        "id": "fee_001",
        "text": "International Wire Transfer Fee Schedule (Typical): Originating bank fees: $25-$50 (outgoing international wire), $10-$15 (incoming international wire). Correspondent/intermediary bank fees: $10-$30 per bank in the chain. Beneficiary bank fees: $10-$25 (may deduct from payment amount). FX spread: 0.5%-3.0% depending on amount, currency, and relationship. Total cost example: $10,000 USD to EUR — Originating: $35, Intermediary: $20, FX spread (1.5%): $150, Beneficiary: $15 = Total: ~$220 (2.2%). SWIFT gpi fee transparency: All fees must be disclosed before payment execution. Charges options: OUR (sender pays all), BEN (beneficiary pays all), SHA (shared — most common).",
        "metadata": {"source": "Internal Policy", "category": "wire_fees", "type": "fee_schedule"},
    },
    {
        "id": "fee_002",
        "text": "Correspondent Bank Fee Types: SWIFT message fees: $0.50-$2.00 per message (MT103, MT202). Payment processing fees: $5-$15 per transaction. Account maintenance: $50-$500/month depending on volume. Nostro/vostro account fees: Earned interest on credit balances, charged for debit balances. FX conversion fees: 0.1%-0.5% above mid-market rate. Reconciliation fees: $0.10-$0.50 per transaction. Investigation/STP fail fees: $25-$100 per inquiry. Clawback/return fees: $25-$75 per returned payment. Key negotiation points: Volume-based pricing, annual commitments, preferred correspondent status.",
        "metadata": {"source": "Internal Policy", "category": "correspondent_fees", "type": "fee_schedule"},
    },
]

FX_TRADING_RULES = [
    {
        "id": "fx_001",
        "text": "FX Rate Types: Spot rate: Rate for immediate delivery (T+2 settlement). The most common rate for customer wires. Forward rate: Rate locked in for future delivery (T+30, T+60, T+90). Used for hedging FX risk. Mid-market rate: The midpoint between bid and ask — the 'true' exchange rate. Not available to retail customers. Bid/Ask spread: Bid = price dealer will buy base currency; Ask = price dealer will sell. Spread = Ask - Bid. Customer rate: Mid-market rate + markup (spread). Typical retail markup: 0.5%-3.0%. Wire markup: 0.2%-1.5% above mid-market.",
        "metadata": {"source": "Internal Policy", "topic": "rate_types", "type": "fx_rules"},
    },
    {
        "id": "fx_002",
        "text": "FX Calculation Example: USD to EUR: Mid-market rate: 1 USD = 0.9200 EUR. Customer buy EUR (sell USD): Rate = 0.9200 - 0.0046 (0.5% markup) = 0.9154. Customer sell EUR (buy USD): Rate = 0.9200 + 0.0046 (0.5% markup) = 0.9246. For $10,000 USD wire to EUR: Customer receives: $10,000 × 0.9154 = €9,154 EUR. FX cost: $10,000 × 0.5% = $50 (embedded in rate). All-in cost: Wire fee ($35) + FX spread ($50) = $85 total.",
        "metadata": {"source": "Internal Policy", "topic": "calculation", "type": "fx_rules"},
    },
]

COMPLIANCE_REQUIREMENTS = [
    {
        "id": "comp_ofac_001",
        "text": "OFAC Sanctions Screening (US): All USD transactions must be screened against OFAC SDN (Specially Designated Nationals) list. Screening covers: Sender name, Beneficiary name, Intermediary banks, Correspondent banks, Beneficial owners. Match types: Exact match → Block transaction, Review match → Hold for compliance review, Possible match → Enhanced screening. OFAC violations: Civil penalties up to $330,000 per violation or twice the transaction value. Criminal penalties: Up to $1M fine and 20 years imprisonment. Real-time screening required for transaction processing. Batch screening for account opening and periodic reviews. OFAC list updates: Daily — systems must refresh within 24 hours.",
        "metadata": {"source": "OFAC", "regulation": "SDN", "type": "sanctions"},
    },
    {
        "id": "comp_fatf_001",
        "text": "FATF Travel Rule: FATF Recommendation 16 requires originator and beneficiary information to accompany wire transfers. Required information: Originator name, Account number (or unique reference), Address or national ID, Beneficiary name, Beneficiary account number. Thresholds: FATF recommends no de minimis threshold. Many countries implement at $1,000 or €1,000. SWIFT compliance: MT103 and ISO 20022 pacs.008 include required fields. Non-compliance: Correspondent banks may reject payments missing required information. Implementation varies by country — check local requirements.",
        "metadata": {"source": "FATF", "regulation": "R.16", "type": "travel_rule"},
    },
]

PAST_TRANSACTIONS = [
    {
        "id": "txn_001",
        "text": "Past Transaction Pattern — Large USD to GBP Wire: Customer: US corporation paying UK supplier. Amount: $250,000 USD. Route: JPMorgan (originator) → Barclays London (beneficiary). Fees: OUR (sender pays all). Originating: $45, Intermediary: $25, FX spread (0.4%): $1,000, SWIFT fees: $8. Total cost: $1,078 (0.43%). Timeline: Initiated T+0, credited T+1 (same-day gpi). SWIFT gpi tracking confirmed credit at 14:32 GMT. Customer feedback: Satisfied with speed and fee transparency.",
        "metadata": {"route": "US_to_UK", "currency": "USD_GBP", "outcome": "success", "type": "pattern"},
    },
    {
        "id": "txn_002",
        "text": "Past Transaction Pattern — Compliance Hold: Customer: Individual sending $15,000 USD to Nigeria. Route: Wells Fargo (originator) → Citibank correspondent → Zenith Bank Lagos. Issue: OFAC screening flagged beneficiary bank's country as high-risk. Action: Payment held for enhanced due diligence (EDD). Required: Source of funds documentation, purpose of payment, beneficiary identification. Resolution: Customer provided invoice and business registration. Compliance approved with SAR filing. Timeline: 3 business days delay. Lesson: Nigeria transfers require enhanced documentation.",
        "metadata": {"route": "US_to_NG", "currency": "USD_NGN", "outcome": "delayed", "type": "pattern"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "correspondent_banking": CORRESPONDENT_BANKING,
        "swift_codes": SWIFT_CODES,
        "country_regulations": COUNTRY_REGULATIONS,
        "fee_schedules": FEE_SCHEDULES,
        "fx_trading_rules": FX_TRADING_RULES,
        "compliance_requirements": COMPLIANCE_REQUIREMENTS,
        "past_transactions": PAST_TRANSACTIONS,
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
