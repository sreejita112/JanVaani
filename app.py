import streamlit as st
import uuid
import base64
from datetime import datetime
from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph import graph
from src.db import supabase
from src.utils import (
    show_highlighted_message,
    is_valid_feedback,
    find_similar_ticket,
    get_embedding_model,
    has_prompt_injection
)

# ---------- Helper: Detect appreciation quickly ----------
def is_appreciation(text: str) -> bool:
    text_lower = text.lower()
    keywords = [
        "beautiful", "well done", "thank", "great", "excellent", "love", 
        "appreciate", "fantastic", "wonderful", "amazing", "good job", "proud"
    ]
    return any(kw in text_lower for kw in keywords)

# ---------- Background image ----------
def get_base64_of_bin_file(relative_path):
    script_dir = Path(__file__).parent
    full_path = script_dir / relative_path
    with open(full_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = "../images/bg1.png"
try:
    img_base64 = get_base64_of_bin_file(img_path)
    bg_image = f"url(data:image/png;base64,{img_base64})"
except FileNotFoundError:
    bg_image = "#1f77b4"

# ---------- Page config ----------
st.set_page_config(page_title="Citizen Grievance Portal", page_icon="🏛️", layout="centered")

# ---------- CSS styling ----------
st.markdown(f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), {bg_image};
        background-size: cover;
        background-attachment: fixed;
    }}
    .main-header {{
        text-align: center;
        color: white;
        padding: 2rem;
        background-color: rgba(0,0,0,0.7);
        border-radius: 10px;
        margin-bottom: 2rem;
    }}
    .main-header h1 {{
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }}
    .main-header p {{
        font-size: 1.1rem;
    }}
    .stTextArea textarea, .stTextInput input {{
        background-color: rgba(255,255,255,0.95);
        border-radius: 8px;
    }}
    .note-box {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-left: 5px solid #1f77b4;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 0.9rem;
    }}
    .stTextInput label, .stTextArea label {{
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.25rem !important;
    }}
    .stCheckbox label {{
        color: white !important;
        font-size: 1rem !important;
        font-weight: 400 !important;
        margin-left: 0.5rem !important;
    }}
    .stCheckbox .st-bw {{
        background-color: rgba(255,255,255,0.9) !important;
        border-radius: 3px !important;
    }}
    div[data-testid="stForm"] .stCheckbox {{
        background-color: rgba(255, 255, 255, 1);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin-top: 0.5rem;
    }}
    footer {{
        text-align: center;
        color: white;
        margin-top: 3rem;
        font-size: 0.8rem;
    }}
</style>
""", unsafe_allow_html=True)

# ---------- Header & notes ----------
st.markdown("""
<div class="main-header">
    <h1>🏛️ CitizenVoice – Government Grievance Portal</h1>
    <p>Your voice matters. Report issues, share suggestions, or appreciate good work.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="note-box">
    📌 <strong>Important Notes:</strong><br>
    • Please provide accurate and respectful feedback.<br>
    • High‑urgency complaints (safety, health, infrastructure) will be prioritised.<br>
    • You will receive a unique ticket ID for tracking.<br>
    • Optional contact details help us follow up if needed.
</div>
""", unsafe_allow_html=True)

# ---------- Form ----------
with st.form("citizen_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name (optional)", placeholder="e.g., Rajesh Kumar")
    with col2:
        email = st.text_input("Email (optional)", placeholder="you@example.com")
    phone = st.text_input("Phone (optional)", placeholder="98765 43210")
    
    complaint_text = st.text_area(
        "Your feedback *",
        height=200,
        placeholder="Describe your complaint, suggestion, or appreciation in detail...",
        help="Mention location, dates, and any relevant details."
    )
    
    consent = st.checkbox("I consent to the collection and processing of my personal data for grievance redressal as per the privacy policy.")
    
    submitted = st.form_submit_button("Submit Feedback", type="primary", use_container_width=True)

# ---------- Submit handling ----------
if submitted:
    # 1. Consent
    if not consent:
        show_highlighted_message("You must consent to proceed.", "error")
        st.stop()
    
    # 2. Empty input
    if not complaint_text.strip():
        show_highlighted_message("Please enter your feedback before submitting.", "error")
        st.stop()
    
    # 3. Input validation
    is_valid, _ = is_valid_feedback(complaint_text)
    if not is_valid:
        st.stop()
    
    # 4. Prompt injection
    if has_prompt_injection(complaint_text):
        show_highlighted_message("Invalid input detected. Please provide genuine feedback.", "error")
        st.stop()
    
    # 5. Session rate limiting
    if "submission_count" not in st.session_state:
        st.session_state.submission_count = 0
        st.session_state.first_submission_time = datetime.now()
    
    if st.session_state.submission_count >= 5:
        elapsed = (datetime.now() - st.session_state.first_submission_time).total_seconds()
        if elapsed < 3600:
            show_highlighted_message("Too many submissions. Please try again later.", "error")
            st.stop()
        else:
            st.session_state.submission_count = 0
            st.session_state.first_submission_time = datetime.now()
    
    # ---------- Check if it's an appreciation (skip duplicate detection) ----------
    appreciation_flag = is_appreciation(complaint_text)
    
    if appreciation_flag:
        # Skip duplicate check entirely
        existing = None
    else:
        # Only check for duplicates for non‑appreciation
        existing = find_similar_ticket(complaint_text, threshold=0.85)
    
    if existing:
        # Duplicate found (only for complaints/suggestions)
        new_freq = existing['frequency'] + 1
        current_reports = existing.get('related_reports', [])
        if isinstance(current_reports, str):
            import json
            current_reports = json.loads(current_reports) if current_reports else []
        
        new_report = {"reported_at": datetime.now().isoformat()}
        if name:
            new_report["name"] = name
        if email:
            new_report["email"] = email
        if phone:
            new_report["phone"] = phone
        current_reports.append(new_report)
        
        supabase.table("tickets").update({
            "frequency": new_freq,
            "related_reports": current_reports
        }).eq("id", existing['id']).execute()
        
        show_highlighted_message(
            f"✅ This issue has been reported {new_freq} times. Your report added to Ticket #{existing['ticket_id']}.",
            "info"
        )
        st.session_state.submission_count += 1
        st.stop()
    
    # ---------- Create new ticket ----------
    ticket_id = f"CV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    initial_state = {
        "ticket_id": ticket_id,
        "citizen_text": complaint_text.strip(),
        "citizen_name": name if name else None,
        "citizen_email": email if email else None,
        "citizen_phone": phone if phone else None,
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
    
    with st.spinner("Processing your feedback..."):
        try:
            final_state = graph.invoke(initial_state)
            
            result = supabase.table("tickets").insert({
                "ticket_id": final_state["ticket_id"],
                "citizen_text": final_state["citizen_text"],
                "citizen_name": final_state.get("citizen_name"),
                "citizen_email": final_state.get("citizen_email"),
                "citizen_phone": final_state.get("citizen_phone"),
                "intent": final_state.get("intent"),
                "sentiment": final_state.get("sentiment"),
                "sector": final_state.get("sector"),
                "subcategory": final_state.get("subcategory"),
                "priority": final_state.get("priority"),
                "risk_level": final_state.get("risk_level"),
                "confidence": final_state.get("confidence"),
                "duplicate_of": final_state.get("duplicate_of"),
                "human_corrections": final_state.get("human_corrections"),
                "email_sent": final_state.get("email_sent", False),
                "status": "pending_review" if final_state.get("needs_review") else "auto_classified",
                "frequency": 1,
                "related_reports": [],
                "created_at": datetime.now().isoformat()
            }).execute()
            
            ticket_uuid = result.data[0]['id']
            model = get_embedding_model()
            embedding = model.encode(complaint_text.strip()).tolist()
            supabase.table("embeddings").insert({
                "ticket_id": ticket_uuid,
                "embedding": embedding
            }).execute()
            
            # ---------- Custom message for appreciation ----------
            if final_state.get("intent") == "Appreciation" or appreciation_flag:
                show_highlighted_message("🙏 Thank you for your kind words and appreciation!", "success")
            else:
                show_highlighted_message(f"Ticket ID: {ticket_id} – Your feedback has been recorded.", "success")
            
            # Additional follow-up for high risk
            if final_state.get("risk_level") == "high":
                show_highlighted_message("This is a high‑priority complaint and will be reviewed soon.", "warning")
            elif final_state.get("intent") not in ["Appreciation"]:
                show_highlighted_message("Your feedback has been automatically categorised. No further action needed.", "info")
            
            st.session_state.submission_count += 1
                
        except Exception as e:
            show_highlighted_message(f"An error occurred. Please try again later. (Ref: {ticket_id})", "error")
            print(f"Error: {e}")

# ---------- Footer ----------
st.markdown("""
<footer>
    © 2026 CitizenVoice | Government | All feedback is confidential.
</footer>
""", unsafe_allow_html=True)