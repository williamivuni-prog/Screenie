import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
from pypdf import PdfReader
from streamlit_pdf_viewer import pdf_viewer
import google.generativeai as genai

# --- 1. CONFIGURATION & SECURE LOAD ---
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '.env'))

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SB_URL = os.getenv("SUPABASE_URL")
SB_KEY = os.getenv("SUPABASE_KEY")

if not all([GEMINI_KEY, SB_URL, SB_KEY]):
    st.error("Missing API Keys! Check your .env file.")
    st.stop()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('models/gemini-3.1-flash-lite-preview')

# Clean, wide layout with the native sidebar fully hidden
st.set_page_config(page_title="Screenie", layout="wide", initial_sidebar_state="collapsed")

# --- 2. SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "show_balloons" not in st.session_state:
    st.session_state.show_balloons = False

# --- 3. DATABASE HELPERS ---
def save_to_supabase(job_url, score, feedback):
    url = f"{SB_URL}/rest/v1/analyses"
    headers = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json"}
    payload = {"job_url": job_url, "score": score, "feedback": feedback[:500]}
    try: requests.post(url, headers=headers, json=payload, timeout=5)
    except: pass

def get_history():
    url = f"{SB_URL}/rest/v1/analyses?select=*&order=created_at.desc&limit=10"
    headers = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        return data if isinstance(data, list) else []
    except: return []

# --- 4. LIQUID GLASS & TAB STYLING ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        background-image: 
            radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.35) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.35) 0px, transparent 50%),
            radial-gradient(at 50% 50%, rgba(236, 72, 153, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(124, 58, 237, 0.25) 0px, transparent 50%);
        color: #FFFFFF;
    }
    
    /* Hide default Streamlit headers */
    header, [data-testid="stHeader"] {
        display: none !important; visibility: hidden !important;
    }
    
    /* Glass form styling */
    .stTextArea textarea, .stFileUploader, [data-testid="stMetric"], .stInfo, .stExpander {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(40px) saturate(200%) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        color: white !important;
    }

    /* Style the native tabs to match the theme */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px 12px 0 0;
        padding: 10px 25px;
        color: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: none;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(59, 130, 246, 0.2);
        color: #FFFFFF;
        border-bottom: 2px solid #3b82f6;
    }

    div.stButton > button {
        background: #FFFFFF !important; color: #000 !important;
        border-radius: 100px !important; font-weight: 800 !important;
        width: 100%; border: none !important; padding: 15px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255,255,255,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. HEADER ---
st.markdown("<h1 style='text-align: center; margin-top: 20px; font-size: 4rem; letter-spacing: -3px;'>Screenie</h1>", unsafe_allow_html=True)
st.caption("<p style='text-align:center; color:#888; margin-top:-20px;'>Career Intelligence Platform</p>", unsafe_allow_html=True)
st.write("---")

# --- 6. MAIN CONTENT (THE TABS) ---
_, center, _ = st.columns([1, 2, 1])

with center:
    tab1, tab2 = st.tabs(["🔍 Scanner", "🕒 History Vault"])

    # ====== TAB 1: THE SCANNER ======
    with tab1:
        uploaded_file = st.file_uploader("Upload Resume", type="pdf", label_visibility="collapsed")
        if uploaded_file:
            with st.expander("📄 View My Resume", expanded=False):
                pdf_viewer(input=uploaded_file.getvalue(), width=None, height=None)

        st.write("##")
        job_input = st.text_area("Job Details", placeholder="Paste Link or Description...", height=120, label_visibility="collapsed")
        
        if st.button("Analyze Experience"):
            if uploaded_file and job_input:
                with st.spinner("Decoding Requirements..."):
                    final_text = job_input
                    if job_input.strip().startswith("http"):
                        try:
                            r = requests.get(f"https://r.jina.ai/{job_input.strip()}", timeout=10)
                            final_text = r.text if r.status_code == 200 else job_input
                        except: pass
                    
                    reader = PdfReader(uploaded_file)
                    resume_text = "".join([p.extract_text() for p in reader.pages])
                    
                    prompt = f"Act as an ATS. Compare Resume and Job. Return format: SCORE: [num]% followed by FEEDBACK: [analysis]. Resume: {resume_text} Job: {final_text}"
                    resp = model.generate_content(prompt).text
                    
                    try: score = int(''.join(filter(str.isdigit, resp.split("SCORE:")[1].split()[0])))
                    except: score = 0
                    
                    fb = resp.split("FEEDBACK:")[1] if "FEEDBACK:" in resp else resp
                    
                    # Update Memory and Database
                    st.session_state.analysis_result = {"score": score, "feedback": fb}
                    save_to_supabase(job_input if job_input.startswith("http") else "Manual Entry", score, fb)
                    
                    st.session_state.show_balloons = True
                    time.sleep(1) # Let the DB catch up before we render the UI
                    st.rerun()
            else:
                st.error("Missing input data!")

        # THE VERDICT & BALLOONS
        if st.session_state.show_balloons:
            st.balloons()
            st.session_state.show_balloons = False

        if st.session_state.analysis_result:
            res = st.session_state.analysis_result
            st.divider()
            
            if res['score'] >= 70:
                st.success("✅ **ATS APPROVED**")
            else:
                st.error("⚠️ **NOT ATS APPROVED**")

            st.metric("Match Score", f"{res['score']}%")
            st.progress(res['score'] / 100)
            st.info(res['feedback'])

    # ====== TAB 2: THE HISTORY VAULT ======
    with tab2:
        st.write("##")
        history = get_history()
        
        if history:
            for item in history:
                # Color code the score: Green for >= 70, Red for anything lower
                score_color = "#4ade80" if item.get('score', 0) >= 70 else "#f87171"
                
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.05); padding:15px 20px; border-radius:12px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.1); display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <small style="color:#888;">{item.get('created_at','')[:10]}</small><br>
                        <a href='{item.get('job_url','#')}' target='_blank' style='color:#3b82f6; text-decoration:none; font-weight:600;'>View Source Link ↗</a>
                    </div>
                    <div>
                        <h2 style='margin:0; color: {score_color};'>{item.get('score', 0)}%</h2>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No history found. Run your first scan to populate the vault!")