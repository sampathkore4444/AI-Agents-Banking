"""
Seed script: Populate ChromaDB with internal banking knowledge base data.

Includes:
- Product details (savings, current, credit cards, loans)
- Standard Operating Procedures (SOPs)
- IT help and troubleshooting guides
- HR policies and benefits
- Compliance training materials
- Process guides
- Regulatory updates
- FAQ and common questions

Usage:
    python seed_knowledge.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import RAGPipeline, COLLECTIONS


# ══════════════════════════════════════════════════════════════════
#  PRODUCT DETAILS
# ══════════════════════════════════════════════════════════════════

PRODUCT_DETAILS = [
    {
        "id": "prod_savings_001",
        "text": (
            "Standard Savings Account: Interest rate 4.10% APY for balances up to $10,000, "
            "3.60% APY for balances above $10,000. No monthly maintenance fee if minimum "
            "balance of $300 is maintained. $5/month fee if balance falls below $300. "
            "FDIC insured up to $250,000. Allows 6 free withdrawals per month (Regulation D). "
            "Additional withdrawals incur $10 fee each. Interest compounded daily, paid monthly. "
            "Minimum opening deposit: $25. Available online, mobile, and in-branch."
        ),
        "metadata": {"source": "Product Team", "category": "savings", "product": "standard_savings", "version": "2024-Q3"},
    },
    {
        "id": "prod_savings_002",
        "text": (
            "High-Yield Savings Account: Interest rate 5.25% APY for all balances. "
            "No monthly maintenance fee. No minimum balance requirement. "
            "FDIC insured up to $250,000. Allows 6 free withdrawals per month. "
            "Additional withdrawals: $15 fee each. Interest compounded daily, paid monthly. "
            "Minimum opening deposit: $100. Online and mobile only — not available in-branch. "
            "Promotional rate guaranteed for first 12 months, then reverts to standard rate."
        ),
        "metadata": {"source": "Product Team", "category": "savings", "product": "high_yield_savings", "version": "2024-Q3"},
    },
    {
        "id": "prod_current_001",
        "text": (
            "Personal Current Account (Checking): No minimum balance requirement. "
            "No monthly maintenance fee for first 12 months, then $12/month waived with "
            "direct deposit of $500+ or average balance of $1,500. Free debit card with "
            "tap-to-pay. 55,000+ fee-free ATMs nationwide. Mobile check deposit. "
            "Overdraft protection available ($35 fee per occurrence, max 3 per day). "
            "FDIC insured up to $250,000. Free online bill pay. Zelle integration for "
            "instant person-to-person transfers."
        ),
        "metadata": {"source": "Product Team", "category": "current", "product": "personal_current", "version": "2024-Q3"},
    },
    {
        "id": "prod_business_001",
        "text": (
            "Business Checking Account: First 250 transactions per month free, "
            "$0.25 per additional transaction. No monthly fee with $5,000 minimum "
            "balance or $10,000 in combined business deposits. Includes free positive "
            "pay for fraud prevention. Multi-user access with role-based permissions. "
            "Integration with QuickBooks and Xero. Wire transfer: $25 domestic, $45 international. "
            "FDIC insured up to $250,000. Business debit card with spending controls."
        ),
        "metadata": {"source": "Product Team", "category": "business", "product": "business_current", "version": "2024-Q3"},
    },
    {
        "id": "prod_credit_001",
        "text": (
            "Platinum Rewards Credit Card: 2% cash back on dining and travel, "
            "1% on all other purchases. No annual fee for first year, $95/year after. "
            "0% APR introductory rate for 15 months on purchases and balance transfers, "
            "then 18.99%-26.99% variable APR. Credit limit $5,000-$50,000 based on "
            "creditworthiness. Free FICO score monthly. Travel insurance included. "
            "Extended warranty protection. No foreign transaction fees. "
            "Late payment fee: up to $41. Returned payment fee: up to $41."
        ),
        "metadata": {"source": "Product Team", "category": "credit_card", "product": "platinum_rewards", "version": "2024-Q3"},
    },
    {
        "id": "prod_credit_002",
        "text": (
            "Secured Credit Card: Designed for credit building. Requires security deposit "
            "of $200-$2,500 which becomes the credit limit. 1% cash back on all purchases. "
            "No annual fee. 24.99% variable APR. Reports to all 3 major credit bureaus "
            "(Equifax, Experian, TransUnion). After 12 months of responsible use, eligible "
            "for upgrade to unsecured card with deposit refund. Free credit monitoring."
        ),
        "metadata": {"source": "Product Team", "category": "credit_card", "product": "secured_card", "version": "2024-Q3"},
    },
    {
        "id": "prod_mortgage_001",
        "text": (
            "Fixed-Rate Mortgage: 30-year fixed starting at 6.25% APR, 15-year fixed "
            "starting at 5.50% APR. Down payment options: 3%, 5%, 10%, 20%. "
            "PMI required if down payment < 20% (0.5%-1% of loan amount annually). "
            "Closing costs: 2%-5% of loan amount. Loan amounts: $50,000-$2,000,000. "
            "Pre-approval available within 24 hours. Rate lock: 30, 45, or 60 days. "
            "First-time homebuyer programs available with reduced down payment."
        ),
        "metadata": {"source": "Product Team", "category": "mortgage", "product": "fixed_rate_mortgage", "version": "2024-Q3"},
    },
    {
        "id": "prod_auto_loan_001",
        "text": (
            "Auto Loan: Rates starting at 4.99% APR for new vehicles, 5.49% APR for used. "
            "Loan terms: 36, 48, 60, 72, or 84 months. Financing for vehicles up to 10 years old. "
            "Loan amounts: $5,000-$100,000. No prepayment penalty. "
            "Pre-approval valid for 30 days. Quick decision within minutes. "
            "Refinancing available for existing auto loans. "
            "GAP insurance and extended warranty available at signing."
        ),
        "metadata": {"source": "Product Team", "category": "auto_loan", "product": "auto_loan", "version": "2024-Q3"},
    },
    {
        "id": "prod_personal_loan_001",
        "text": (
            "Personal Loan: Fixed rates from 7.99%-15.99% APR depending on creditworthiness. "
            "Loan amounts: $1,000-$50,000. Terms: 12, 24, 36, 48, or 60 months. "
            "No origination fee. No prepayment penalty. "
            "Funds available within 1-2 business days. "
            "Joint applications accepted. Co-borrower option available. "
            "Autopay discount: 0.25% rate reduction. "
            "Hardship program available for financial difficulty."
        ),
        "metadata": {"source": "Product Team", "category": "personal_loan", "product": "personal_loan", "version": "2024-Q3"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  STANDARD OPERATING PROCEDURES
# ══════════════════════════════════════════════════════════════════

STANDARD_OPERATING_PROCEDURES = [
    {
        "id": "sop_account_opening_001",
        "text": (
            "SOP: Personal Account Opening — Step-by-step procedure: "
            "1. Verify customer identity (government-issued photo ID + proof of address). "
            "2. Check OFAC/sanctions screening (clear = proceed, hit = escalate to compliance). "
            "3. Complete CDD (Customer Due Diligence) form with customer details. "
            "4. Run soft credit pull (no impact on credit score). "
            "5. Select account type and features per customer request. "
            "6. Collect opening deposit (cash, check, or transfer). "
            "7. Issue debit card (instant issuance available in-branch). "
            "8. Set up online banking access. "
            "9. Provide welcome packet with fee schedule and contact information. "
            "10. Document all steps in CRM within 24 hours."
        ),
        "metadata": {"source": "Operations", "category": "account_management", "doc_type": "sop", "version": "2024-Q3"},
    },
    {
        "id": "sop_account_opening_002",
        "text": (
            "SOP: Business Account Opening — Additional requirements beyond personal: "
            "1. Certificate of Incorporation or Articles of Organization. "
            "2. EIN (Employer Identification Number) letter from IRS. "
            "3. Business license (if applicable). "
            "4. Operating agreement or corporate resolution. "
            "5. Beneficial ownership declaration (25%+ ownership). "
            "6. Government-issued ID for all signers. "
            "7. Proof of business address (utility bill, lease agreement). "
            "8. Business plan or financial projections (for new businesses). "
            "Processing time: 3-5 business days for standard accounts, "
            "7-10 business days for high-risk business categories."
        ),
        "metadata": {"source": "Operations", "category": "account_management", "doc_type": "sop", "version": "2024-Q3"},
    },
    {
        "id": "sop_dispute_001",
        "text": (
            "SOP: Dispute Resolution Process — Timeline: "
            "Day 0: Customer reports dispute (phone, branch, online, mobile). "
            "Day 1: Log dispute in system, issue provisional credit within 10 business days. "
            "Day 2-20: Investigate — contact merchant, review transaction records. "
            "Day 21-45: Complete investigation and render decision. "
            "Day 46: Notify customer of final decision in writing. "
            "If resolved in customer favor: provisional credit becomes permanent. "
            "If resolved against customer: reverse provisional credit, notify customer of right to appeal. "
            "Time limits: 60 days for unauthorized transactions, 120 days for billing errors. "
            "Documentation: All disputes must be documented with case number, customer contact info, "
            "transaction details, investigation notes, and resolution."
        ),
        "metadata": {"source": "Operations", "category": "disputes", "doc_type": "sop", "version": "2024-Q3"},
    },
    {
        "id": "sop_wire_transfer_001",
        "text": (
            "SOP: Wire Transfer Processing — Domestic: "
            "1. Verify customer identity and account status. "
            "2. Confirm sufficient funds (including wire fee: $25 domestic). "
            "3. Collect recipient details: name, bank name, routing number, account number. "
            "4. For wires over $3,000: additional verification required (phone callback). "
            "5. For wires over $10,000: CTR (Currency Transaction Report) required. "
            "6. Process through Fedwire or CHIPS. "
            "7. Provide customer with tracking/reference number. "
            "8. Domestic wires: same-day settlement if submitted before 4:00 PM ET. "
            "International wires: $45 fee, 1-3 business day settlement, SWIFT code required."
        ),
        "metadata": {"source": "Operations", "category": "payments", "doc_type": "sop", "version": "2024-Q3"},
    },
    {
        "id": "sop_fraud_001",
        "text": (
            "SOP: Fraud Alert Response — When fraud alert triggered: "
            "1. Immediately freeze affected card/account if unauthorized activity confirmed. "
            "2. Contact customer within 30 minutes of alert. "
            "3. Verify recent transactions with customer (read last 5 transactions). "
            "4. If confirmed fraud: issue new card/account, file SAR (Suspicious Activity Report). "
            "5. If customer confirms legitimate: unfreeze and document. "
            "6. For confirmed fraud over $5,000: escalate to Fraud Investigation Unit. "
            "7. Send fraud affidavit to customer for completion. "
            "8. Provisional credit: issue within 10 business days. "
            "9. Final resolution: within 45 business days (Regulation E). "
            "10. Update fraud database with new patterns/MO."
        ),
        "metadata": {"source": "Security", "category": "fraud", "doc_type": "sop", "version": "2024-Q3"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  IT HELP AND SUPPORT
# ══════════════════════════════════════════════════════════════════

IT_HELP_AND_SUPPORT = [
    {
        "id": "it_password_001",
        "text": (
            "IT Help: Password Reset — Employee self-service password reset: "
            "1. Go to https://passwordreset.bank.internal. "
            "2. Enter employee ID and registered email. "
            "3. Check email for 6-digit verification code (expires in 10 minutes). "
            "4. Enter code and set new password (minimum 12 characters, must include "
            "uppercase, lowercase, number, and special character). "
            "5. Cannot reuse last 12 passwords. "
            "If self-service fails: Call IT Help Desk at ext. 4357 (HELP). "
            "Identity verification required: employee ID + last 4 of SSN + manager name. "
            "Reset processed within 15 minutes during business hours. "
            "After-hours resets: next business day."
        ),
        "metadata": {"source": "IT Department", "category": "access", "doc_type": "help_article", "priority": "high"},
    },
    {
        "id": "it_vpn_001",
        "text": (
            "IT Help: VPN Connection Issues — Troubleshooting steps: "
            "1. Verify internet connection is working. "
            "2. Check VPN client is updated to latest version (currently v4.12.3). "
            "3. Clear VPN cache: Settings > Advanced > Clear Cache. "
            "4. Disconnect and reconnect. "
            "5. Try alternate VPN server: US-EAST-1, US-WEST-1, EU-CENTRAL-1. "
            "6. If persistent: restart computer and retry. "
            "7. Check firewall/antivirus isn't blocking VPN client. "
            "8. Verify certificate hasn't expired (check VPN client > Settings > Certificates). "
            "If none work: Submit IT ticket (Category: VPN > Connection Issues) "
            "or call IT Help Desk ext. 4357. "
            "Required info: employee ID, error message, device type, OS version."
        ),
        "metadata": {"source": "IT Department", "category": "networking", "doc_type": "help_article", "priority": "medium"},
    },
    {
        "id": "it_email_001",
        "text": (
            "IT Help: Email Setup — Outlook Configuration: "
            "Server: mail.bank.internal (Exchange Online). "
            "Auto-discover: enabled — just enter email address and password. "
            "Manual setup if auto-discover fails: "
            "Incoming server: outlook.office365.com, port 993, SSL/TLS. "
            "Outgoing server: smtp.office365.com, port 587, STARTTLS. "
            "Authentication: use employee email and network password. "
            "Mobile setup: Install Outlook app, use same credentials. "
            "If 2FA issues: Use authenticator app (Microsoft Authenticator recommended). "
            "Email quota: 50GB mailbox, 10GB archive. "
            "Shared mailboxes: request through manager via ServiceNow."
        ),
        "metadata": {"source": "IT Department", "category": "email", "doc_type": "help_article", "priority": "medium"},
    },
    {
        "id": "it_hardware_001",
        "text": (
            "IT Help: Hardware Request Process — "
            "1. Submit request via ServiceNow (Category: Hardware Request). "
            "2. Include: employee name, department, manager approval, specific hardware needed. "
            "3. Standard equipment: Dell Latitude 5540 laptop ($1,200), Dell 27\" monitor ($350), "
            "keyboard/mouse combo ($50). "
            "4. Special requests (dual monitors, standing desk, ergonomic equipment): "
            "require manager + HR approval. "
            "5. Processing time: 5-7 business days for standard, 10-14 for special. "
            "6. Asset tagged and registered in inventory system. "
            "7. Return old equipment when upgrading (data wipe required). "
            "Emergency replacements: submit Priority 1 ticket, processed within 24 hours."
        ),
        "metadata": {"source": "IT Department", "category": "hardware", "doc_type": "help_article", "priority": "low"},
    },
    {
        "id": "it_system_outage_001",
        "text": (
            "IT Help: System Outage Reporting — When you encounter a system outage: "
            "1. Check IT Status Dashboard (https://status.bank.internal) for known outages. "
            "2. If not listed: submit Priority 1 ticket immediately. "
            "3. Include: affected system, error message, time started, impact description. "
            "4. Call IT Operations Hotline: ext. 5555 for critical system outages. "
            "5. For core banking system: auto-escalation to VP of Technology. "
            "6. Communication: IT will send email updates every 30 minutes during outage. "
            "7. Resolution: post-mortem within 48 hours, root cause analysis within 5 business days. "
            "Planned maintenance: announced 72 hours in advance via email and intranet."
        ),
        "metadata": {"source": "IT Department", "category": "operations", "doc_type": "help_article", "priority": "critical"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  HR POLICIES AND BENEFITS
# ══════════════════════════════════════════════════════════════════

HR_POLICIES_AND_BENEFITS = [
    {
        "id": "hr_leave_001",
        "text": (
            "HR Policy: Annual Leave — Full-time employees accrue: "
            "Years 1-3: 15 days (1.25 days/month). "
            "Years 4-7: 20 days (1.67 days/month). "
            "Years 8+: 25 days (2.08 days/month). "
            "Maximum carryover: 5 days to next calendar year. "
            "Requests: submit via HR portal at least 2 weeks in advance. "
            "Blackout periods: year-end close (Dec 15-Jan 5), audit periods. "
            "Approval required from direct manager. "
            "Unused days beyond carryover: forfeited (use-it-or-lose-it policy). "
            "Sick leave: 12 days/year, no carryover, requires doctor's note after 3 consecutive days."
        ),
        "metadata": {"source": "HR Department", "category": "leave", "doc_type": "policy", "version": "2024-Q3"},
    },
    {
        "id": "hr_benefits_001",
        "text": (
            "HR Policy: Health Insurance — Options: "
            "1. PPO Plan: $200/month employee, $500/month family. $500 deductible, "
            "$20 copay primary care, $40 specialist. Out-of-pocket max: $4,000 individual. "
            "2. HMO Plan: $150/month employee, $400/month family. $250 deductible, "
            "$15 copay primary care, $30 specialist. Out-of-pocket max: $3,000 individual. "
            "3. HDHP + HSA: $100/month employee, $300/month family. $2,000 deductible, "
            "20% coinsurance. Bank contributes $500/year to HSA. "
            "Open enrollment: November 1-30 each year. "
            "Life insurance: 2x annual salary, company-paid. "
            "Disability: 60% of salary, 180-day elimination period."
        ),
        "metadata": {"source": "HR Department", "category": "benefits", "doc_type": "policy", "version": "2024-Q3"},
    },
    {
        "id": "hr_remote_001",
        "text": (
            "HR Policy: Remote Work — Eligible roles: determined by department head. "
            "Hybrid model: minimum 3 days in-office (Tue, Wed, Thu required). "
            "Fully remote: available for select roles with VP approval. "
            "Requirements: dedicated workspace, reliable internet (25+ Mbps), "
            "webcam for meetings, VPN access. "
            "Equipment: company provides laptop, monitor, headset. "
            "Home office stipend: $500 one-time setup, $50/month ongoing. "
            "Core hours: 10:00 AM - 3:00 PM local time (flexible outside). "
            "Performance: measured by output, not hours. "
            "Review period: 90-day trial, then semi-annual reviews."
        ),
        "metadata": {"source": "HR Department", "category": "work_arrangements", "doc_type": "policy", "version": "2024-Q3"},
    },
    {
        "id": "hr_conduct_001",
        "text": (
            "HR Policy: Code of Conduct — Key principles: "
            "1. Act with integrity in all business dealings. "
            "2. Maintain confidentiality of customer and bank information. "
            "3. Avoid conflicts of interest (disclose any potential conflicts to compliance). "
            "4. No insider trading or sharing non-public information. "
            "5. Treat all customers, colleagues, and partners with respect and dignity. "
            "6. Report any suspected violations through compliance hotline (anonymous). "
            "7. Comply with all applicable laws and regulations. "
            "8. No harassment, discrimination, or bullying. "
            "9. Gift policy: no gifts over $50 from vendors, no cash gifts from customers. "
            "Violations: progressive discipline up to and including termination."
        ),
        "metadata": {"source": "HR Department", "category": "conduct", "doc_type": "policy", "version": "2024-Q3"},
    },
    {
        "id": "hr_training_001",
        "text": (
            "HR Policy: Mandatory Training — Annual requirements: "
            "1. Information Security Awareness (1 hour) — Phishing, data handling, passwords. "
            "2. Anti-Money Laundering (AML) (2 hours) — Red flags, SAR filing, CTR requirements. "
            "3. Fair Lending (1 hour) — ECOA, HMDA, prohibited basis factors. "
            "4. Code of Conduct (30 minutes) — Ethics, conflicts, gift policy. "
            "5. Workplace Safety (30 minutes) — Emergency procedures, ergonomics. "
            "Deadline: all training completed by December 31 each year. "
            "Tracking: completed via LMS (Learning Management System). "
            "Consequences of non-completion: compliance hold on bonus, "
            "escalation to manager and HR. New hires: complete within 30 days of start date."
        ),
        "metadata": {"source": "HR Department", "category": "training", "doc_type": "policy", "version": "2024-Q3"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  COMPLIANCE TRAINING
# ══════════════════════════════════════════════════════════════════

COMPLIANCE_TRAINING = [
    {
        "id": "comp_aml_001",
        "text": (
            "Compliance Training: AML Red Flags — Employees must be able to identify: "
            "1. Unusually large cash transactions (over $10,000). "
            "2. Structuring: breaking transactions into amounts just under $10,000 to avoid CTR filing. "
            "3. Rapid movement of funds: deposits followed immediately by wire transfers. "
            "4. Accounts used by multiple unrelated parties. "
            "5. Transactions inconsistent with customer's known business or profile. "
            "6. Reluctance to provide identification or business documentation. "
            "7. Frequent changes in signers or beneficial owners. "
            "8. Wire transfers to/from high-risk jurisdictions (FATF grey/black list). "
            "9. Unusual patterns: large round-dollar transactions, just-above-threshold amounts. "
            "10. Customer showing unusual concern about BSA/AML reporting requirements."
        ),
        "metadata": {"source": "Compliance", "category": "aml", "doc_type": "training", "priority": "critical"},
    },
    {
        "id": "comp_fair_lending_001",
        "text": (
            "Compliance Training: Fair Lending — Prohibited factors in credit decisions: "
            "Race, color, religion, national origin, sex, marital status, age (if applicant "
            "has capacity), receipt of public assistance, good faith exercise of Consumer "
            "Credit Protection Act rights. "
            "Permitted risk-based pricing factors: credit score, LTV ratio, loan amount, "
            "property type, occupancy status, geographic location, loan term. "
            "Documentation: all pricing exceptions must be documented with business justification. "
            "Testing: quarterly fair lending analysis (regression analysis, matched-pair testing). "
            "Penalties for violations: fines up to $10,000 per violation, consent orders, "
            "reputational damage, potential criminal charges."
        ),
        "metadata": {"source": "Compliance", "category": "fair_lending", "doc_type": "training", "priority": "critical"},
    },
    {
        "id": "comp_data_privacy_001",
        "text": (
            "Compliance Training: Data Privacy (GLBA) — Bank employees must: "
            "1. Collect only necessary customer information (data minimization). "
            "2. Use customer data only for authorized business purposes. "
            "3. Never share customer data with unauthorized parties. "
            "4. Secure physical documents (clean desk policy, locked cabinets). "
            "5. Never leave customer data unattended on screens or desks. "
            "6. Report any data breach within 1 hour to Information Security team. "
            "7. Use encrypted channels for transmitting sensitive data. "
            "8. Shred documents containing customer information. "
            "9. Never use personal email for bank business. "
            "10. Complete annual privacy training and acknowledge privacy policy. "
            "Violations: immediate investigation, potential termination, regulatory penalties."
        ),
        "metadata": {"source": "Compliance", "category": "privacy", "doc_type": "training", "priority": "critical"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  PROCESS GUIDES
# ══════════════════════════════════════════════════════════════════

PROCESS_GUIDES = [
    {
        "id": "proc_loan_approval_001",
        "text": (
            "Process Guide: Loan Approval Workflow — "
            "Stage 1: Application Intake — Collect application, verify identity, pull credit. "
            "Stage 2: Document Collection — Gather income docs, asset docs, property info. "
            "Stage 3: Processing — Verify employment, appraise property, check title. "
            "Stage 4: Underwriting — Review complete file, render decision. "
            "Stage 5: Conditions — Clear any conditions (additional docs, explanations). "
            "Stage 6: Clear to Close — Final approval, prepare closing documents. "
            "Stage 7: Closing — Sign documents, fund loan, record lien. "
            "Stage 8: Post-Closing — Package loan, sell to secondary market (if applicable). "
            "SLAs: Pre-approval: 24 hours. Processing: 5-7 business days. "
            "Underwriting: 2-3 business days. Clear to close: 1-2 business days."
        ),
        "metadata": {"source": "Lending Operations", "category": "lending", "doc_type": "process", "version": "2024-Q3"},
    },
    {
        "id": "proc_crm_001",
        "text": (
            "Process Guide: CRM Data Entry — All customer interactions must be logged: "
            "1. Log every phone call (inbound/outbound) within 1 hour. "
            "2. Log every branch visit (purpose, outcome, follow-up items). "
            "3. Log email correspondence (subject, summary, action items). "
            "4. Tag interactions by category: inquiry, complaint, sales, service, complaint. "
            "5. Set follow-up reminders for any unresolved items. "
            "6. Update customer profile with new information. "
            "7. Document referrals to other departments. "
            "8. Log any commitments made to customer. "
            "CRM fields required: contact date, contact method, summary, next steps, "
            "responsible party, due date. "
            "Audit: CRM entries reviewed monthly by managers."
        ),
        "metadata": {"source": "Operations", "category": "customer_service", "doc_type": "process", "version": "2024-Q3"},
    },
    {
        "id": "proc_incident_001",
        "text": (
            "Process Guide: Incident Reporting — When an incident occurs: "
            "1. Contain the incident (isolate affected systems, preserve evidence). "
            "2. Notify your manager immediately. "
            "3. Submit incident report within 2 hours via Incident Management Portal. "
            "4. Include: what happened, when, who was affected, what data was involved. "
            "5. Severity levels: P1 (Critical: data breach, system down), "
            "P2 (High: partial outage, potential risk), "
            "P3 (Medium: limited impact, workaround available), "
            "P4 (Low: minor issue, no customer impact). "
            "6. P1/P2: War room activated, CEO/CTO notified. "
            "7. P3/P4: Normal resolution process. "
            "8. Post-incident review: within 5 business days. "
            "9. Regulatory reporting: as required (breach notification laws)."
        ),
        "metadata": {"source": "Security Operations", "category": "security", "doc_type": "process", "version": "2024-Q3"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  REGULATORY UPDATES
# ══════════════════════════════════════════════════════════════════

REGULATORY_UPDATES = [
    {
        "id": "reg_tila_2024_001",
        "text": (
            "Regulatory Update: TILA-RESPA Integration (TRID) — Effective: October 2024. "
            "Key changes: Updated Loan Estimate (LE) and Closing Disclosure (CD) forms. "
            "New tolerance thresholds: 0% for changed circumstances, 10% for cumulative change. "
            "Electronic delivery: e-signed disclosures now explicitly permitted. "
            "Action required: Update all LE/CD templates by October 1, 2024. "
            "Training: All loan officers must complete TRID refresher by September 15. "
            "Compliance: 30-day look-back period for audits."
        ),
        "metadata": {"source": "Compliance", "category": "regulation", "doc_type": "update", "effective_date": "2024-10-01"},
    },
    {
        "id": "reg_bsa_2024_001",
        "text": (
            "Regulatory Update: BSA/AML Beneficial Ownership — FinCEN Final Rule. "
            "Key changes: Updated beneficial ownership reporting requirements. "
            "New threshold: 25% ownership (unchanged), but enhanced verification for "
            "legal entity customers. CDD Rule: expanded to include verification of "
            "beneficial owners' identities. Deadline for compliance: March 2025. "
            "Action required: Update CDD forms, train all customer-facing staff, "
            "update onboarding system workflows. "
            "Penalties for non-compliance: up to $50,000 per violation per day."
        ),
        "metadata": {"source": "Compliance", "category": "regulation", "doc_type": "update", "effective_date": "2025-03-01"},
    },
]


# ══════════════════════════════════════════════════════════════════
#  FAQ AND COMMON QUESTIONS
# ══════════════════════════════════════════════════════════════════

FAQ_AND_COMMON_QUESTIONS = [
    {
        "id": "faq_hours_001",
        "text": (
            "FAQ: Bank Branch Hours — Standard hours: Monday-Friday 9:00 AM - 5:00 PM. "
            "Extended hours: Thursday 9:00 AM - 7:00 PM. "
            "Saturday: 9:00 AM - 2:00 PM (selected branches). "
            "Sunday: Closed. "
            "Holiday schedule: New Year's Day, MLK Day, Presidents' Day, Memorial Day, "
            "Independence Day, Labor Day, Columbus Day, Veterans Day, Thanksgiving, "
            "Day after Thanksgiving, Christmas Eve, Christmas Day. "
            "Online banking: 24/7/365. "
            "ATM: 24/7 at all branch locations and standalone ATMs."
        ),
        "metadata": {"source": "Operations", "category": "general", "doc_type": "faq", "priority": "medium"},
    },
    {
        "id": "faq_routing_001",
        "text": (
            "FAQ: Routing Number — Our bank's routing number: 021000021. "
            "Used for: direct deposit, ACH transfers, wire transfers, bill pay setup. "
            "Where to find: bottom left of checks, online banking (Account Details), "
            "mobile app (Account Info). "
            "Wire transfers (domestic): routing number 021000021. "
            "Wire transfers (international/SWIFT): BOFAUS3N. "
            "Note: Routing number may vary by region for legacy acquisitions. "
            "If unsure, contact Operations at ext. 2222."
        ),
        "metadata": {"source": "Operations", "category": "general", "doc_type": "faq", "priority": "high"},
    },
    {
        "id": "faq_overdraft_001",
        "text": (
            "FAQ: Overdraft Policy — Standard overdraft protection: "
            "1. Standard Coverage: automatic enrollment, $35 fee per overdraft, "
            "maximum 3 overdrafts per day ($105 max daily fees). "
            "2. Grace Period: $5 buffer (no fee if balance goes to -$5 or less). "
            "3. Savings Link: link savings account for overdraft protection "
            "($10 transfer fee, but avoids $35 overdraft fee). "
            "4. Credit Line: overdraft line of credit available for qualified customers "
            "(variable rate, currently 18% APR). "
            "5. Opt-Out: customers can opt out of standard overdraft coverage "
            "(transactions declined instead). "
            "6. Regulation E: customers have until 11:59 PM to deposit funds to avoid fee. "
            "7. Continuous Authorization: holds may be placed for up to 7 days."
        ),
        "metadata": {"source": "Product Team", "category": "fees", "doc_type": "faq", "priority": "high"},
    },
    {
        "id": "faq_fraud_001",
        "text": (
            "FAQ: Reporting Fraud — How to report suspected fraud: "
            "1. Call Fraud Hotline immediately: 1-800-555-FRAUD (available 24/7). "
            "2. Freeze card via mobile app (Card Controls > Lock Card). "
            "3. Visit any branch with ID for in-person reporting. "
            "4. Email: fraud@bank.com (response within 24 hours). "
            "Information needed: account/card number, date/time of suspicious activity, "
            "amount, merchant name, description of what happened. "
            "Provisional credit: issued within 10 business days. "
            "New card: expedited shipping (1-2 business days) at no charge. "
            "Police report: recommended but not required for investigation. "
            "Follow-up: case manager assigned within 48 hours."
        ),
        "metadata": {"source": "Security", "category": "fraud", "doc_type": "faq", "priority": "critical"},
    },
]


def seed() -> None:
    """Seed all collections with sample data."""
    print("Initializing RAG pipeline...")
    rag = RAGPipeline()

    data_map = {
        "product_details": PRODUCT_DETAILS,
        "standard_operating_procedures": STANDARD_OPERATING_PROCEDURES,
        "it_help_and_support": IT_HELP_AND_SUPPORT,
        "hr_policies_and_benefits": HR_POLICIES_AND_BENEFITS,
        "compliance_training": COMPLIANCE_TRAINING,
        "process_guides": PROCESS_GUIDES,
        "regulatory_updates": REGULATORY_UPDATES,
        "faq_and_common_questions": FAQ_AND_COMMON_QUESTIONS,
    }

    for collection_name, documents in data_map.items():
        print(f"\nSeeding {collection_name} ({len(documents)} documents)...")
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        rag.add_documents(collection_name, texts, metadatas, ids)
        count = rag.collection_count(collection_name)
        print(f"  OK {collection_name}: {count} documents")

    print("\nKnowledge base seeded successfully!")
    print(f"\nCollections:")
    for name in COLLECTIONS:
        count = rag.collection_count(name)
        print(f"  - {name}: {count} documents")


if __name__ == "__main__":
    seed()
