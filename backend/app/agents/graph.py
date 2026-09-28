import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.nodes import (
    supervisor_node,
    agent_fraud_risk_node,
    agent_merchant_intel_node,
    agent_personalization_node
)

logger = logging.getLogger(__name__)


def route_next_step(state: AgentState) -> Literal["agent_fraud_risk", "agent_merchant_intel", "agent_personalization", "__end__"]:
    """Conditional Edge Evaluator based on supervisor decision."""
    next_step = state.get("next_step", "FINISH")
    if next_step == "agent_fraud_risk":
        return "agent_fraud_risk"
    elif next_step == "agent_merchant_intel":
        return "agent_merchant_intel"
    elif next_step == "agent_personalization":
        return "agent_personalization"
    else:
        return "__end__"


def build_arbitrage_agent_graph():
    """
    Builds the production Orchestrator-Worker Multi-Agent Graph for RevSplit.
    """
    builder = StateGraph(AgentState)

    # 1. Add Agent & Orchestrator Nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("agent_fraud_risk", agent_fraud_risk_node)
    builder.add_node("agent_merchant_intel", agent_merchant_intel_node)
    builder.add_node("agent_personalization", agent_personalization_node)

    # 2. Entrypoint
    builder.set_entry_point("supervisor")

    # 3. Add Conditional Routing Edges from Supervisor
    builder.add_conditional_edges(
        "supervisor",
        route_next_step,
        {
            "agent_fraud_risk": "agent_fraud_risk",
            "agent_merchant_intel": "agent_merchant_intel",
            "agent_personalization": "agent_personalization",
            "__end__": END
        }
    )

    # 4. Worker Nodes return back to Supervisor to check next state (Supervisor-Worker Pattern)
    builder.add_edge("agent_fraud_risk", "supervisor")
    builder.add_edge("agent_merchant_intel", "supervisor")
    builder.add_edge("agent_personalization", "supervisor")

    # 5. Checkpointer for state persistence & fault-tolerant resumption
    memory_checkpointer = MemorySaver()

    # Compile Executable Graph
    compiled_graph = builder.compile(checkpointer=memory_checkpointer)
    logger.info("LangGraph Arbitrage Multi-Agent System compiled successfully.")
    return compiled_graph


# Instantiated Singleton Graph
agent_graph = build_arbitrage_agent_graph()
