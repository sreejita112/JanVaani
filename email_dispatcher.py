import os
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = "aiswaryababy91@gmail.com"
SENDER_NAME = "CitizenVoice Grievance Portal"

# Map sector to department email addresses (update for production)
DEPT_EMAILS = {
    "Health": "aiswarya180@gmail.com",
    "Education": "education@city.gov",
    "Transport": "roads@city.gov",
    "Sanitation": "sanitation@city.gov",
    "Electricity": "power@city.gov",
    "Water": "water@city.gov",
    "PublicSafety": "police@city.gov",
    "Infrastructure": "infra@city.gov",
    "General": "admin@city.gov"
}

def send_high_risk_email(ticket: dict, corrections: dict = None) -> bool:
    """
    Send email to the appropriate department for a high‑risk complaint.
    Requests a written explanation to be sent back to the grievance team.
    Returns True if sent successfully, False otherwise.
    """
    if corrections is None:
        corrections = {}
    
    sector = corrections.get("sector", ticket.get("sector", "General"))
    priority = corrections.get("priority", ticket.get("priority", "P2"))
    
    # SLA mapping (hours)
    sla_map = {"P0": 4, "P1": 24, "P2": 72, "P3": 120, "P4": 168}
    sla_hours = sla_map.get(priority, 48)
    
    # Department email
    to_email = DEPT_EMAILS.get(sector, DEPT_EMAILS["General"])
    
    subject = f"[URGENT {priority}] Explanation Required: {sector} - {ticket.get('subcategory', 'General')}"
    
    # Plain text version
    body_text = f"""
OFFICIAL GRIEVANCE NOTIFICATION – EXPLANATION REQUIRED ASAP
===========================================================

Ticket ID: {ticket['ticket_id']}
Priority: {priority} (SLA: {sla_hours} hours)
Sector: {sector}
Subcategory: {ticket.get('subcategory', 'General')}

CITIZEN COMPLAINT:
{ticket['citizen_text']}

CONTACT DETAILS (for follow-up):
Name: {ticket.get('citizen_name', 'Anonymous')}
Phone: {ticket.get('citizen_phone', 'Not provided')}
Email: {ticket.get('citizen_email', 'Not provided')}

ACTION REQUIRED – URGENT:

1. Investigate the above complaint immediately.
2. Send a written explanation / action taken report to:
   ⇒ grievances@citizenvoice.gov
   ⇒ Subject line: "Explanation for Ticket {ticket['ticket_id']}"

Deadline: Within {sla_hours} hours of this email.

This is an auto-generated message. Do not reply directly to this email.
Send your explanation to the address above.
"""
    
    # HTML version
    body_html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
<div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
    <div style="background: #dc3545; color: white; padding: 20px; text-align: center;">
        <h2 style="margin: 0;">⚠️ URGENT – Explanation Required</h2>
        <p style="margin: 5px 0 0;">Action Required Within {sla_hours} Hours</p>
    </div>
    <div style="padding: 20px;">
        <p><strong>Ticket ID:</strong> {ticket['ticket_id']}<br>
        <strong>Priority:</strong> {priority}<br>
        <strong>Sector:</strong> {sector}<br>
        <strong>Subcategory:</strong> {ticket.get('subcategory', 'General')}</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0;">
            <strong>📝 Citizen Complaint:</strong><br>
            {ticket['citizen_text']}
        </div>
        
        <div style="background: #e8f4f8; padding: 15px; margin: 15px 0;">
            <strong>📞 Citizen Contact (for follow-up):</strong><br>
            Name: {ticket.get('citizen_name', 'Anonymous')}<br>
            Phone: {ticket.get('citizen_phone', 'Not provided')}<br>
            Email: {ticket.get('citizen_email', 'Not provided')}
        </div>
        
        <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107;">
            <strong>✅ IMMEDIATE ACTION REQUIRED:</strong><br><br>
            <strong>1.</strong> Investigate this complaint without delay.<br>
            <strong>2.</strong> Send a written explanation / action taken report to:<br>
            &nbsp;&nbsp;&nbsp;<strong>grievances@citizenvoice.gov</strong><br>
            &nbsp;&nbsp;&nbsp;Subject line: <strong>"Explanation for Ticket {ticket['ticket_id']}"</strong><br>
            <strong>3.</strong> Deadline: Within <strong>{sla_hours} hours</strong> of this email.
        </div>
        
        <p style="font-size: 12px; color: #666; margin-top: 20px;">
            This is an auto-generated message. Do not reply directly.<br>
            Send your explanation to the email address above.
        </p>
    </div>
</div>
</body>
</html>
"""
    
    # Prepare Brevo API request
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": body_html,
        "textContent": body_text
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 201:
            print(f"✅ Email sent to {to_email} for ticket {ticket['ticket_id']}")
            print(f"Brevo response: {response.text}")
            return True
        else:
            print(f"❌ Brevo error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Email exception: {e}")
        return False