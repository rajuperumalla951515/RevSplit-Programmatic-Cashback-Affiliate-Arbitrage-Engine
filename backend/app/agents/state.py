from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator


class AgentExecutionTrace(TypedDict):
    step: int
    agent_name: str
    action_taken: str
    timestamp: str


class AgentState(TypedDict):
    """
    Typed State Dictionary for RevSplit Multi-Agent Orchestrator.
    Passed between Supervisor Node and Worker Agents (Merchant Intel, Fraud Risk, Personalization).
    """
    user_id: str
    sub_id: Optional[str]
    merchant_slug: Optional[str]
    gross_sale_amount: float
    click_to_conversion_seconds: int
    user_ip_country: str
    
    # Financial & Risk State
    risk_score: float                  # 0.0 (Safe) to 1.0 (Critical Risk)
    risk_flagged: bool
    risk_reasons: List[str]
    
    # Intelligence & Recommendations State
    best_margin_path: Optional[Dict[str, Any]]
    recommended_deals: List[Dict[str, Any]]
    personalized_message_md: Optional[str]
    
    # Orchestrator & Safety Control
    next_step: str                     # "agent_merchant_intel", "agent_fraud_risk", "agent_personalization", "FINISH"
    step_count: int                    # Circuit breaker step counter
    max_steps: int                     # Maximum allowed steps (default: 6)
    messages: Annotated[List[Dict[str, Any]], operator.add]
    execution_trace: Annotated[List[AgentExecutionTrace], operator.add]
