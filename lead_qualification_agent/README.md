# Lead Qualification Agent

An AI agent for qualifying inbound banking leads using **RAG**, **MCP**, and **embeddings**. Qualifies leads from web, chat, and referrals by gathering information, scoring intent, and routing to appropriate sales teams.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Lead Qualification Agent                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Lead       │  │    Lead      │  │ Qualification│         │
│  │  Management  │  │   Scoring    │  │  Criteria    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │ Conversation │  │   Calendar   │  │    Sales     │         │
│  │  Analysis    │  │   Booking    │  │  Playbooks   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │Notifications │  │     CRM      │  │    RAG       │         │
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
- **Qualification Criteria** — BANT, CHAMP, MEDDIC frameworks
- **Sales Playbooks** — Inbound, outbound, referral, digital workflows
- **Lead Scoring Models** — Demographic, behavioral, firmographic scoring
- **Conversion Patterns** — What converts, conversion rates by channel
- **Product Eligibility** — Requirements by product type
- **Compliance Rules** — TCPA, DNC, consent requirements
- **Competitor Intelligence** — Market positioning and counter-strategies

### MCP Tools (40+ tools)

| Category | Tools | Description |
|----------|-------|-------------|
| **Lead Management** | `create_lead`, `get_lead`, `update_lead`, `search_leads`, `convert_lead`, `close_lead`, `lead_pipeline`, `overdue_follow_ups` | Full lead lifecycle |
| **Lead Scoring** | `score_lead`, `score_leads_batch`, `scoring_model`, `update_scoring_weights` | Multi-model scoring |
| **Qualification** | `evaluate_lead`, `qualification_checklist`, `qualification_frameworks` | BANT/CHAMP/MEDDIC evaluation |
| **Conversation** | `analyze_conversation`, `conversation_history`, `intent_keywords` | Intent and signal detection |
| **Calendar** | `book_consultation`, `available_slots`, `cancel_appointment`, `reschedule`, `list_appointments`, `list_advisors` | Consultation booking |
| **Notifications** | `send_notification`, `send_welcome`, `send_follow_up`, `send_qualified`, `send_reminder`, `notification_history`, `templates` | Multi-channel outreach |
| **CRM** | `create_account`, `get_account`, `update_account`, `log_activity`, `crm_activities`, `crm_pipeline`, `search_accounts` | Salesforce-style CRM |
| **Playbooks** | `get_sales_playbook`, `all_playbooks`, `handle_objection`, `conversation_starters` | Guided sales workflows |
| **RAG** | `knowledge_search` | Search qualification knowledge |

### Lead Scoring Model

| Factor | Weight | Scoring Rules |
|--------|--------|---------------|
| Demographic | 35% | Age 25-45 (+25), Income $100K+ (+25), Credit 750+ (+20), Homeowner (+15) |
| Behavioral | 35% | Pages 5+ (+25), Calculator (+25), Application started (+35) |
| Intent | 30% | Referral (+30), Chat (+25), Webinar (+20), High-intent product (+25) |

### Lead Tiers

| Tier | Score Range | Action |
|------|-------------|--------|
| Hot | 80-100 | Route to senior advisor immediately |
| Warm | 60-79 | Route to sales team |
| Cool | 40-59 | Add to nurture campaign |
| Cold | 0-39 | Add to database for future outreach |

### Agent Capabilities
- **Guardrails** — Eligibility checks, scoring thresholds
- **Human-in-the-Loop** — Approval for high-value leads
- **Memory** — Conversation context tracking
- **Streaming** — Real-time qualification output
- **TCPA Compliance** — DNC checking, consent tracking

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

# Lead Qualification Parameters
MIN_LEAD_SCORE=30
AUTO_QUALIFY_SCORE=80
ROUTING_THRESHOLD=60
```

## Qualification Flow

```
Inbound Lead
    │
    ├─→ Acknowledge within 5 minutes
    │
    ├─→ Gather Information (name, interest, source)
    │
    ├─→ Score Lead (demographic + behavioral + intent)
    │
    ├─→ Qualify against Framework (BANT/CHAMP/MEDDIC)
    │
    ├─→ Check Product Eligibility (credit, income, age)
    │
    ├─→ Determine Tier (hot/warm/cool/cold)
    │
    ├─→ Route or Nurture
    │     ├─ Hot → Senior Advisor (book consultation)
    │     ├─ Warm → Sales Team
    │     ├─ Cool → Nurture Campaign
    │     └─ Cold → Database
    │
    └─→ Execute Sales Playbook
          ├─ Mortgages → Mortgage Playbook
          ├─ Credit Cards → Card Shopper Playbook
          ├─ Savings → Savings Seeker Playbook
          └─ Investments → Investment Curious Playbook
```

## Project Structure

```
lead_qualification_agent/
├── server.py                      # MCP server with 40+ tools
├── rag_pipeline.py                # RAG engine (7 collections)
├── config.py                      # Settings
├── seed_knowledge.py              # Qualification knowledge base
├── compare_agents.py              # Compare Ollama/vLLM/SGLang
├── requirements.txt
├── README.md
├── llm/
│   ├── base_agent.py              # Guardrails, HITL, memory
│   ├── agent_ollama.py            # Ollama
│   ├── agent_vllm.py              # vLLM
│   └── agent_sglang.py            # SGLang
└── tools/
    ├── lead_management.py         # Lead lifecycle
    ├── lead_scoring.py            # Multi-model scoring
    ├── qualification_criteria.py  # BANT/CHAMP/MEDDIC
    ├── conversation_analysis.py   # Intent detection
    ├── calendar_booking.py        # Consultation scheduling
    ├── notifications.py           # Outreach
    ├── crm.py                     # Salesforce-style CRM
    └── sales_playbooks.py         # Guided workflows
```
