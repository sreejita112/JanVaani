# src/agents/sector.py
import json
from src.state import AgentState
from src.llm_client import llm_client

SYSTEM_PROMPT = """You are a government grievance classifier. Classify the feedback into one sector.

Allowed sectors: Health, Education, Transport, Sanitation, Electricity, Water, PublicSafety, Infrastructure, General

Output ONLY JSON: {"sector": "selected sector", "confidence": 0.95}"""

def sector_agent(state: AgentState) -> AgentState:
    user_prompt = f"Feedback: {state['citizen_text']}\nIntent: {state.get('intent', 'Unknown')}"
    
    response, latency, error = llm_client.call_with_fallback(SYSTEM_PROMPT, user_prompt)
    
    if error or not response:
        state["sector"] = "General"
        state["confidence"] = min(state["confidence"], 0.5)
        state["needs_review"] = True
        state["errors"].append(f"Sector agent failed: {error}")
        return state
    
    try:
        parsed = json.loads(response.strip())
        state["sector"] = parsed.get("sector", "General")
        # Combine confidence (average of intent and sector confidence)
        sector_conf = parsed.get("confidence", 0.8)
        state["confidence"] = (state["confidence"] + sector_conf) / 2
    except:
        state["sector"] = "General"
        state["confidence"] *= 0.8
        state["needs_review"] = True
    
    return state