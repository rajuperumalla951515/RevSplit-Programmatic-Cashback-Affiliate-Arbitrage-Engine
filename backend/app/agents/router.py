from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.agents.graph import agent_graph

router = APIRouter(tags=["Autonomous AI Agents"])


class AgentExecutionRequest(BaseModel):
    user_id: str
    merchant_slug: str
    gross_sale_amount: float = Field(..., gt=0)
    click_to_conversion_seconds: int = 30
    user_ip_country: str = "IND"
    thread_id: Optional[str] = "default_thread"


class AgentExecutionResponse(BaseModel):
    user_id: str
    merchant_slug: str
    risk_score: float
    risk_flagged: bool
    risk_reasons: List[str]
    best_margin_path: Optional[Dict[str, Any]]
    recommended_deals: List[Dict[str, Any]]
    personalized_message_md: Optional[str]
    execution_trace: List[Dict[str, Any]]


@router.post("/api/v1/agents/execute", response_model=AgentExecutionResponse, status_code=status.HTTP_200_OK)
async def execute_multi_agent_pipeline(request: AgentExecutionRequest):
    """
    FastAPI Bridge Endpoint:
    Triggers the LangGraph Orchestrator-Worker Multi-Agent Workflow asynchronously.
    Executes Fraud Risk Scoring (Agent B), Merchant Intelligence (Agent A), and Personalization (Agent C).
    """
    initial_state = {
        "user_id": request.user_id,
        "sub_id": None,
        "merchant_slug": request.merchant_slug,
        "gross_sale_amount": request.gross_sale_amount,
        "click_to_conversion_seconds": request.click_to_conversion_seconds,
        "user_ip_country": request.user_ip_country,
        "risk_score": None,
        "risk_flagged": False,
        "risk_reasons": [],
        "best_margin_path": None,
        "recommended_deals": [],
        "personalized_message_md": None,
        "next_step": "supervisor",
        "step_count": 0,
        "max_steps": 6,
        "messages": [],
        "execution_trace": []
    }

    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        final_state = await agent_graph.ainvoke(initial_state, config=config)

        return AgentExecutionResponse(
            user_id=final_state["user_id"],
            merchant_slug=final_state["merchant_slug"],
            risk_score=final_state.get("risk_score", 0.0),
            risk_flagged=final_state.get("risk_flagged", False),
            risk_reasons=final_state.get("risk_reasons", []),
            best_margin_path=final_state.get("best_margin_path"),
            recommended_deals=final_state.get("recommended_deals", []),
            personalized_message_md=final_state.get("personalized_message_md"),
            execution_trace=final_state.get("execution_trace", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-Agent Workflow Error: {str(e)}")
