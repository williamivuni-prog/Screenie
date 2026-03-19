# 🔍 Screenie: Career Intelligence Platform

Screenie is an AI-powered ATS (Applicant Tracking System) simulator designed to help job seekers optimize their resumes. By leveraging Google's Gemini API, Screenie instantly compares a user's resume against a specific job description, generating a match score and actionable feedback.

### 🚀 Tech Stack
* **Frontend:** Streamlit (Python)
* **AI/LLM:** Google Gemini 3.1 Flash-Lite API
* **Database:** Supabase (PostgreSQL)
* **Document Parsing:** PyPDF

### ✨ Features
* **Instant ATS Scoring:** Upload a PDF resume and paste a job description to get a compatibility score out of 100%.
* **AI Feedback:** Receive targeted, actionable advice on missing keywords and formatting improvements.
* **History Vault:** Automatically saves past scans to a connected Supabase database, accessible via a sleek, native UI dashboard.

### 💡 Local Setup
To run this project locally, you will need to add a `.env` file to the root directory with the following API keys:
* `GEMINI_API_KEY`
* `SUPABASE_URL`
* `SUPABASE_KEY`
