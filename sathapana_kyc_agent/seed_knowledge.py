"""
Seed script: Populate the vector store with Sathapana Bank / NBC KYC knowledge.

Cambodia-localized content: the 2020 Law on AML/CFT, NBC KYC requirements,
document schemas for Khmer identity documents, Cambodia-specific risk
typologies (casino/gaming, cash-intensive sectors), Sathapana product
policies, and past KYC decisions.

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS
from config import settings

# ── NBC Regulatory Content ────────────────────────────────────────
NBC_REGULATIONS = [
    {
        "id": "reg_kh_aml_law_001",
        "text": (
            "Under the Kingdom of Cambodia Law on Anti-Money Laundering and Combating the "
            "Financing of Terrorism (promulgated 2020), financial institutions must apply "
            "Customer Due Diligence (CDD) before establishing a business relationship or "
            "conducting an occasional transaction. CDD comprises: (a) identifying the "
            "customer by reliable, independent source documents; (b) understanding the "
            "purpose and intended nature of the business relationship; (c) conducting "
            "ongoing due diligence on the relationship and transactions."
        ),
        "metadata": {"source": "NBC", "section": "AML/CFT Law 2020, CDD Obligations", "jurisdiction": "KH", "type": "cdd_requirement", "language": "en"},
    },
    {
        "id": "reg_kh_aml_law_002",
        "text": (
            "Enhanced Due Diligence (EDD) under Cambodia's AML/CFT Law applies to: "
            "(a) Politically Exposed Persons (PEPs) and their family/close associates; "
            "(b) customers from high-risk jurisdictions identified by FATF; "
            "(c) complex, unusually large transactions with no clear economic purpose; "
            "(d) customers connected to gambling, gaming and casino activities; "
            "(e) situations presenting higher risk of money laundering or terrorist financing. "
            "EDD includes additional identity information, source-of-funds verification, "
            "senior management approval to establish the relationship, and enhanced monitoring."
        ),
        "metadata": {"source": "NBC", "section": "AML/CFT Law 2020, EDD", "jurisdiction": "KH", "type": "edd_requirement", "language": "en"},
    },
    {
        "id": "reg_kh_ubo_001",
        "text": (
            "For legal persons and legal arrangements, Cambodian institutions must identify "
            "and take reasonable steps to verify the beneficial owner. The beneficial owner "
            "is the natural person who ultimately owns or controls the legal person, "
            "including persons holding a significant ownership interest or exercising "
            "effective control. NBC risk-based guidance applies reduced thresholds "
            "(e.g. 10%) for customers identified as higher risk; the default registration "
            "threshold follows FATF standards (25%). Information on UBOs must be obtained "
            "before account opening and kept current."
        ),
        "metadata": {"source": "NBC", "section": "UBO / CDD on legal persons", "jurisdiction": "KH", "type": "ubo_requirement", "language": "en"},
    },
    {
        "id": "reg_kh_reporting_001",
        "text": (
            "Reporting obligations: institutions must report suspicious or unusual "
            "transactions to the Cambodia Financial Intelligence Unit (CAMFIU) proactively. "
            "Banks also file currency/border transaction reports required by NBC regulations "
            "and retain KYC documentation — including copies of identification, beneficial "
            "ownership information, and account files — for at least five years after the "
            "end of the relationship."
        ),
        "metadata": {"source": "NBC/CAMFIU", "section": "Reporting & Record Keeping", "jurisdiction": "KH", "type": "sar_requirement", "language": "en"},
    },
    {
        "id": "reg_kh_sanctions_001",
        "text": (
            "Every customer must be screened before onboarding against: "
            "(a) the United Nations Security Council consolidated sanctions lists "
            "(including UNSCR 1267/1989 terrorist designations and UNSCR 1718), "
            "(b) NBC-disclosed and Cambodia-issued targeted financial sanctions, "
            "(c) prudent foreign regimes relied upon by the bank (OFAC, EU), and "
            "(d) domestically relevant PEP lists (Cambodian high-level officials and "
            "their family/associates). A positive hit requires filing with CAMFIU and "
            "freezing of funds pending guidance; onboarding must not proceed."
        ),
        "metadata": {"source": "NBC", "section": "Targeted Financial Sanctions", "jurisdiction": "KH", "type": "sanctions_requirement", "language": "en"},
    },
    {
        "id": "reg_kh_docs_001",
        "text": (
            "Accepted identity documents for Cambodian nationals: the Khmer National "
            "Identification Card (issued by General Department of Identification), a valid "
            "Cambodian passport, or a family/residence book supported by a photo ID. "
            "Foreign nationals: valid passport with valid visa/permit; additional residence "
            "proof required. Proof of address may include utility bills, rental or land "
            "agreements, landlord letters, or commune/village certificates — Cambodia does "
            "not rely on postal addressing, so geolocation and reference persons are accepted."
        ),
        "metadata": {"source": "NBC", "section": "Documentation", "jurisdiction": "KH", "type": "documentation", "language": "en"},
    },
    {
        "id": "reg_fatf_kh_001",
        "text": (
            "Cambodia was removed from the FATF grey list in February 2023 following "
            "compliance actions including the 2020 AML/CFT Law and improved supervision. "
            "Cambodia remains in FATF enhanced follow-up, so financial institutions must "
            "monitor risks in sectors named in past CAR recommendations: casinos and junkets, "
            "money service providers, the real-estate sector, and cash-intensive businesses. "
            "Customers connected to these sectors warrant strengthened measures."
        ),
        "metadata": {"source": "FATF", "section": "Cambodia jurisdiction risk", "jurisdiction": "KH", "type": "jurisdiction_risk", "language": "en"},
    },
]

# ── Sathapana Product Policies ────────────────────────────────────
PRODUCT_POLICIES = [
    {
        "id": "pol_retail_savings_kh_001",
        "text": (
            "Retail Savings / Current Account (USD & KHR): Cambodian national or foreign "
            "resident aged 18+. Documents: National ID Card or passport, xerox copy of "
            "family/residence book or lease, telephone number. For foreign residents: valid "
            "passport, visa/permit, and employer confirmation or residence proof. "
            "Minimum opening deposit: USD 25 (or KHR 100,000). Dual-currency optionality; "
            "Bakong mobile linkage available after account opening."
        ),
        "metadata": {"product": "retail_savings", "region": "KH", "version": "2026-Q3"},
    },
    {
        "id": "pol_sme_loan_kh_001",
        "text": (
            "SME Loan Account: business must hold a valid Business Registration Certificate "
            "from the Ministry of Commerce and a tax registration (Patent) certificate from "
            "the General Department of Taxation. Documents: registration and patent "
            "certificates, VAT identification number, business license, 6 months bank "
            "statements, proof of address (lease or ownership title — including "
            "land/hard title where available), owner/director IDs and UBO declaration. "
            "Collateral typically required; cash-flow and collateral-based underwriting."
        ),
        "metadata": {"product": "sme_loan", "region": "KH", "version": "2026-Q3"},
    },
    {
        "id": "pol_corporate_kh_001",
        "text": (
            "Corporate Account: company registered with the Ministry of Commerce (MoC) "
            "certificate of incorporation, patent/VATIN registration, board resolution "
            "appointing signatories, list of directors and shareholding, UBO declaration "
            "with identity verification of each beneficial owner meeting the threshold, "
            "and proof of registered address. Non-resident companies may be accepted "
            "under EDD with HQ confirmation and group account opening standards."
        ),
        "metadata": {"product": "corporate_account", "region": "KH", "version": "2026-Q3"},
    },
    {
        "id": "pol_risk_tiers_kh_001",
        "text": (
            "Customer Risk Tiers (Sathapana / NBC-aligned): Tier 1 (Low): Cambodian "
            "resident individual, standard retail products, verified ID, clean screening; "
            "review every 5 years. Tier 2 (Medium): SME/corporate customers, foreign "
            "residents, moderate complexity, cash-intensive retail trade; enhanced "
            "monitoring; review every 3 years. Tier 3 (High): casino/gaming, money "
            "service providers, PEPs and associates, complex structures, adverse media; "
            "full EDD with senior management approval; review every 12 months or less."
        ),
        "metadata": {"topic": "risk_tiers", "region": "KH", "version": "2026-Q3"},
    },
]

# ── Cambodia Document Schemas ─────────────────────────────────────
DOCUMENT_SCHEMAS = [
    {
        "id": "doc_national_id_kh_001",
        "text": (
            "Khmer National ID Card schema — Required fields: full_name (Khmer and Latin "
            "transliteration), gender, date_of_birth (YYYY-MM-DD), id_number, address "
            "(village, commune, district, province), issue_date, expiry_date, photo. "
            "Checks: Khmer script OCR support required, MRZ/secure print inspection for "
            "older cards, photo quality. Rejection: expired or battered card, "
            "name/photo mismatch, suspected forgery."
        ),
        "metadata": {"doc_type": "national_id", "fields": ["full_name_kh", "full_name_latin", "gender", "date_of_birth", "id_number", "address", "issue_date", "expiry_date"], "language": "km"},
    },
    {
        "id": "doc_passport_kh_001",
        "text": (
            "Cambodian Passport schema — Required fields: full_name, nationality (KH), "
            "date_of_birth, passport_number, issue_date, expiry_date, MRZ line, photo. "
            "Foreign passports accepted for non-residents with valid visa/permit. "
            "Checks: MRZ validation, duplicate-issuance log, liveness. Rejection: expired "
            "(must be valid for onboarding), MRZ mismatch, suspected tampering."
        ),
        "metadata": {"doc_type": "passport", "fields": ["full_name", "nationality", "date_of_birth", "passport_number", "issue_date", "expiry_date", "mrz"], "language": "km"},
    },
    {
        "id": "doc_family_book_kh_001",
        "text": (
            "Family Book / Residence Book schema — Required fields: household head name, "
            "member names and relationship, date of birth of members, address (village, "
            "commune, district, province), book number, issuing commune. Used mainly to "
            "corroborate address and household composition; must be paired with a photo ID "
            "of the applicant. Rejection: book not matching applicant address, "
            "unverifiable issuing commune."
        ),
        "metadata": {"doc_type": "family_book", "fields": ["household_head", "members", "address", "book_number", "issuing_commune"], "language": "km"},
    },
    {
        "id": "doc_business_reg_kh_001",
        "text": (
            "Business Registration Certificate (Ministry of Commerce) schema — Required "
            "fields: company_name (Khmer and English), MoC registration number, date of "
            "registration, registered address, legal form, owner/director names, "
            "authorized capital. Verified against the MoC public registry where possible. "
            "Rejection: expired, suspended, or mismatched details against the registry."
        ),
        "metadata": {"doc_type": "business_registration", "fields": ["company_name", "registration_number", "registration_date", "registered_address", "legal_form", "directors", "authorized_capital"], "language": "km"},
    },
    {
        "id": "doc_tax_patent_kh_001",
        "text": (
            "Tax Registration (Patent) Certificate / VATIN schema — Required fields: "
            "taxpayer name, VAT identification number (VATIN), patent year, patent series, "
            "business activity, registered address. Confirms the business is in good "
            "standing with the General Department of Taxation. Rejection: expired patent, "
            "mismatched taxpayer name."
        ),
        "metadata": {"doc_type": "tax_certificate", "fields": ["taxpayer_name", "vatin", "patent_year", "patent_series", "business_activity", "address"], "language": "km"},
    },
    {
        "id": "doc_address_kh_001",
        "text": (
            "Proof of address (Cambodia) schema — Required fields: full_name, address "
            "(village, commune, district, province), document type, issue date, reference "
            "person or geolocation. Accepted: utility statements, rental or land agreement, "
            "landlord reference letter, commune/village certificate. Given Cambodia's "
            "addressing norms, GPS coordinates and a referee's contact are acceptable "
            "supplements. Rejection: name mismatch, document older than accepted validity, "
            "no verifiable location."
        ),
        "metadata": {"doc_type": "proof_of_address", "fields": ["full_name", "address", "document_type", "issue_date", "reference"], "language": "km"},
    },
    {
        "id": "doc_collateral_kh_001",
        "text": (
            "Collateral documents (SME) schema — Hard (land) title issued by the Ministry "
            "of Land Management or certified transfer documents, vehicle title, or "
            "registered movable security. Required fields: owner name(s), certificate "
            "number, parcel/village identification, encumbrance status. Rejection: "
            "informal paper/soft titles without cadastral validation, mismatched owner, "
            "existing encumbrances not disclosed."
        ),
        "metadata": {"doc_type": "collateral", "fields": ["owner_name", "certificate_number", "parcel_id", "encumbrance_status"], "language": "km"},
    },
]

# ── Cambodia Risk Typologies ──────────────────────────────────────
RISK_TYPOLOGIES = [
    {
        "id": "risk_high_casino_kh_001",
        "text": (
            "High-risk: casino and gaming operators, junket promoters, and persons whose "
            "funds derive from gambling proceeds. Cambodia licenses casinos under the "
            "Law on Management of Commercial Gambling (2020). Indicators: chip/bet cash "
            "flows, commission-based junket structures, cash-heavy operations. Action: "
            "prohibited or full EDD with senior management approval, source-of-funds "
            "verification, enhanced monitoring; file STR to CAMFIU where warranted."
        ),
        "metadata": {"risk": "high", "category": "gambling", "applies": ["KH"]},
    },
    {
        "id": "risk_high_cashintensive_kh_001",
        "text": (
            "High-risk: cash-intensive businesses — gold and precious-metals dealers, "
            "pawnshops, money changers / money service providers, fuel and commodity "
            "traders, and real-estate developers accepting large cash. Indicators: cash "
            "deposits inconsistent with stated business, layered cash withdrawals, "
            "unexplained third-party funding, thin accounting. Address verification and "
            "source-of-funds proof are mandatory; monitoring thresholds tightened."
        ),
        "metadata": {"risk": "high", "category": "cash_intensive", "applies": ["KH"]},
    },
    {
        "id": "risk_high_pep_kh_001",
        "text": (
            "High-risk: Cambodian PEPs — high-ranking officials in government, the National "
            "Assembly, the judiciary, the military/police, central bank and SOE leadership, "
            "plus their family members and close associates. EDD is mandatory: source of "
            "wealth and source of funds, senior management approval to establish the "
            "relationship, ongoing enhanced monitoring."
        ),
        "metadata": {"risk": "high", "category": "pep", "applies": ["KH"]},
    },
    {
        "id": "risk_medium_crossborder_kh_001",
        "text": (
            "Medium-risk: cross-border and trade-linked exposure along Cambodia's borders "
            "and remittance corridors (Thai baht and USD, informal value transfer). "
            "Indicators: frequent border-adjacent activity, inconsistent trade documents, "
            "TF/odious-nature sectors, reliance on cash couriers. Mitigation: verify "
            "economic substance, capture transaction purpose, screen counterparties, "
            "monitor for structuring."
        ),
        "metadata": {"risk": "medium", "category": "cross_border", "applies": ["KH"]},
    },
    {
        "id": "risk_low_retail_kh_001",
        "text": (
            "Low-risk profile — streamlined onboarding eligible: Cambodian resident "
            "individual, standard retail savings/current account, verified national ID, "
            "clean screening (no sanctions, no PEP, no adverse media), salary or "
            "low-turnover cash flows consistent with stated purpose. Standard CDD "
            "sufficient; auto-approval eligible when all checks pass; review every 5 years."
        ),
        "metadata": {"risk": "low", "category": "retail", "applies": ["KH"]},
    },
]

# ── Past KYC Decisions (Cambodia context) ─────────────────────────
PAST_KYC_DECISIONS = [
    {
        "id": "case_approved_kh_001",
        "text": (
            "Approved: Cambodian individual, retail savings account in USD and KHR. "
            "National ID verified (liveness pass), family book corroborated address in "
            "Phnom Penh, screening clear on UNSC/OFAC/EU and domestic PEP list. Salary-"
            "funded. Risk: Low. Auto-approved under standard CDD. Bakong linkage "
            "completed post-opening. Review: 5 years."
        ),
        "metadata": {"decision": "approved", "risk": "low", "sector": "retail", "jurisdiction": "KH"},
    },
    {
        "id": "case_approved_kh_002",
        "text": (
            "Approved with conditions: SME garment trading company with MoC registration "
            "and patent certificate. UBO was sole shareholder (100%); identity verified, "
            "screening clear. Collateral: hard land title. Conditions: EDD applied as the "
            "sector is cash-intensive retail; monthly monitoring, transaction thresholds "
            "set, annual review. Approved by senior management."
        ),
        "metadata": {"decision": "approved_with_conditions", "risk": "medium", "sector": "sme", "jurisdiction": "KH"},
    },
    {
        "id": "case_rejected_kh_001",
        "text": (
            "Rejected and STR filed to CAMFIU: applicant linked to a casino junket "
            "operation; source of funds could not be established; cash volumes "
            "inconsistent with declared activity; name appeared in adverse media "
            "connected to gambling debts. Identity partially verified only. CDD could not "
            "be completed, relationship declined, suspicious transaction report filed."
        ),
        "metadata": {"decision": "rejected", "risk": "high", "sector": "gambling", "jurisdiction": "KH"},
    },
    {
        "id": "case_rejected_kh_002",
        "text": (
            "Rejected: screening hit on UN Consolidated List (potential match). Customer "
            "details matched on name and approximate DOB against a UNSCR 1267 "
            "designation related to terrorist financing. Onboarding prohibited; funds, if "
            "any, subject to freezing guidelines; CAMFIU notified."
        ),
        "metadata": {"decision": "rejected", "risk": "critical", "sector": "unsc_hit", "jurisdiction": "KH"},
    },
]


def seed(rag: RAGPipeline | None = None) -> None:
    """Seed all collections with NBC/Sathapana content (idempotent)."""
    print("Initializing RAG pipeline...")
    rag = rag or RAGPipeline()

    for name in COLLECTIONS:
        full = f"{settings.vector_collection_prefix}_{name}"
        rag.store.reset(full)
    for name in COLLECTIONS:
        full = f"{settings.vector_collection_prefix}_{name}"
        rag.store.get_or_create_collection(full)

    data_map: dict[str, list[dict]] = {
        "nbc_regulations": NBC_REGULATIONS,
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
        print(f"  [OK] {collection_name}: {rag.collection_count(collection_name)} documents")

    print("[OK] Sathapana/NBC knowledge base seeded successfully!")
    for name in COLLECTIONS:
        print(f"  - {name}: {rag.collection_count(name)} documents")


if __name__ == "__main__":
    seed()