# Cross-Border Payment Assistant Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Cross-Border Payment Assistant Agent that uses **RAG** for correspondent banking knowledge retrieval and **MCP** for tool orchestration across FX rates, SWIFT tracking, correspondent bank discovery, sanctions screening, compliance checking, and country regulations.
>
> **Covers all 7.3 Cross-Border Payment Assistant Agent capabilities.**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  CROSS-BORDER PAYMENT ASSISTANT AGENT                      │
│                                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────────────────────────┐  │
│  │           │    │              │    │       MCP Tool Server            │  │
│  │  Customer │───▶│   LLM Core   │◀──▶│  ┌──────────┐ ┌───────────┐   │  │
│  │   Chat    │    │  (GPT-4o /   │    │  │ FX Rate  │ │ SWIFT gpi │   │  │
│  │ Interface │◀───│  Claude /    │    │  │ API      │ │ Tracking  │   │  │
│  │           │    │  Gemini)     │    │  └──────────┘ └───────────┘   │  │
│  └───────────┘    └──────┬───────┘    │  ┌──────────┐ ┌───────────┐   │  │
│                          │             │  │Correspon-│ │ Sanctions │   │  │
│                          │             │  │dent Bank │ │ Screening │   │  │
│                          ▼             │  └──────────┘ └───────────┘   │  │
│                   ┌──────────────┐     │  ┌──────────┐ ┌───────────┐   │  │
│                   │              │     │  │Compliance│ │ Country   │   │  │
│                   │   RAG Engine │     │  │ Checker  │ │ Regs      │   │  │
│                   │              │     │  └──────────┘ └───────────┘   │  │
│                   │  ┌────────┐  │     │  ┌──────────┐ ┌───────────┐   │  │
│                   │  │Query   │  │     │  │ Payment  │ │ Notify    │   │  │
│                   │  │Rewrite │  │     │  │ Quotes   │ │ Customer  │   │  │
│                   │  └───┬────┘  │     │  └──────────┘ └───────────┘   │  │
│                   │      │       │     └──────────────────────────────────┘  │
│                   │      ▼       │                                          │
│                   │  ┌────────┐  │     ┌──────────────────────────────────┐  │
│                   │  │Hybrid  │  │     │       External APIs              │  │
│                   │  │Search  │  │     │  ┌──────────┐ ┌───────────┐    │  │
│                   │  │(BM25 + │  │     │  │ Bloomberg│ │ SWIFT     │    │  │
│                   │  │Semantic)│  │     │  │ Reuters  │ │ gpi API   │    │  │
│                   │  └───┬────┘  │     │  │ ECB      │ │           │    │  │
│                   │      │       │     │  └──────────┘ └───────────┘    │  │
│                   │      ▼       │     │  ┌──────────┐ ┌───────────┐    │  │
│                   │  ┌────────┐  │     │  │ OFAC SDN │ │ Fedwire   │    │  │
│                   │  │Re-rank │  │     │  │ EU Lists │ │ CHIPS     │    │  │
│                   │  └───┬────┘  │     │  │ UN Lists │ │ CLS       │    │  │
│                   │      │       │     │  └──────────┘ └───────────┘    │  │
│                   └──────┼───────┘     └──────────────────────────────────┘  │
│                          │                                                   │
└──────────────────────────┼───────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     Vector Database     │
              │                        │
              │  ┌──────────────────┐  │
              │  │  Correspondent   │  │
              │  │  Banking         │  │
              │  ├──────────────────┤  │
              │  │  SWIFT Codes     │  │
              │  ├──────────────────┤  │
              │  │  Country         │  │
              │  │  Regulations     │  │
              │  ├──────────────────┤  │
              │  │  Fee Schedules   │  │
              │  ├──────────────────┤  │
              │  │  FX Trading      │  │
              │  │  Rules           │  │
              │  ├──────────────────┤  │
              │  │  Compliance      │  │
              │  │  Requirements    │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

---

## Detailed Component Flow

### The Cross-Border Payment Journey — Step by Step

```
CUSTOMER                  AGENT (LLM + RAG + MCP)              EXTERNAL SYSTEMS
────────                  ────────────────────────              ─────────────────

  │                              │                                    │
  │  1. "I need to send          │                                    │
  │      $25,000 to my           │                                    │
  │      supplier in the UK"     │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  2. Intent: COMPLEX                │
  │                              │     RAG: Retrieve UK regulations,  │
  │                              │     correspondent banking details  │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → UK FCA regulations          │
  │                              │     → GBP payment requirements    │
  │                              │     → Correspondent bank fees     │
  │                              │                                    │
  │  3. "Let me check FX rates   │                                    │
  │      and fees..."            │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │                              │  4. MCP: Get FX rate              │
  │                              │──────┐                             │
  │                              │      │  GET /fx/rate              │
  │                              │      │  (USD → GBP)               │
  │                              │◀─────┘                             │
  │                              │     → Mid-market: 0.7900          │
  │                              │     → Customer rate: 0.7861       │
  │                              │     → Converted: £19,652.50       │
  │                              │     → FX cost: $125               │
  │                              │                                    │
  │                              │  5. MCP: Find correspondent       │
  │                              │──────┐                             │
  │                              │      │  GET /correspondent/USD    │
  │                              │◀─────┘                             │
  │                              │     → Recommended: JPMorgan NY    │
  │                              │     → BIC: CHASUS33               │
  │                              │     → gpi member: YES             │
  │                              │                                    │
  │                              │  6. MCP: Sanctions screening      │
  │                              │──────┐                             │
  │                              │      │  POST /screen/entity      │
  │                              │◀─────┘                             │
  │                              │     → Decision: CLEAR             │
  │                              │     → No matches on OFAC/EU/UN    │
  │                              │                                    │
  │                              │  7. MCP: Compliance check         │
  │                              │──────┐                             │
  │                              │      │  POST /compliance/check   │
  │                              │◀─────┘                             │
  │                              │     → Decision: APPROVED          │
  │                              │     → Travel Rule: PASS           │
  │                              │     → Country risk: STANDARD      │
  │                              │                                    │
  │                              │  8. MCP: Generate quote           │
  │                              │──────┐                             │
  │                              │      │  POST /quote/generate     │
  │                              │◀─────┘                             │
  │                              │     → Total cost: $168 (0.67%)    │
  │                              │     → Wire fee: $35               │
  │                              │     → Intermediary: $25           │
  │                              │     → FX spread: $125             │
  │                              │     → Delivery: 2 business days   │
  │                              │                                    │
  │  9. "Here's the breakdown:   │                                    │
  │      Send amount: $25,000    │                                    │
  │      You receive: £19,652    │                                    │
  │      Total cost: $168        │                                    │
  │      Delivery: 2 days        │                                    │
  │      via JPMorgan → Barclays"│                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │  10. "Looks good,            │                                    │
  │       initiate the           │                                    │
  │       payment"               │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  11. MCP: Initiate payment        │
  │                              │──────┐                             │
  │                              │      │  POST /payment/initiate   │
  │                              │      │  (SWIFT MT103)             │
  │                              │◀─────┘                             │
  │                              │     → UETR: 550e8400-e29b...     │
  │                              │     → Status: initiated           │
  │                              │                                    │
  │                              │  12. MCP: Notify customer         │
  │                              │──────┐                             │
  │                              │      │  POST /notify/send        │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  13. "Payment initiated!     │                                    │
  │       UETR: 550e8400...      │                                    │
  │       Tracking shows          │                                    │
  │       delivery by Jan 17"    │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
```

---

## MCP Tool Definitions

```jsonc
// mcp-server-crossborder.json
{
  "mcpServers": {
    "cross-border-payment": {
      "description": "Cross-Border Payment Assistant MCP Server — tools for FX rates, SWIFT tracking, correspondent banks, sanctions screening, compliance, and country regulations",
      "tools": [
        {
          "name": "get_rate",
          "description": "Get current exchange rate for a currency pair with customer markup",
          "inputSchema": {
            "type": "object",
            "properties": {
              "source_currency": { "type": "string" },
              "target_currency": { "type": "string" },
              "amount": { "type": "number" }
            },
            "required": ["source_currency", "target_currency"]
          }
        },
        {
          "name": "track_wire",
          "description": "Track a cross-border payment using SWIFT gpi UETR",
          "inputSchema": {
            "type": "object",
            "properties": {
              "uetr": { "type": "string" }
            },
            "required": ["uetr"]
          }
        },
        {
          "name": "send_wire",
          "description": "Initiate a cross-border wire transfer",
          "inputSchema": {
            "type": "object",
            "properties": {
              "source_currency": { "type": "string" },
              "target_currency": { "type": "string" },
              "amount": { "type": "number" },
              "originator_name": { "type": "string" },
              "originator_account": { "type": "string" },
              "beneficiary_name": { "type": "string" },
              "beneficiary_account": { "type": "string" },
              "beneficiary_bank_bic": { "type": "string" },
              "purpose": { "type": "string" },
              "charges_type": { "type": "string", "enum": ["OUR", "BEN", "SHA"] }
            },
            "required": ["source_currency", "target_currency", "amount", "originator_name", "originator_account", "beneficiary_name", "beneficiary_account", "beneficiary_bank_bic", "purpose"]
          }
        },
        {
          "name": "screen_entity",
          "description": "Screen an entity against OFAC, EU, and UN sanctions lists",
          "inputSchema": {
            "type": "object",
            "properties": {
              "entity_name": { "type": "string" },
              "country": { "type": "string" },
              "entity_type": { "type": "string", "enum": ["individual", "entity", "vessel"] }
            },
            "required": ["entity_name"]
          }
        },
        {
          "name": "get_quote",
          "description": "Generate an all-in cost quote for a cross-border payment",
          "inputSchema": {
            "type": "object",
            "properties": {
              "source_currency": { "type": "string" },
              "target_currency": { "type": "string" },
              "amount": { "type": "number" },
              "originator_country": { "type": "string" },
              "beneficiary_country": { "type": "string" },
              "charges_type": { "type": "string", "enum": ["OUR", "BEN", "SHA"] },
              "urgency": { "type": "string", "enum": ["standard", "express", "urgent"] }
            },
            "required": ["source_currency", "target_currency", "amount", "originator_country", "beneficiary_country"]
          }
        },
        {
          "name": "get_regulations",
          "description": "Get cross-border payment regulations for a country",
          "inputSchema": {
            "type": "object",
            "properties": {
              "country_code": { "type": "string" }
            },
            "required": ["country_code"]
          }
        },
        {
          "name": "find_correspondent",
          "description": "Find correspondent banks for a currency and routing path",
          "inputSchema": {
            "type": "object",
            "properties": {
              "currency": { "type": "string" },
              "source_country": { "type": "string" },
              "target_country": { "type": "string" }
            },
            "required": ["currency"]
          }
        }
      ]
    }
  }
}
```

---

## RAG Pipeline Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                             │
│                                                                 │
│  ┌─────────────┐                                                │
│  │  Customer    │  "What are the fees for sending USD            │
│  │  Query       │   to Japan?"                                  │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 1. QUERY    │  Rewrites for better retrieval:                │
│  │   REWRITE   │  "USD JPY wire transfer fees correspondent     │
│  │             │   bank Japan BOJ regulations"                  │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────┐                   │
│  │ 2. HYBRID SEARCH                         │                   │
│  │                                          │                   │
│  │  ┌────────────┐    ┌────────────────┐    │                   │
│  │  │  BM25      │    │  Semantic      │    │                   │
│  │  │  (Keyword) │    │  (Embedding)   │    │                   │
│  │  │            │    │                │    │                   │
│  │  │ "USD"      │    │  Vector        │    │                   │
│  │  │ "JPY"      │    │  Similarity    │    │                   │
│  │  │ "Japan"    │    │  Search        │    │                   │
│  │  │ "fees"     │    │  (top-k=20)    │    │                   │
│  │  └─────┬──────┘    └───────┬────────┘    │                   │
│  │        │                   │             │                   │
│  │        └───────┬───────────┘             │                   │
│  │                ▼                         │                   │
│  │        ┌──────────────┐                  │                   │
│  │        │   Reciprocal  │                 │                   │
│  │        │   Rank Fusion │                 │                   │
│  │        └───────┬──────┘                  │                   │
│  └────────────────┼─────────────────────────┘                   │
│                   │                                             │
│                   ▼                                             │
│          ┌────────────────┐                                     │
│  │ 3. RE-RANKING  │  Cross-encoder re-ranks top 20              │
│          │   (top-5)      │  → Best 5 chunks selected           │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│  │ 4. CONTEXT     │  Assembles retrieved chunks:                │
│          │   ASSEMBLY     │  - Fee schedule for JPY wires       │
│          │                │  - Japan FSA regulations            │
│          │                │  - Correspondent bank (Citi Tokyo)  │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│  │ 5. ANSWER      │  LLM generates answer with                  │
│          │   GENERATION   │  citations and source references    │
│          └───────┬────────┘                                     │
│                  │                                              │
│                  ▼                                              │
│          ┌────────────────┐                                     │
│  │ 6. CITATION    │  Attach source document references          │
│          │   ATTACHMENT   │  for audit trail and compliance     │
│          └────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
                    ┌───────────────────┐
                    │   Customer Input   │
                    │  "Send $25K to     │
                    │   supplier in UK"  │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │    LLM Core       │
                    │  (Orchestration)  │
                    └────┬───────────┬──┘
                         │           │
            ┌────────────▼──┐   ┌───▼────────────┐
            │   RAG Engine  │   │  MCP Tool Server│
            │               │   │                │
            │  ┌─────────┐  │   │  ┌───────────┐ │
            │  │ Vector  │  │   │  │ FX Rates  │ │
            │  │ DB      │  │   │  ├───────────┤ │
            │  │         │  │   │  │ SWIFT gpi │ │
            │  │ → Corresp│ │  │  │ Tracking  │ │
            │  │ → SWIFT │  │   │  ├───────────┤ │
            │  │ → Regs  │  │   │  │Correspond.│ │
            │  │ → Fees  │  │   │  │ Banks     │ │
            │  │ → FX    │  │   │  ├───────────┤ │
            │  │ → Compl.│  │   │  │ Sanctions │ │
            │  └─────────┘  │   │  ├───────────┤ │
            │               │   │  │ Compliance│ │
            └───────────────┘   │  ├───────────┤ │
                                │  │ Country   │ │
                                │  │ Regs      │ │
                                │  ├───────────┤ │
                                │  │ Quotes    │ │
                                │  ├───────────┤ │
                                │  │ Notify    │ │
                                │  └───────────┘ │
                                └────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Customer Response   │
                    │  "Total cost: $168   │
                    │   Delivery: 2 days   │
                    │   UETR: 550e8400..." │
                    │  + Audit Trail       │
                    │  + Compliance Log    │
                    └─────────────────────┘
```

---

## SWIFT gpi Payment Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                  SWIFT GPI PAYMENT LIFECYCLE                     │
│                                                                 │
│  ┌──────────┐                                                   │
│  │ Initiate │  Customer initiates wire via online banking       │
│  │ (T+0)    │  → UETR assigned (UUID v4)                       │
│  │          │  → MT103 created                                  │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐                                                   │
│  │ Originator│  Originating bank processes instruction           │
│  │ Bank      │  → OFAC/sanctions screening                     │
│  │ (T+0)     │  → Compliance checks                            │
│  │          │  → SWIFT message sent                             │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐                                                   │
│  │Intermediary│  USD correspondent receives payment              │
│  │ Bank      │  → Validates SWIFT message                       │
│  │ (T+0/T+1) │  → Processes through Fedwire/CHIPS              │
│  │          │  → Forwards to beneficiary bank                   │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐                                                   │
│  │Beneficiary│  Beneficiary bank receives funds                 │
│  │ Bank      │  → Credits beneficiary account                   │
│  │ (T+1/T+2) │  → Sends gpi confirmation                       │
│  │          │  → UETR status updated to ACSP                    │
│  └──────────┘                                                   │
│                                                                 │
│  Tracking: Customer can track via SWIFT gpi API at any stage    │
│  Total typical time: 1-2 business days for major currencies     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Hybrid Search** | BM25 + Semantic | Keyword catches SWIFT codes/country names; semantic handles paraphrased queries |
| **Re-ranking** | Cross-encoder | Precision critical — wrong regulation = compliance violation |
| **MCP over direct API** | MCP protocol | Standardized; swap FX providers, SWIFT APIs without changing agent logic |
| **Sanctions Screening** | Pre-payment mandatory | OFAC violations carry criminal penalties — must screen before execution |
| **Travel Rule** | FATF-compliant | Required for wire transfers > $1,000 (varies by jurisdiction) |
| **Correspondent Routing** | Rule-based + gpi | Optimize for cost, speed, and tracking capability |
| **FX Markup** | Transparent comparison | Customers should understand total cost before committing |
| **Country Risk** | Tiered (high/medium/standard) | Differentiated due diligence based on jurisdiction risk |
| **Human-in-Loop** | Wire initiation > $100K | Large transfers require approval per bank policy |
| **Fee Transparency** | OUR/BEN/SHA options | Customers choose who pays — avoids surprise deductions |
| **gpi Tracking** | End-to-end | Standard for cross-border — enables real-time status updates |
| **Audit Trail** | Every action logged | Regulatory requirement for cross-border payment compliance |

---

*Architecture designed for Cross-Border Payment Assistant Agent (7.3) — August 2026*
