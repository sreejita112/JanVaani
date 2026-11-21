import json
from src.state import AgentState
from src.llm_client import llm_client

SYSTEM_PROMPT = """You are an AI assistant for a government grievance system. Classify the citizen's feedback.

Output ONLY a JSON object with these fields:
{
    "intent": "Complaint" or "Suggestion" or "Appreciation" or "Other",
    "sentiment": "Positive" or "Neutral" or "Negative",
    "confidence": a number between 0 and 1 (how certain you are)
}

Do not add any other text or explanation."""

def extract_json(text: str) -> dict:
    """Extract JSON from LLM response (handles markdown etc.)"""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())

def rule_based_intent(text: str) -> tuple[str, str, float]:
    """Fallback when LLM fails – uses keyword rules."""
    text_lower = text.lower()
    appreciation = ["beautiful", "well done", "thank", "great", "excellent", "love",
                    "appreciate", "fantastic", "wonderful", "amazing", "good job",
                    "proud", "impressed", "quick", "fast", "responsive", "helpful",
                    "professional", "satisfied", "grateful", "outstanding", "superb",
                    "commend", "brilliant", "perfect", "nice", "lovely", "pleased"]
    if any(kw in text_lower for kw in appreciation):
        return "Appreciation", "Positive", 0.85
    suggestion = ["should", "suggest", "recommend", "improve", "add", "enhance", "propose",
                  "it would be better", "could be", "need more", "install", "build"]
    if any(kw in text_lower for kw in suggestion):
        return "Suggestion", "Neutral", 0.75
    complaint = ["no", "lack", "missing", "problem", "issue", "bad", "poor", "broken",
                 "failure", "wrong", "not working", "delay", "shortage", "unavailable"]
    if any(kw in text_lower for kw in complaint) or len(text) > 5:
        return "Complaint", "Negative", 0.65
    return "Other", "Neutral", 0.5

def intent_agent(state: AgentState) -> AgentState:
    user_prompt = f"Citizen feedback: {state['citizen_text']}"

    # 1. LLM generates intent
    response, latency, error = llm_client.call_with_fallback(SYSTEM_PROMPT, user_prompt)
    
    if error or not response:
        # fallback to rule‑based 
        intent, sentiment, conf = rule_based_intent(state["citizen_text"])
        state["intent"] = intent
        state["sentiment"] = sentiment
        state["confidence"] = conf
        state["needs_review"] = conf < 0.7
        state["errors"].append(f"Intent agent fallback (LLM failed): {error}")
        return state
    
    # 2. Extract JSON from LLM output
    try:
        parsed = extract_json(response)
        state["intent"] = parsed.get("intent", "Other")
        state["sentiment"] = parsed.get("sentiment", "Neutral")
        state["confidence"] = parsed.get("confidence", 0.5)
    except json.JSONDecodeError as e:
        # If LLM returns invalid JSON, use rule-based fallback as safety
        intent, sentiment, conf = rule_based_intent(state["citizen_text"])
        state["intent"] = intent
        state["sentiment"] = sentiment
        state["confidence"] = conf
        state["needs_review"] = True
        state["errors"].append(f"Intent agent JSON parse error: {e}, used fallback")    
    return state