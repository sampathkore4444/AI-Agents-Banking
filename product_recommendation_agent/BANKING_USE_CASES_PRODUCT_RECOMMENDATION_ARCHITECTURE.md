# Product Recommendation Agent — Architecture

## High-Level Architecture

```
                          ┌─────────────────────────────────────────┐
                          │       PRODUCT RECOMMENDATION AGENT       │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   CUSTOMER           │          │   RECOMMENDATION    │          │   PRODUCT           │
│   INTELLIGENCE LAYER │          │   ENGINE            │          │   CATALOG LAYER     │
│                     │          │                      │          │                     │
│ • Customer 360      │◄────────►│ • Rule Engine        │◄────────►│ • Product DB        │
│ • Segmentation      │          │ • ML Matching        │          │ • Eligibility       │
│ • Lifecycle Stage   │          │ • Cross-Sell Rules   │          │ • Fee Schedules     │
│ • Behavior Analysis │          │ • Embedding Match    │          │ • Competitor Data   │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
           │                                  │                                  │
           └──────────────────────────────────┼──────────────────────────────────┘
                                              │
                                              ▼
                          ┌─────────────────────────────────────────┐
                          │              MCP SERVER                  │
                          │         (45+ Tools Exposed)              │
                          └─────────────────────────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│   RAG KNOWLEDGE     │          │   EMBEDDING         │          │   LLM AGENT         │
│   BASE              │          │   VECTOR DB         │          │   (Ollama/vLLM/     │
│                     │          │                      │          │    SGLang)          │
│ • Product Catalog   │          │ • Product Embs       │          │                     │
│ • Eligibility       │          │ • Customer Embs      │          │ • Guardrails        │
│ • Cross-Sell Rules  │          │ • Preference Match   │          │ • HITL              │
│ • Promotions        │          │ • Customer Clusters  │          │ • Memory            │
│ • Segments          │          │                      │          │ • Streaming         │
│ • Fee Schedules     │          │                      │          │ • Fair Lending      │
│ • Competitors       │          │                      │          │                     │
└─────────────────────┘          └─────────────────────┘          └─────────────────────┘
```

## Detailed Component Flow

```
Step 1: Customer Request
    │
    ▼
Step 2: Get Customer 360 Profile
    │
    ├─ Demographics (age, income, segment)
    ├─ Existing products
    ├─ Credit score
    ├─ Lifecycle stage
    │
    ▼
Step 3: Eligibility Check
    │
    ├─ Credit score minimum
    ├─ Income requirement
    ├─ Age requirement
    ├─ Residency requirement
    │
    ▼
Step 4: Product Matching
    │
    ├─ Segment match (student, professional, family, affluent, retiree)
    ├─ Lifecycle fit (entry, growth, accumulation, preservation, distribution)
    ├─ Category diversity (different from held products)
    ├─ Credit sweet spot (score just above minimum)
    │
    ▼
Step 5: Cross-Sell Detection
    │
    ├─ Checking → Savings
    ├─ Debit → Credit Card
    ├─ Savings → Investment
    ├─ Auto Loan → Insurance
    ├─ Mortgage → HELOC
    │
    ▼
Step 6: ML Embedding Match
    │
    ├─ Customer preference embedding
    ├─ Product feature embedding
    ├─ Cosine similarity scoring
    │
    ▼
Step 7: Generate Recommendations
    │
    ├─ Rank by relevance score
    ├─ Apply guardrails (min relevance, max count)
    ├─ Check for required approval
    │
    ▼
Step 8: Present to Customer
    │
    ├─ Explain why recommended
    ├─ Show eligibility status
    ├─ Highlight relevant promotions
    ├─ Provide alternatives
```

## MCP Tool Definitions

### Get Recommendations
```json
{
  "name": "get_recommendations",
  "description": "Generate personalized product recommendations",
  "parameters": {
    "customer_id": {"type": "string", "required": true},
    "max_recommendations": {"type": "integer", "default": 10},
    "strategy": {"type": "string", "enum": ["balanced", "cross_sell", "upsell", "win_back"]}
  }
}
```

### Search Products
```json
{
  "name": "search_products",
  "description": "Search products by category, segment, credit score",
  "parameters": {
    "category": {"type": "string", "enum": ["deposit", "credit", "lending", "investment"]},
    "target_segment": {"type": "string"},
    "min_credit_score": {"type": "integer"},
    "max_annual_fee": {"type": "number"}
  }
}
```

### Create Offer
```json
{
  "name": "create_offer",
  "description": "Create a promotional offer",
  "parameters": {
    "offer_id": {"type": "string", "required": true},
    "name": {"type": "string", "required": true},
    "offer_type": {"type": "string", "enum": ["apy_bonus", "cash_back", "rate_reduction", "fee_waiver"]},
    "target_segments": {"type": "array"},
    "start_date": {"type": "string"},
    "end_date": {"type": "string"}
  }
}
```

## RAG Pipeline Detail

```
Step 1: Query Rewrite
    │
    ▼ "What credit card is best for a young professional?"
    │
Step 2: Embed Query
    │
    ▼ [0.023, -0.156, 0.089, ...] (128-dim)
    │
Step 3: Search All Collections (7 parallel)
    │
    ├─ product_catalog (finds credit cards)
    ├─ eligibility_criteria (checks requirements)
    ├─ cross_sell_rules (cross-sell potential)
    ├─ promotional_offers (active promos)
    ├─ customer_segments (segment match)
    ├─ fee_schedules (fee comparison)
    └─ competitor_products (market positioning)
    │
Step 4: Merge & Rerank
    │
    ▼ Top 5 chunks by relevance score
    │
Step 5: Assemble Context
    │
    ▼ "[1] (catalog) Cash Back Rewards Credit Card — 2% on all purchases..."
    │
Step 6: Generate Response with Citations
```

## Vector Database Schema

| Collection | Documents | Description |
|------------|-----------|-------------|
| `product_catalog` | 12 | Full product details |
| `eligibility_criteria` | 7 | Requirements by product |
| `cross_sell_rules` | 6 | Affinity and triggers |
| `promotional_offers` | 5 | Active campaigns |
| `customer_segments` | 6 | Life stages and personas |
| `fee_schedules` | 4 | Fee structures |
| `competitor_products` | 3 | Market benchmarks |

## Embedding Dimensions

| Vector | Dimensions | Purpose |
|--------|------------|---------|
| Product Embedding | 128 | Product feature representation |
| Customer Preference | 128 | Customer needs and preferences |
| Customer-Product Match | — | Cosine similarity score |

## Recommendation Scoring

```
                    ┌──────────────────────────────┐
                    │   RECOMMENDATION SCORE        │
                    └──────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   RULE-BASED  │          │   ML-BASED    │          │   CONTEXTUAL  │
│   (40%)       │          │   (35%)       │          │   (25%)       │
│               │          │               │          │               │
│ • Segment     │          │ • Embedding   │          │ • Lifecycle   │
│ • Eligibility │          │   Similarity  │          │ • Season      │
│ • Category    │          │ • Clustering  │          │ • Promotions  │
│   Diversity   │          │ • Affinity    │          │ • History     │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │   COMBINED SCORE (0-100)      │
                    └──────────────────────────────┘
```

## Fair Lending Compliance

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAIR LENDING CHECKPOINTS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CONSISTENT TREATMENT                                        │
│     • Same eligibility rules for all customers in same segment  │
│     • No recommendations based on protected classes             │
│     • Document all recommendation rationale                     │
│                                                                 │
│  2. TRANSPARENCY                                                │
│     • Explain why product was recommended                       │
│     • Disclose all fees and terms                               │
│     • Provide alternatives if declined                          │
│                                                                 │
│  3. EQUAL ACCESS                                                │
│     • No steering to higher-cost products                       │
│     • Consistent pricing across segments                        │
│     • Equal promotion visibility                                │
│                                                                 │
│  4. AUDIT TRAIL                                                 │
│     • Log all recommendations made                              │
│     • Track acceptance/rejection rates                          │
│     • Monitor for disparate impact                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    END-TO-END DATA FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CUSTOMER INTELLIGENCE                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Customer │───►│ Segment  │───►│ Lifecycle│                  │
│  │ 360      │    │ Match    │    │ Stage    │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  PRODUCT MATCHING                                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Eligibil-│───►│ Cross-   │───►│ ML       │                  │
│  │ ity Check│    │ Sell     │    │ Embedding│                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  RECOMMENDATION                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Score &  │───►│ Guard-   │───►│ Present  │                  │
│  │ Rank     │    │ rails    │    │ to Cust. │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **7 RAG collections** | Separate concerns for better retrieval |
| **128-dim embeddings** | Balance between expressiveness and speed |
| **Eligibility pre-check** | Avoid recommending ineligible products |
| **Cross-sell rules** | Structured triggers for product affinity |
| **Lifecycle stages** | Products vary by customer life stage |
| **Fair lending guardrails** | Regulatory compliance |
| **Human-in-the-loop** | High-value offers need approval |
| **Customer clustering** | Group similar profiles for batch recommendations |
| **Offer personalization** | Target offers to relevant segments |
| **CRM integration** | Track conversion and ROI |
