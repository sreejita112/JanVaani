# src/agents/subcategory.py
import json
from src.state import AgentState
from src.llm_client import llm_client

# Map sector to possible subcategories
SUBCATEGORY_MAP = {
    "Health": ["Doctor availability", "Medicine stock", "Cleanliness", "Equipment failure", "Ambulance"],
    "Education": ["Teacher attendance", "Textbooks", "Infrastructure", "Mid-day meal"],
    "Transport": ["Road condition", "Traffic signals", "Public bus", "Parking"],
    "Sanitation": ["Garbage collection", "Drainage", "Public toilet"],
    "Electricity": ["Power outage", "Voltage fluctuation", "Bill issues"],
    "Water": ["Supply disruption", "Quality", "Pipeline leakage"],
    "PublicSafety": ["Police response", "Street lighting", "Crime"],
}

def subcategory_agent(state: AgentState) -> AgentState:
    sector = state.get("sector", "General")
    options = SUBCATEGORY_MAP.get(sector, ["General"])
    
    system_prompt = f"""You are a government grievance classifier. Choose the most appropriate subcategory from: {options}
Output JSON: {{"subcategory": "selected subcategory", "confidence": 0.9}}"""
    
    user_prompt = f"Feedback: {state['citizen_text']}\nSector: {sector}"
    
    response, latency, error = llm_client.call_with_fallback(system_prompt, user_prompt)
    
    if error or not response:
        state["subcategory"] = options[0] if options else "General"
        state["confidence"] *= 0.9
    else:
        try:
            parsed = json.loads(response.strip())
            state["subcategory"] = parsed.get("subcategory", options[0])
        except:
            state["subcategory"] = options[0]
    
    return state