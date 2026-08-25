"""
Seed script: Populate ChromaDB with AML knowledge base data.

Includes:
- AML regulations (BSA, PATRIOT Act, CTA, OFAC)
- Red flag typologies (structuring, layering, trade-based, shell companies)
- SAR filing guidelines (FinCEN requirements, timelines, narratives)
- CTR requirements (filing, aggregation, exemptions)
- PEP guidelines (identification, risk assessment, enhanced due diligence)
- Beneficial ownership rules (CDD, FinCEN rules, verification)
- Sanctions regulations (OFAC SDN, EU, UN sanctions)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  AML REGULATIONS
# ══════════════════════════════════════════════════════════════════

AML_REGULATIONS = [
    {
        "id": "reg_bsa_001",
        "text": "Bank Secrecy Act (BSA): The foundational U.S. anti-money laundering law requiring financial institutions to assist government agencies in detecting and preventing money laundering. Key requirements include: 1) Currency Transaction Reports (CTRs) for cash transactions over $10,000, 2) Suspicious Activity Reports (SARs) for suspicious transactions of $5,000+, 3) Customer identification programs, 4) Record keeping requirements, 5) Compliance program requirements including designation of BSA compliance officer, training, and independent testing.",
        "metadata": {"source": "FinCEN", "section": "BSA", "jurisdiction": "US", "type": "regulation"},
    },
    {
        "id": "reg_patriot_001",
        "text": "USA PATRIOT Act (2001): Strengthened BSA requirements post-9/11. Title III enhanced AML provisions including: 1) Enhanced due diligence for correspondent and private banking accounts, 2) Customer identification program (CIP) requirements, 3) Information sharing between financial institutions and law enforcement, 4) Enhanced monitoring of high-risk accounts, 5) Due diligence programs for private banking accounts held by non-U.S. persons. Section 314(a) enables law enforcement to request financial institution assistance in investigations. Section 314(b) allows voluntary information sharing between institutions.",
        "metadata": {"source": "FinCEN", "section": "PATRIOT Act", "jurisdiction": "US", "type": "regulation"},
    },
    {
        "id": "reg_cta_001",
        "text": "Corporate Transparency Act (CTA) (2024): Requires most companies to report beneficial ownership information (BOI) to FinCEN. Key provisions: 1) Companies must report individuals who own or control at least 25% of the company, 2) Reporting must occur within 30 days of company creation (for new entities), 3) Updated reports required within 30 days of changes, 4) FinCEN maintains a non-public BOI database accessible to law enforcement and financial institutions with customer consent, 5) Penalties for willful non-compliance include civil fines of up to $500/day and criminal penalties of up to 2 years imprisonment.",
        "metadata": {"source": "FinCEN", "section": "CTA", "jurisdiction": "US", "type": "regulation"},
    },
    {
        "id": "reg_ofac_001",
        "text": "OFAC Sanctions Program: The Office of Foreign Assets Control (OFAC) administers and enforces economic sanctions programs against targeted foreign countries, regimes, terrorists, international narcotics traffickers, and those engaged in proliferation of WMD. Financial institutions must: 1) Screen all transactions against the SDN (Specially Designated Nationals) list, 2) Block/reject transactions involving sanctioned parties, 3) File blocking reports within 10 business days, 4) Maintain records for 5 years, 5) Face strict liability for sanctions violations — no intent requirement. Penalties can reach millions of dollars per violation.",
        "metadata": {"source": "OFAC", "section": "Sanctions", "jurisdiction": "US", "type": "regulation"},
    },
    {
        "id": "reg_bsa_program_001",
        "text": "BSA/AML Compliance Program Requirements (31 CFR 1020.210): Every financial institution must establish and maintain an effective AML program that includes: 1) Designation of a BSA compliance officer, 2) AML policies, procedures, and controls, 3) Ongoing employee training, 4) Independent testing/audit, 5) Risk-based procedures for conducting ongoing customer due diligence (CDD), 6) Beneficial ownership identification and verification for legal entity customers. The program must be commensurate with the institution's size, complexity, and risk profile.",
        "metadata": {"source": "FinCEN", "section": "BSA 1020.210", "jurisdiction": "US", "type": "compliance"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  RED FLAG TYPOLOGIES
# ══════════════════════════════════════════════════════════════════

RED_FLAGTYPOLOGIES = [
    {
        "id": "type_structuring_001",
        "text": "Structuring (Smurfing): Deliberately breaking large amounts of money into smaller transactions to avoid CTR reporting thresholds. Red flags: 1) Multiple cash deposits/withdrawals just below $10,000, 2) Multiple individuals making deposits to the same account, 3) Pattern of round-number transactions, 4) Cash deposits followed immediately by wire transfers, 5) Accounts with high cash activity inconsistent with business type. Structuring is a federal crime under 31 USC 5324, even if the underlying funds are legitimate.",
        "metadata": {"category": "structuring", "severity": "critical", "typology": "hiding_funds"},
    },
    {
        "id": "type_layering_001",
        "text": "Layering: Complex series of transactions designed to obscure the audit trail and distance illicit funds from their source. Red flags: 1) Rapid movement of funds through multiple accounts, 2) Wire transfers to/from high-risk jurisdictions, 3) Transactions with no apparent economic purpose, 4) Use of shell companies across multiple jurisdictions, 5) Circular fund flows (funds returning to originator through intermediaries), 6) Multiple currency conversions, 7) Complex corporate structures with no clear business rationale.",
        "metadata": {"category": "layering", "severity": "high", "typology": "obfuscation"},
    },
    {
        "id": "type_trade_based_001",
        "text": "Trade-Based Money Laundering (TBML): Uses trade transactions to move value and disguise the origin of funds. Red flags: 1) Over/under-invoicing of goods, 2) Multiple invoicing for the same shipment, 3) Goods inconsistent with the parties' business profiles, 4) Shipping routes inconsistent with trade patterns, 5) Significant discrepancies between goods description and value, 6) Unusual payment terms (advance payment with no guarantee), 7) Shell companies used as intermediaries, 8) Frequent amendments to letters of credit.",
        "metadata": {"category": "trade_based", "severity": "high", "typology": "trade_misuse"},
    },
    {
        "id": "type_shell_001",
        "text": "Shell Company Abuse: Use of companies with no active business or minimal employees to layer illicit funds. Red flags: 1) Company registered in secrecy jurisdiction, 2) Nominee directors/shareholders, 3) Multiple companies sharing registered address, 4) Rapid formation and dissolution, 5) No physical office or employees, 6) Bank accounts in multiple jurisdictions, 7) Beneficial owner cannot be determined, 8) Company exists only on paper with no tangible operations.",
        "metadata": {"category": "shell_company", "severity": "critical", "typology": "obfuscation"},
    },
    {
        "id": "type_real_estate_001",
        "text": "Real Estate Money Laundering: Using real estate purchases to launder funds. Red flags: 1) All-cash purchases above $300,000, 2) Purchases through LLC or shell company, 3) Below-market transactions, 4) Rapid resale (flipping), 5) Purchase from/offshore shell company, 6) Buyer in high-risk jurisdiction, 7) No apparent source of funds, 8) Properties used as collateral for loans (extraction), 9) Geographic areas known for real estate laundering.",
        "metadata": {"category": "real_estate", "severity": "high", "typology": "asset_laundering"},
    },
    {
        "id": "type_crypto_001",
        "text": "Cryptocurrency Money Laundering: Using digital assets to obscure fund origins. Red flags: 1) Large deposits converted to crypto and immediately transferred, 2) Use of mixing/tumbling services, 3) Privacy coins (Monero, Zcash), 4) Rapid conversion between crypto and fiat, 5) Transactions through multiple wallets, 6) Use of unhosted wallets, 7) Peer-to-peer exchange activity, 8) DeFi protocol usage for obfuscation, 9) NFT purchases with unexplained funds.",
        "metadata": {"category": "cryptocurrency", "severity": "high", "typology": "digital_asset"},
    },
    {
        "id": "type_nras_001",
        "text": "Non-Resident Alien (NRA) Account Abuse: Using accounts held by non-residents to move funds. Red flags: 1) Large wire transfers from high-risk countries, 2) Funds passing through NRA account with no clear purpose, 3) Account used primarily for wire transfers, 4) Multiple NRA accounts with similar patterns, 5) Funds received from offshore and immediately wired elsewhere, 6) NRA account with domestic address inconsistent with residence.",
        "metadata": {"category": "nra_abuse", "severity": "medium", "typology": "cross_border"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  SAR FILING GUIDELINES
# ══════════════════════════════════════════════════════════════════

SAR_FILING_GUIDELINES = [
    {
        "id": "sar_requirements_001",
        "text": "SAR Filing Requirements (31 CFR 1020.320): A financial institution must file a SAR when it knows, suspects, or has reason to suspect that a transaction: 1) Involves funds derived from illegal activity, 2) Is designed to evade BSA reporting requirements, 3) Has no lawful purpose, or 4) Involves the use of the institution to facilitate criminal activity. Filing threshold: $5,000 or more. Filing deadline: 30 calendar days from initial detection (may extend to 60 days if suspect is unknown). Must be filed electronically via BSA E-Filing system. Retain copy for 5 years from filing date.",
        "metadata": {"source": "FinCEN", "section": "31 CFR 1020.320", "type": "filing_requirement"},
    },
    {
        "id": "sar_narrative_001",
        "text": "SAR Narrative Best Practices: The narrative section is the most important part of a SAR. It should answer: WHO is conducting the suspicious activity (full names, addresses, SSNs/TINs, dates of birth). WHAT instruments or methods are being used (account numbers, transaction types). WHEN did the activity occur (specific dates, time periods). WHERE did the activity take place (branches, locations, countries). WHY is the activity suspicious (specific red flags, patterns). HOW was the activity conducted (step-by-step flow of funds). The narrative should be concise, factual, and chronological. Avoid opinions, speculation, or conclusions about criminal activity.",
        "metadata": {"source": "FinCEN", "section": "SAR Narrative", "type": "best_practice"},
    },
    {
        "id": "sar_continuing_001",
        "text": "Continuing Activity SARs: When suspicious activity continues beyond the initial SAR filing, a continuing activity SAR must be filed every 90 days until: 1) The activity ceases, 2) The investigation is complete, or 3) The matter is referred to law enforcement. Each continuing SAR should reference the original SAR number and provide updates on the investigation. If no new information is available, file a continuing SAR noting 'No new information since last filing.' Track the 90-day cycle to ensure timely filings.",
        "metadata": {"source": "FinCEN", "section": "Continuing Activity", "type": "filing_requirement"},
    },
    {
        "id": "sar_voluntary_001",
        "text": "Voluntary Self-Disclosure (VSD): Financial institutions may voluntarily disclose BSA violations to FinCEN. Benefits: 1) May result in reduced penalties, 2) Demonstrates good faith compliance, 3) May prevent criminal referrals. Requirements: 1) Disclose the nature and extent of the violation, 2) Identify responsible individuals, 3) Describe remedial measures taken. VSD should be filed through FinCEN's BSA E-Filing system. Note: VSD is separate from SAR filing — both may be required.",
        "metadata": {"source": "FinCEN", "section": "VSD", "type": "best_practice"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CTR REQUIREMENTS
# ══════════════════════════════════════════════════════════════════

CTR_REQUIREMENTS = [
    {
        "id": "ctr_filing_001",
        "text": "Currency Transaction Report (CTR) Filing: Required for each currency transaction (cash or coin) exceeding $10,000 in a single business day. Must be filed within 15 calendar days of the transaction. Filed electronically via BSA E-Filing. Key data points: customer identification, transaction details, source of funds, occupation/business type. Exemptions exist for certain government agencies, banks, and specific account types. Penalties for failure to file: up to $100,000 per violation for negligent violations; criminal penalties for willful violations.",
        "metadata": {"source": "FinCEN", "section": "CTR", "jurisdiction": "US", "type": "filing_requirement"},
    },
    {
        "id": "ctr_aggregation_001",
        "text": "CTR Aggregation Rules: Multiple cash transactions that individually do not exceed $10,000 must be aggregated and reported as a single CTR if the financial institution knows or has reason to know that the transactions are designed to avoid reporting. Aggregation factors: 1) Same customer within a single business day, 2) Multiple transactions by related parties, 3) Transactions structured to avoid $10,000 threshold, 4) Pattern of just-below-threshold transactions. The 15-day look-back rule: if the institution identifies aggregation patterns, it must file CTR for the aggregated transactions within 15 days.",
        "metadata": {"source": "FinCEN", "section": "CTR Aggregation", "jurisdiction": "US", "type": "filing_requirement"},
    },
    {
        "id": "ctr_exemptions_001",
        "text": "CTR Exemptions: Certain transactions are exempt from CTR filing: 1) Transactions between domestic banks, 2) Transactions involving government agencies, 3) Transactions from clearly identified pre-existing accounts (exemption must be documented), 4) ATM transactions at bank-operated ATMs (with certain conditions). Exemption requirements: documented business rationale, written policies, compliance officer approval, periodic review of exemptions. Maintaining false exemptions can result in criminal penalties.",
        "metadata": {"source": "FinCEN", "section": "CTR Exemptions", "jurisdiction": "US", "type": "exemption"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  PEP GUIDELINES
# ══════════════════════════════════════════════════════════════════

PEP_GUIDELINES = [
    {
        "id": "pep_definition_001",
        "text": "Politically Exposed Persons (PEPs): Individuals who hold or have held prominent public functions. Categories: 1) Foreign PEPs — heads of state, senior politicians, senior government officials, judicial/military officials, senior executives of state-owned enterprises, important political party officials. 2) Domestic PEPs — same categories within the home jurisdiction. 3) International organization PEPs — senior officials of international organizations (UN, World Bank, IMF). 4) Relatives and close associates (RCAs) of all PEP categories. PEPs are not inherently suspicious — enhanced due diligence is required regardless of risk level.",
        "metadata": {"source": "FATF", "section": "PEP Definition", "type": "guideline"},
    },
    {
        "id": "pep_edd_001",
        "text": "PEP Enhanced Due Diligence (EDD): Required for all PEP relationships. Steps: 1) Identify PEP status through screening (ongoing monitoring), 2) Obtain senior management approval for establishing/maintaining relationship, 3) Establish source of funds and wealth, 4) Conduct enhanced ongoing monitoring, 5) Determine if transaction is consistent with known legitimate activities, 6) Document decision rationale. EDD must be proportionate to the risk level — higher-risk PEPs (e.g., heads of state) warrant more extensive due diligence.",
        "metadata": {"source": "FATF", "section": "PEP EDD", "type": "guideline"},
    },
    {
        "id": "pep_risk_assessment_001",
        "text": "PEP Risk Assessment Framework: Assess PEP risk based on: 1) Role and influence level (head of state > junior official), 2) Country risk (high-corruption jurisdictions increase risk), 3) Nature of the business relationship, 4) Transaction patterns and volumes, 5) Source of wealth clarity, 6) Adverse media screening results, 7) Previous regulatory actions. Risk tiers: Low (domestic PEP, low-risk country, clear source of wealth), Medium (senior official, moderate-risk country), High (head of state, high-risk country, unclear funds). Each tier determines monitoring frequency and EDD depth.",
        "metadata": {"source": "FATF", "section": "PEP Risk Assessment", "type": "guideline"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  BENEFICIAL OWNERSHIP RULES
# ══════════════════════════════════════════════════════════════════

BENEFICIAL_OWNERSHIP_RULES = [
    {
        "id": "bo_cdd_001",
        "text": "Customer Due Diligence (CDD) Rule — Beneficial Ownership: Financial institutions must identify and verify beneficial owners of legal entity customers at account opening. Definition of beneficial owner: 1) Each individual who, directly or indirectly, owns 25% or more of the equity interests of the legal entity (ownership prong), OR 2) A single individual with significant responsibility to control, manage, or direct the legal entity (control prong). Verification methods: 1) Certification from the customer, 2) Documentary verification (formation documents, ownership agreements), 3) Non-documentary verification (public databases, independent research). Must be completed within a reasonable time after account opening.",
        "metadata": {"source": "FinCEN", "section": "CDD Rule", "jurisdiction": "US", "type": "requirement"},
    },
    {
        "id": "bo_ultimate_001",
        "text": "Ultimate Beneficial Owner (UBO) Identification: For complex ownership structures, institutions must identify the natural person(s) who ultimately own or control 25% or more of the entity. When indirect ownership exists: 1) Trace through all intermediate entities, 2) Calculate effective ownership percentage at each level, 3) Identify any individual with ≥25% indirect ownership, 4) If no individual meets threshold, identify the senior managing official. Common structures requiring tracing: holding companies, trusts, partnerships, foundations, nominee arrangements. Enhanced scrutiny for ownership through multiple jurisdictions.",
        "metadata": {"source": "FATF", "section": "UBO Identification", "type": "guideline"},
    },
    {
        "id": "bo_ongoing_001",
        "text": "Beneficial Ownership Ongoing Monitoring: Institutions must maintain accurate beneficial ownership information and update when: 1) Customer provides updated information, 2) Institution becomes aware of changes, 3) During periodic reviews (risk-based schedule). Red flags for beneficial ownership: 1) Frequent changes in ownership, 2) Use of nominee shareholders, 3) Complex multi-layered structures, 4) Ownership by entities in secrecy jurisdictions, 5) Beneficial owner cannot be identified, 6) Inconsistency between stated ownership and entity activities. Failure to maintain accurate BO information is a compliance violation.",
        "metadata": {"source": "FinCEN", "section": "BO Monitoring", "type": "requirement"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  SANCTIONS REGULATIONS
# ══════════════════════════════════════════════════════════════════

SANCTIONS_REGULATIONS = [
    {
        "id": "sanctions_ofac_001",
        "text": "OFAC SDN List: The Specially Designated Nationals and Blocked Persons List maintained by OFAC. Contains individuals and entities owned/controlled by or acting for targeted countries, as well as those designated under terrorism, narcotics trafficking, WMD proliferation, and other sanctions programs. Financial institutions must: 1) Screen all transactions and customers against SDN list, 2) Block (freeze) assets of SDN-listed persons, 3) Prohibit all transactions with SDN-listed persons, 4) File blocking reports within 10 business days, 5) Maintain records for 5 years. Strict liability — no intent required for violations.",
        "metadata": {"source": "OFAC", "section": "SDN List", "jurisdiction": "US", "type": "sanctions"},
    },
    {
        "id": "sanctions_eu_001",
        "text": "EU Sanctions (Restrictive Measures): The European Union imposes restrictive measures against targeted countries, entities, and individuals. Key features: 1) Asset freezes, 2) Travel bans, 3) Arms embargoes, 4) Sectoral restrictions (finance, energy, defense). EU sanctions are implemented through Regulations directly applicable in all member states. Screening requirements: 1) Screen against EU consolidated list, 2) Apply to all EU-established entities, 3) Branch/subsidiary of EU bank must comply, 4) Penalties vary by member state but include criminal sanctions. Note: EU sanctions may differ from OFAC — dual compliance required.",
        "metadata": {"source": "EU", "section": "Restrictive Measures", "jurisdiction": "EU", "type": "sanctions"},
    },
    {
        "id": "sanctions_un_001",
        "text": "UN Security Council Sanctions: Binding on all UN member states. Maintained by UN Security Council Sanctions Committees. Lists: 1) Al-Qaida/ISIL sanctions list, 2) DPRK sanctions list, 3) Iran sanctions list, 4) Country-specific lists. Financial institutions must: 1) Screen against UN consolidated list, 2) Implement targeted asset freezes, 3) Report to national competent authority, 4) Cooperate with UN monitoring teams. UN sanctions form the baseline — national/regional sanctions may be more extensive.",
        "metadata": {"source": "UN", "section": "Security Council", "jurisdiction": "Global", "type": "sanctions"},
    },
    {
        "id": "sanctions_screening_001",
        "text": "Sanctions Screening Best Practices: Effective screening requires: 1) Real-time screening for all transactions, 2) Fuzzy matching algorithms (Levenshtein, Jaro-Winkler) to catch name variations, 3) Phonetic matching (Soundex, Metaphone) for transliteration issues, 4) Alias screening (nicknames, abbreviations), 5) Country screening against sanctioned jurisdictions, 6) Vessel screening (IMO numbers, flag state), 7) Regular list updates (OFAC updates SDN list ~weekly), 8) Documentation of all hits and dispositions, 9) Escalation procedures for true matches, 10) De-duplication to reduce false positives.",
        "metadata": {"source": "Wolfsberg", "section": "Screening", "type": "best_practice"},
    },
    {
        "id": "sanctions_penalties_001",
        "text": "Sanctions Violation Penalties: OFAC penalties can be severe: 1) Civil penalties up to $330,000 per violation (or twice the transaction amount), 2) Criminal penalties up to $1,000,000 and/or 20 years imprisonment, 3) Debarment from U.S. financial system, 4) Reputational damage, 5) Loss of correspondent banking relationships. Notable enforcement actions: BNP Paribas ($8.9B in 2014), Standard Chartered ($1.1B in 2019), HSBC ($1.9B in 2012). Mitigating factors: self-reporting, cooperation, remediation, compliance program enhancements.",
        "metadata": {"source": "OFAC", "section": "Enforcement", "jurisdiction": "US", "type": "enforcement"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "aml_regulations": AML_REGULATIONS,
        "red_flag_typologies": RED_FLAGTYPOLOGIES,
        "sar_filing_guidelines": SAR_FILING_GUIDELINES,
        "ctr_requirements": CTR_REQUIREMENTS,
        "pep_guidelines": PEP_GUIDELINES,
        "beneficial_ownership_rules": BENEFICIAL_OWNERSHIP_RULES,
        "sanctions_regulations": SANCTIONS_REGULATIONS,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  ✓ {collection_name}: {count} documents")

    print("\n✅ AML Alert Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
