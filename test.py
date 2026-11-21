# # test_intent.py
# import sys
# sys.path.insert(0, "src")

# import os
# from dotenv import load_dotenv
# load_dotenv()

# # Check API keys
# if not os.getenv("GROQ_API_KEY_A"):
#     print("❌ GROQ_API_KEY not found in .env")
#     sys.exit(1)

# from state import AgentState
# from agents.intent import intent_agent

# initial_state: AgentState = {
#     "ticket_id": "TEST-001",
#     "citizen_text": "The primary health center has no doctor for two weeks",
#     "citizen_name": None,
#     "citizen_email": None,
#     "citizen_phone": None,
#     "intent": None,
#     "sentiment": None,
#     "sector": None,
#     "subcategory": None,
#     "priority": None,
#     "risk_level": None,
#     "confidence": 0.0,
#     "duplicate_of": None,
#     "embedding": None,
#     "needs_review": False,
#     "human_corrections": {},
#     "email_sent": False,
#     "retry_count": 0,
#     "errors": []
# }

# result = intent_agent(initial_state)
# print(f"Intent: {result['intent']}")
# print(f"Sentiment: {result['sentiment']}")
# print(f"Confidence: {result['confidence']}")
# print(f"Errors: {result['errors']}")


import sys
sys.path.insert(0, "src")

from src.state import AgentState
from src.graph import graph

initial_state: AgentState = {
    "ticket_id": "TEST-001",
    "citizen_text": "The primary health center has no doctor for two weeks, pregnant women suffer",
    "citizen_name": None,
    "citizen_email": None,
    "citizen_phone": None,
    "intent": None,
    "sentiment": None,
    "sector": None,
    "subcategory": None,
    "priority": None,
    "risk_level": None,
    "confidence": 0.0,
    "duplicate_of": None,
    "embedding": None,
    "needs_review": False,
    "human_corrections": {},
    "email_sent": False,
    "retry_count": 0,
    "errors": []
}

result = graph.invoke(initial_state)
print(f"Intent: {result['intent']}")
print(f"Sector: {result['sector']}")
print(f"Subcategory: {result['subcategory']}")
print(f"Priority: {result['priority']}")
print(f"Risk: {result['risk_level']}")
print(f"Confidence: {result['confidence']}")