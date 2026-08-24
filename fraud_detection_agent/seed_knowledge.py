"""
Seed script: Populate ChromaDB with fraud detection knowledge base data.

Includes:
- Fraud regulations (Reg E, Reg Z, BSA, CFPB guidelines)
- Fraud typologies (card fraud, account takeover, identity theft, synthetic identity)
- Detection rules (velocity, geo, behavioral, device fingerprinting)
- Investigation playbooks (step-by-step workflows)
- Case precedents (historical fraud cases and outcomes)
- Compliance guidelines (customer rights, dispute resolution, SAR filing)
- Chargeback rules (Visa/Mastercard dispute reason codes)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  FRAUD REGULATIONS
# ══════════════════════════════════════════════════════════════════

FRAUD_REGULATIONS = [
    {
        "id": "reg_e_001",
        "text": "Regulation E (Electronic Fund Transfer Act) governs electronic fund transfers including debit card transactions. Consumers have 60 days from the statement date to dispute unauthorized electronic transactions. The bank must investigate within 10 business days and resolve within 45 days (90 days for new accounts). Provisional credit must be issued within 10 business days if investigation is not complete.",
        "metadata": {"source": "CFPB", "section": "Reg E", "jurisdiction": "US", "type": "dispute_resolution"},
    },
    {
        "id": "reg_z_001",
        "text": "Regulation Z (Truth in Lending Act) provides chargeback rights for credit card transactions. Cardholders have 60 days from the statement date to dispute billing errors. For unauthorized charges, liability is capped at $50 if reported within 2 business days, $500 if reported within 60 days, and unlimited after 60 days. Issuers must acknowledge disputes within 30 days and resolve within 90 days.",
        "metadata": {"source": "CFPB", "section": "Reg Z", "jurisdiction": "US", "type": "chargeback"},
    },
    {
        "id": "reg_bsa_001",
        "text": "Bank Secrecy Act (BSA) requires financial institutions to file Suspicious Activity Reports (SARs) for transactions of $5,000 or more that the bank knows, suspects, or has reason to suspect involve funds from illegal activity or are designed to evade reporting requirements. SARs must be filed within 30 days of detection. Failure to file can result in criminal penalties.",
        "metadata": {"source": "FinCEN", "section": "BSA", "jurisdiction": "US", "type": "reporting"},
    },
    {
        "id": "reg_cfpb_fraud_001",
        "text": "CFPB Guidelines on Fraud Prevention: Banks must implement reasonable security measures to protect consumer accounts. This includes multi-factor authentication, transaction monitoring, real-time alerts, and customer verification procedures. Banks are liable for unauthorized transactions if they fail to implement adequate safeguards. Customers must be notified of suspected fraud within 30 days.",
        "metadata": {"source": "CFPB", "section": "Fraud Prevention", "jurisdiction": "US", "type": "security"},
    },
    {
        "id": "reg_ecfa_001",
        "text": "Electronic Fund Transfer Act — Error Resolution: When a consumer notifies the financial institution of an error, the institution must investigate and determine whether an error occurred within 10 business days. If the investigation takes longer than 10 business days, the institution must provisionally credit the consumer's account within 10 business days and may take up to 45 calendar days to complete the investigation.",
        "metadata": {"source": "CFPB", "section": "Reg E §1005.11", "jurisdiction": "US", "type": "error_resolution"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  FRAUD TYPOLOGIES
# ══════════════════════════════════════════════════════════════════

FRAUD_TYPOLOGIES = [
    {
        "id": "type_card_fraud_001",
        "text": "Card-Not-Present (CNP) Fraud: The most common type of card fraud. Fraudsters use stolen card numbers to make online or phone purchases. Indicators: multiple small test transactions, unusual merchant categories, transactions from foreign IP addresses, rapid succession of purchases, mismatch between billing address and IP location.",
        "metadata": {"category": "card_fraud", "severity": "high", "detection": "real-time"},
    },
    {
        "id": "type_card_fraud_002",
        "text": "Card-Counterfeit Fraud: Physical card is duplicated using skimming devices at ATMs, gas stations, or POS terminals. Indicators: transactions in geographic areas where the cardholder hasn't been, multiple cards used at same terminal, ATM skimmer patterns, magnetic stripe data anomalies.",
        "metadata": {"category": "card_fraud", "severity": "high", "detection": "real-time"},
    },
    {
        "id": "type_ato_001",
        "text": "Account Takeover (ATO): Fraudster gains unauthorized access to a customer's account through stolen credentials, phishing, or social engineering. Indicators: login from new device/IP, password change followed by large transfer, unusual time of access, changes to contact information, high-value wire transfers after access.",
        "metadata": {"category": "account_takeover", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "type_identity_001",
        "text": "Identity Theft: Fraudster uses stolen personal information to open new accounts or make transactions in the victim's name. Indicators: new account applications with mismatched information, address changes, credit inquiries from multiple institutions, accounts opened in geographic areas where victim doesn't live.",
        "metadata": {"category": "identity_theft", "severity": "critical", "detection": "batch"},
    },
    {
        "id": "type_synthetic_001",
        "text": "Synthetic Identity Fraud: Fraudster creates a fake identity by combining real and fabricated information (e.g., real SSN with fake name). Often involves building credit over time before 'bust-out' fraud. Indicators: SSN linked to multiple names, thin credit file with recent rapid buildup, address anomalies, age/SSN mismatch.",
        "metadata": {"category": "synthetic_identity", "severity": "critical", "detection": "batch"},
    },
    {
        "id": "type_insider_001",
        "text": "Insider Fraud: Employee or contractor misuses access to commit fraud. Indicators: unusual access patterns, transactions outside normal scope, override of controls, access to accounts of interest, circumvention of dual-control requirements.",
        "metadata": {"category": "insider_fraud", "severity": "critical", "detection": "batch"},
    },
    {
        "id": "type_wire_fraud_001",
        "text": "Wire Transfer Fraud (BEC - Business Email Compromise): Fraudster impersonates a business executive or vendor to redirect wire transfers. Indicators: urgent wire request, changed bank details, email from lookalike domain, new beneficiary with high-value transfer, unusual timing.",
        "metadata": {"category": "wire_fraud", "severity": "critical", "detection": "real-time"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  DETECTION RULES
# ══════════════════════════════════════════════════════════════════

DETECTION_RULES = [
    {
        "id": "rule_velocity_001",
        "text": "Velocity Rule — Transaction Count: Flag if more than 5 transactions within 1 hour, or more than 20 transactions within 24 hours on a single card/account. Thresholds: Hourly: 5 transactions (medium risk). Daily: 20 transactions (high risk). Weekly: 50 transactions (critical risk). Action: Block transactions exceeding daily threshold, alert for hourly threshold.",
        "metadata": {"rule_type": "velocity", "severity": "medium", "action": "alert"},
    },
    {
        "id": "rule_velocity_002",
        "text": "Velocity Rule — Transaction Amount: Flag if cumulative daily amount exceeds $50,000 or single transaction exceeds $10,000 (CTR threshold). Thresholds: Single transaction: $10,000 (CTR required). Daily cumulative: $50,000 (high risk). Weekly cumulative: $150,000 (critical risk). Action: Block and escalate for review.",
        "metadata": {"rule_type": "velocity", "severity": "high", "action": "block"},
    },
    {
        "id": "rule_geo_001",
        "text": "Geo-Velocity Rule: Flag if transactions occur in locations more than 500km apart within 2 hours (physically impossible travel). Additional geo rules: Foreign country transaction when cardholder has no travel notification. Transaction in high-risk jurisdiction (FATF gray/black list). Multiple countries within 24 hours. Action: Block and send verification request.",
        "metadata": {"rule_type": "geo", "severity": "high", "action": "block"},
    },
    {
        "id": "rule_amount_001",
        "text": "Amount Anomaly Rule: Flag transactions that deviate significantly from the cardholder's normal spending pattern. Thresholds: Single transaction > 3x average transaction amount. Daily total > 5x average daily spend. Transaction at unusual time (2am-5am local time). Action: Risk score adjustment, alert for amounts > 5x average.",
        "metadata": {"rule_type": "amount_anomaly", "severity": "medium", "action": "score_adjust"},
    },
    {
        "id": "rule_device_001",
        "text": "Device Fingerprint Rule: Flag transactions from unrecognized devices or suspicious device patterns. Indicators: New device ID not previously associated with account. Device emulator detected. Multiple accounts using same device. Rooted/jailbroken device. VPN or proxy detected. Action: Require step-up authentication for new devices.",
        "metadata": {"rule_type": "device", "severity": "medium", "action": "step_up_auth"},
    },
    {
        "id": "rule_behavioral_001",
        "text": "Behavioral Biometrics Rule: Flag deviations from normal user behavior patterns. Indicators: Unusual typing speed or mouse movement. Changes in navigation patterns. Session duration anomalies. Time between actions significantly different from baseline. Action: Risk score adjustment, stealth monitoring.",
        "metadata": {"rule_type": "behavioral", "severity": "low", "action": "monitor"},
    },
    {
        "id": "rule_merchant_001",
        "text": "Merchant Category Rule: Flag transactions at high-risk merchant categories. High-risk categories: Gambling (MCC 7995), Wire transfers (MCC 6012), Money orders (MCC 6540), Crypto exchanges (MCC 6051). Additional flags: First transaction at this merchant type. Multiple high-risk merchants in short period. Action: Enhanced monitoring for high-risk MCCs.",
        "metadata": {"rule_type": "merchant", "severity": "medium", "action": "enhanced_monitoring"},
    },
    {
        "id": "rule_chip_001",
        "text": "EMV Chip Override Rule: Flag card-present transactions where chip was not used (magnetic stripe fallback). This may indicate: counterfeit card using skimmed magnetic stripe data. Card testing at POS. Transaction at terminal without chip reader. Action: Higher scrutiny for mag-stripe fallback transactions.",
        "metadata": {"rule_type": "emv", "severity": "medium", "action": "enhanced_scrutiny"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  INVESTIGATION PLAYBOOKS
# ══════════════════════════════════════════════════════════════════

INVESTIGATION_PLAYBOOKS = [
    {
        "id": "playbook_card_fraud_001",
        "text": "Card Fraud Investigation Playbook: Step 1: Pull last 30 days of transactions for affected card. Step 2: Identify first unauthorized transaction (FUT - First Unauthorized Transaction). Step 3: Check for card-present vs card-not-present transactions. Step 4: Review device fingerprints and IP addresses. Step 5: Check for other accounts using same device/IP. Step 6: Contact cardholder to confirm legitimate transactions. Step 7: Issue new card if fraud confirmed. Step 8: File chargeback for unauthorized transactions. Step 9: File SAR if threshold met. Step 10: Document findings and close case.",
        "metadata": {"category": "card_fraud", "type": "investigation", "steps": 10},
    },
    {
        "id": "playbook_ato_001",
        "text": "Account Takeover Investigation Playbook: Step 1: Review login history for the past 90 days. Step 2: Identify first unauthorized access. Step 3: Check for credential changes (password, email, phone). Step 4: Review all transactions since first unauthorized access. Step 5: Check for new payees or beneficiaries added. Step 6: Review device and IP history. Step 7: Contact customer to verify identity. Step 8: Revoke all active sessions. Step 9: Reset credentials and re-verify identity. Step 10: File SAR if applicable. Step 11: Monitor account for 90 days post-incident.",
        "metadata": {"category": "account_takeover", "type": "investigation", "steps": 11},
    },
    {
        "id": "playbook_dispute_001",
        "text": "Dispute Resolution Playbook: Step 1: Receive dispute from cardholder (verbal or written). Step 2: Log dispute in case management system with reason code. Step 3: Provisional credit within 10 business days (Reg E) or 1 billing cycle (Reg Z). Step 4: Investigate — contact merchant, review transaction data. Step 5: Determine if unauthorized or billing error. Step 6: If unauthorized — apply zero liability (Visa/MC). Step 7: If billing error — resolve per Reg Z. Step 8: Send resolution letter to cardholder. Step 9: If cardholder disagrees — escalate to arbitration (Visa/MC). Step 10: Document and close.",
        "metadata": {"category": "dispute", "type": "investigation", "steps": 10},
    },
    {
        "id": "playbook_sar_001",
        "text": "SAR Filing Playbook: Step 1: Identify suspicious activity meeting filing threshold ($5,000+). Step 2: Gather all supporting documentation. Step 3: Complete FinCEN SAR Form 111. Step 4: Include narrative with who, what, when, where, why, how. Step 5: File electronically via BSA E-Filing. Step 6: Retain copy for 5 years. Step 7: Alert compliance officer if insider involvement suspected. Step 8: Do not disclose SAR filing to the subject (tipping off is a crime). Step 9: Set follow-up review in 90 days.",
        "metadata": {"category": "sar", "type": "investigation", "steps": 9},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CASE PRECEDENTS
# ══════════════════════════════════════════════════════════════════

CASE_PRECEDENTS = [
    {
        "id": "case_001",
        "text": "Case #1247 — Card-Not-Present Fraud Ring: Detection: 15 cards used for online purchases within 2 hours from same IP range. Investigation revealed compromised merchant terminal at online retailer. Action: Blocked 47 cards, issued chargebacks totaling $127,000, filed SAR, notified card networks. Outcome: Merchant terminated, 3 accounts closed, fraud ring identified across 3 states.",
        "metadata": {"case_type": "cnf_ring", "outcome": "resolved", "amount": 127000},
    },
    {
        "id": "case_002",
        "text": "Case #1289 — Account Takeover via Phishing: Detection: Password changed at 3am, followed by $25,000 wire transfer to new beneficiary. Investigation: Customer's email compromised, password reset email intercepted. Action: Reversed wire (recovered $22,500), issued new credentials, filed SAR. Outcome: Funds mostly recovered, customer educated on phishing. Bank absorbed $2,500 loss.",
        "metadata": {"case_type": "ato", "outcome": "partially_recovered", "amount": 25000},
    },
    {
        "id": "case_003",
        "text": "Case #1312 — Synthetic Identity Fraud: Detection: New account opened with SSN belonging to a minor. Account built credit over 18 months before $45,000 bust-out. Investigation: SSN belonged to 8-year-old child, name was fabricated, address was mail drop. Action: Closed account, wrote off $45,000, filed SAR, reported to FTC. Outcome: Loss absorbed, enhanced identity verification implemented.",
        "metadata": {"case_type": "synthetic", "outcome": "loss", "amount": 45000},
    },
    {
        "id": "case_004",
        "text": "Case #1356 — Business Email Compromise (BEC): Detection: CFO email spoofed requesting $180,000 wire to new account. Investigation: Attackers monitored email for 3 months, identified pending acquisition. Action: Wire was international — recovery efforts initiated through correspondent bank. Recovered $95,000. Filed SAR, FBI IC3 report. Outcome: $85,000 loss, enhanced wire verification procedures implemented.",
        "metadata": {"case_type": "bec", "outcome": "partially_recovered", "amount": 180000},
    },
    {
        "id": "case_005",
        "text": "Case #1389 — Insider Fraud: Detection: Bank employee accessed 47 customer accounts without business justification and made cash withdrawals. Investigation: Employee used legitimate access to steal $67,000 over 6 months. Action: Employee terminated, criminal charges filed, all customer losses reimbursed, filed SAR. Outcome: Full recovery from employee (restitution order), enhanced access controls implemented.",
        "metadata": {"case_type": "insider", "outcome": "fully_recovered", "amount": 67000},
    },
]

# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE GUIDELINES
# ══════════════════════════════════════════════════════════════════

COMPLIANCE_GUIDELINES = [
    {
        "id": "comp_customer_rights_001",
        "text": "Customer Rights in Fraud Cases: 1) Right to zero liability for unauthorized transactions (Visa/Mastercard) if reported within 60 days. 2) Right to provisional credit within 10 business days (Reg E) or 1 billing cycle (Reg Z). 3) Right to receive written explanation of investigation results. 4) Right to dispute investigation results and request re-investigation. 5) Right to obtain free copy of fraud report. 6) Right to place fraud alert on credit report (1 year initial, 7 years extended).",
        "metadata": {"topic": "customer_rights", "regulation": "Reg E/Reg Z"},
    },
    {
        "id": "comp_data_retention_001",
        "text": "Fraud Data Retention Requirements: SARs must be retained for 5 years from filing date. Transaction records for fraud cases must be retained for 5 years. Customer communications related to disputes must be retained for 3 years. CCTV footage from fraud locations must be retained for 30-90 days. Device fingerprint data must be retained for 1 year. Investigation case files must be retained for 7 years after closure.",
        "metadata": {"topic": "data_retention", "regulation": "BSA/AML"},
    },
    {
        "id": "comp_tipping_off_001",
        "text": "Anti-Tipping Off Rules: It is a federal crime to disclose to any person that a SAR has been or will be filed. This includes: telling the account holder, telling the subject of the investigation, disclosing SAR existence to non-essential personnel, discussing SAR content outside of official duties. Exceptions: disclosures to FinCEN, law enforcement, federal banking regulators, self-disclosure in legal proceedings. Penalties: up to $250,000 fine and/or 5 years imprisonment.",
        "metadata": {"topic": "tipping_off", "regulation": "BSA §5318(g)(2)"},
    },
    {
        "id": "comp_provisional_credit_001",
        "text": "Provisional Credit Rules: Reg E: Must issue within 10 business days of error notification. Can be held for up to 45 calendar days for new accounts (opened < 30 days) or POS transactions. Reg Z: Must issue within 1 billing cycle (max 54 days) for billing errors. Provisional credit must include any interest/fees charged during investigation. If investigation finds no error, must give 5 business days written notice before debiting provisional credit.",
        "metadata": {"topic": "provisional_credit", "regulation": "Reg E/Reg Z"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CHARGEBACK RULES
# ══════════════════════════════════════════════════════════════════

CHARGEBCK_RULES = [
    {
        "id": "cb_10_1_001",
        "text": "Visa Dispute Reason Code 10.1 — EMV Liability Shift Counterfeit Fraud: Cardholder or their account was counterfeit fraud victim. Merchant processed transaction using counterfeit card at EMV-enabled terminal. Liability shifts to issuer if terminal was not EMV-capable. Time limit: 120 days from transaction date. Compelling evidence required: transaction receipt, chip transaction logs.",
        "metadata": {"network": "Visa", "code": "10.1", "category": "counterfeit"},
    },
    {
        "id": "cb_10_2_001",
        "text": "Visa Dispute Reason Code 10.2 — EMV Liability Shift Non-Counterfeit Fraud: Cardholder claims fraud for card-present transaction where chip card was used but merchant did not process as chip. Time limit: 120 days. Compelling evidence: chip transaction records, terminal logs. Merchant bears liability if EMV capable but did not process chip.",
        "metadata": {"network": "Visa", "code": "10.2", "category": "non_counterfeit"},
    },
    {
        "id": "cb_10_4_001",
        "text": "Visa Dispute Reason Code 10.4 — Other Fraud: Card-present fraud not involving EMV liability shift. Time limit: 120 days. Compelling evidence: signed receipt, cardholder verification method logs, delivery confirmation for CNP. Zero liability applies for cardholders who report within 60 days.",
        "metadata": {"network": "Visa", "code": "10.4", "category": "other_fraud"},
    },
    {
        "id": "cb_4837_001",
        "text": "Mastercard Dispute Reason Code 4837 — No Cardholder Authorization: Cardholder claims they did not authorize or participate in the transaction. Time limit: 90 days. Compelling evidence: signed receipt, authentication logs, IP/device data for CNP. Mastercard zero liability applies if reported within 60 days and card was not lost/stolen.",
        "metadata": {"network": "Mastercard", "code": "4837", "category": "unauthorized"},
    },
    {
        "id": "cb_4863_001",
        "text": "Mastercard Dispute Reason Code 4863 — Cardholder Does Not Recognize Transaction: Cardholder does not recognize the transaction on their statement. May be fraud or merchant name confusion. Time limit: 90 days. Resolution: Provide detailed transaction descriptor, merchant contact info. If confirmed fraud, process as 4837.",
        "metadata": {"network": "Mastercard", "code": "4863", "category": "unrecognized"},
    },
    {
        "id": "cb_4853_001",
        "text": "Mastercard Dispute Reason Code 4853 — Not as Described/Defective Merchandise: Cardholder claims goods/services were not as described or were defective. Time limit: 90 days. Merchant must provide proof of delivery and description match. Not a fraud claim — falls under billing error. Resolution: merchant refund or arbitration.",
        "metadata": {"network": "Mastercard", "code": "4853", "category": "not_as_described"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "fraud_regulations": FRAUD_REGULATIONS,
        "fraud_typologies": FRAUD_TYPOLOGIES,
        "detection_rules": DETECTION_RULES,
        "investigation_playbooks": INVESTIGATION_PLAYBOOKS,
        "case_precedents": CASE_PRECEDENTS,
        "compliance_guidelines": COMPLIANCE_GUIDELINES,
        "chargeback_rules": CHARGEBCK_RULES,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  ✓ {collection_name}: {count} documents")

    print("\n✅ Fraud Detection Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
