# Product Recommendation Agent

An AI agent for personalized banking product recommendations using **RAG**, **MCP**, and **embeddings**. Recommends banking products based on customer profiles, eligibility, and cross-sell opportunities.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Product Recommendation Agent                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Product     │  │  Customer    │  │ Recommendation│         │
│  │   Catalog     │  │  360         │  │ Engine        │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │   Offer      │  │  Campaign    │  │  Product     │         │
│  │  Management  │  │  Management  │  │  Embedding   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │ Notifications│  │     CRM      │  │    RAG       │         │
│  │              │  │              │  │   Engine     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM Agent (Ollama/vLLM/SGLang)             │   │
│  │  • Guardrails • HITL • Memory • Streaming • Tracing     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### RAG Knowledge Base (7 collections)
- **Product Catalog** — Savings, checking, credit cards, loans, investments
- **Eligibility Criteria** — Credit score, income, age, residency requirements
- **Cross-Sell Rules** — Product affinity, lifecycle triggers, bundling
- **Promotional Offers** — Current campaigns, seasonal promotions
- **Customer Segments** — Life stages, behavioral, value-based
- **Fee Schedules** — Account fees, transaction fees
- **Competitor Products** — Benchmarking, feature comparison

### MCP Tools (45+ tools)

| Category | Tools | Description |
|----------|-------|-------------|
| **Product Catalog** | `search_products`, `get_product_details`, `compare_products`, `get_related_products`, `add_new_product`, `update_product_details`, `deactivate_product` | Manage and query product catalog |
| **Customer 360** | `get_customer_profile`, `search_customers`, `customer_products`, `customer_transactions`, `update_customer`, `add_new_customer`, `customer_segments`, `high_value_customers` | Complete customer view |
| **Recommendation Engine** | `get_recommendations`, `explain_recommendation`, `upsell_opportunities`, `win_back_recommendations` | Personalized recommendations |
| **Offer Management** | `active_offers`, `offer_details`, `create_new_offer`, `update_offer_details`, `deactivate_offer`, `redeem_offer`, `offer_analytics`, `personalized_offers` | Promotional offers |
| **Campaign Management** | `create_new_campaign`, `launch_campaign`, `pause_campaign`, `close_campaign`, `campaign_analytics`, `schedule_campaign_outreach` | Marketing campaigns |
| **Product Embeddings** | `embed_product`, `embed_customer_prefs`, `match_customer_products`, `similar_products`, `cluster_customer_base`, `embedding_stats` | ML-based matching |
| **Notifications** | `send_product_rec`, `send_offer`, `send_cross_sell`, `notification_history`, `notification_stats` | Customer outreach |
| **CRM** | `log_customer_interaction`, `customer_interaction_history`, `create_sales_lead`, `update_sales_lead`, `convert_sales_lead`, `crm_stats`, `pending_follow_ups` | Sales tracking |
| **RAG** | `knowledge_search` | Search product knowledge base |

### ML Embeddings
- **Product Embedding** — 128-dim vector from product features
- **Customer Preference Embedding** — Risk tolerance, income, age, lifecycle
- **Customer-Product Matching** — Cosine similarity matching
- **Customer Clustering** — K-means grouping by preferences

### Agent Capabilities
- **Guardrails** — Eligibility checks, relevance thresholds
- **Human-in-the-Loop** — Approval for high-value offers
- **Memory** — Customer interaction context
- **Streaming** — Real-time recommendation output
- **Fair Lending** — Consistent treatment across segments

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Knowledge Base
```bash
python seed_knowledge.py
```

### 3. Run with Ollama
```bash
ollama serve
ollama pull llama3.1:8b
python -m llm.agent_ollama
```

### 4. Or Run MCP Server
```bash
python server.py
```

### 5. Compare Backends
```bash
python compare_agents.py
```

## Configuration

Create a `.env` file:
```env
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o

# Recommendation Parameters
MIN_RELEVANCE_SCORE=0.6
MAX_RECOMMENDATIONS=10
CROSS_SELL_THRESHOLD=0.7
```

## Recommendation Flow

```
Customer Request
    │
    ├─→ Get Customer 360 Profile
    │
    ├─→ Check Existing Products
    │
    ├─→ Eligibility Check (credit, income, age)
    │
    ├─→ Segment & Lifecycle Match
    │
    ├─→ Cross-Sell Detection
    │
    ├─→ ML Embedding Match
    │
    ├─→ Generate Recommendations
    │
    ├─→ Apply Guardrails
    │
    └─→ Return Ranked Recommendations
```

## Customer Segments

| Segment | Age | Income | Best Products |
|---------|-----|--------|---------------|
| Students | 18-24 | $0-25K | Student checking, Roth IRA |
| Young Professionals | 25-35 | $40-80K | Cash back card, savings, Roth IRA |
| Families | 30-50 | $80-150K | Mortgage, HELOC, 529 plan |
| Affluent | 35-65 | $150K+ | Travel card, brokerage, private banking |
| Retirees | 65+ | $30-80K | CDs, bonds, trust services |

## Project Structure

```
product_recommendation_agent/
├── server.py                    # MCP server with 45+ tools
├── rag_pipeline.py              # RAG engine (7 collections)
├── config.py                    # Settings
├── seed_knowledge.py            # Product knowledge base
├── compare_agents.py            # Compare Ollama/vLLM/SGLang
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py            # Guardrails, HITL, memory
│   ├── agent_ollama.py          # Ollama backend
│   ├── agent_vllm.py            # vLLM backend
│   └── agent_sglang.py          # SGLang backend
└── tools/
    ├── product_catalog.py       # Product management
    ├── customer_360.py          # Customer profiles
    ├── recommendation_engine.py # Recommendation logic
    ├── offer_management.py      # Promotional offers
    ├── campaign_management.py   # Marketing campaigns
    ├── product_embedding.py     # ML matching
    ├── notifications.py         # Customer outreach
    └── crm.py                   # Sales tracking
```
