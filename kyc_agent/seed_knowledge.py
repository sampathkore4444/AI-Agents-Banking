"""
Seed script: Populate ChromaDB with sample KYC knowledge base data.

Run this script before starting the MCP server to populate the vector DB
with regulations, policies, document schemas, risk typologies, and past cases.

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

# Ensure the kyc_agent package is on the path
sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ── Sample Data ───────────────────────────────────────────────────

KYC_REGULATIONS = [
    {
        "id": "reg_uk_mlr_001",
        "text": (
            "Under the Money Laundering Regulations 2017 (MLR 2017), Regulation 28 requires "
            "regulated firms to apply Customer Due Diligence (CDD) measures before establishing "
            "a business relationship. This includes verifying the customer's identity using "
            "reliable, independent source documents, data, or information."
        ),
        "metadata": {"source": "FCA", "section": "MLR 2017 Reg 28", "jurisdiction": "UK", "type": "cdd_requirement"},
    },
    {
        "id": "reg_uk_mlr_002",
        "text": (
            "Enhanced Due Diligence (EDD) is required for: (a) Politically Exposed Persons (PEPs), "
            "(b) customers from high-risk third countries identified by FATF, (c) complex or unusually "
            "large transactions, (d) other situations presenting a higher risk of money laundering. "
            "EDD measures include obtaining additional information on the customer, beneficial owner, "
            "and the reasons for intended or performed transactions."
        ),
        "metadata": {"source": "FCA", "section": "MLR 2017 Reg 33", "jurisdiction": "UK", "type": "edd_requirement"},
    },
    {
        "id": "reg_uk_mlr_003",
        "text": (
            "For legal entity customers, firms must identify and verify: (a) the legal entity's name, "
            "(b) registered office address, (c) company registration number or equivalent, "
            "(d) names of directors or equivalent senior management, (e) the nature of the entity's "
            "business, (f) the names and identity of beneficial owners holding 25% or more shares or voting rights."
        ),
        "metadata": {"source": "FCA", "section": "MLR 2017 Reg 28(3)", "jurisdiction": "UK", "type": "corporate_kyc"},
    },
    {
        "id": "reg_us_bsa_001",
        "text": (
            "Under the Bank Secrecy Act (BSA), financial institutions must file a Currency Transaction "
            "Report (CTR) for cash transactions exceeding $10,000. Suspicious Activity Reports (SARs) "
            "must be filed for transactions of $5,000 or more where the institution suspects the "
            "transaction involves funds from illegal activity or is designed to evade BSA requirements."
        ),
        "metadata": {"source": "FinCEN", "section": "BSA/AML", "jurisdiction": "US", "type": "sar_requirement"},
    },
    {
        "id": "reg_eu_5amld_001",
        "text": (
            "The EU 5th Anti-Money Laundering Directive (5AMLD) requires customer identification "
            "using at least two independent sources. For remote/digital onboarding, electronic "
            "identification methods must be approved under eIDAS regulation or equivalent. "
            "Video identification is accepted as an alternative in Germany (BaFin) and other EU states."
        ),
        "metadata": {"source": "EU", "section": "5AMLD Art 13", "jurisdiction": "EU", "type": "remote_onboarding"},
    },
]

PRODUCT_POLICIES = [
    {
        "id": "pol_biz_acct_uk_001",
        "text": (
            "Business Current Account — Eligibility for UK Limited Companies: "
            "1. Must be a UK-registered limited company (Companies House registration required). "
            "2. Registered office must be in the UK. "
            "3. At least one director must be a UK resident or EEA national. "
            "4. Required documents: Certificate of Incorporation, Articles of Association, "
            "proof of registered address, director IDs, and UBO declarations if applicable. "
            "5. Minimum opening deposit: £100."
        ),
        "metadata": {"product": "business_current_account", "region": "UK", "version": "2024-Q3"},
    },
    {
        "id": "pol_biz_acct_uk_002",
        "text": (
            "Business Current Account — Eligibility for Sole Traders: "
            "1. Must be UK resident with a valid National Insurance number. "
            "2. Trading must have been active for at least 3 months. "
            "3. Required documents: Proof of identity (passport/driving licence), "
            "proof of address (utility bill/bank statement dated within 3 months), "
            "HMRC UTR number for self-assessment. "
            "4. No minimum deposit required."
        ),
        "metadata": {"product": "business_current_account", "region": "UK", "version": "2024-Q3"},
    },
    {
        "id": "pol_personal_acct_001",
        "text": (
            "Personal Current Account — Eligibility: "
            "1. Must be 18 years or older. "
            "2. Must be a UK resident (including EU nationals with settled/pre-settled status). "
            "3. Required documents: Valid photo ID, proof of UK address. "
            "4. Non-UK nationals: Valid passport + valid visa/BRP + proof of UK address. "
            "5. For under-18s: Junior savings account available with parent/guardian consent."
        ),
        "metadata": {"product": "personal_current_account", "region": "UK", "version": "2024-Q3"},
    },
    {
        "id": "pol_risk_tiers_001",
        "text": (
            "Customer Risk Tiers: "
            "Tier 1 (Low Risk): Individual UK resident, verified identity, no sanctions hits, "
            "no PEP status, no adverse media, standard products. Review cycle: every 5 years. "
            "Tier 2 (Medium Risk): Business accounts, foreign nationals, PEP-adjacent, moderate "
            "complexity. Enhanced monitoring. Review cycle: every 3 years. "
            "Tier 3 (High Risk): High-risk jurisdictions, complex structures, PEPs, adverse media, "
            "cash-intensive businesses. Full EDD required. Review cycle: every 12 months."
        ),
        "metadata": {"topic": "risk_tiers", "version": "2024-Q3"},
    },
]

DOCUMENT_SCHEMAS = [
    {
        "id": "doc_passport_001",
        "text": (
            "Passport verification schema — Required fields: full_name (must match application), "
            "nationality (ISO 3166-1 alpha-2), date_of_birth (YYYY-MM-DD), passport_number "
            "(alphanumeric, country-specific format), expiry_date (must be valid for 6+ months). "
            "Additional checks: photo quality assessment, MRZ code validation, "
            "hologram/security feature detection. Rejection criteria: expired document, "
            "name mismatch > 2 characters, photo similarity < 0.7."
        ),
        "metadata": {"doc_type": "passport", "fields": ["full_name", "nationality", "date_of_birth", "passport_number", "expiry_date"]},
    },
    {
        "id": "doc_drivers_licence_001",
        "text": (
            "Driver's licence verification schema — Required fields: full_name, date_of_birth, "
            "licence_number (format varies by country), address, expiry_date, photo. "
            "Acceptable as proof of identity AND proof of address if address is printed. "
            "Must be a full (non-provisional) licence for some products. "
            "Rejection criteria: expired, provisional only, address not matching application."
        ),
        "metadata": {"doc_type": "drivers_license", "fields": ["full_name", "date_of_birth", "licence_number", "address", "expiry_date"]},
    },
    {
        "id": "doc_proof_address_001",
        "text": (
            "Proof of address schema — Required fields: full_name (must match applicant), "
            "address (must match application), utility_provider or bank_name, issue_date. "
            "Accepted documents: utility bill (gas, electric, water, broadband), bank statement, "
            "council tax bill, tenancy agreement, NHS letter. "
            "Must be dated within the last 3 months. "
            "Rejection criteria: older than 3 months, name mismatch, address mismatch, "
            "mobile phone bills not accepted."
        ),
        "metadata": {"doc_type": "proof_of_address", "fields": ["full_name", "address", "utility_provider", "issue_date"]},
    },
    {
        "id": "doc_articles_001",
        "text": (
            "Articles of Incorporation / Certificate of Incorporation schema — Required fields: "
            "company_name, registration_number (Companies House format), registered_address, "
            "incorporation_date, director_names. "
            "Must be an original or certified copy. Companies House printout accepted. "
            "Additional for beneficial ownership: PSC (Persons with Significant Control) "
            "register showing individuals with 25%+ ownership or voting rights."
        ),
        "metadata": {"doc_type": "articles_of_incorporation", "fields": ["company_name", "registration_number", "registered_address", "incorporation_date"]},
    },
]

RISK_TYPOLOGIES = [
    {
        "id": "risk_high_indicators_001",
        "text": (
            "High-risk indicators for business accounts: "
            "(a) Complex ownership structures with multiple layers of holding companies, "
            "(b) Company registered in a high-risk jurisdiction (FATF grey/black list), "
            "(c) Beneficial owners who are PEPs or PEP family members, "
            "(d) Adverse media concerning money laundering, terrorism financing, or sanctions evasion, "
            "(e) Cash-intensive business model without clear economic rationale, "
            "(f) Unusually high transaction volumes expected relative to stated business purpose. "
            "Action: Full EDD required. Escalate to MLRO for decision."
        ),
        "metadata": {"risk": "high", "category": "business", "applies": ["UK", "EU", "US"]},
    },
    {
        "id": "risk_medium_indicators_001",
        "text": (
            "Medium-risk indicators: "
            "(a) Foreign national without long UK residency history, "
            "(b) Business in regulated industry (e.g., crypto, gambling, arms), "
            "(c) Customer operating in multiple jurisdictions, "
            "(d) PEP-adjacent relationships (family, close associates), "
            "(e) Non-standard product requests (high-value transfers, multiple accounts). "
            "Action: Enhanced monitoring, additional documentation may be requested."
        ),
        "metadata": {"risk": "medium", "category": "general", "applies": ["UK", "EU", "US"]},
    },
    {
        "id": "risk_low_indicators_001",
        "text": (
            "Low-risk indicators — typical profile for streamlined onboarding: "
            "(a) UK resident individual with verifiable address, "
            "(b) Standard personal or simple business account, "
            "(c) No sanctions or PEP flags, "
            "(d) No adverse media, "
            "(e) Clear source of funds. "
            "Action: Standard CDD sufficient. Auto-approval eligible if all checks pass."
        ),
        "metadata": {"risk": "low", "category": "general", "applies": ["UK"]},
    },
]

PAST_KYC_DECISIONS = [
    {
        "id": "case_approved_001",
        "text": (
            "Approved: UK Ltd (fintech sector), beneficial ownership clearly disclosed. "
            "Three UBOs each holding 30%+ shares, all UK residents with verifiable identities. "
            "No sanctions hits, no PEP, no adverse media. Company registered 2019, "
            "trading history available. Account opened with standard monitoring. "
            "Risk rating: Medium (fintech sector). Review: 3 years."
        ),
        "metadata": {"decision": "approved", "risk": "medium", "sector": "fintech"},
    },
    {
        "id": "case_approved_002",
        "text": (
            "Approved: Individual personal account. UK resident, EU national with settled status. "
            "Passport verified, proof of address confirmed (utility bill within 1 month). "
            "No flags on any screening. Standard salary account. "
            "Risk rating: Low. Auto-approved. Review: 5 years."
        ),
        "metadata": {"decision": "approved", "risk": "low", "sector": "personal"},
    },
    {
        "id": "case_rejected_001",
        "text": (
            "Rejected: Offshore company registered in BVI. Beneficial ownership could not be "
            "independently verified. Director refused to provide personal identification. "
            "Adverse media found linking company to corruption investigation. "
            "Sanctions screening: potential match (requires manual verification). "
            "Decision: Application rejected due to inability to complete CDD. "
            "SAR filed with NCA."
        ),
        "metadata": {"decision": "rejected", "risk": "high", "sector": "offshore"},
    },
    {
        "id": "case_review_001",
        "text": (
            "Approved with conditions: Charity organization (UK registered). Complex funding "
            "structure with international donors. All UK-based directors verified. "
            "No sanctions, no PEP, but some adverse media mentioning the charity in a "
            "negative context (unrelated to financial crime). Enhanced monitoring applied. "
            "Annual review cycle. Transaction limits imposed pending first-year review."
        ),
        "metadata": {"decision": "approved_with_conditions", "risk": "medium", "sector": "charity"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map: dict[str, list[dict]] = {
        "kyc_regulations": KYC_REGULATIONS,
        "product_policies": PRODUCT_POLICIES,
        "document_schemas": DOCUMENT_SCHEMAS,
        "risk_typologies": RISK_TYPOLOGIES,
        "past_kyc_decisions": PAST_KYC_DECISIONS,
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
