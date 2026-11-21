# src/utils.py
import re
import streamlit as st
from src.db import supabase
from datetime import datetime, timedelta
import numpy as np
from sentence_transformers import SentenceTransformer

# Cache embedding model globally
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def find_similar_ticket(text: str, threshold: float = 0.85):
    """
    Find an existing ticket semantically similar to the given text.
    Returns the ticket dict if found, otherwise None.
    """
    model = get_embedding_model()
    query_embedding = model.encode(text).tolist()
    
    # Using pgvector cosine similarity
    response = supabase.rpc(
        'find_similar_tickets',
        {
            'query_embedding': query_embedding,
            'similarity_threshold': threshold,
            'days_back': 30
        }
    ).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None

def find_existing_ticket(text: str):
    """Return existing ticket dict if exact match found in last 30 days."""
    text_clean = text.strip().lower()
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    tickets = supabase.table("tickets").select("id, ticket_id, citizen_text, frequency, related_reports").gte("created_at", cutoff).execute()
    for ticket in tickets.data:
        existing_text = ticket["citizen_text"].strip().lower()
        if existing_text == text_clean:
            return ticket
    return None

def show_highlighted_message(msg: str, msg_type: str = "info"):
    styles = {
        "success": {"bg": "#d4edda", "border": "#28a745", "icon": "✅", "text_color": "#155724"},
        "error":   {"bg": "#f8d7da", "border": "#dc3545", "icon": "❌", "text_color": "#721c24"},
        "warning": {"bg": "#fff3cd", "border": "#ffc107", "icon": "⚠️", "text_color": "#856404"},
        "info":    {"bg": "#e8f4f8", "border": "#1f77b4", "icon": "ℹ️", "text_color": "#0c4e6e"},
    }
    s = styles.get(msg_type, styles["info"])
    st.markdown(f"""
    <div style="background-color: {s['bg']}; border-left: 5px solid {s['border']}; 
                padding: 1rem; border-radius: 10px; color: {s['text_color']}; margin: 1rem 0;">
        {s['icon']} <strong>{msg}</strong>
    </div>
    """, unsafe_allow_html=True)

def is_rate_limited(ip: str) -> tuple[bool, str]:
    """Stub – rate limiting is now handled in user_ui.py via session state.
       This function is kept only to avoid import errors if any code still uses it.
    """
    return False, ""

def has_prompt_injection(text: str) -> bool:
    text_lower = text.lower()
    patterns = [
        "ignore previous", "forget your", "system prompt", "you are now",
        "act as", "pretend to be", "override", "disregard", "new instruction"
    ]
    return any(p in text_lower for p in patterns)

def is_valid_feedback(text: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message) and automatically shows highlighted message if invalid."""
    text = text.strip()
    
    if len(text) < 10:
        msg = "Please provide more details (at least 10 characters)."
        show_highlighted_message(msg, "error")
        return False, msg
    
    if len(set(text)) < 3:
        msg = "Your feedback appears to contain only repeated characters. Please write a meaningful description."
        show_highlighted_message(msg, "error")
        return False, msg
    
    if re.search(r'(.)\1{5,}', text):
        msg = "Please avoid typing repeated characters. Describe your issue clearly."
        show_highlighted_message(msg, "error")
        return False, msg
    
    words = text.split()
    if len(words) < 3:
        msg = "Please describe your feedback in at least a few words."
        show_highlighted_message(msg, "error")
        return False, msg
    
    has_vowel_word = any(re.search(r'[aeiouAEIOU]', word) for word in words)
    if not has_vowel_word:
        msg = "Your feedback doesn't look like a real sentence. Please explain your concern."
        show_highlighted_message(msg, "error")
        return False, msg
    
    return True, ""

def is_duplicate(text: str) -> tuple[bool, str]:
    """Check if exact duplicate exists in last 30 days."""
    text_clean = text.strip().lower()
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    existing = supabase.table("tickets").select("ticket_id, citizen_text").gte("created_at", cutoff).execute()
    for ticket in existing.data:
        existing_text = ticket["citizen_text"].strip().lower()
        if existing_text == text_clean:
            return True, ticket["ticket_id"]
    return False, None