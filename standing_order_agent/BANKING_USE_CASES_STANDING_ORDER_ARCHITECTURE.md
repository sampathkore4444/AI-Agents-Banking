# Standing Order & Bill Payment Agent — Architecture

## 1. Overview

The Standing Order & Bill Payment Agent manages recurring payment schedules, enabling customers to set up, modify, and cancel standing orders through natural language interactions.

### 1.1 Business Objectives
- Enable customers to self-serve recurring payment management
- Reduce call center volume for bill payment inquiries
- Ensure compliance with Reg E, NACHA, and UDAAP
- Provide intelligent biller recommendations
- Detect and prevent unauthorized recurring payment changes

### 1.2 Key Metrics
- Setup completion rate: > 90%
- Payment success rate: > 98%
- Customer satisfaction: > 4.5/5
- Average task completion time: < 2 minutes
- Compliance incident rate: 0%

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  Mobile App  │  Online Banking  │  Voice (IVR)  │  Branch       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                     MCP SERVER LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Standing Order & Bill Payment Agent (server.py)        │    │
│  │  ├── 40+ MCP Tools                                      │    │
│  │  ├── Intent Parser (NLU)                                │    │
│  │  ├── Guardrails Engine                                  │    │
│  │  └── Human-in-the-Loop                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                     TOOL LAYER                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Standing     │ │ Biller       │ │ Payment      │            │
│  │ Order Mgmt   │ │ Directory    │ │ Scheduling   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Calendar &   │ │ Notifications│ │ Customer     │            │
│  │ Reminders    │ │              │ │ Profile      │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐                                              │
│  │ Payment      │                                              │
│  │ Embeddings   │                                              │
│  └──────────────┘                                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                     DATA LAYER                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RAG Pipeline (ChromaDB)                                 │  │
│  │  ├── standing_order_policies (5 docs)                    │  │
│  │  ├── biller_directory (7 docs)                           │  │
│  │  ├── payment_schedules (6 docs)                          │  │
│  │  ├── recurring_payment_rules (5 docs)                    │  │
│  │  ├── compliance_requirements (4 docs)                    │  │
│  │  ├── customer_billing_knowledge (5 docs)                 │  │
│  │  └── operational_playbooks (4 docs)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Embeddings (SentenceTransformer)                        │  │
│  │  ├── Payment intent vectors (128-dim)                    │  │
│  │  ├── Payment pattern vectors (128-dim)                   │  │
│  │  └── Biller match vectors (128-dim)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Design

### 3.1 Standing Order Management
- **CRUD operations**: Create, Read, Update, Delete standing orders
- **Status management**: Active, Paused, Suspended, Cancelled
- **Failure handling**: 3-retry logic with escalating delays
- **Approval workflow**: Amount thresholds trigger human review

### 3.2 Biller Directory
- **Fuzzy search**: RapidFuzz-based name matching (≥60% threshold)
- **Verification**: Account number and customer name validation
- **Categories**: Utility, mortgage, insurance, subscription, loan, telecom, government
- **Auto-pay discounts**: Tracked per biller

### 3.3 Payment Scheduling
- **Calendar engine**: Holiday-aware scheduling using Fed calendar
- **Weekend/holiday adjustment**: Automatic deferral to next business day
- **Retry logic**: 3 attempts with increasing delays (next day → 3 days → suspension)
- **Execution window**: 2:00 AM - 6:00 AM ET batch processing

### 3.4 Natural Language Understanding
- **Intent parsing**: Pattern matching + LLM for complex requests
- **Entity extraction**: Amount, frequency, payee, dates from natural language
- **Example**: "Pay my rent on the 1st of every month" → `create_standing_order(payee="Landlord", frequency="monthly", day=1)`

### 3.5 Compliance
- **Reg E**: Stop payment rights, error resolution (10 business days)
- **NACHA**: Authorization requirements, return timeframes (R07 within 60 days)
- **UDAAP**: Clear disclosures, easy cancellation, no hidden fees
- **BSA/AML**: Structuring detection for recurring suspicious patterns

---

## 4. Data Model

### 4.1 Standing Order
```json
{
  "standing_order_id": "SO-XXXXXXXX",
  "account_id": "ACC-CHK-001",
  "customer_name": "John Smith",
  "payee_name": "Con Edison",
  "payee_account_number": "****1234",
  "payee_routing": "021000021",
  "amount": 150.00,
  "frequency": "monthly",
  "start_date": "2024-01-01",
  "end_date": null,
  "next_execution": "2024-02-01T02:00:00Z",
  "payment_method": "ach_debit",
  "status": "active",
  "failure_count": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "history": [...]
}
```

### 4.2 Biller
```json
{
  "biller_id": "BLR-CONED",
  "name": "Con Edison",
  "category": "utility",
  "payment_methods": ["ach_debit"],
  "typical_amount_range": "$50-$400",
  "billing_cycle": "monthly",
  "auto_pay_discount": 2.50,
  "verification_required": false
}
```

### 4.3 Payment Intent
```json
{
  "intent": "create",
  "confidence": 0.95,
  "extracted_entities": {
    "amount": 1500,
    "frequency": "monthly",
    "day_of_month": 1,
    "payee_name": "ABC Property Management"
  },
  "suggested_action": {
    "tool": "create_standing_order",
    "params": {...},
    "missing_fields": ["account_id", "payee_account_number"]
  }
}
```

---

## 5. Security & Compliance

### 5.1 Authentication & Authorization
- Two-factor authentication for standing order creation
- Step-up authentication for modifications > $10,000
- Session timeout: 15 minutes for standing order operations
- IP geolocation validation for remote access

### 5.2 Data Protection
- Payee account numbers masked in responses (show last 4)
- PII encrypted at rest and in transit
- Audit trail for all standing order actions
- Retention: 7 years per regulatory requirements

### 5.3 Fraud Prevention
- New payee verification (first payment delayed/capped)
- Amount change detection (>20% triggers review)
- Velocity limits (max 50 active standing orders)
- Unusual pattern detection (structuring for recurring payments)

---

## 6. Deployment

### 6.1 Infrastructure
- MCP Server: Containerized (Docker/Kubernetes)
- ChromaDB: Persistent volume for vector storage
- LLM: Ollama (dev) / vLLM (prod) / SGLang (batch)
- Redis: Session management and caching

### 6.2 Scaling
- Horizontal scaling: Multiple MCP server instances
- ChromaDB: Read replicas for query performance
- LLM: GPU cluster for inference throughput
- Database: Sharded by account_id

### 6.3 Monitoring
- Payment success/failure rates
- Standing order creation/modification volumes
- Compliance alert frequency
- LLM latency and error rates
- Customer satisfaction scores

---

## 7. Integration Points

| System | Protocol | Purpose |
|---|---|---|
| Core Banking | REST API | Account validation, balance checks |
| ACH Network | NACHA files | Payment processing |
| Biller Network | REST API | Biller verification, payment routing |
| Notification Service | REST API | Email, SMS, push notifications |
| Calendar Service | REST API | Reminder scheduling |
| OFAC/Sanctions | REST API | Payee screening |
| Audit System | Event stream | Action logging |
