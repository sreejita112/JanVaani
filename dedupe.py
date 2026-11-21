# src/agents/dedupe.py
from sentence_transformers import SentenceTransformer
from src.db import supabase
import numpy as np

# Cache model
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model
def dedupe_agent(state):
    import re
    text = re.sub(r'[^\w\s]', '', state["citizen_text"].strip().lower())
    existing = supabase.table("tickets").select("ticket_id").execute()
    for row in existing.data:
        existing_text = re.sub(r'[^\w\s]', '', row.get("citizen_text", "").lower())
        if existing_text == text:
            state["duplicate_of"] = row["ticket_id"]
            break
    return state