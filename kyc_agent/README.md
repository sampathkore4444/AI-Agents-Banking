# KYC Onboarding Agent — MCP + LLM

A **Model Context Protocol (MCP)** server for KYC (Know Your Customer) onboarding in banking, powered by a **RAG pipeline** for regulatory knowledge retrieval and **3 LLM backends** (Ollama, vLLM, SGLang) for orchestration.

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     KYC ONBOARDING AGENT                          │
│                                                                    │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────────┐  │
│  │  User     │───▶│  LLM Core   │───▶│  MCP Tool Server         │  │
│  │  Query    │    │  (ReAct     │◀───│  ├── knowledge_search    │  │
│  │           │◀───│   Agent)    │    │  ├── verify_identity     │  │
│  │           │    │             │    │  ├── screen_sanctions    │  │
│  │           │    │  Options:   │    │  ├── create_bank_account │  │
│  │           │    │  • Ollama   │    │  ├── open_compliance_case│  │
│  │           │    │  • vLLM     │    │  └── notify_customer     │  │
│  │           │    │  • SGLang   │    └──────────────────────────┘  │
│  └──────────┘    └──────┬──────┘                                  │
│                         │                                         │
│                         ▼                                         │
│                  ┌──────────────┐                                  │
│                  │  RAG Engine  │                                  │
│                  │  (ChromaDB)  │                                  │
│                  │  • Regulations│                                 │
│                  │  • Policies  │                                  │
│                  │  • Doc Schemas│                                 │
│                  │  • Risk Rules│                                  │
│                  │  • Past Cases│                                  │
│                  └──────────────┘                                  │
└────────────────────────────────────────────────────────────────────┘
```

## Tools Exposed

| Tool | Description |
|------|-------------|
| `knowledge_search` | RAG-powered search over KYC regulations, policies, and past cases |
| `get_document_schema` | Retrieve expected fields for a document type |
| `extract_and_classify_document` | OCR + schema validation for uploaded documents |
| `verify_customer_identity` | Liveness, document authenticity, and face match |
| `screen_customer_sanctions` | OFAC, EU, UN sanctions + PEP screening |
| `create_bank_account` | Create customer profile and bank account |
| `lookup_customer` | Query core banking system |
| `open_compliance_case` | Create case for manual officer review |
| `get_case` / `update_case` | Retrieve and update compliance cases |
| `notify_customer` | Send email, SMS, or in-app notifications |
| `assess_kyc_risk` | RAG-powered risk assessment with scoring |

## LLM Backends

Three LLM backends are provided, all implementing the same `BaseAgent` interface:

| Backend | Best For | Setup | Speed |
|---------|----------|-------|-------|
| **Ollama** | Local dev, privacy | `ollama serve` | ~2-5s |
| **vLLM** | Production, high throughput | `vllm serve <model>` | ~0.5-2s |
| **SGLang** | Structured output, caching | `sglang.launch_server` | ~0.3-1.5s |

### Backend Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                     Backend Comparison                          │
├─────────────┬─────────────┬─────────────┬──────────────────────┤
│ Feature     │ Ollama      │ vLLM        │ SGLang               │
├─────────────┼─────────────┼─────────────┼──────────────────────┤
│ Local       │ ✓           │ ✓           │ ✓                    │
│ OpenAI API  │ ✓           │ ✓           │ ✓                    │
│ Tool Calling│ ✓           │ ✓           │ ✓                    │
│ Structured  │ ✗           │ ✗           │ ✓ (JSON schema)      │
│ Output      │             │             │                      │
│ PagedAttn   │ ✗           │ ✓           │ ✓ (RadixAttention)   │
│ Prefix      │ ✗           │ ✗           │ ✓                    │
│ Caching     │             │             │                      │
│ Multi-GPU   │ Limited     │ ✓           │ ✓                    │
│ Streaming   │ ✓           │ ✓           │ ✓                    │
│ Ease of Use │ ★★★★★      │ ★★★★       │ ★★★                  │
│ Throughput  │ Low         │ High        │ High                 │
│ Latency     │ Medium      │ Low         │ Low                  │
└─────────────┴─────────────┴─────────────┴──────────────────────┘
```

## Quick Start

### 1. Install dependencies

```bash
cd kyc_agent
pip install -r requirements.txt
```

### 2. Seed the knowledge base

```bash
python seed_knowledge.py
```

### 3. Start an LLM backend

**Option A: Ollama (easiest)**
```bash
# Install: https://ollama.ai
ollama pull llama3.1:8b
ollama serve  # starts on port 11434
```

**Option B: vLLM (high performance)**
```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

**Option C: SGLang (structured output)**
```bash
pip install sglang
python -m sglang.launch_server --model meta-llama/Llama-3.1-8B-Instruct --port 30000
```

### 4. Run the agent

```bash
# Interactive mode
python -m llm.agent_ollama    # Uses Ollama
python -m llm.agent_vllm      # Uses vLLM
python -m llm.agent_sglang    # Uses SGLang

# Compare all three
python compare_agents.py
```

### 5. Or use MCP server mode

```bash
python server.py  # Starts MCP server on stdio
```

## Project Structure

```
kyc_agent/
├── server.py              # MCP server — tool definitions (no LLM)
├── rag_pipeline.py        # RAG engine — ChromaDB + hybrid search
├── config.py              # Settings from environment variables
├── seed_knowledge.py      # Seed script for vector DB
├── compare_agents.py      # Compare all 3 LLM backends
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── llm/
│   ├── __init__.py
│   ├── base_agent.py      # Base agent — ReAct loop, tools, memory, guardrails
│   ├── agent_ollama.py    # Ollama integration (local, free)
│   ├── agent_vllm.py      # vLLM integration (high throughput)
│   └── agent_sglang.py    # SGLang integration (structured output)
└── tools/
    ├── __init__.py
    ├── identity_verification.py    # Jumio/Onfido stub
    ├── sanctions_screening.py      # OFAC/EU/UN stub
    ├── document_extraction.py      # OCR stub
    ├── core_banking.py             # Core banking API stub
    ├── compliance.py               # Case management stub
    └── notifications.py            # Notification service stub
```

## Extending

### Add a new tool

```python
# In server.py
@mcp.tool()
async def my_new_tool(param1: str, param2: int) -> dict:
    """
    Description of what this tool does.

    Args:
        param1: Description
        param2: Description
    """
    # Your logic here
    return {"result": "done"}
```

### Add new knowledge

```python
# In seed_knowledge.py, add to the appropriate list:
KYC_REGULATIONS.append({
    "id": "reg_new_001",
    "text": "Your regulation text here...",
    "metadata": {"source": "FCA", "type": "new_rule"},
})
```

### Switch vector database

Replace ChromaDB with Pinecone, Weaviate, Qdrant, or pgvector by updating
`rag_pipeline.py`. The MCP tool interface stays the same.

## Production Patterns

The `BaseAgent` class implements **6 production-ready patterns** in `llm/base_agent.py`:

| # | Pattern | Class | Purpose |
|---|---------|-------|---------|
| 1 | Intent Routing | `IntentRouter` | Classifies queries and routes simple ones to RAG (no LLM) |
| 2 | Guardrails | `Guardrails` | Risk-based tool access control + output safety checks |
| 3 | Human-in-the-Loop | `HumanApprovalManager` | Pauses for approval on high-risk actions |
| 4 | Memory Management | `ConversationMemory` | Token-aware history with summarization |
| 5 | Error Handling | `ErrorHandler` | Retry with backoff, fallback strategies |
| 6 | Observability | `AgentTracer` | Structured traces for every operation |

---

### 1. Intent Routing (`IntentRouter`)

**Why:** Not every query needs the full ReAct loop. Simple questions like "What documents do I need?" can be answered directly from RAG without calling the LLM.

**How it works:**

```
User Query
    │
    ▼
┌─────────────────┐
│ IntentRouter    │
│ .classify(query)│
└───────┬─────────┘
        │
   ┌────┴────────────────────────────┐
   │              │                   │
   ▼              ▼                   ▼
 SIMPLE        MODERATE            COMPLEX/CRITICAL
   │              │                   │
   ▼              ▼                   ▼
 Direct RAG    1-2 tool calls     Full ReAct loop
 (no LLM)      + LLM              + tools + approval
```

**Classification rules:**

| Complexity | Patterns | Action |
|------------|----------|--------|
| `SIMPLE` | "what is", "how to", "explain", "tell me about" | Direct RAG search, no LLM |
| `MODERATE` | General queries | 1-2 tool calls |
| `COMPLEX` | "process application", "verify identity", "screen sanctions" | Multi-step ReAct loop |
| `CRITICAL` | "approve", "reject", "block", "freeze", "file SAR" | Requires human approval |

**Code:**
```python
from llm.base_agent import IntentRouter, QueryComplexity

complexity = IntentRouter.classify("What documents do I need?")
# → QueryComplexity.SIMPLE

complexity = IntentRouter.classify("Process this KYC application")
# → QueryComplexity.COMPLEX

complexity = IntentRouter.classify("Approve this account and block the other")
# → QueryComplexity.CRITICAL
```

---

### 2. Guardrails (`Guardrails`)

**Why:** Not all tools should be callable without restrictions. Creating a bank account or updating a compliance case are high-risk actions that need safeguards.

**Tool Risk Levels:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      TOOL RISK LEVELS                          │
├─────────────┬───────────────────────────────────────────────────┤
│ SAFE        │ knowledge_search, get_document_schema,            │
│ (auto)      │ get_case, lookup_customer, assess_kyc_risk        │
├─────────────┼───────────────────────────────────────────────────┤
│ LOW         │ extract_document, notify_customer                 │
│ (auto)      │ Minor side effects, safe to auto-execute          │
├─────────────┼───────────────────────────────────────────────────┤
│ MEDIUM      │ verify_identity, screen_sanctions,                │
│ (approval)  │ open_compliance_case                              │
├─────────────┼───────────────────────────────────────────────────┤
│ HIGH        │ create_bank_account, update_case                  │
│ (required)  │ Irreversible, ALWAYS requires human approval      │
└─────────────┴───────────────────────────────────────────────────┘
```

**Output Safety:**
- Blocks responses containing sensitive data (SSN, credit cards, emails)
- Detects prompt injection attempts ("ignore previous instructions")
- Redacts sensitive data in logs

**Code:**
```python
from llm.base_agent import Guardrails, ToolRiskLevel

guardrails = Guardrails()

# Check tool call
allowed, reason, risk = guardrails.check_tool_call("create_bank_account", {...})
# → (False, "Tool 'create_bank_account' requires human approval (risk=high)", HIGH)

allowed, reason, risk = guardrails.check_tool_call("knowledge_search", {...})
# → (True, "OK", SAFE)

# Check output
allowed, reason = guardrails.check_output("Your SSN is 123-45-6789")
# → (False, "Response may contain sensitive data: [SSN_REDACTED]")
```

---

### 3. Human-in-the-Loop (`HumanApprovalManager`)

**Why:** High-risk banking actions (creating accounts, modifying cases) must have human oversight for regulatory compliance.

**Flow:**

```
Agent wants to call create_bank_account()
    │
    ▼
┌─────────────────────────┐
│ Guardrails says:        │
│ risk = HIGH             │
│ requires approval       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ ApprovalManager         │
│ .request_approval()     │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
  APPROVED      REJECTED
     │             │
     ▼             ▼
  Execute       Return error:
  tool          "Rejected by human"
```

**Modes:**

| Mode | Use Case | Behavior |
|------|----------|----------|
| `auto_approve=True` | Development/testing | All approvals granted |
| `auto_approve=False` | Production | Blocks and waits for human |
| `on_approval_needed` callback | Slack/email integration | Sends notification, waits for webhook |

**Code:**
```python
from llm.base_agent import HumanApprovalManager, ToolCall

manager = HumanApprovalManager(auto_approve=False)

# Simulate approval request
approved, reason = await manager.request_approval(
    tool_call=ToolCall(id="123", name="create_bank_account", arguments={...}),
    risk_level=ToolRiskLevel.HIGH,
    context="New business account for XYZ Corp"
)
# Prints:
# ⚠️  APPROVAL REQUIRED
#    Tool: create_bank_account
#    Risk: high
#    Args: {...}
# Approve? (yes/no):
```

---

### 4. Memory Management (`ConversationMemory`)

**Why:** LLMs have limited context windows. Without memory management, conversations get too long and expensive.

**Features:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY MANAGEMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Token Counting        │  Estimates tokens per message         │
│  (1 token ≈ 4 chars)   │  Tracks total usage                  │
│                        │                                       │
├────────────────────────┼───────────────────────────────────────┤
│  Sliding Window        │  Keeps system prompt + recent msgs   │
│                        │  Drops oldest when over limit         │
│                        │                                       │
├────────────────────────┼───────────────────────────────────────┤
│  Summarization         │  Compresses old messages              │
│                        │  "User asked: X; Agent said: Y"      │
│                        │                                       │
├────────────────────────┼───────────────────────────────────────┤
│  Key Facts             │  Extracts important info              │
│                        │  "Customer ID: CUST-123"             │
│                        │  Preserved across truncation          │
│                        │                                       │
├────────────────────────┼───────────────────────────────────────┤
│  Session Persistence   │  save_session() → JSON                │
│                        │  load_session(data) ← restore         │
└────────────────────────┴───────────────────────────────────────┘
```

**Code:**
```python
from llm.base_agent import ConversationMemory

memory = ConversationMemory(max_tokens=8000)

# Add messages
memory.add("user", "I want to open an account")
memory.add("assistant", "Sure! Let me search for requirements...")
memory.add("tool", "Found 5 regulation documents", is_key_fact=True)

# Check usage
usage = memory.get_token_usage()
# {"total_tokens": 234, "max_tokens": 8000, "utilization": 0.03}

# Get context (auto-truncates if over limit)
context = memory.get_context()

# Save/restore session
session_data = memory.save_session()
memory.load_session(session_data)
```

---

### 5. Error Handling (`ErrorHandler`)

**Why:** LLM calls and tool executions can fail. Without retry logic, transient errors crash the agent.

**Strategy:**

```
Operation fails
    │
    ▼
┌─────────────────┐
│ Should retry?   │
│ (attempt < max) │
└───────┬─────────┘
        │
   ┌────┴────┐
   ▼         ▼
  YES        NO (auth/permission errors)
   │         │
   ▼         ▼
  Wait       Raise
  (backoff)  immediately
   │
   ▼
┌─────────────────┐
│ Retry operation │
└─────────────────┘
```

**Exponential backoff:**

| Attempt | Delay |
|---------|-------|
| 1 | 1.5s |
| 2 | 2.25s |
| 3 | 3.375s |

**Non-retryable errors:** `authentication`, `permission`, `not found`, `invalid`

**Code:**
```python
from llm.base_agent import ErrorHandler

handler = ErrorHandler(max_retries=3, backoff_factor=1.5)

# With retry
result = await handler.with_retry(
    operation=lambda: call_llm(messages),
    operation_name="llm_call",
    tracer=self.tracer,
)

# Error summary
errors = handler.get_error_summary()
# {"TimeoutError": 2, "ConnectionError": 1}
```

---

### 6. Observability (`AgentTracer`)

**Why:** In production, you need to understand *why* the agent made certain decisions. Structured traces provide this.

**Trace structure:**

```
agent_run (1234ms)
├── intent:classify (0.5ms)
├── llm_call (800ms)
│   ├── retry:llm_call (0ms, no retry needed)
├── tool:knowledge_search (150ms)
├── tool:screen_sanctions (200ms)
├── llm_call (600ms)
└── tool:create_bank_account (300ms)
    ├── approval_requested (event)
    ├── approval_result (event)
```

**Output format:**
```json
{
  "total_spans": 7,
  "total_duration_ms": 1234,
  "llm_calls": 2,
  "tool_calls": 3,
  "errors": 0,
  "spans": [
    {"name": "agent_run", "duration_ms": 1234, "status": "ok"},
    {"name": "llm_call", "duration_ms": 800, "status": "ok"},
    {"name": "tool:knowledge_search", "duration_ms": 150, "status": "ok"}
  ]
}
```

**Features:**
- **Parent-child spans** — understand execution hierarchy
- **Events** — track retries, approvals, errors within spans
- **Export to JSON** — send to monitoring systems (Datadog, Prometheus)
- **Sensitive data redaction** — logs never contain SSNs, card numbers, etc.

**Code:**
```python
from llm.base_agent import AgentTracer

tracer = AgentTracer()

# Start/end spans
span_id = tracer.start_span("my_operation", {"key": "value"})
# ... do work ...
tracer.end_span(span_id, "ok", {"result": "success"})

# Add events
tracer.add_event(span_id, "retry", {"attempt": 2})

# Get trace
summary = tracer.get_trace_summary()
print(tracer.export_json())
```

---

### Full Agent Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT EXECUTION FLOW                            │
│                                                                         │
│  1. USER QUERY                                                          │
│     "I want to open a UK business account"                              │
│     │                                                                   │
│     ▼                                                                   │
│  2. INTENT ROUTING (IntentRouter.classify)                               │
│     Complexity: COMPLEX                                                 │
│     │                                                                   │
│     ▼                                                                   │
│  3. MEMORY (ConversationMemory.add)                                      │
│     Store user message, check token limits                              │
│     │                                                                   │
│     ▼                                                                   │
│  4. SYSTEM PROMPT (with tool descriptions + complexity instructions)     │
│     │                                                                   │
│     ▼                                                                   │
│  5. ReAct LOOP (max_steps iterations)                                    │
│     │                                                                   │
│     ├── 5a. LLM CALL (call_llm with retry)                              │
│     │       → LLM thinks, decides tool calls                             │
│     │                                                                   │
│     ├── 5b. GUARDRAILS CHECK (Guardrails.check_tool_call)               │
│     │       → Risk level? Safe to execute?                               │
│     │                                                                   │
│     ├── 5c. HUMAN APPROVAL (if risk = HIGH)                             │
│     │       → Pause, request approval, wait                             │
│     │                                                                   │
│     ├── 5d. TOOL EXECUTION (execute_tool with retry)                    │
│     │       → Call MCP tool, collect results                            │
│     │                                                                   │
│     ├── 5e. MEMORY UPDATE (add tool results)                            │
│     │       → Store observation, extract key facts                      │
│     │                                                                   │
│     └── 5f. TRACES (AgentTracer records everything)                     │
│             → Spans, events, timing                                     │
│     │                                                                   │
│     ▼                                                                   │
│  6. OUTPUT GUARDRAILS (Guardrails.check_output)                          │
│     → Block sensitive data, prompt injection                            │
│     │                                                                   │
│     ▼                                                                   │
│  7. RESPONSE (AgentResponse with full trace)                             │
│     {                                                                   │
│       answer: "To open a UK business account...",                       │
│       steps: [...],                                                     │
│       tool_calls: [...],                                                │
│       complexity: "COMPLEX",                                            │
│       metrics: { tokens, duration, memory_usage, trace_summary }        │
│     }                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Additional Components

### Tool Registry (`ToolRegistry`)

Central registry for all agent tools with OpenAI-compatible schemas:

```python
from llm.base_agent import ToolRegistry, ToolRiskLevel

registry = ToolRegistry()
registry.register(
    name="my_tool",
    description="Does something useful",
    parameters={"type": "object", "properties": {...}},
    handler=my_handler_func,
    risk_level=ToolRiskLevel.MEDIUM,
)

# Get schemas for LLM
schemas = registry.get_schemas()  # OpenAI function calling format

# Get all tool descriptions
print(registry.get_tool_descriptions())
# - my_tool [medium]: Does something useful (params: ...)
```

### RAG Pipeline (`RAGPipeline`)

Hybrid search over 5 knowledge collections:

| Collection | Content | Example Query |
|------------|---------|---------------|
| `kyc_regulations` | FCA, FinCEN, EU rules | "What does MLR 2017 say about CDD?" |
| `product_policies` | Account eligibility | "Business account requirements" |
| `document_schemas` | Required fields | "Passport verification fields" |
| `risk_typologies` | Risk indicators | "High-risk business indicators" |
| `past_kyc_decisions` | Approved/rejected cases | "Fintech company KYC decisions" |

### Agent Response (`AgentResponse`)

Complete response object with full trace:

```python
response = await agent.run("Process this KYC application")

print(response.answer)           # "Based on the regulations..."
print(response.complexity)       # QueryComplexity.COMPLEX
print(response.tool_calls)       # [ToolCall(name="knowledge_search", ...)]
print(response.total_duration_ms)  # 1234.5
print(response.tokens_used)      # {"prompt_tokens": 500, ...}
print(response.rag_sources)      # [{"text": "...", "score": 0.87}]
print(response.metrics)          # Full execution metrics

# Export trace for monitoring
for span in response.trace:
    print(f"{span.name}: {span.duration_ms}ms ({span.status})")
```

---

## Application Layer vs Infrastructure Layer

Understanding what we implemented vs what's handled by the LLM serving backends:

### What We Implemented (Application Layer)

These are the **agent logic patterns** in `base_agent.py` that make the agent production-ready:

```
┌─────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER (Our Code)                                   │
│                                                                 │
│  ✅ Intent Routing    — Routes simple queries to RAG            │
│  ✅ Guardrails        — Blocks dangerous tools, output safety   │
│  ✅ Human-in-Loop     — Pauses for approval on high-risk        │
│  ✅ Memory Management — Token counting, truncation, summary     │
│  ✅ Error Handling    — Retry with exponential backoff           │
│  ✅ Observability     — Structured traces for every operation   │
│  ✅ Tool Registry     — Dynamic tool registration               │
│  ✅ ReAct Loop        — Think → Act → Observe → Repeat          │
└─────────────────────────────────────────────────────────────────┘
```

### What's Handled by Infrastructure (LLM Backends)

These are **GPU/inference concerns** handled automatically by Ollama, vLLM, and SGLang:

```
┌─────────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER (LLM Backends)                            │
│                                                                 │
│  ⚙️ Batching          — vLLM handles automatically              │
│  ⚙️ KV Cache          — All backends use for efficiency         │
│  ⚙️ Quantization      — Configure via server flags              │
│  ⚙️ GPU Memory        — CUDA/cuDNN manages VRAM                 │
│  ⚙️ Scheduling        — vLLM uses continuous batching           │
└─────────────────────────────────────────────────────────────────┘
```

### Why We Don't Need Infrastructure Patterns

```
Our KYC Agent (Single-user):                Production Banking (Multi-user):
┌──────────────┐                             ┌──────────────┐
│   1 User     │ ← 1 person typing           │  10,000+     │ ← Thousands of users
│              │                             │  Users       │
└──────┬───────┘                             └──────┬───────┘
       │                                           │
       ▼                                           ▼
┌──────────────┐                             ┌──────────────┐
│   1 Request  │ ← Sequential processing     │   Load       │ ← Needs batching,
│   at a time  │                             │   Balancer   │   scheduling
└──────┬───────┘                             └──────┬───────┘
       │                                           │
       ▼                                           ▼
┌──────────────┐                             ┌──────────────┐
│   1 GPU      │ ← Fits in single GPU        │  10+ GPUs    │ ← Needs memory
│              │                             │  Cluster     │   management
└──────────────┘                             └──────────────┘
```

### When You WOULD Need Infrastructure Patterns

| Pattern | When Required | Example |
|---------|--------------|---------|
| **Batching** | Processing many documents simultaneously | Nightly: embed 100,000 customer profiles |
| **KV Cache** | Multiple users sharing same LLM | 50 users chatting with same bank bot |
| **Quantization** | Limited GPU memory | Running 70B model on single A100 |
| **GPU Memory** | Multiple models on same GPU | Fraud model + chatbot + document model |
| **Scheduling** | Mixed priority workloads | Fraud detection (fast) vs batch reporting (slow) |

### How To Configure Infrastructure (When Needed)

```bash
# Batching — vLLM handles automatically
vllm serve meta-llama/Llama-3.1-8B-Instruct --max-num-seqs 16

# KV Cache — vLLM handles automatically (PagedAttention)
vllm serve meta-llama/Llama-3.1-8B-Instruct --gpu-memory-utilization 0.9

# Quantization — just a flag
vllm serve meta-llama/Llama-3.1-8B-Instruct --quantization awq

# GPU Memory — CUDA environment variable
export CUDA_VISIBLE_DEVICES=0,1  # Use GPU 0 and 1

# Scheduling — vLLM config
vllm serve meta-llama/Llama-3.1-8B-Instruct --max-model-len 8192
```

### Summary

> **We built the *brain* (agent logic). The *muscle* (GPU, batching, caching) is handled by the serving infrastructure.**

The 6 patterns in `base_agent.py` (Intent Routing, Guardrails, Human-in-Loop, Memory, Error Handling, Observability) are the **application-level concerns** that matter for a banking agent. The infrastructure patterns (batching, KV cache, quantization, GPU memory, scheduling) are handled by Ollama/vLLM/SGLang automatically.

---

## Notes

- Tool stubs return deterministic results based on input hashing — swap for real API calls in production
- The RAG pipeline uses `all-MiniLM-L6-v2` embeddings — upgrade to `text-embedding-3-large` for production accuracy
- ChromaDB is ephemeral in development — use a hosted instance for persistence
- All tool calls are logged for audit trail compliance
- For production, consider adding: rate limiting, authentication, monitoring, alerting
- Memory management uses character-based token estimation — use `tiktoken` for accurate counting
- The `compare_agents.py` script runs the same query across all 3 backends for benchmarking
- For multi-user production systems, configure batching and scheduling in vLLM/SGLang
- For resource-constrained environments, use quantization flags when starting the server
