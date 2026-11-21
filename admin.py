import streamlit as st
from src.db import supabase
import pandas as pd
from datetime import datetime
from email_dispatcher import send_high_risk_email
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Admin Dashboard", layout="wide")

# ========== AUTHENTICATION & SESSION ==========
def check_authentication():
    """Return True if authenticated and session not expired."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.login_time = None
    
    if st.session_state.authenticated:
        # Check session expiry (30 minutes)
        if st.session_state.login_time and (datetime.now() - st.session_state.login_time).seconds > 1800:
            st.session_state.authenticated = False
            st.session_state.login_time = None
            st.rerun()
            return False
        return True
    return False

def log_admin_action(admin_name, ticket_id, action, details):
    """Log admin actions to audit_log table."""
    supabase.table("audit_log").insert({
        "agent_name": "admin_action",
        "request_id": str(uuid.uuid4()),
        "output": {"admin": admin_name, "ticket": ticket_id, "action": action, "details": details},
        "timestamp": datetime.now().isoformat()
    }).execute()

# ========== LOGIN PAGE ==========
if not check_authentication():
    st.title("🔐 Admin Login")
    password_input = st.text_input("Enter Admin Password", type="password")
    
    # Get correct password from secrets or .env
    try:
        correct_password = st.secrets.get("ADMIN_PASSWORD")
    except:
        correct_password = None
    if not correct_password:
        correct_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    if st.button("Login"):
        if password_input == correct_password:
            st.session_state.authenticated = True
            st.session_state.login_time = datetime.now()
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()  # Stop rendering until logged in

# ========== MAIN DASHBOARD ==========
st.title("🏛️ Admin Dashboard – CitizenVoice")

tab1, tab2, tab3 = st.tabs(["📋 Review Queue", "📊 All Tickets", "⚙️ Metrics"])

# ========== TAB 1: REVIEW QUEUE ==========
with tab1:
    st.subheader("High‑Risk / Unresolved Tickets")
    pending = supabase.table("tickets").select("*").eq("status", "pending_review").execute()
    if pending.data:
        for ticket in pending.data:
            with st.expander(f"{ticket['ticket_id']} – {ticket['sector'] or 'Unknown'}"):
                st.write(f"**Citizen Text:** {ticket['citizen_text']}")
                st.write("**Agent Predictions:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Intent: {ticket['intent']}")
                    st.write(f"Sector: {ticket['sector']}")
                with col2:
                    st.write(f"Priority: {ticket['priority']}")
                    st.write(f"Confidence: {ticket['confidence']}")
                
                with st.form(key=f"review_{ticket['ticket_id']}"):
                    new_sector = st.selectbox(
                        "Correct Sector",
                        ["Health","Education","Transport","Sanitation","Electricity","Water","PublicSafety","Infrastructure"],
                        index=0
                    )
                    new_priority = st.selectbox("Priority", ["P0","P1","P2","P3","P4"], index=2)
                    submitted = st.form_submit_button("Approve & Send")
                    
                    if submitted:
                        # Update ticket with corrections
                        supabase.table("tickets").update({
                            "sector": new_sector,
                            "priority": new_priority,
                            "status": "approved",
                            "human_corrections": {"sector": new_sector, "priority": new_priority}
                        }).eq("ticket_id", ticket["ticket_id"]).execute()
                        
                        # Log admin action
                        log_admin_action("admin", ticket["ticket_id"], "approve", f"Changed sector to {new_sector}, priority to {new_priority}")
                        
                        # Send email to department
                        email_sent = send_high_risk_email(ticket, corrections={"sector": new_sector, "priority": new_priority})
                        if email_sent:
                            supabase.table("tickets").update({
                                "email_sent": True,
                                "email_sent_at": datetime.now().isoformat()
                            }).eq("ticket_id", ticket["ticket_id"]).execute()
                            st.success(f"✅ Ticket {ticket['ticket_id']} approved and email sent to {new_sector} department.")
                        else:
                            st.warning(f"⚠️ Ticket updated but email failed. Check Brevo API key or department email mapping.")
                        st.rerun()
    else:
        st.info("No pending tickets.")

# ========== TAB 2: ALL TICKETS ==========
with tab2:
    st.subheader("All Submitted Tickets")
    all_tickets = supabase.table("tickets").select("*").order("created_at", desc=True).limit(100).execute()
    if all_tickets.data:
        df = pd.DataFrame(all_tickets.data)
        
        # Select columns to display
        display_cols = ["ticket_id", "citizen_text", "frequency", "sector", "priority", "risk_level", "status", "email_sent", "created_at"]
        df_display = df[display_cols].copy()
        
        # Define highlighting function
        def highlight_high_risk(row):
            if row['risk_level'] == 'high':
                return ['background-color: #ffcccc'] * len(row)
            else:
                return [''] * len(row)
        
        # Apply style
        styled_df = df_display.style.apply(highlight_high_risk, axis=1)
        
        # Display
        st.dataframe(styled_df, use_container_width=True)
        st.caption("💡 High‑risk complaints are highlighted in **light red**. Use the review queue tab for approval.")
    else:
        st.info("No tickets yet.")

# ========== TAB 3: METRICS ==========
with tab3:
    total = supabase.table("tickets").select("count", count="exact").execute()
    high = supabase.table("tickets").select("count", count="exact").eq("risk_level", "high").execute()
    st.metric("Total Complaints", total.count)
    st.metric("High‑Risk Pending", high.count)