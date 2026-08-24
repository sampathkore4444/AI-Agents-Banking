# AI Agents in Banking — Concepts & Real-World Scenarios

> A practical guide explaining every concept behind our KYC Onboarding Agent, with real banking examples.

---

## Table of Contents

1. [LLM (Large Language Model)](#1-llm-large-language-model)
2. [RAG (Retrieval Augmented Generation)](#2-rag-retrieval-augmented-generation)
3. [MCP (Model Context Protocol)](#3-mcp-model-context-protocol)
4. [Embeddings](#4-embeddings)
5. [Vector Database](#5-vector-database)
6. [Context Window](#6-context-window)
7. [Batching](#7-batching)
8. [KV Cache](#8-kv-cache)
9. [GPU Memory](#9-gpu-memory)
10. [Scheduling & Inference](#10-scheduling--inference)
11. [How It All Fits Together](#11-how-it-all-fits-together)

---

## 1. LLM (Large Language Model)

### What It Is

An LLM is a neural network trained on trillions of words that can understand and generate human language. Think of it as an extremely sophisticated autocomplete — but one that has "read" essentially the entire internet and can reason, summarize, translate, and answer questions.

**Key insight:** An LLM doesn't "know" things like a database does. It has learned *patterns* from training data. When you ask "What is KYC?", it generates an answer based on patterns it saw during training — not because it looked up KYC in a database.

### How It Works (Simplified)

```
Input: "What documents do I need for a UK business account?"

Tokenization: ["What", " documents", " do", " I", " need", " for", " a", " UK", " business", " account", "?"]
                    ↓
Embedding: Each token → vector (list of numbers representing meaning)
                    ↓
Transformer Layers: 96 layers of attention mechanisms process the vectors
                    ↓
Next Token Prediction: The model predicts one token at a time
                    ↓
Output: "To open a UK business account, you typically need..."
```

### Real-World Banking Scenario

**Scenario:** A customer calls the bank's AI assistant at 2 AM.

```
Customer: "I'm a US citizen living in London. Can I open a savings account?"

LLM generates:
"You can open a savings account with us. As a US citizen residing in the UK,
you'll need:
1. Valid US passport or UK BRP (Biometric Residence Permit)
2. Proof of UK address (utility bill, bank statement)
3. Social Security Number (for FATCA compliance)
4. UK National Insurance Number (if applicable)

Would you like me to start the application process?"
```

**What the LLM did:**
- Understood the customer's dual-country situation
- Retrieved knowledge about US/UK banking regulations (from training)
- Generated a coherent, helpful response
- Offered next steps

### Banking Use Cases

| Use Case | What LLM Does |
|----------|---------------|
| Customer Support | Answers questions about products, fees, policies |
| Document Summarization | Summarizes long legal documents for officers |
| Email Drafting | Generates compliance emails, customer responses |
| Report Writing | Creates regulatory reports from structured data |
| Code Generation | Writes SQL queries for data analysis |
| Meeting Summarization | Transcribes and summarizes branch meetings |

### Limitations in Banking

| Problem | Example | Risk |
|---------|---------|------|
| **Hallucination** | LLM invents a regulation that doesn't exist | Compliance violation |
| **Outdated knowledge** | LLM doesn't know about regulations from last week | Wrong information |
| **No access to live data** | LLM can't check account balance | Useless for real-time queries |
| **No audit trail** | Can't explain *how* it got an answer | Regulatory non-compliance |

**This is why we need RAG, MCP, and other components — to give the LLM real data and tools.**

---

## 2. RAG (Retrieval Augmented Generation)

### What It Is

RAG is a technique that combines **retrieval** (searching a database) with **generation** (LLM writing text). Instead of relying solely on the LLM's training data, RAG first *retrieves* relevant documents from a knowledge base, then feeds them to the LLM as context.

**Without RAG:**
```
User: "What's the KYC requirement for UK business accounts?"
LLM: [Uses training data from 2023 — may be outdated]
```

**With RAG:**
```
User: "What's the KYC requirement for UK business accounts?"
    ↓
Step 1: RETRIEVE → Search vector DB → Found: MLR 2017 Reg 28 (latest version)
    ↓
Step 2: AUGMENT → LLM gets: "Here's the current regulation: [regulation text]"
    ↓
Step 3: GENERATE → LLM writes answer based on actual regulation
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                             │
│                                                                 │
│  INDEXING (One-time, offline):                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Documents │───▶│ Chunking │───▶│Embedding │───▶│ Vector DB│  │
│  │ (PDFs,   │    │ Split into│    │ Convert  │    │ Store    │  │
│  │  HTML,   │    │ 500-word │    │ to vectors│    │ vectors  │  │
│  │  docs)   │    │ chunks   │    │          │    │          │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
│  RETRIEVAL (Every query, online):                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ User     │───▶│ Embed    │───▶│ Search   │───▶│ Top-K    │  │
│  │ Query    │    │ query    │    │ similar  │    │ chunks   │  │
│  │          │    │          │    │ vectors  │    │ retrieved│  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
│  GENERATION (Every query, online):                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Retrieved│───▶│ LLM      │───▶│ Answer   │                  │
│  │ chunks + │    │ generates│    │ with     │                  │
│  │ query    │    │ response │    │ citations│                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Banking Scenario

**Scenario:** Compliance officer needs to understand a new regulation.

```
Without RAG:
  Officer reads 200-page regulation document manually (2 hours)

With RAG:
  Officer: "What are the new EDD requirements for crypto businesses under FCA's 2024 rules?"

  RAG Pipeline:
  1. Query embedding → search vector DB
  2. Retrieved chunks:
     - FCA PS23/14: "Crypto businesses must apply EDD for transactions > £1,000..."
     - FCA Guidance: "EDD measures include source of funds verification..."
     - MLR 2017 amendment: "Regulation 33 now covers crypto-asset service providers..."
  3. LLM generates:
     "Under FCA's PS23/14 (effective March 2024), crypto businesses must:
      1. Apply EDD for all transactions exceeding £1,000
      2. Verify source of funds for high-value transactions
      3. Enhanced monitoring for wallets associated with mixing services
      Reference: PS23/14 Section 4.2, MLR 2017 Reg 33"
  
  Time: 30 seconds instead of 2 hours
```

### Hybrid Search

Our RAG pipeline uses **hybrid search** — combining two search methods:

```
User Query: "UK limited company business account KYC"

┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID SEARCH                                │
│                                                                 │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │  BM25 (Keyword) │      │  Semantic       │                  │
│  │                 │      │  (Embedding)    │                  │
│  │  Finds exact    │      │  Finds similar  │                  │
│  │  matches:       │      │  meaning:       │                  │
│  │  • "UK"         │      │  • "UK" ≈ "United Kingdom"         │
│  │  • "limited     │      │  • "limited company" ≈ "Ltd"       │
│  │    company"     │      │  • "KYC" ≈ "customer due diligence"│
│  │  • "business"   │      │                 │                  │
│  └────────┬────────┘      └────────┬────────┘                  │
│           │                        │                            │
│           └──────────┬─────────────┘                            │
│                      │                                          │
│                      ▼                                          │
│            ┌──────────────────┐                                 │
│            │  Rank Fusion     │                                 │
│            │  (Combine &      │                                 │
│            │   re-rank)       │                                 │
│            └──────────────────┘                                 │
```

**Why both?**
- BM25 catches exact terms (regulation numbers, specific product names)
- Semantic search catches paraphrases ("How do I verify identity?" ≈ "identity verification process")

### Banking Use Cases

| Use Case | What RAG Does |
|----------|---------------|
| Policy Search | "What's the overdraft policy?" → retrieves actual policy document |
| Regulation Lookup | "What does FCA say about PEPs?" → retrieves specific regulation |
| Risk Assessment | Retrieves similar past cases to inform current decision |
| Product Information | "What fees apply to international transfers?" → retrieves fee schedule |
| Compliance Playbook | "What's the procedure for filing a SAR?" → retrieves step-by-step guide |

---

## 3. MCP (Model Context Protocol)

### What It Is

MCP is a standardized way for AI agents to connect to external tools and data sources. Think of it as a **USB port for AI** — a universal interface that lets any LLM talk to any tool.

**Without MCP:**
```
Each AI agent needs custom code to connect to:
- Bank's API (custom integration)
- Sanctions database (custom integration)
- Core banking system (custom integration)
= Months of integration work per agent
```

**With MCP:**
```
AI agent connects via standard MCP protocol:
┌─────────┐     MCP     ┌──────────────────┐
│  Agent  │◀───────────▶│  Tool Server     │
│         │             │  (exposes tools) │
└─────────┘             └──────────────────┘

Swap tools without changing agent code!
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP ARCHITECTURE                              │
│                                                                 │
│  ┌─────────────┐         ┌──────────────────────────────────┐   │
│  │  MCP Client │◀───────▶│  MCP Server (Tool Provider)      │   │
│  │  (Your      │  stdio/ │                                  │   │
│  │   Agent)    │  HTTP   │  Tools:                          │   │
│  │             │         │  ├── verify_identity()           │   │
│  │  Calls:     │         │  ├── screen_sanctions()          │   │
│  │  session.   │         │  ├── create_bank_account()       │   │
│  │  call_tool( │         │  └── notify_customer()           │   │
│  │    "tool",  │         │                                  │   │
│  │    {args})  │         │  Each tool has:                  │   │
│  │             │         │  • name                          │   │
│  └─────────────┘         │  • description                   │   │
│                          │  • input schema                  │   │
│                          │  • handler function              │   │
│                          └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Banking Scenario

**Scenario:** Processing a high-value international transfer.

```
Customer: "I want to send £50,000 to my supplier in Germany"

Agent flow using MCP tools:

Step 1: knowledge_search(query="international transfer requirements")
  → MCP calls RAG pipeline
  → Returns: FCA rules, correspondent bank fees, sanctions requirements

Step 2: screen_sanctions(name="Supplier GmbH", jurisdiction="DE")
  → MCP calls OFAC/EU sanctions API
  → Returns: CLEAR (not on any list)

Step 3: verify_beneficiary(iban="DE89370400440532013000", name="Supplier GmbH")
  → MCP calls payment system API
  → Returns: IBAN valid, bank confirmed

Step 4: assess_risk(amount=50000, beneficiary_jurisdiction="DE", customer_risk="low")
  → MCP calls risk engine
  → Returns: medium risk (large amount) → requires approval

Step 5: request_approval(reason="£50k transfer to DE", risk="medium")
  → MCP notifies compliance officer
  → Officer approves via Slack

Step 6: execute_transfer(amount=50000, currency="GBP", iban="DE89370400...")
  → MCP calls payment gateway
  → Returns: Transfer completed, ref: TXN-2024-XYZ

Step 7: notify_customer(customer_id="CUST-123", message="Transfer sent successfully")
  → MCP calls notification service
  → Customer receives email + SMS
```

### Banking Use Cases

| Use Case | MCP Tools Used |
|----------|----------------|
| Account Opening | `extract_document`, `verify_identity`, `screen_sanctions`, `create_account` |
| Fraud Detection | `get_transaction`, `check_velocity`, `block_card`, `notify_customer` |
| Loan Processing | `check_credit`, `verify_income`, `calculate_affordability`, `create_loan` |
| Compliance | `search_regulations`, `file_sar`, `update_case`, `notify_officer` |
| Payments | `validate_iban`, `screen_sanctions`, `execute_transfer`, `reconcile` |

---

## 4. Embeddings

### What It Is

An embedding is a way to convert text into a list of numbers (a vector) that captures the *meaning* of the text. Words or sentences with similar meanings get similar number lists.

**Simple example:**

```
"dog"      → [0.2, 0.8, 0.1, 0.9, ...]  (768 numbers)
"puppy"    → [0.2, 0.7, 0.1, 0.8, ...]  (very similar!)
"cat"      → [0.9, 0.1, 0.8, 0.2, ...]  (different — it's a cat)
"bank"     → [0.5, 0.3, 0.6, 0.4, ...]  (financial institution)
"riverbank"→ [0.5, 0.3, 0.6, 0.4, ...]  (similar embedding = same word sense)
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMBEDDING PROCESS                             │
│                                                                 │
│  Text: "What are the KYC requirements for UK business accounts?"│
│         │                                                       │
│         ▼                                                       │
│  Tokenizer: ["What", "are", "the", "KYC", "requirements",      │
│              "for", "UK", "business", "accounts", "?"]          │
│         │                                                       │
│         ▼                                                       │
│  Embedding Model (e.g., all-MiniLM-L6-v2):                     │
│                                                                 │
│  Each token → 384-dimensional vector                            │
│  All token vectors → pooled → single vector                     │
│                                                                 │
│         │                                                       │
│         ▼                                                       │
│  Output: [0.12, -0.45, 0.78, 0.23, ..., 0.56]                 │
│          (384 numbers representing the MEANING of the query)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Visual Representation

```
                    Embedding Space (simplified to 2D)
                    
    ▲
    │
    │   * KYC requirements
    │   * customer due diligence          * credit score
    │   * identity verification           * credit check
    │   * document verification           
    │
    │                              * loan application
    │                              * mortgage application
    │
    ├──────────────────────────────────────────────▶
    │
    │   * fraud detection
    │   * suspicious activity
    │   * money laundering
    │
    │
    
    (Points close together = similar meaning)
```

### Real-World Banking Scenario

**Scenario:** Customer asks a vague question.

```
Customer: "How do I prove who I am?"

Without embeddings (keyword search):
  Search for "prove who I am" → No exact match found
  Result: "Sorry, I don't understand"

With embeddings:
  Query embedding: [0.23, -0.67, 0.89, ...]
  
  Search vector DB for similar embeddings:
  1. "Identity verification process" (similarity: 0.91)
  2. "KYC document requirements" (similarity: 0.87)
  3. "Proof of identity documents" (similarity: 0.85)
  
  Result: Agent finds relevant policy and answers:
  "To verify your identity, you can provide:
   - Passport, or
   - Driving licence, or
   - National ID card
   Plus proof of address (utility bill, bank statement)"
```

### Why Embeddings Matter

| Without Embeddings | With Embeddings |
|--------------------|-----------------|
| Keyword: "prove who I am" → no match | Semantic: "prove who I am" → "identity verification" |
| Must use exact words from documents | Understands synonyms and paraphrases |
| Misses relevant results | Finds semantically similar content |

### Banking Use Cases

| Use Case | What Embeddings Do |
|----------|-------------------|
| Semantic Search | Customer asks in plain English, finds regulatory docs |
| Document Classification | Auto-classify uploaded documents (passport, tax return, etc.) |
| Anomaly Detection | Compare transaction patterns against known fraud embeddings |
| Deduplication | Find duplicate customer records across systems |
| Recommendation | Match customer profile to suitable products |
| Clustering | Group similar complaints for batch processing |

---

## 5. Vector Database

### What It Is

A vector database is a specialized database designed to store and search embeddings (vectors) efficiently. Unlike traditional databases that search by exact match, vector databases find *similar* items.

**Traditional DB vs Vector DB:**

```
Traditional DB (SQL):
  SELECT * FROM customers WHERE name = 'John Smith'
  → Exact match only

Vector DB:
  SELECT * FROM documents WHERE embedding SIMILAR TO [0.23, -0.67, ...]
  → Finds similar meaning, not exact match
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR DATABASE                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Collection: kyc_regulations                             │   │
│  │                                                          │   │
│  │  ┌─────────┬────────────────────┬──────────────┬──────┐  │   │
│  │  │  ID     │  Text              │  Embedding   │ Meta │  │   │
│  │  ├─────────┼────────────────────┼──────────────┼──────┤  │   │
│  │  │ reg_001 │ "Under MLR 2017..."│ [0.12, 0.45, │ FCA  │  │   │
│  │  │         │                    │  0.78, ...]  │      │  │   │
│  │  ├─────────┼────────────────────┼──────────────┼──────┤  │   │
│  │  │ reg_002 │ "Enhanced Due      │ [0.34, 0.22, │ FCA  │  │   │
│  │  │         │  Diligence..."     │  0.91, ...]  │      │  │   │
│  │  ├─────────┼────────────────────┼──────────────┼──────┤  │   │
│  │  │ reg_003 │ "For legal entity  │ [0.56, 0.11, │ UK   │  │   │
│  │  │         │  customers..."     │  0.88, ...]  │ Gov  │  │   │
│  │  └─────────┴────────────────────┴──────────────┴──────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Search: "What EDD rules apply to businesses?"                  │
│  Query embedding: [0.31, 0.28, 0.85, ...]                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ANN Index (Approximate Nearest Neighbor)                │   │
│  │  HNSW graph → fast similarity search                     │   │
│  │                                                          │   │
│  │  Returns top-K most similar vectors:                     │   │
│  │  1. reg_002 (score: 0.91) - "Enhanced Due Diligence..."  │   │
│  │  2. reg_003 (score: 0.88) - "For legal entity..."        │   │
│  │  3. reg_001 (score: 0.78) - "Under MLR 2017..."          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Vector DB Options for Banking

| Database | Best For | Why |
|----------|----------|-----|
| **Pinecone** | Production | Managed, low-latency, high throughput |
| **Weaviate** | Hybrid search | Combines keyword + semantic search |
| **Qdrant** | Real-time filtering | Fast filtering by metadata (jurisdiction, date) |
| **Milvus** | Large-scale analytics | Handles billions of vectors |
| **Chroma** | Development/Prototyping | Simple, lightweight, good for PoCs |
| **pgvector** | Existing PostgreSQL | Use if bank already runs PostgreSQL |

### Real-World Banking Scenario

**Scenario:** Compliance officer searches 10,000 regulation documents.

```
Without vector DB:
  Officer searches "crypto regulations" in SharePoint
  → Keyword search returns 50 documents
  → Many are irrelevant (contain "crypto" but different context)
  → Officer reads through manually (2 hours)

With vector DB:
  Officer asks agent: "What are the FCA's latest rules on crypto assets?"
  
  Vector DB search:
  1. Embeds query → [0.45, 0.23, 0.67, ...]
  2. ANN search across 10,000 regulation chunks
  3. Returns top 5 most relevant (in 50ms):
     - FCA PS23/14 on crypto (score: 0.94)
     - MLR 2017 crypto amendments (score: 0.91)
     - FATF guidance on virtual assets (score: 0.87)
  
  LLM synthesizes answer from these 5 chunks
  Time: 5 seconds
```

### Banking Use Cases

| Use Case | What Vector DB Stores |
|----------|----------------------|
| KYC Knowledge Base | Regulations, policies, past cases |
| Customer Similarity | Find customers with similar profiles |
| Fraud Patterns | Known fraud signatures and behaviors |
| Document Repository | All bank documents for semantic search |
| Product Catalog | Banking products for recommendation |

---

## 6. Context Window

### What It Is

The context window is the **maximum amount of text** an LLM can "see" at one time. Everything the LLM processes — your prompt, retrieved documents, conversation history — must fit within this window.

**Analogy:** Think of it as the LLM's working memory or desktop space. If you have too many papers (tokens) on the desk, you can't see everything at once.

### Token Limits

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW SIZES                         │
│                                                                 │
│  Model                Context Window    Approx Pages of Text    │
│  ─────────────────    ──────────────    ────────────────────    │
│  GPT-4o               128,000 tokens    ~200 pages              │
│  Claude 3.5           200,000 tokens    ~300 pages              │
│  Llama 3.1 8B         128,000 tokens    ~200 pages              │
│  Llama 3.1 70B        128,000 tokens    ~200 pages              │
│  Mistral 7B           32,000 tokens     ~50 pages               │
│                                                                 │
│  1 token ≈ 0.75 words ≈ 4 characters                            │
│  1,000 tokens ≈ 750 words ≈ 1.5 pages                           │
└─────────────────────────────────────────────────────────────────┘
```

### How Context is Used in Our Agent

```
┌─────────────────────────────────────────────────────────────────┐
│  CONTEXT WINDOW (128K tokens for Llama 3.1)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  System Prompt (2,000 tokens)                            │   │
│  │  "You are a KYC agent. Here are your tools..."           │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Conversation History (growing)                          │   │
│  │  User: "I want to open a business account"               │   │
│  │  Agent: "Sure! Let me check requirements..."             │   │
│  │  Tool: [knowledge_search results]                        │   │
│  │  Agent: "You'll need these documents..."                 │   │
│  │  User: "What about proof of address?"                    │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Retrieved Context (RAG results, ~3,000 tokens)          │   │
│  │  [1] Under MLR 2017, Regulation 28...                    │   │
│  │  [2] Business account eligibility requires...            │   │
│  │  [3] Proof of address must be dated within 3 months...   │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Current Query (200 tokens)                              │   │
│  │  "What about proof of address?"                          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Available for output: ~122,800 tokens                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  If total exceeds 128K → must truncate or summarize             │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Banking Scenario

**Scenario:** Long compliance consultation.

```
Turn 1: "What are KYC requirements?" (200 tokens)
Turn 2: Agent answers with regulation details (500 tokens)
Turn 3: "What about for business accounts?" (50 tokens)
Turn 4: Agent retrieves + answers (800 tokens)
Turn 5: "What documents do I need?" (100 tokens)
Turn 6: Agent retrieves + answers (600 tokens)
...
Turn 15: Total conversation: ~8,000 tokens

Context window: 128,000 tokens → still fits!

BUT if we're also loading:
- 5 retrieved documents: ~3,000 tokens
- Tool definitions: ~1,000 tokens
- System prompt: ~500 tokens

Total: ~12,500 tokens → plenty of room
```

**When it gets tight:**
- Customer uploads 10 documents (each ~2,000 tokens = 20,000 tokens)
- Long conversation (50+ turns = ~25,000 tokens)
- Complex risk assessment with many tools (~5,000 tokens)

**Solution:** Our `ConversationMemory` truncates old messages and summarizes them.

---

## 7. Batching

### What It Is

Batching is processing multiple inputs together in one go, rather than one at a time. This is critical for GPU efficiency — GPUs are designed to do many calculations simultaneously.

**Without batching:**
```
Process document 1: 100ms
Process document 2: 100ms
Process document 3: 100ms
Total: 300ms (3 sequential operations)
```

**With batching:**
```
Process [doc1, doc2, doc3] together: 120ms
Total: 120ms (1 parallel operation)
```

### How Batching Works in Banking

```
┌─────────────────────────────────────────────────────────────────┐
│                    BATCH PROCESSING                             │
│                                                                 │
│  Scenario: Process 1,000 KYC applications overnight             │
│                                                                 │
│  Without Batching:                                              │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ... ┌─────┐            │
│  │App 1│→│App 2│→│App 3│→│App 4│→│App 5│→...→│App  │            │
│  │100ms│ │100ms│ │100ms│ │100ms│ │100ms│     │100ms│            │
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘     └─────┘            │
│  Total: 100,000ms = 100 seconds                                 │
│                                                                 │
│  With Batching (batch size = 10):                               │
│  ┌─────────────────┐ ┌─────────────────┐ ... ┌─────────────────┐│
│  │ Apps 1-10       │→│ Apps 11-20      │→...→│ Apps 991-1000   ││
│  │ 200ms           │ │ 200ms           │     │ 200ms           ││
│  └─────────────────┘ └─────────────────┘     └─────────────────┘│
│  Total: 10,000ms = 10 seconds (10x faster!)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Banking Scenario

**Scenario:** Nightly batch processing of transactions for fraud detection.

```
Bank processes 5 million transactions per day

Without batching:
  5,000,000 × 1ms each = 5,000 seconds = 83 minutes
  (Barely fits in overnight window)

With batching (batch size = 256):
  5,000,000 / 256 = 19,531 batches
  19,531 × 8ms each = 156 seconds = 2.6 minutes
  (Fits easily, leaves room for other processing)
```

### Banking Use Cases

| Use Case | Batch Operation |
|----------|-----------------|
| Fraud Detection | Score 10,000 transactions simultaneously |
| Document Processing | OCR 500 uploaded documents in parallel |
| Sanctions Screening | Screen 1,000 names against watchlists at once |
| Customer Segmentation | Embed 100,000 customer profiles in batches |
| Report Generation | Generate 100 monthly reports simultaneously |

---

## 8. KV Cache

### What It Is

KV Cache (Key-Value Cache) is a memory optimization that stores previously computed attention keys and values, so the LLM doesn't have to recompute them for every token generation step.

**Without KV Cache:**
```
Generate token 1: Process entire prompt (1000 tokens)
Generate token 2: Re-process entire prompt + token 1 (1001 tokens)
Generate token 3: Re-process everything again (1002 tokens)
...
Generate token 100: Process 1099 tokens again
= Quadratic time complexity → Very slow!
```

**With KV Cache:**
```
Generate token 1: Process entire prompt, CACHE the K/V tensors
Generate token 2: Only process token 1 (previous tokens are cached)
Generate token 3: Only process token 2 (previous tokens are cached)
...
= Linear time complexity → Much faster!
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    KV CACHE                                     │
│                                                                 │
│  Prompt: "The customer must provide proof of identity"          │
│                                                                 │
│  Step 1: Process "The customer must provide proof of identity"  │
│  ┌──────────────────────────────────────────────┐               │
│  │  Key Cache:   [K₁, K₂, K₃, K₄, K₅, K₆, K₇] │                 │
│  │  Value Cache: [V₁, V₂, V₃, V₄, V₅, V₆, V₇] │                 │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
│  Step 2: Generate "and"                                         │
│  ┌──────────────────────────────────────────────┐               │
│  │  New token: K₈, V₈ (only compute for "and")  │               │
│  │  Append to cache: [K₁..K₇, K₈]               │               │
│  │  Attention: Q₈ × [K₁..K₈] → reuse K₁..K₇     │               │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
│  Step 3: Generate "address"                                     │
│  ┌──────────────────────────────────────────────┐               │
│  │  New token: K₉, V₉ (only compute for new)    │               │
│  │  Append to cache: [K₁..K₈, K₉]               │               │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
│  Savings: Instead of 7+8+9 = 24 matrix multiplications,         │
│           we do 7+1+1 = 9 (62% reduction!)                      │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Banking Scenario

**Scenario:** Real-time fraud detection on streaming transactions.

```
Without KV Cache:
  Each transaction: 50ms processing
  1,000 transactions/second → need 50 GPUs!

With KV Cache (prefix caching):
  First transaction: 50ms (full processing)
  Subsequent transactions with same context: 5ms (cached prefix)
  1,000 transactions/second → need 5 GPUs!

Savings: 90% reduction in compute cost
```

### Banking Use Cases

| Use Case | KV Cache Benefit |
|----------|------------------|
| Chatbot | Cache system prompt + conversation history |
| Batch Scoring | Cache common context across similar queries |
| Document Analysis | Cache document chunks when analyzing multiple aspects |
| Real-time Decisions | Low-latency responses by caching frequent patterns |

---

## 9. GPU Memory

### What It Is

GPU memory (VRAM) is the high-speed memory on graphics cards that stores the LLM's weights, activations, and KV cache. It's the **bottleneck** for running large models — if the model doesn't fit in GPU memory, it can't run (or runs very slowly).

### GPU Memory Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                    GPU MEMORY (e.g., 24GB VRAM)                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Model Weights (~70% = 16.8GB)                           │   │
│  │  The trained parameters of the LLM                       │   │
│  │  Llama 3.1 8B = ~16GB in FP16                            │   │
│  │  Llama 3.1 8B = ~8GB in INT4 quantization                │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  KV Cache (~20% = 4.8GB)                                 │   │
│  │  Stores attention keys/values for context                │   │
│  │  Grows with: batch_size × sequence_length                │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Activations (~10% = 2.4GB)                              │   │
│  │  Temporary computations during forward pass              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Available for new requests = Remaining VRAM                    │
└─────────────────────────────────────────────────────────────────┘
```

### Model Sizes vs GPU Requirements

```
┌─────────────────────────────────────────────────────────────────┐
│  Model            Parameters   FP16 Size   INT4 Size   GPU Req  │
│  ──────────────── ───────────  ──────────  ─────────   ──────── │
│  Llama 3.1 8B     8B           16GB        4GB         1×A10G   │
│  Llama 3.1 70B    70B          140GB       35GB        2×A100   │
│  Llama 3.1 405B   405B         810GB       200GB       8×A100   │
│  Mistral 7B       7B           14GB        3.5GB       1×A10G   │
│  Mixtral 8x7B     47B (8×7B)   94GB        24GB        2×A100   │
└─────────────────────────────────────────────────────────────────┘

FP16 = Full precision (2 bytes per parameter)
INT4 = Quantized (0.5 bytes per parameter) — 4x smaller, slight quality loss
```

### Real-World Banking Scenario

**Scenario:** Deploying KYC agent on bank's infrastructure.

```
Bank has: 4× NVIDIA A100 (80GB each) = 320GB total VRAM

Option 1: Single 70B model
  Model: 140GB (FP16)
  KV Cache: ~20GB
  Total: 160GB → Fits on 2×A100
  Throughput: ~50 requests/second
  Cost: $20/hour

Option 2: Two 8B models (one for simple, one for complex)
  Simple model: 16GB (for FAQ, direct answers)
  Complex model: 16GB (for multi-step reasoning)
  Total: 32GB → Fits on 1×A10G
  Throughput: ~200 requests/second
  Cost: $3/hour

Option 3: Quantized 70B model
  Model: 35GB (INT4)
  KV Cache: ~10GB
  Total: 45GB → Fits on 1×A100
  Throughput: ~80 requests/second
  Cost: $10/hour
```

### Quantization

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUANTIZATION                                 │
│                                                                 │
│  Original (FP16):                                               │
│  Weight: 0.1234567890123456 → 2 bytes                           │
│                                                                 │
│  Quantized (INT8):                                              │
│  Weight: 0.123 → lookup table → 0.1234567890123456              │
│  1 byte per weight → 50% smaller                                │
│                                                                 │
│  Quantized (INT4):                                              │
│  Weight: 0.12 → lookup table → 0.1234567890123456               │
│  0.5 bytes per weight → 75% smaller                             │
│                                                                 │
│  Quality trade-off:                                             │
│  FP16: 100% quality (baseline)                                  │
│  INT8: ~99% quality (negligible loss)                           │
│  INT4: ~97% quality (slight loss, acceptable for most tasks)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Scheduling & Inference

### What It Is

Scheduling is how the system decides **which requests to process, in what order, and on which GPUs**. Inference is the actual process of the LLM generating responses.

### Inference Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    INFERENCE PIPELINE                           │
│                                                                 │
│  Request arrives: "What are the KYC requirements?"              │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │  Tokenize   │ Convert text to token IDs                      │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │  Prefill    │ Process ALL tokens in parallel                 │
│  │  Phase      │ (compute KV cache for prompt)                  │
│  │             │ Time: ~50ms for 1000 tokens                    │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │  Decode     │ Generate tokens ONE AT A TIME                  │
│  │  Phase      │ (use KV cache for efficiency)                  │
│  │             │ Time: ~10ms per token                          │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  Output: "To open a UK business account, you need..."           │
│  Total time: 50ms + (200 tokens × 10ms) = 2.05 seconds          │
└─────────────────────────────────────────────────────────────────┘
```

### Scheduling Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCHEDULING STRATEGIES                        │
│                                                                 │
│  1. FIFO (First In, First Out)                                  │
│     Request 1 → GPU → Done → Request 2 → GPU → Done             │
│     Simple, but long requests block short ones                  │
│                                                                 │
│  2. Priority Scheduling                                         │
│     High priority (fraud detection) → GPU first                 │
│     Medium priority (customer chat) → wait                      │
│     Low priority (batch processing) → wait longer               │
│                                                                 │
│  3. Continuous Batching                                         │
│     Mix different requests in same batch                        │
│     When one request finishes, insert new request               │
│     Maximum GPU utilization                                     │
│                                                                 │
│  4. Speculative Decoding                                        │
│     Small model generates draft tokens                          │
│     Large model verifies/corrects in parallel                   │
│     2-3x faster with same quality                               │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Banking Scenario

**Scenario:** Mixed workload during business hours.

```
┌─────────────────────────────────────────────────────────────────┐
│  Time: 10:00 AM on Monday                                       │
│                                                                 │
│  Incoming requests:                                             │
│  ├── 50 × Customer chat (low priority, interactive)             │
│  ├── 10 × Fraud alerts (HIGH priority, < 100ms latency)         │
│  ├── 5  × Compliance officer queries (medium priority)          │
│  └── 1  × Batch: 10,000 transaction scoring (low priority)      │
│                                                                 │
│  Scheduler decisions:                                           │
│  1. Fraud alerts → Dedicated GPU, immediate processing          │
│  2. Customer chat → Shared GPU, round-robin scheduling          │
│  3. Compliance queries → Shared GPU, prioritized                │
│  4. Batch scoring → Off-peak hours (evening), full GPU          │
│                                                                 │
│  Resource allocation:                                           │
│  GPU 0: Fraud detection (always available)                      │
│  GPU 1: Customer chat (shared)                                  │
│  GPU 2: Compliance queries (shared)                             │
│  GPU 3: Batch processing (evening only)                         │
└─────────────────────────────────────────────────────────────────┘
```

### Latency vs Throughput

| Metric | What It Means | Banking Requirement |
|--------|---------------|---------------------|
| **Latency** | Time for single request | < 100ms for fraud detection |
| **Throughput** | Requests per second | 1,000+ transactions/second |
| **Time to First Token** | How fast response starts | < 500ms for chatbots |
| **Tokens per Second** | Generation speed | > 50 tokens/s for interactive |

### vLLM Scheduling (PagedAttention)

```
┌─────────────────────────────────────────────────────────────────┐
│  vLLM uses PagedAttention for efficient GPU memory management   │
│                                                                 │
│  Traditional:                                                   │
│  Pre-allocate max context for each request                      │
│  Request 1: [████████████████████] (128K reserved, using 1K)    │
│  Request 2: [████████████████████] (128K reserved, using 2K)    │
│  → 95% memory wasted!                                           │
│                                                                 │
│  vLLM PagedAttention:                                           │
│  Allocate memory in pages (like OS virtual memory)              │
│  Request 1: [██] (only 1K allocated)                            │
│  Request 2: [████] (only 2K allocated)                          │
│  → Memory used on demand, 2-4x more requests in same GPU        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. How It All Fits Together

### Complete Flow: KYC Application Processing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE SYSTEM FLOW                                 │
│                                                                         │
│  CUSTOMER: "I want to open a business account for my UK limited company"│
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 1: INTENT ROUTING                                         │    │
│  │  IntentRouter.classify(query) → COMPLEX                         │    │
│  │  (Needs tools, multi-step processing)                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 2: MEMORY MANAGEMENT                                      │    │
│  │  ConversationMemory.add("user", query)                          │    │
│  │  Check token limits, truncate if needed                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 3: LLM CALL (via vLLM/Ollama/SGLang)                      │    │
│  │  GPU processes prompt using KV cache                            │    │
│  │  Prefill phase: 50ms (parallel token processing)                │    │
│  │  LLM decides: "I need to search knowledge base first"           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 4: RAG RETRIEVAL                                          │    │
│  │  1. Embed query → [0.23, -0.67, 0.89, ...]                      │    │
│  │  2. Vector DB search (ANN) → 5 relevant chunks                  │    │
│  │  3. Hybrid search (BM25 + semantic)                             │    │
│  │  4. Re-rank top 20 → top 5                                      │    │
│  │  Time: ~200ms                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 5: MCP TOOL CALL                                          │    │
│  │  LLM calls: knowledge_search(query="UK business account")       │    │
│  │  MCP server executes tool → returns regulation text             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 6: GUARDRAILS CHECK                                       │    │
│  │  Tool risk: SAFE (knowledge_search) → auto-execute              │    │
│  │  Output check: No sensitive data → approved                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 7: LLM GENERATES RESPONSE                                 │    │
│  │  Decode phase: ~200 tokens × 10ms = 2 seconds                   │    │
│  │  Uses KV cache (no re-computation)                              │    │
│  │  Response: "To open a UK business account, you need..."         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  STEP 8: OBSERVABILITY                                          │    │
│  │  AgentTracer records:                                           │    │
│  │  - 2 LLM calls (800ms + 600ms)                                  │    │
│  │  - 1 tool call (150ms)                                          │    │
│  │  - Total: 1.55 seconds                                          │    │
│  │  - Tokens: prompt=1200, completion=180                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                          │
│                              ▼                                          │
│  RESPONSE: "To open a UK business account for your UK limited company,  │
│  you'll need: 1. Certificate of Incorporation, 2. Articles of           │
│  Association, 3. Proof of registered address, 4. Director IDs..."       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    OUR KYC AGENT STACK                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  APPLICATION LAYER                                       │   │
│  │  ├── BaseAgent (ReAct loop, orchestration)               │   │
│  │  ├── IntentRouter (simple vs complex)                    │   │
│  │  ├── Guardrails (safety, approval)                       │   │
│  │  └── ConversationMemory (token management)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LLM LAYER                                               │   │
│  │  ├── Ollama (local, dev)                                 │   │
│  │  ├── vLLM (production, PagedAttention)                   │   │
│  │  └── SGLang (structured output)                          │   │
│  │  Running on: GPU with KV cache                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  KNOWLEDGE LAYER                                         │   │
│  │  ├── RAG Pipeline (hybrid search)                        │   │
│  │  ├── ChromaDB (vector storage)                           │   │
│  │  └── Embeddings (all-MiniLM-L6-v2)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  TOOL LAYER (MCP)                                        │   │
│  │  ├── Identity Verification (Jumio/Onfido)                │   │
│  │  ├── Sanctions Screening (OFAC/EU)                       │   │
│  │  ├── Core Banking API                                    │   │
│  │  ├── Compliance System                                   │   │
│  │  └── Notification Service                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  INFRASTRUCTURE                                          │   │
│  │  ├── GPU (A100/A10G) with VRAM                           │   │
│  │  ├── Batching (continuous batching)                      │   │
│  │  ├── Scheduling (priority-based)                         │   │
│  │  └── Monitoring (traces, metrics)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

*Last updated: August 2026*
