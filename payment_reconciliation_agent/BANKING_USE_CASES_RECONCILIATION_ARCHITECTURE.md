# Payment Reconciliation Agent — RAG + MCP Architecture

> A complete architecture diagram for an AI-powered Payment Reconciliation Agent that uses **RAG** for reconciliation rules and standards retrieval and **MCP** for tool orchestration across bank statement import, payment matching, ledger management, exception handling, discrepancy resolution, and payment reference embedding.
>
> **Covers all 7.2 Payment Reconciliation Agent capabilities.**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PAYMENT RECONCILIATION AGENT                            │
│                                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────────────────────────┐  │
│  │           │    │              │    │       MCP Tool Server            │  │
│  │  Financial│───▶│   LLM Core   │◀──▶│  ┌──────────┐ ┌───────────┐   │  │
│  │  Analyst  │    │  (GPT-4o /   │    │  │ Payment  │ │ Bank      │   │  │
│  │   Chat    │◀───│  Claude /    │    │  │ Matching │ │ Statement │   │  │
│  │  Interface│    │  Gemini)     │    │  └──────────┘ └───────────┘   │  │
│  └───────────┘    └──────┬───────┘    │  ┌──────────┐ ┌───────────┐   │  │
│                          │             │  │ Ledger   │ │ Exception │   │  │
│                          │             │  │ Mgmt     │ │ Handling  │   │  │
│                          ▼             │  └──────────┘ └───────────┘   │  │
│                   ┌──────────────┐     │  ┌──────────┐ ┌───────────┐   │  │
│                   │              │     │  │Discrepan-│ │ Payment   │   │  │
│                   │   RAG Engine │     │  │cy Resol. │ │ Embedding │   │  │
│                   │              │     │  └──────────┘ └───────────┘   │  │
│                   │  ┌────────┐  │     │  ┌──────────┐ ┌───────────┐   │  │
│                   │  │Query   │  │     │  │Accounting│ │ Notify    │   │  │
│                   │  │Rewrite │  │     │  │ System   │ │ Analyst   │   │  │
│                   │  └───┬────┘  │     │  └──────────┘ └───────────┘   │  │
│                   │      │       │     └──────────────────────────────────┘  │
│                   │      ▼       │                                          │
│                   │  ┌────────┐  │     ┌──────────────────────────────────┐  │
│                   │  │Hybrid  │  │     │       External Systems           │  │
│                   │  │Search  │  │     │  ┌──────────┐ ┌───────────┐    │  │
│                   │  │(BM25 + │  │     │  │ Payment  │ │ Core      │    │  │
│                   │  │Semantic)│  │     │  │ Gateway  │ │ Banking   │    │  │
│                   │  └───┬────┘  │     │  │ (SWIFT,  │ │ (GL,      │    │  │
│                   │      │       │     │  │  ACH,    │ │  Ledger)  │    │  │
│                   │      ▼       │     │  │  Wire)   │ │           │    │  │
│                   │  ┌────────┐  │     │  └──────────┘ └───────────┘    │  │
│                   │  │Re-rank │  │     │  ┌──────────┐ ┌───────────┐    │  │
│                   │  └───┬────┘  │     │  │ Bank     │ │ Accounting│    │  │
│                   │      │       │     │  │Statement │ │ System    │    │  │
│                   └──────┼───────┘     │  │ (MT940,  │ │ (SAP,     │    │  │
│                          │             │  │  BAI2,   │ │  Oracle)  │    │  │
│                          │             │  │  CSV)    │ │           │    │  │
│                          │             │  └──────────┘ └───────────┘    │  │
│                          │             └──────────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     Vector Database     │
              │                        │
              │  ┌──────────────────┐  │
              │  │  Reconciliation  │  │
              │  │  Rules           │  │
              │  ├──────────────────┤  │
              │  │  Payment         │  │
              │  │  Standards       │  │
              │  ├──────────────────┤  │
              │  │  Exception       │  │
              │  │  Handling        │  │
              │  ├──────────────────┤  │
              │  │  Accounting      │  │
              │  │  Standards       │  │
              │  ├──────────────────┤  │
              │  │  Past            │  │
              │  │  Discrepancies   │  │
              │  ├──────────────────┤  │
              │  │  Matching        │  │
              │  │  Patterns        │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

---

## Detailed Component Flow

### The Reconciliation Journey — Step by Step

```
ANALYST                  AGENT (LLM + RAG + MCP)              EXTERNAL SYSTEMS
──────                   ────────────────────────              ─────────────────

  │                              │                                    │
  │  1. "Reconcile January       │                                    │
  │      for account             │                                    │
  │      1000-OPERATING"         │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  2. Intent: COMPLEX                │
  │                              │     RAG: Retrieve reconciliation   │
  │                              │     rules and standards            │
  │                              │──────┐                             │
  │                              │      │  Query Vector DB            │
  │                              │◀─────┘                             │
  │                              │     → Matching criteria rules      │
  │                              │     → MT940/BAI2 format specs     │
  │                              │     → Exception handling procedures│
  │                              │                                    │
  │  3. "Let me import the       │                                    │
  │      bank statement          │                                    │
  │      and ledger data..."     │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │  4. [Analyst uploads         │                                    │
  │      MT940 file]             │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  5. MCP: Import bank statement     │
  │                              │──────┐                             │
  │                              │      │  POST /import/statement    │
  │                              │      │  (MT940 parser)            │
  │                              │◀─────┘                             │
  │                              │     → 7 entries imported           │
  │                              │     → Balance validated            │
  │                              │     → 1 flagged item (check)       │
  │                              │                                    │
  │                              │  6. MCP: Get ledger entries        │
  │                              │──────┐                             │
  │                              │      │  GET /ledger/entries        │
  │                              │◀─────┘                             │
  │                              │     → 5 ledger entries retrieved   │
  │                              │     → Total credits: $183,750     │
  │                              │     → Total debits: $12,950       │
  │                              │                                    │
  │                              │  7. MCP: Run auto-match            │
  │                              │──────┐                             │
  │                              │      │  POST /match/auto          │
  │                              │      │  (3-tier matching engine)  │
  │                              │◀─────┘                             │
  │                              │     → Match rate: 83%             │
  │                              │     → 4 exact matches             │
  │                              │     → 1 fuzzy match ($1 diff)     │
  │                              │     → 3 unmatched items           │
  │                              │                                    │
  │  8. "I see a $1 discrepancy  │                                    │
  │      and an unmatched        │                                    │
  │      check deposit..."       │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
  │                              │  9. MCP: Find discrepancies        │
  │                              │──────┐                             │
  │                              │      │  POST /discrepancies       │
  │                              │◀─────┘                             │
  │                              │     → 1 amount mismatch found     │
  │                              │     → $1.00 diff on INV-2024-004  │
  │                              │                                    │
  │                              │  10. MCP: Investigate              │
  │                              │──────┐                             │
  │                              │      │  POST /discrepancy/invest. │
  │                              │◀─────┘                             │
  │                              │     → Possible causes:            │
  │                              │       Rounding, ACH fee, FX       │
  │                              │     → Suggest: Check bank fees    │
  │                              │                                    │
  │                              │  11. MCP: Investigate exception    │
  │                              │──────┐                             │
  │                              │      │  POST /exception/invest.   │
  │                              │◀─────┘                             │
  │                              │     → Severity: HIGH              │
  │                              │     → Possible fraud (check alt.) │
  │                              │     → Escalate to supervisor      │
  │                              │                                    │
  │  12. "Resolve the $1 as      │                                    │
  │       write-off, and         │                                    │
  │       escalate the           │                                    │
  │       check fraud..."        │                                    │
  │─────────────────────────────▶│                                    │
  │                              │                                    │
  │                              │  13. MCP: Resolve discrepancy     │
  │                              │──────┐                             │
  │                              │      │  POST /discrepancy/resolve │
  │                              │◀─────┘                             │
  │                              │     → $1.00 write-off approved   │
  │                              │                                    │
  │                              │  14. MCP: Post adjustment         │
  │                              │──────┐                             │
  │                              │      │  POST /adjustment/post     │
  │                              │      │  (SOX audit logged)        │
  │                              │◀─────┘                             │
  │                              │     → JE-ADJ-A1B2C3D4 posted     │
  │                              │                                    │
  │                              │  15. MCP: Escalate exception      │
  │                              │──────┐                             │
  │                              │      │  POST /exception/escalate  │
  │                              │◀─────┘                             │
  │                              │     → Escalated to finance_mgr   │
  │                              │                                    │
  │                              │  16. MCP: Generate report         │
  │                              │──────┐                             │
  │                              │      │  POST /report/generate     │
  │                              │◀─────┘                             │
  │                              │     → Report ID: RPT-E5F6G7H8    │
  │                              │     → Reconciled: YES             │
  │                              │     → Adjustments: 1              │
  │                              │                                    │
  │                              │  17. MCP: Notify team             │
  │                              │──────┐                             │
  │                              │      │  POST /notify/send         │
  │                              │◀─────┘                             │
  │                              │                                    │
  │  18. "Reconciliation          │                                    │
  │       complete. 83% auto-    │                                    │
  │       matched, $1 write-off, │                                    │
  │       1 fraud exception      │                                    │
  │       escalated."            │                                    │
  │◀─────────────────────────────│                                    │
  │                              │                                    │
```

---

## MCP Tool Definitions

```jsonc
// mcp-server-reconciliation.json
{
  "mcpServers": {
    "payment-reconciliation": {
      "description": "Payment Reconciliation MCP Server — tools for bank statement import, payment matching, ledger management, exception handling, discrepancy resolution, and reconciliation reporting",
      "tools": [
        {
          "name": "run_auto_match",
          "description": "Auto-match bank statement entries to ledger entries using exact, fuzzy, and semantic matching",
          "inputSchema": {
            "type": "object",
            "properties": {
              "bank_entries": { "type": "array" },
              "ledger_entries": { "type": "array" },
              "match_threshold": { "type": "number" },
              "amount_tolerance_pct": { "type": "number" },
              "date_tolerance_days": { "type": "integer" }
            },
            "required": ["bank_entries", "ledger_entries"]
          }
        },
        {
          "name": "import_statement",
          "description": "Import a bank statement in MT940, BAI2, ISO 20022, or CSV format",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_number": { "type": "string" },
              "format_type": { "type": "string", "enum": ["MT940", "BAI2", "ISO20022", "CSV"] },
              "statement_date": { "type": "string" },
              "opening_balance": { "type": "number" },
              "closing_balance": { "type": "number" },
              "entries": { "type": "array" }
            },
            "required": ["account_number", "format_type", "statement_date", "opening_balance", "closing_balance"]
          }
        },
        {
          "name": "get_ledger",
          "description": "Retrieve internal ledger entries with optional filters",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_number": { "type": "string" },
              "start_date": { "type": "string" },
              "end_date": { "type": "string" },
              "transaction_type": { "type": "string" },
              "limit": { "type": "integer" }
            }
          }
        },
        {
          "name": "investigate_disc",
          "description": "Investigate a discrepancy and suggest possible causes",
          "inputSchema": {
            "type": "object",
            "properties": {
              "discrepancy_id": { "type": "string" }
            },
            "required": ["discrepancy_id"]
          }
        },
        {
          "name": "resolve_disc",
          "description": "Resolve a discrepancy (adjust_ledger, write_off, bank_notification, no_action)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "discrepancy_id": { "type": "string" },
              "resolution_type": { "type": "string", "enum": ["adjust_ledger", "write_off", "bank_notification", "no_action"] },
              "adjusting_amount": { "type": "number" },
              "description": { "type": "string" },
              "approved_by": { "type": "string" }
            },
            "required": ["discrepancy_id", "resolution_type"]
          }
        },
        {
          "name": "post_adjustment",
          "description": "Post an adjusting journal entry to the GL (SOX audit logged)",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_number": { "type": "string" },
              "amount": { "type": "number" },
              "adjustment_type": { "type": "string" },
              "description": { "type": "string" },
              "reference": { "type": "string" },
              "approved_by": { "type": "string" }
            },
            "required": ["account_number", "amount", "adjustment_type", "description", "reference"]
          }
        },
        {
          "name": "find_similar",
          "description": "Find invoices similar to a payment using embedding-based semantic similarity",
          "inputSchema": {
            "type": "object",
            "properties": {
              "payment_id": { "type": "string" },
              "top_k": { "type": "integer" }
            },
            "required": ["payment_id"]
          }
        },
        {
          "name": "gen_recon_report",
          "description": "Generate a formal reconciliation report for a period with sign-off",
          "inputSchema": {
            "type": "object",
            "properties": {
              "account_number": { "type": "string" },
              "period": { "type": "string" }
            },
            "required": ["account_number", "period"]
          }
        }
      ]
    }
  }
}
```

---

## Three-Tier Matching Engine

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREE-TIER MATCHING ENGINE                   │
│                                                                 │
│  Input: Bank Statement Entries + Ledger Entries                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TIER 1: EXACT MATCH (Confidence ≥ 95%)                 │    │
│  │                                                         │    │
│  │  Criteria:                                              │    │
│  │  ├─ Reference number: EXACT match                       │    │
│  │  ├─ Amount: EXACT match (±$0.01)                        │    │
│  │  ├─ Date: Within ±1 business day                        │    │
│  │  └─ Counterparty: EXACT or known alias                  │    │
│  │                                                         │    │
│  │  Weight: Ref=40% + Amt=35% + Date=15% + CP=10%        │    │
│  │  Auto-match threshold: ≥ 0.95                           │    │
│  │  Action: Auto-reconcile, log for audit                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                    Unmatched items                               │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TIER 2: FUZZY MATCH (Confidence 75-94%)                │    │
│  │                                                         │    │
│  │  Criteria:                                              │    │
│  │  ├─ Reference: Partial match (last 6+ chars)            │    │
│  │  ├─ Amount: Within ±1% tolerance                        │    │
│  │  ├─ Date: Within ±2-5 business days                     │    │
│  │  └─ Counterparty: 50%+ name overlap                     │    │
│  │                                                         │    │
│  │  Action: Flag for analyst review, suggest candidates    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                    Still unmatched                               │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ TIER 3: SEMANTIC MATCH (Confidence 60-74%)             │    │
│  │                                                         │    │
│  │  Uses embedding-based similarity:                       │    │
│  │  ├─ Payment reference embedding vs invoice embedding    │    │
│  │  ├─ Amount + date + counterparty composite embedding    │    │
│  │  └─ Cosine similarity scoring                           │    │
│  │                                                         │    │
│  │  Action: Present top candidates for manual matching     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                    Still unmatched                               │
│                          ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ EXCEPTION QUEUE                                         │    │
│  │                                                         │    │
│  │  Categorize by type:                                    │    │
│  │  ├─ Unmatched bank entry (possible unrecorded tx)       │    │
│  │  ├─ Unmatched ledger entry (check not cleared, etc.)    │    │
│  │  ├─ Amount discrepancy (fees, FX, partial payment)      │    │
│  │  ├─ Duplicate entry (double posting)                     │    │
│  │  └─ Fraudulent alteration (check tampering)              │    │
│  │                                                         │    │
│  │  Severity assignment:                                   │    │
│  │  ├─ LOW: < $100, simple timing difference               │    │
│  │  ├─ MEDIUM: $100-$10,000, requires investigation       │    │
│  │  ├─ HIGH: > $10,000 or suspected fraud                 │    │
│  │  └─ CRITICAL: > $100,000 or regulatory issue           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                             │
│                                                                 │
│  ┌─────────────┐                                                │
│  │  Analyst     │  "What's the process for reconciling          │
│  │  Query       │   international wire transfers?"              │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 1. QUERY    │  Rewrites for better retrieval:                │
│  │   REWRITE   │  "International wire reconciliation process    │
│  │             │   SWIFT MT940 matching rules"                  │
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
│  │  │ "wire"     │    │  Vector        │    │                   │
│  │  │ "reconcil" │    │  Similarity    │    │                   │
│  │  │ "MT940"    │    │  Search        │    │                   │
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
│          │   ASSEMBLY     │  - Wire reconciliation rules        │
│          │                │  - MT940 format spec                 │
│          │                │  - Exception handling procedures     │
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
                    │   Analyst Input    │
                    │  "Reconcile        │
                    │   January"         │
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
            │  │ Vector  │  │   │  │ Payment   │ │
            │  │ DB      │  │   │  │ Matching  │ │
            │  │         │  │   │  ├───────────┤ │
            │  │ → Rules │  │   │  │ Bank Stmt │ │
            │  │ → Std.  │  │   │  │ Import    │ │
            │  │ → Except│  │   │  ├───────────┤ │
            │  │ → GAAP  │  │   │  │ Ledger    │ │
            │  │ → Cases │  │   │  │ Mgmt      │ │
            │  │ → Match │  │   │  ├───────────┤ │
            │  └─────────┘  │   │  │ Exception │ │
            │               │   │  │ Handling  │ │
            └───────────────┘   │  ├───────────┤ │
                                │  │ Discrepan.│ │
                                │  │ Resolution│ │
                                │  ├───────────┤ │
                                │  │ Embedding │ │
                                │  │ Matching  │ │
                                │  ├───────────┤ │
                                │  │ Accounting│ │
                                │  │ System    │ │
                                │  ├───────────┤ │
                                │  │ Notify    │ │
                                │  │ Analyst   │ │
                                │  └───────────┘ │
                                └────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Reconciliation      │
                    │  Report              │
                    │  "83% matched,       │
                    │   $1 write-off,      │
                    │   1 fraud escalated" │
                    │  + Audit Trail       │
                    │  + SOX Compliance    │
                    └─────────────────────┘
```

---

## Exception Aging & Escalation Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│              EXCEPTION AGING & ESCALATION MATRIX                │
│                                                                 │
│  Age        Action              Escalation                     │
│  ─────────  ──────────────────  ─────────────────────────────  │
│  0-3 days   Auto-notify analyst Review by assigned analyst     │
│                                                                 │
│  4-7 days   Daily follow-up     Supervisor notification        │
│             required            Required                       │
│                                                                 │
│  8-14 days  Formal              Manager review                 │
│             investigation       Root cause analysis required   │
│                                                                 │
│  15-30 days Director review     Director + VP notification     │
│             Root cause analysis Written explanation required   │
│                                                                 │
│  31+ days   VP/CFO              CFO notification               │
│             notification        Write-off approval may needed  │
│                                                                 │
│  Materiality Thresholds:                                        │
│  ├─ > $10,000:     Immediate supervisor escalation              │
│  ├─ > $50,000:     Manager escalation                           │
│  ├─ > $100,000:    Director escalation                          │
│  └─ > $500,000:    CFO escalation                               │
│                                                                 │
│  Fraud Detection:                                               │
│  ├─ Check alteration:     Immediately HIGH severity             │
│  ├─ Duplicate payment:    MEDIUM severity, auto-investigate     │
│  ├─ Unknown counterparty: HIGH severity, freeze account         │
│  └─ Pattern anomalies:    MEDIUM, flag for AML review           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Three-Tier Matching** | Exact → Fuzzy → Semantic | Progressive matching catches more with less manual effort |
| **Hybrid Search** | BM25 + Semantic | Keyword catches regulation numbers; semantic handles paraphrased queries |
| **Re-ranking** | Cross-encoder | Precision critical — wrong match = financial misstatement |
| **MCP over direct API** | MCP protocol | Standardized; swap bank APIs, GL systems without changing agent logic |
| **Embedding Matching** | 128-dim payment vectors | Matches unmatched payments to invoices by semantic similarity |
| **Exception Aging** | 5-tier escalation | SOX compliance requires timely resolution; prevents audit findings |
| **SOX Compliance** | Every adjustment logged | Regulatory requirement; segregation of duties enforced |
| **Multi-format Import** | MT940, BAI2, ISO 20022, CSV | Banks use different formats; agent must handle all |
| **Amount Tolerance** | Configurable ±1% | Prevents false exceptions on minor rounding/FX differences |
| **Write-off Threshold** | $5.00 (configurable) | Small discrepancies resolved without full investigation |
| **Human-in-Loop** | Journal entries, reversals, write-offs | Financial adjustments require approval per SOX |
| **Audit Trail** | Every action logged | Regulators require full traceability of reconciliation |

---

*Architecture designed for Payment Reconciliation Agent (7.2) — August 2026*
