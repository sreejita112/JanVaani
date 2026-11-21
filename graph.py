from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agents.intent import intent_agent
from src.agents.sector import sector_agent
from src.agents.subcategory import subcategory_agent
from src.agents.urgency import urgency_agent
from src.agents.dedupe import dedupe_agent   # import your dedupe agent

builder = StateGraph(AgentState)

# Add all nodes
builder.add_node("dedupe", dedupe_agent)
builder.add_node("intent", intent_agent)
builder.add_node("sector", sector_agent)
builder.add_node("subcategory", subcategory_agent)
builder.add_node("urgency", urgency_agent)

# Set entry point to dedupe (only once!)
builder.set_entry_point("dedupe")

# Define edges
builder.add_edge("dedupe", "intent")
builder.add_edge("intent", "sector")
builder.add_edge("sector", "subcategory")
builder.add_edge("subcategory", "urgency")
builder.add_edge("urgency", END)

graph = builder.compile()