import json
import os
import datetime
import logging
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agents.state import AgentState, AgentExecutionTrace
from app.agents.tools import (
    fetch_merchant_margin_data,
    evaluate_transaction_risk_rules,
    format_user_deal_alert
)

logger = logging.getLogger(__name__)

# Initialize LLM with Gemini if API Key is configured, fallback to structured agent evaluation
google_api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0.1,
    google_api_key=google_api_key
) if google_api_key else None


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor / Orchestrator Node:
    Inspects current workflow state and dynamically routes execution to Agent A, B, or C, or FINISH.
    Enforces loop caps and max_steps circuit breaker.
    """
    step_count = state.get("step_count", 0) + 1
    max_steps = state.get("max_steps", 6)

    # 1. Circuit breaker check to prevent infinite agent loops
    if step_count >= max_steps:
        logger.warning(f"[Supervisor] Circuit breaker triggered! Reached max steps ({max_steps}). Finishing workflow.")
        trace: AgentExecutionTrace = {
            "step": step_count,
            "agent_name": "Supervisor",
            "action_taken": "Circuit breaker max steps reached -> Terminating flow",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        return {
            "next_step": "FINISH",
            "step_count": step_count,
            "execution_trace": [trace]
        }

    # 2. Sequential / Conditional Routing Logic
    # Workflow Pipeline: Fraud Check (Agent B) -> Merchant Intelligence (Agent A) -> Personalization (Agent C) -> FINISH
    
    if state.get("risk_score") is None or "risk_score" not in state:
        next_agent = "agent_fraud_risk"
    elif state.get("best_margin_path") is None:
        next_agent = "agent_merchant_intel"
    elif state.get("personalized_message_md") is None:
        next_agent = "agent_personalization"
    else:
        next_agent = "FINISH"

    trace: AgentExecutionTrace = {
        "step": step_count,
        "agent_name": "Supervisor",
        "action_taken": f"Routed to '{next_agent}'",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    return {
        "next_step": next_agent,
        "step_count": step_count,
        "execution_trace": [trace]
    }


def agent_fraud_risk_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent B: Fraud & Risk Scoring Agent.
    Evaluates transaction telemetry using deterministic rules and LLM validation.
    """
    sale_amount = state.get("gross_sale_amount", 0.0)
    velocity_seconds = state.get("click_to_conversion_seconds", 30)
    country = state.get("user_ip_country", "IND")

    # Call deterministic risk tool
    rules_json = evaluate_transaction_risk_rules.invoke({
        "sale_amount": sale_amount,
        "click_to_conversion_seconds": velocity_seconds,
        "user_ip_country": country
    })
    rule_results = json.loads(rules_json)

    risk_score = rule_results["risk_score"]
    risk_flagged = rule_results["risk_flagged"]
    reasons = rule_results["reasons"]

    # If LLM is available, enhance risk rationale evaluation
    if llm:
        try:
            prompt = f"Analyze risk factors for transaction: sale_amount=${sale_amount}, velocity={velocity_seconds}s, country={country}. Rule Findings: {reasons}. Provide 1 sentence risk summary."
            llm_response = llm.invoke(prompt)
            reasons.append(f"AI Audit: {llm_response.content}")
        except Exception as e:
            logger.warning(f"[Agent B] LLM evaluation skipped: {e}")

    trace: AgentExecutionTrace = {
        "step": state.get("step_count", 0),
        "agent_name": "Agent B (Fraud & Risk)",
        "action_taken": f"Calculated risk_score={risk_score}, flagged={risk_flagged}",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    return {
        "risk_score": risk_score,
        "risk_flagged": risk_flagged,
        "risk_reasons": reasons,
        "execution_trace": [trace]
    }


def agent_merchant_intel_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent A: Merchant Intelligence Agent.
    Extracts margin paths and active deals for target merchant.
    """
    merchant_slug = state.get("merchant_slug", "amazon")

    # Invoke Merchant Intel Tool
    intel_json = fetch_merchant_margin_data.invoke({"merchant_slug": merchant_slug})
    try:
        intel_data = json.loads(intel_json)
        deals = intel_data.get("active_promotions", [])
    except Exception:
        intel_data = {"error": intel_json}
        deals = []

    trace: AgentExecutionTrace = {
        "step": state.get("step_count", 0),
        "agent_name": "Agent A (Merchant Intelligence)",
        "action_taken": f"Fetched margin path for '{merchant_slug}'",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    return {
        "best_margin_path": intel_data,
        "recommended_deals": deals,
        "execution_trace": [trace]
    }


def agent_personalization_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent C: Personalization & Notification Agent.
    Generates rich markdown alert for the user.
    """
    user_id = state.get("user_id", "User")
    merchant_slug = state.get("merchant_slug", "Merchant")
    sale_amount = state.get("gross_sale_amount", 0.0)
    deals = state.get("recommended_deals", [])

    # Approximate cashback (70% of estimated 8% commission)
    estimated_cashback = sale_amount * 0.08 * 0.70

    # Call formatting tool
    markdown_message = format_user_deal_alert.invoke({
        "user_name": f"User {user_id[:8]}",
        "merchant_name": merchant_slug.upper(),
        "cashback_amount": estimated_cashback,
        "currency": "INR",
        "top_deals": deals
    })

    trace: AgentExecutionTrace = {
        "step": state.get("step_count", 0),
        "agent_name": "Agent C (Personalization & Alert)",
        "action_taken": "Generated personalized markdown deal alert",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    return {
        "personalized_message_md": markdown_message,
        "execution_trace": [trace]
    }
