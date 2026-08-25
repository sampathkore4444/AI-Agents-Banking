"""
Seed script: Populate ChromaDB with payment fraud knowledge base data.

Includes:
- Payment fraud policies (wire, ACH, check, RTP)
- Wire fraud patterns (BEC,invoice fraud, account compromise)
- ACH fraud typologies ( unauthorized ACH, check fraud converted to ACH)
- BEC (Business Email Compromise) schemes
- Check fraud rules (forgery, alteration, counterfeiting)
- Real-time payment fraud risks (RTP, FedNow, Zelle)
- Investigation playbooks (step-by-step workflows)

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS

# ══════════════════════════════════════════════════════════════════
#  PAYMENT FRAUD POLICIES
# ══════════════════════════════════════════════════════════════════

PAYMENT_FRAUD_POLICIES = [
    {
        "id": "policy_wire_001",
        "text": "Wire Transfer Fraud Prevention Policy: All outgoing wire transfers must be validated against the following criteria: 1) Originator identity verification (out-of-band confirmation for wires > $25,000), 2) Beneficiary name matching against known payee database, 3) Sanctions screening of all parties, 4) Velocity checks (no more than 3 wires per day per account), 5) Amount threshold review (> $25,000 requires dual approval, > $100,000 requires manager approval), 6) International wire enhanced due diligence (purpose of payment, correspondent bank details), 7) Same-day reversal monitoring for returned wires.",
        "metadata": {"source": "Payment Operations", "category": "wire", "type": "policy"},
    },
    {
        "id": "policy_ach_001",
        "text": "ACH Fraud Prevention Policy: ACH transactions must be monitored for: 1) Unauthorized entries (customer-reported unauthorized debits), 2) Truncated checks converted to ACH without authorization, 3) Employer payroll diversion (account number changes), 4) Bill payment redirection, 5) Velocity limits (10 ACH debits per day, $50,000 daily limit), 6) New payee monitoring (first-time ACH recipients flagged for 30 days), 7) cross-border ACH (international ACH transactions require additional screening). NACHA rules require same-day notification of unauthorized entries.",
        "metadata": {"source": "Payment Operations", "category": "ach", "type": "policy"},
    },
    {
        "id": "policy_check_001",
        "text": "Check Fraud Prevention Policy: Check fraud remains the largest category of payment fraud losses. Prevention measures: 1) Positive Pay matching (check number, amount, payee), 2) Payee Positive Pay (payee name verification), 3) Duplicate detection (same check number presented multiple times), 4) High-dollar check review (checks > $5,000), 5) Account number validation, 6) Check stock controls (限制 check ordering to account holders), 7) Image analysis for alteration detection, 8) Post-issuance review of stop payment requests.",
        "metadata": {"source": "Payment Operations", "category": "check", "type": "policy"},
    },
    {
        "id": "policy_rtp_001",
        "text": "Real-Time Payment (RTP) Fraud Prevention: Real-time payments (RTP, FedNow, Zelle) present unique fraud challenges due to irrevocability. Prevention measures: 1) Recipient validation before initiation, 2) New payee cooling period (first payment to new payee delayed 1 hour), 3) Amount limits ($2,500 per transaction, $10,000 daily), 4) Device fingerprint verification, 5) Geolocation consistency check, 6) Behavioral biometrics, 7) Shared fraud database across participating banks, 8) Customer education on authorized push payment (APP) fraud.",
        "metadata": {"source": "Payment Operations", "category": "rtp", "type": "policy"},
    },
    {
        "id": "policy_reg_e_001",
        "text": "Regulation E — Electronic Fund Transfer Liability: For unauthorized electronic fund transfers: 1) Consumer liability capped at $50 if reported within 2 business days of learning of loss/theft, 2) $500 liability if reported within 60 days of statement, 3) Unlimited liability if reported after 60 days. Bank obligations: 1) Investigate within 10 business days, 2) Provisional credit within 10 business days, 3) Resolve within 45 calendar days (90 for new accounts), 4) Written investigation results. Applies to debit card, ACH, wire transfers initiated by consumers.",
        "metadata": {"source": "CFPB", "category": "regulation", "type": "compliance"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  WIRE FRAUD PATTERNS
# ══════════════════════════════════════════════════════════════════

WIRE_FRAUD_PATTERNS = [
    {
        "id": "wire_bec_001",
        "text": "Business Email Compromise (BEC) — Invoice Fraud: Fraudster compromises vendor email, sends fake invoice with changed bank details. Indicators: 1) New bank details in email, 2) Urgent payment request, 3) Invoice amount deviates from historical average, 4) Payment to new beneficiary, 5) Email from lookalike domain (e.g., vendor-name.com vs vendorname.com), 6) Request to bypass normal approval workflow. Prevention: Always verify bank detail changes via out-of-band communication (phone call to known number).",
        "metadata": {"category": "bec", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "wire_bec_002",
        "text": "BEC — CEO/CFO Impersonation: Fraudster impersonates executive via compromised or spoofed email, requests urgent wire transfer. Indicators: 1) Email from executive's account or lookalike, 2) Urgency and secrecy ('Don't tell anyone'), 3) Unusual beneficiary (first-time payee), 4) Amount just below approval threshold, 5) Request outside business hours, 6) Follow-up emails to pressure. Prevention: Dual approval for all wires, callback verification for unusual requests.",
        "metadata": {"category": "bec", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "wire_account_001",
        "text": "Account Compromise Wire Fraud: Fraudster gains access to business account and initiates unauthorized wires. Indicators: 1) Login from new device/IP, 2) Password change before wire, 3) Wire to foreign jurisdiction, 4) Amount near daily limit, 5) Multiple wires in rapid succession, 6) Wire initiated outside normal business hours. Prevention: Device fingerprinting, behavioral biometrics, step-up auth for high-value wires.",
        "metadata": {"category": "account_compromise", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "wire_triage_001",
        "text": "Triangulation Fraud (Wire Component): Fraudster operates fake marketplace, collects buyer payment, uses stolen card/account to purchase item from legitimate merchant, ships to buyer. Indicators: 1) Buyer pays via wire to personal account, 2) Merchant receives different payment method, 3) Buyer and seller in different jurisdictions, 4) Price significantly below market. This is a variation of triangulation fraud adapted for wire transfers.",
        "metadata": {"category": "triangulation", "severity": "high", "detection": "batch"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  ACH FRAUD TYPOLOGIES
# ══════════════════════════════════════════════════════════════════

ACH_FRAUDTYPOLOGIES = [
    {
        "id": "ach_unauthorized_001",
        "text": "Unauthorized ACH Entry: Fraudster submits ACH debit without customer authorization. Indicators: 1) Customer reports unauthorized debit, 2) ACH company ID not recognized by customer, 3) Entry originated from unfamiliar ODFI, 4) Multiple unauthorized debits from same originator. Customer rights: Must report within 60 days of statement. Bank must investigate within 10 business days and provisionally credit within 10 business days. NACHA unauthorized return reason codes: R05 (illegal transaction), R07 (authorization revoked), R10 (customer dispute).",
        "metadata": {"category": "unauthorized", "severity": "high", "detection": "real-time"},
    },
    {
        "id": "ach_payroll_001",
        "text": "Payroll Diversion Fraud: Employee's direct deposit redirected to fraudster's account. Indicators: 1) Account change request near payday, 2) Change submitted via email/phone (not in-person), 3) New account at different bank, 4) Change made outside normal HR process, 5) Employee reports not receiving paycheck. Prevention: Out-of-band verification for account changes, multi-channel confirmation, audit trail for all payroll changes.",
        "metadata": {"category": "payroll_diversion", "severity": "high", "detection": "real-time"},
    },
    {
        "id": "ach_billpay_001",
        "text": "Bill Payment Redirection: Fraudster intercepts bill payment and redirects to their account. Indicators: 1) Payee name changed but payment amount consistent, 2) Account number changed for established payee, 3) New payee added with similar name to legitimate payee, 4) Payment timing unusual. Prevention: Payee change confirmation, dual authorization for changes, monitoring for name similarity attacks.",
        "metadata": {"category": "billpay_redirection", "severity": "high", "detection": "real-time"},
    },
    {
        "id": "ach_check_convert_001",
        "text": "Check-to-ACH Conversion Fraud: Stolen check converted to ACH for deposit. Indicators: 1) Check presented via mobile deposit and ACH, 2) Same check number used in multiple channels, 3) Deposit to new account, 4) Amount matches known check stock. Prevention: Duplicate check detection across channels, Positive Pay integration, image forensics.",
        "metadata": {"category": "check_conversion", "severity": "high", "detection": "batch"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  BEC SCHEMES
# ══════════════════════════════════════════════════════════════════

BEC_SCHEMES = [
    {
        "id": "bec_001",
        "text": "BEC — Vendor Email Compromise: Fraudster compromises vendor email system, monitors communications, identifies pending invoices, sends modified payment instructions. Indicators: 1) Payment instructions changed mid-stream, 2) Email headers show unusual routing, 3) Request to change bank details, 4) Urgency to avoid detection. FBI IC3 reports BEC losses exceeding $2.7 billion annually. Prevention: Vendor onboarding verification, periodic bank detail confirmation, dual approval for changes.",
        "metadata": {"category": "vendor_compromise", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "bec_002",
        "text": "BEC — Attorney Impersonation: Fraudster impersonates attorney involved in real estate transaction or legal matter, directs wire transfer. Indicators: 1) Urgent wire from 'attorney', 2) New payee, 3) Wire to personal account, 4) Amount consistent with real estate transaction, 5) Pressure to close quickly. Prevention: Verify attorney identity through bar association, confirm wire instructions via known phone number.",
        "metadata": {"category": "attorney_impersonation", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "bec_003",
        "text": "BEC — Real Estate Wire Fraud: Fraudster compromises real estate transaction emails, redirects down payment/closing funds. Indicators: 1) Wire instructions sent close to closing, 2) Last-minute changes to wiring instructions, 3) Wire to new account, 4) Email from compromised realtor/attorney account. This is the fastest-growing BEC variant. Prevention: Verify closing agent identity in person or by phone, never trust wiring instructions received only by email.",
        "metadata": {"category": "real_estate_wire", "severity": "critical", "detection": "real-time"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  CHECK FRAUD RULES
# ══════════════════════════════════════════════════════════════════

CHECK_FRAUD_RULES = [
    {
        "id": "check_alteration_001",
        "text": "Check Alteration Fraud: Fraudster chemically or mechanically alters a stolen check. Common alterations: 1) Payee name changed (pay to the order of), 2) Amount increased (check washing), 3) Date changed, 4) Routing/account numbers modified. Detection indicators: 1) Bleaching or discoloration of check stock, 2) Inconsistent fonts, 3) Amount written differently than numerical, 4) Signature inconsistent with card. Prevention: Security features (watermarks, microprinting, chemical sensitivity), Positive Pay.",
        "metadata": {"category": "alteration", "severity": "high", "detection": "batch"},
    },
    {
        "id": "check_counterfeit_001",
        "text": "Counterfeit Check Fraud: Fraudster creates fake check using stolen account information. Indicators: 1) Check stock not matching bank's standard, 2) Missing security features, 3) Account number doesn't match bank's format, 4) MICR line inconsistent, 5) First-time check from new account. Prevention: Check stock controls, Positive Pay, image analysis for authenticity.",
        "metadata": {"category": "counterfeit", "severity": "high", "detection": "batch"},
    },
    {
        "id": "check_steal_001",
        "text": "Stolen Check Fraud: Fraudster steals check from mailbox or business, modifies and deposits. Indicators: 1) Check presented at different bank than account holder's, 2) Endorsement inconsistent, 3) Deposit via mobile with poor image quality, 4) Check from outside normal geographic area. Prevention: Informed delivery, secure mailbox, positive pay, payee positive pay.",
        "metadata": {"category": "stolen", "severity": "high", "detection": "batch"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  RTP FRAUD RISKS
# ══════════════════════════════════════════════════════════════════

RTP_FRAUD_RISKS = [
    {
        "id": "rtp_app_001",
        "text": "Authorized Push Payment (APP) Fraud: Customer is socially engineered into sending RTP payment to fraudster. Indicators: 1) Customer pressured by urgency ('act now'), 2) Payment to new recipient, 3) Amount inconsistent with customer's profile, 4) Customer unable to explain payment purpose, 5) Multiple RTPs to same recipient in short period. Unlike unauthorized fraud, customer authorized the payment. Bank liability varies by jurisdiction. Prevention: Confirmation screens, cooling periods, recipient warnings.",
        "metadata": {"category": "app_fraud", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "rtp_mule_001",
        "text": "Money Mule Recruitment via RTP: Fraudster recruits individuals to receive and forward RTP payments. Indicators: 1) Account receives multiple RTPs from different senders, 2) Funds immediately forwarded via RTP to different account, 3) Account holder has no apparent business reason for high-volume RTPs, 4) Recipient account newly opened. Prevention: Monitor for rapid pass-through patterns, flag accounts receiving from multiple unrelated parties.",
        "metadata": {"category": "money_mule", "severity": "critical", "detection": "real-time"},
    },
    {
        "id": "rtp_impersonation_001",
        "text": "RTP Impersonation Fraud: Fraudster impersonates known contact via compromised messaging, requests RTP payment. Indicators: 1) Request from known contact via unusual channel, 2) Urgency, 3) Request to send to different account than usual, 4) Amount unusual. Prevention: Verify via phone call, confirmation delays for new recipients, recipient name display.",
        "metadata": {"category": "impersonation", "severity": "high", "detection": "real-time"},
    },
]

# ══════════════════════════════════════════════════════════════════
#  INVESTIGATION PLAYBOOKS
# ══════════════════════════════════════════════════════════════════

INVESTIGATION_PLAYBOOKS = [
    {
        "id": "playbook_wire_001",
        "text": "Wire Fraud Investigation Playbook: Step 1: Identify the unauthorized or suspicious wire transfer. Step 2: Initiate recall request immediately (within 24 hours for best recovery chance). Step 3: Contact beneficiary bank with wire recall request. Step 4: Verify originator identity and authorization. Step 5: Check for related suspicious wires (same beneficiary, same amount). Step 6: Review account access logs for unauthorized access. Step 7: Contact customer to confirm/ deny authorization. Step 8: File SAR if $5,000+ suspicious activity. Step 9: Contact law enforcement if loss exceeds $50,000. Step 10: Document all findings and close case.",
        "metadata": {"category": "wire_fraud", "type": "investigation", "steps": 10},
    },
    {
        "id": "playbook_bec_001",
        "text": "BEC Investigation Playbook: Step 1: Verify the BEC with customer (was email compromised?). Step 2: Initiate wire recall immediately. Step 3: Contact beneficiary bank and request freeze. Step 4: Report to FBI IC3 (ic3.gov). Step 5: File SAR. Step 6: Review all accounts accessed from compromised email. Step 7: Check for additional fraudulent wires. Step 8: Implement enhanced monitoring on affected accounts. Step 9: Customer credential reset. Step 10: Document and close with recommendations for prevention.",
        "metadata": {"category": "bec", "type": "investigation", "steps": 10},
    },
    {
        "id": "playbook_check_001",
        "text": "Check Fraud Investigation Playbook: Step 1: Identify fraudulent check (alteration, counterfeit, or stolen). Step 2: Place stop payment if check not yet cleared. Step 3: Review check image for alteration indicators. Step 4: Compare with known check stock. Step 5: Identify presenting bank and deposit account. Step 6: Request copy of check from presenting bank. Step 7: Compare endorsement with signature card. Step 8: File Reg E dispute if unauthorized. Step 9: Implement Positive Pay if not already active. Step 10: Document and close.",
        "metadata": {"category": "check_fraud", "type": "investigation", "steps": 10},
    },
    {
        "id": "playbook_ach_001",
        "text": "ACH Fraud Investigation Playbook: Step 1: Identify unauthorized ACH entry. Step 2: Initiate NACHA return within timeframe (R07 within 60 days). Step 3: Provisional credit to customer within 10 business days. Step 4: Investigate originator and ODFI. Step 5: Check for related unauthorized entries. Step 6: Review account change history. Step 7: Contact originator to verify. Step 8: File SAR if applicable. Step 9: Implement enhanced ACH monitoring. Step 10: Document and close.",
        "metadata": {"category": "ach_fraud", "type": "investigation", "steps": 10},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "payment_fraud_policies": PAYMENT_FRAUD_POLICIES,
        "wire_fraud_patterns": WIRE_FRAUD_PATTERNS,
        "ach_fraud_typologies": ACH_FRAUDTYPOLOGIES,
        "bec_schemes": BEC_SCHEMES,
        "check_fraud_rules": CHECK_FRAUD_RULES,
        "rtp_fraud_risks": RTP_FRAUD_RISKS,
        "investigation_playbooks": INVESTIGATION_PLAYBOOKS,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  OK {collection_name}: {count} documents")

    print("\nPayment Fraud Prevention Knowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
