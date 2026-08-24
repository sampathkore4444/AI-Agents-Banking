# Loan Application Processing Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for loan application processing in banking, powered by a **RAG pipeline** for regulatory knowledge retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

**Covers both 3.1 Loan Application Processing AND 3.2 Credit Scoring & Risk Assessment.**

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    LOAN APPLICATION PROCESSING AGENT                      │
│                                                                          │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────────────┐ │
│  │  User     │───▶│  LLM Core   │───▶│  MCP Tool Server                │ │
│  │  Query    │    │  (ReAct     │◀───│  ├── knowledge_search           │ │
│  │           │◀───│   Agent)    │    │  ├── check_credit               │ │
│  │           │    │             │    │  ├── verify_income              │ │
│  │           │    │  Options:   │    │  ├── verify_document            │ │
│  │           │    │  • Ollama   │    │  ├── create_application         │ │
│  │           │    │  • vLLM     │    │  ├── assess_risk                │ │
│  │           │    │  • SGLang   │    │  ├── analyze_bank_statement  ← NEW │
│  │           │    │             │    │  ├── check_alternative_data  ← NEW │
│  │           │    │             │    │  ├── embed_profile           ← NEW │
│  │           │    │             │    │  ├── explain_loan_decision   ← NEW │
│  │           │    │             │    │  └── notify_customer            │ │
│  └──────────┘    └──────┬──────┘    └──────────────────────────────────┘ │
│                         │                                                │
│                         ▼                                                │
│                  ┌──────────────┐                                         │
│                  │  RAG Engine  │                                         │
│                  │  (ChromaDB)  │                                         │
│                  │  • Regulations│                                        │
│                  │  • Policies  │                                         │
│                  │  • Eligibility│                                        │
│                  │  • Underwriting│                                       │
│                  │  • Past Cases│                                         │
│                  │  • Fair Lending ← NEW                                  │
│                  │  • Credit Scoring ← NEW                                │
│                  └──────────────┘                                         │
└────────────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed

### 3.1 Loan Application Processing (Original)

| Tool | Description |
|------|-------------|
| `knowledge_search` | RAG-powered search over loan regulations and policies |
| `create_application` | Create a new loan application |
| `get_application_status` | Check application status |
| `update_application_status` | Update documents, status, decisions |
| `check_credit` | Pull credit report from bureau |
| `verify_customer_income` | Verify income from multiple sources |
| `verify_document` | OCR + validation for loan documents |
| `calculate_loan_affordability` | DTI, monthly payment, total cost |
| `assess_risk` | Risk score + underwriting decision |

### 3.2 Credit Scoring & Risk Assessment (NEW)

| Tool | Description |
|------|-------------|
| `analyze_bank_statement` | Deep transaction categorization, spending patterns, irregularity detection |
| `check_alternative_credit_data` | Rent, utilities, phone, employment data for thin credit files |
| `embed_profile` | ML embedding of customer financial profile for clustering |
| `explain_loan_decision` | ECOA-compliant decision explanation with adverse action reasons |

## Loan Application Flow

```
Customer: "I want to apply for a $350,000 mortgage"
    │
    ├── 1. create_application()
    │
    ├── 2. knowledge_search("conventional mortgage requirements")
    │
    ├── 3. check_credit(name, dob, ssn)
    │
    ├── 4. verify_income(customer_id, claimed_income, employment_type)
    │
    ├── 5. verify_document(payslip_url, "payslip")
    │
    ├── 6. verify_document(tax_return_url, "tax_return")
    │
    ├── 7. analyze_bank_statement(customer_id, statement_url, 6)  ← NEW
    │
    ├── 8. check_alternative_credit_data(customer_id)  ← NEW (if thin file)
    │
    ├── 9. calculate_loan_affordability(income, debts, amount, rate, term)
    │
    ├── 10. assess_risk(credit_score, income, amount, ltv, dti)
    │
    ├── 11. embed_profile(customer_id, ...)  ← NEW
    │
    ├── 12. update_application_status(app_id, decision="approved")
    │
    ├── 13. explain_loan_decision(app_id, decision, ...)  ← NEW
    │
    └── 14. notify_customer(customer_id, "application_approved")
```

## Quick Start

```bash
cd loan_agent
pip install -r requirements.txt
python seed_knowledge.py

# Start an LLM backend
ollama serve  # or vllm serve / sglang

# Run the agent
python -m llm.agent_ollama
```

## Project Structure

```
loan_agent/
├── server.py              # MCP server with all 14 tools
├── rag_pipeline.py        # RAG engine (7 collections)
├── config.py              # Settings
├── seed_knowledge.py      # Seed loan knowledge (30+ docs)
├── compare_agents.py      # Compare LLM backends
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py      # Base agent with production patterns
│   ├── agent_ollama.py    # Ollama
│   ├── agent_vllm.py      # vLLM
│   └── agent_sglang.py    # SGLang
└── tools/
    ├── __init__.py
    ├── credit_bureau.py           # Credit report (3.1)
    ├── income_verification.py     # Income verification (3.1)
    ├── document_verification.py   # Loan document OCR (3.1)
    ├── application_management.py  # App lifecycle + affordability (3.1)
    ├── credit_scoring.py          # Risk assessment + ML embedding (3.1+3.2)
    ├── bank_statement_analysis.py # Deep transaction analysis (3.2) ← NEW
    ├── alternative_data.py        # Rent, utilities, non-traditional (3.2) ← NEW
    ├── explainability.py          # ECOA decision explanations (3.2) ← NEW
    └── notifications.py           # Customer notifications
```

## Knowledge Base (7 Collections)

| Collection | Content | Documents |
|------------|---------|-----------|
| `loan_regulations` | TILA, ECOA, QM rules, HMDA, fair lending | 5 |
| `product_policies` | Conventional, FHA, auto, personal loan requirements | 4 |
| `eligibility_criteria` | Credit tiers, income verification, property eligibility | 3 |
| `underwriting_guidelines` | DTI, LTV, appraisal, manual underwriting rules | 2 |
| `past_loan_decisions` | Approved, declined, conditional cases | 3 |
| `fair_lending_guidelines` | ECOA adverse action, disparate impact, pricing fairness | 4 ← NEW |
| `credit_scoring_models` | FICO factors, scoring ranges, alternative scoring, best practices | 4 ← NEW |

## What Was Added from 3.2

### Bank Statement Analysis
- Transaction categorization (income, housing, utilities, food, irregular)
- Income stability detection
- Cash flow analysis (savings rate, minimum balance)
- Irregularity detection (NSF fees, overdrafts, large cash withdrawals)
- Creditworthiness scoring (0-100)

### Alternative Credit Data
- Rent payment history (on-time rate, landlord verification)
- Utility payment history (disconnects, on-time rate)
- Phone/internet payment history
- Employment stability (years, industry, income trend)
- Education verification
- Alternative credit score for thin-file customers

### ML Customer Embedding
- 128-dimensional profile embedding
- Risk cluster assignment (prime, near-prime, subprime, high-risk)
- Default probability prediction
- Similar historical profile matching

### Decision Explainability
- Plain-English decision explanation
- Factor-by-factor breakdown
- ECOA-compliant adverse action notice
- Specific reasons for denial
- Steps to improve (if declined)

## Production Patterns

Same as KYC Agent — see `llm/base_agent.py`:

| Pattern | Class |
|---------|-------|
| Intent Routing | `IntentRouter` |
| Guardrails | `Guardrails` |
| Human-in-the-Loop | `HumanApprovalManager` |
| Memory Management | `ConversationMemory` |
| Error Handling | `ErrorHandler` |
| Observability | `AgentTracer` |

## LLM Backends

| Backend | Best For | Speed |
|---------|----------|-------|
| **Ollama** | Local dev | ~2-5s |
| **vLLM** | Production | ~0.5-2s |
| **SGLang** | Structured output | ~0.3-1.5s |

## Notes

- Tool stubs return deterministic results — swap for real APIs in production
- Bank statement analysis uses simulated transaction data
- ML embedding is synthetic — production uses trained models (XGBoost, LightGBM)
- Explainability tool generates ECOA-compliant adverse action notices
- Alternative data sources are simulated — real integration requires Plaid, Finicity, etc.
- Credit scoring cluster assignment is rule-based — production uses ML clustering
