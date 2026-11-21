# src/agents/urgency.py
import re
from src.state import AgentState

def urgency_agent(state: AgentState) -> AgentState:
    text = state["citizen_text"].lower()
    intent = state.get("intent", "")
    sector = state.get("sector", "")
    sentiment = state.get("sentiment", "")
    confidence = state.get("confidence", 0.0)
    
    # Default values
    priority = "P3"
    risk_level = "low"
    
    # Rule 1: Critical keywords (highest priority)
    urgent_keywords = ["death", "injury", "accident", "emergency", "danger", "safety", "critical"]
    if any(kw in text for kw in urgent_keywords):
        priority = "P0"
        risk_level = "high"
    
    # Rule 2: Health complaints (high risk)
    elif sector == "Health" and intent == "Complaint":
        priority = "P1"
        risk_level = "high"
    
    # Rule 3: Negative sentiment complaints (medium risk, depends on confidence)
    elif sentiment == "Negative" and intent == "Complaint":
        priority = "P2"
        if confidence < 0.8:
            risk_level = "high"
        else:
            risk_level = "low"
    
    # Rule 4: Low confidence complaints (except "Other")
    elif confidence < 0.7 and intent != "Other":
        priority = "P2"
        risk_level = "high"
    
    # Rule 5: Suggestions / Appreciation (low risk)
    elif intent in ["Suggestion", "Appreciation"]:
        priority = "P4"
        risk_level = "low"
    
    # Default: normal complaint
    else:
        priority = "P3"
        risk_level = "low"
    
    # Set needs_review based on final risk_level (do NOT override)
    state["needs_review"] = (risk_level == "high")
    state["priority"] = priority
    state["risk_level"] = risk_level
    
    return state