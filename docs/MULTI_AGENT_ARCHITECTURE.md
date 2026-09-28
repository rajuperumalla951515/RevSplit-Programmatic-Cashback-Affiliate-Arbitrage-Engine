# RevSplit Autonomous Multi-Agent AI System

## Architecture & Technical Specification

RevSplit incorporates an **Orchestrator-Worker (Supervisor)** Multi-Agent AI architecture built on **LangGraph**. It acts as an intelligent decision-making layer that operates asynchronously over incoming transaction events and user clicks.

---

## 1. Multi-Agent System Diagram

```
                               ┌───────────────────────────┐
                               │   FastAPI / Kafka Event   │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   Supervisor Node         │
                               │   (Orchestrator Router)   │
                               └─────────────┬─────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               │ Conditional Edge            │ Conditional Edge            │ Conditional Edge
               ▼                             ▼                             ▼
   ┌───────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
   │ Agent B: Fraud & Risk │     │ Agent A: Merchant     │     │ Agent C:              │
   │ Scoring Agent         │     │ Intelligence Agent    │     │ Personalization Agent │
   └───────────┬───────────┘     └───────────┬───────────┘     └───────────┬───────────┘
               │                             │                             │
               └─────────────────────────────┼─────────────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │  State Checkpointer       │
                               │  (Memory / Postgres)      │
                               └───────────────────────────┘
```

---

## 2. Agent Roles & Technical Responsibilities

### Supervisor (Orchestrator Node)
- **Role**: Inspects current `AgentState`, determines execution path, enforces maximum step limits (`max_steps=6`), and prevents runaway execution loops.
- **Routing Rules**:
  - `risk_score is None` $\rightarrow$ Route to **Agent B (Fraud & Risk)**
  - `best_margin_path is None` $\rightarrow$ Route to **Agent A (Merchant Intelligence)**
  - `personalized_message_md is None` $\rightarrow$ Route to **Agent C (Personalization)**
  - All completed or `step_count >= max_steps` $\rightarrow$ Route to `__end__` (FINISH)

### Agent A: Merchant Intelligence Agent
- **Role**: Evaluates e-commerce merchant margin tables, extracts best commission splits, and finds active promo codes.
- **Tools Used**: `fetch_merchant_margin_data`

### Agent B: Fraud & Risk Scoring Agent
- **Role**: Hybrid deterministic rule engine + LLM evaluator analyzing conversion velocity, transaction anomalies, and geo-mismatches.
- **Output**: Risk score between 0.0 (Safe) and 1.0 (Critical Risk), flag status, and risk rationale list.
- **Tools Used**: `evaluate_transaction_risk_rules`

### Agent C: Personalization & Notification Agent
- **Role**: Generates markdown alert templates with user name, pending cashback earned, and handpicked deals.
- **Tools Used**: `format_user_deal_alert`

---

## 3. Circuit Breakers & Checkpointing
- **State Checkpointer**: Uses `MemorySaver` to checkpoint graph state at every step. If a node fails, execution can resume from the last saved state using `thread_id`.
- **Step Limit Cap**: Enforces `max_steps` constraint to guarantee deterministic termination and protect LLM token budget.
