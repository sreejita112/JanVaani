# JanVaani– AI-Powered Government Grievance Portal

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1.0-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**GRIEVAIJanVaani** is a complete multi-agent system that automates the classification,deduplication,routibg, and escalation of citizen feedback,ideas, and complaints. Built entirely on free tiers from Groq,Gemini,Supabase,Brevo, and Streamlit, it offers a production-ready pilot at zero recurring monthly expenses.

- **Citizen submission** – government‑themed web form with validation, consent, and rate limiting.  
- **Multi‑agent AI** – LangGraph orchestrates intent, sector, subcategory, urgency, and deduplication agents.  
- **Semantic deduplication** – embeddings (`sentence-transformers`) + `pgvector` group similar complaints and increment a frequency counter.  
- **Human‑in‑the‑Loop (HITL)** – admin dashboard to review high‑risk tickets, correct predictions, and approve email dispatch.  
- **Automated email** – Brevo sends an actionable email to the responsible department, requesting a written explanation (no dashboard login required).  
- **Security** – session‑based rate limiting, prompt injection detection, consent checkbox, admin session expiry, audit logs.

---

## 📦 Tech Stack

| Area | Technology |
|------|------------|
| Frontend | Streamlit |
| Multi‑agent orchestration | LangGraph |
| LLM providers | Groq (primary), Gemini (fallback), keyword fallback |
| Embeddings | Sentence‑Transformers (`all-MiniLM-L6-v2`) |
| Vector & relational DB | Supabase `pgvector` + PostgreSQL |
| Email | Brevo (Sendinblue) free tier |
| Deployment | Streamlit Cloud / AWS EC2 free tier |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com) account (free tier)
- API keys from [Groq](https://console.groq.com), [Google Gemini](https://aistudio.google.com), and [Brevo](https://brevo.com)
- (Optional) Git

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/JanVaani.git
cd JanVaani
```

## 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Set up environment variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GROQ_API_KEY_A=your-groq-key
GEMINI_API_KEY_A=your-gemini-key
BREVO_API_KEY=your-brevo-key
ADMIN_PASSWORD=your-secure-password
```

For cloud deployment (Streamlit Cloud), add these as secrets instead (TOML format).

## 5. Configure Supabase

Run the provided SQL script (see `supabase/schema.sql` in the repository) to:

* Create tables: `tickets`, `embeddings`, `review_queue`, `audit_log`, `rate_limit`
* Enable the vector extension
* Create the `find_similar_tickets` function for semantic deduplication

## 6. Run the application

```bash
streamlit run src/app.py
```

* Open `http://localhost:8501` – Citizen submission form
* Open `http://localhost:8501/admin` – Admin dashboard (password from `.env`)

# 🧠 How It Works

1. Citizen submits feedback via the web form (optional name/email/phone, consent checkbox).

2. Input is validated (length, gibberish, prompt injection) and rate‑limited (5 submissions/hour per session).

3. Semantic deduplication compares the embedding with existing tickets (last 30 days).

4. If a similar issue is found:

   * Frequency is incremented
   * Citizen contact info is appended to `related_reports`
   * No new ticket is created

5. If the complaint is new, the multi‑agent pipeline runs sequentially:

### Intent Agent

* Classifies intent (`Complaint`, `Suggestion`, `Appreciation`)
* Detects sentiment (`Positive`, `Neutral`, `Negative`)
* Assigns confidence score

### Sector Agent

Maps the complaint to one of the following sectors:

* Health
* Education
* Transport
* Sanitation
* Electricity
* Water
* PublicSafety
* Infrastructure
* General

### Subcategory Agent

Selects a sector‑specific subcategory.

Example:

* `Doctor availability` → Health

### Urgency & Risk Agent

Assigns:

* Priority (`P0`–`P4`)
* `risk_level` (`high` or `low`)

Based on:

* Keywords
* Sector
* Sentiment
* Confidence

6. High‑risk tickets (`risk_level = high`) are placed in the review queue (`status = pending_review`).

7. Low‑risk tickets are auto‑classified and stored without human review.

8. Admin logs in to the dashboard, reviews pending high‑risk tickets, corrects sector/priority if needed, and clicks `Approve & Send`.

9. Email is dispatched via Brevo to the department responsible (mapped by sector), asking for a written explanation and including SLA deadlines.

10. The email is self‑contained – the department does not need to log into any dashboard.

11. Audit log records every admin approval for compliance.


🔐 Security & Compliance

Session‑based rate limiting – 5 submissions per hour per browser session.
Prompt injection detection – blocks malicious inputs like “ignore previous instructions”.
Consent checkbox – citizens must agree to data processing before submission.
Admin session expiry – automatic logout after 30 minutes of inactivity.
Audit log – every admin approval is recorded in the audit_log table.
Environment variables / secrets – all API keys and passwords are kept outside the codebase.