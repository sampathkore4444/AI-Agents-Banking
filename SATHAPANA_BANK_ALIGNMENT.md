# Sathapana Bank — AI Agent Alignment Summary

> Maps the 16 banking agents in this workspace to Sathapana Bank (Cambodia) — a retail and SME-focused commercial bank, subsidiary of Bank of Ayudhya (Krungsri) / MUFG, regulated by the National Bank of Cambodia (NBC).

---

## Sathapana Profile (What Drives the Alignment)

| Factor | Implication for Agent Selection |
|--------|---------------------------------|
| Core business is retail + SME lending | Loan, credit risk, and collections agents score highest |
| Strong branch network, growing digital/Bakong presence | Customer service and KYC self-service are high volume |
| NBC AML/KYC enforcement (prakas, SARs, sanctions) | KYC and AML agents are non-negotiable |
| Dual-currency (USD/KHR), heavy cash + Bakong payments | Payment fraud, reconciliation, and cross-border agents matter |
| Deep network with MUFG/Krungsri | Cross-border, internal knowledge, and document digitization leverage group capabilities |

---

## Tier 1 — Priority Alignment (Build First)

| Agent (folder) | Why It Fits Sathapana |
|----------------|-----------------------|
| **KYC Onboarding** (`kyc_agent`) | NBC mandates KYC for every account and SME loan. Automates ID checks (passport/NID), PEP/sanctions screening, risk profiling. Highest regulatory payoff, high volume, clear ROI. |
| **Loan Application Processing** (`loan_agent`) | SME lending is the growth engine. Covers credit checks, income verification, statement analysis, underwriting, and explainable decisions. |
| **Credit Risk Monitoring** (`credit_risk_agent`) | Continuous early-warning on the SME portfolio; detects deteriorating accounts before default. |
| **AML Alert** (`aml_alert_agent`) | NBC reporting obligations (SAR filing, red-flag typologies). Complements KYC agent on the same account data. |

**Tip for Cambodia:** KYC + loan agents should share one RAG vector DB of NBC prakas and internal credit policies to keep retrieval consistent.

> **Implementation status (Sep 2026):** A Cambodia-localized, end-to-end KYC onboarding agent has been built in **`sathapana_kyc_agent/`** — NBC/CAMFIU-aligned RAG knowledge base, Khmer document schemas, UBO screening (25% / risk-based 10%), Bakong linkage, USD/KHR accounts, audit trail, dependency-free MCP stdio server, deterministic demo, and a passing pytest suite. Run: `cd sathapana_kyc_agent && python main.py seed && python main.py demo`.

---

## Tier 2 — High Value, Medium Effort

| Agent (folder) | Why It Fits Sathapana |
|----------------|-----------------------|
| **Customer Service** (`customer_service_agent`) | Covers FAQ, account info, disputes, complaints — all with Khmer/English multilingual support (1.4 pattern). Deflects branch/call-center load. |
| **Document Digitization** (`document_digitization_agent`) | SME loan files and KYC packs are paper-heavy; OCR + classification removes back-office bottleneck. |
| **Payment Fraud Prevention** (`payment_fraud_prevention_agent`) | Dollar-denominated Bakong and transfer fraud is a live risk; validates beneficiaries and flags unusual amounts in real time. |
| **Loan Collections** (`loan_collections_agent`) | Delinquent SME/retail loans need compliant (NBC/LMCI-code) communication and payment-plan negotiation. |
| **Payment Reconciliation** (`payment_reconciliation_agent`) | High-volume dollar/riel payments + Bakong make reconciliation mismatches routine; agent auto-matches and flags exceptions. |

---

## Tier 3 — Strategic / Enablement

| Agent (folder) | Why It Fits Sathapana |
|----------------|-----------------------|
| **Financial Statement Analysis** (`financial_statement_agent`) | Powers SME credit decisions and audit support with consistent ratio analysis. |
| **Fraud Detection** (`fraud_detection_agent`) | Transaction-level real-time monitoring for account takeover on digital channels. |
| **Internal Knowledge** (`internal_knowledge_agent`) | Bank-wide SOP, product, IT and HR queries for thousands of staff across branches. |
| **Product Recommendation** (`product_recommendation_agent`) | Cross-sell loans, savings, and insurance to the retail/SME base (e.g., loan-to-savings upsell). |
| **Cross-Border Payment** (`cross_border_payment_agent`) | Region remittance corridor (Cambodia–Thailand, Cambodia–various) + MUFG network; explains fees, FX, compliance. |
| **Lead Qualification** (`lead_qualification_agent`) | Qualifies SME loan leads from web/chat/referrals before routing to branch officers. |
| **Standing Order / Bill Payment** (`standing_order_agent`) | Recurring rent, salary, and bill payments — big retail self-service win on Bakong. |

---

## Recommended 6-Quarter Roadmap

| Phase | Agents | Goal |
|-------|--------|------|
| **Q1–Q2 (now)** | KYC, Loan, Credit Risk, AML | Fastest regulatory + credit ROI; reuse one vector DB |
| **Q3–Q4** | Customer Service, Document Digitization, Payment Fraud Prevention | Cut branch/call-center load and OCR backlog |
| **Q5–Q6** | Financial Statement, Collections, Reconciliation, Product Recommendation | Deepen SME credit quality and cross-sell |

---

## Key Considerations Specific to Sathapana

- **Language:** Embeddings must handle Khmer + English (cross-lingual embeddings) for customer-facing agents.
- **Regulator:** Vector DB and logs must survive NBC audit (source citations, audit trails, data residency in-country).
- **Bakong:** Integration via NBC's Bakong API is a priority MCP tool for payment, reconciliation, and standing-order agents.
- **Dual currency:** Models must reason over USD and KHR amounts consistently (FX-aware prompts).
- **Group synergy:** Reuse MUFG/Krungsri patterns for cross-border and internal knowledge rather than building from scratch.

---

*Prepared for the AI Agents RAG MPC workspace. Agents map to BANKING_USE_CASES.md sections: KYC=4.1, Loan=3.1/3.2, Credit Risk=6.1, AML=2.3, Customer Service=1.x, etc.*