import streamlit as st
import tempfile
import os
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Pickleball Biomechanics Coach",
    page_icon="🏓",
    layout="wide"
)

# --- MODERN ATHLETIC TECH CSS & STYLING ---
st.markdown("""
    <style>
    /* Global Theme */
    .main .block-container {
        background-color: #0F172A; /* Deep Slate Background */
        color: #F8FAFC;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700;
    }

    /* Auth Card Styling */
    .auth-card {
        background: #1E293B;
        padding: 2.5rem;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        max-width: 450px;
        margin: 5rem auto;
        text-align: center;
    }
    
    /* Sleek KPI Cards */
    .metric-card {
        background: #1E293B;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38BDF8; /* Bright Cyan Accent */
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* Coaching Breakdown Box */
    .coaching-output {
        background: #1E293B;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #334155;
        color: #E2E8F0;
        line-height: 1.7;
        font-size: 1rem;
    }

    /* Upload Box Polish */
    div[data-testid="stFileUploader"] {
        background: #1E293B;
        border: 2px dashed #475569;
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = "Athlete"
if "video_ref" not in st.session_state:
    st.session_state.video_ref = None
if "active_shot" not in st.session_state:
    st.session_state.active_shot = "Forehand Drive"
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = "Upload your gameplay video and click 'Run AI Analysis' to receive expert biomechanical feedback."

# --- AUTHENTICATION SCREEN ---
if not st.session_state.authenticated:
    st.markdown("""
        <div class="auth-card">
            <h1 style="font-size: 1.8rem; margin-bottom: 0.5rem;">🏓 PickleSync AI</h1>
            <p style="color: #94A3B8; margin-bottom: 2rem;">Sign in to access your elite biometric coaching dashboard.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("🔵 Continue with Google", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Shivansh"
            st.rerun()
            
        if st.button("📘 Continue with Meta", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Shivansh"
            st.rerun()
            
        st.markdown("<p style='text-align: center; color: #64748B; margin: 1rem 0;'>or sign in with email</p>", unsafe_allow_html=True)
        email_input = st.text_input("Email address", placeholder="athlete@pickleball.com", label_visibility="collapsed")
        if st.button("Sign In with Email", type="primary", use_container_width=True):
            if email_input:
                st.session_state.authenticated = True
                st.session_state.user_name = email_input.split("@")[0].capitalize()
                st.rerun()
            else:
                st.warning("Please enter a valid email address.")
    st.stop()

# --- SECURE API KEY LOAD ---
try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    api_key = ""
    st.error("API Key not found in secrets. Please configure it.")

# --- SIDEBAR NAVIGATION & SETTINGS ---
with st.sidebar:
    st.markdown(f"### 👋 Welcome, {st.session_state.user_name}")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("## ⚙️ Coaching Controls")
    shot_type = st.selectbox("Select Shot Type", ["Forehand Drive", "Backhand Slice", "Serve", "Dink", "Volley"])
    skill_level = st.slider("DUPR Skill Level", 1.0, 6.0, 3.5, 0.5)
    
    st.markdown("---")
    st.markdown("## 👥 Match Scope")
    analysis_scope = st.radio(
        "Evaluation Target",
        ["All players in video", "Specific player target"]
    )
    player_target = ""
    if analysis_scope == "Specific player target":
        player_target = st.text_input("Player description", placeholder="e.g. Near side player in blue")

# --- MAIN APP INTERFACE ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("🏓 AI Pickleball Biomechanics Coach")
    st.markdown("<p style='color: #94A3B8; margin-top: -10px;'>Multimodal AI performance analysis powered by Gemini Flash.</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Layout: Video Upload & Preview (Left) vs Metrics & Focus (Right)
col_video, col_insights = st.columns([1.2, 1], gap="large")

with col_video:
    st.subheader("📹 Gameplay Footage (Up to 1 GB)")
    uploaded_video = st.file_uploader("Drag and drop MP4 or MOV file here", type=["mp4", "mov"])
    
    if uploaded_video:
        st.video(uploaded_video)
        
        if st.session_state.video_ref is None or uploaded_video.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("Processing video upload securely..."):
                try:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(uploaded_video.read())
                    tfile.close()
                    
                    client = genai.Client(api_key=api_key)
                    st.session_state.video_ref = client.files.upload(file=tfile.name)
                    st.session_state.last_uploaded_name = uploaded_video.name
                    os.unlink(tfile.name)
                    st.success("Video ready for analysis!")
                except Exception as e:
                    st.error(f"Error processing video: {e}")

with col_insights:
    st.subheader("📊 Session Quick Metrics")
    m1, m2, m3 = st.columns(3)
    
    metrics = [("Velocity", "42 MPH"), ("Spin Rate", "1.8k RPM"), ("Form Rating", "91/100")]
    for col, (lbl, val) in zip([m1, m2, m3], metrics):
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{val}</div>
                    <div class="metric-lbl">{lbl}</div>
                </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚡ Instant Shot Switcher")
    s_col1, s_col2 = st.columns(2)
    
    with s_col1:
        if st.button("Forehand Drive", use_container_width=True):
            st.session_state.active_shot = "Forehand Drive"
    with s_col2:
        if st.button("Backhand Slice", use_container_width=True):
            st.session_state.active_shot = "Backhand Slice"
            
    st.info(f"Active Focus: **{st.session_state.active_shot}** (Switch instantly without re-uploading)")

# --- AI ANALYSIS SECTION ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.subheader("🧠 Expert Coaching Breakdown")

if st.button("🚀 Run Comprehensive AI Video Analysis", type="primary", use_container_width=True):
    if not api_key:
        st.error("API Key missing from secrets.")
    elif not st.session_state.video_ref:
        st.error("Please upload a video file first.")
    else:
        with st.spinner(f"Analyzing motion for {st.session_state.active_shot}..."):
            try:
                client = genai.Client(api_key=api_key)
                target_clause = f"Focus specifically on {player_target}." if player_target else "Evaluate players visible in the video."
                
                prompt = f"""
                You are an elite, encouraging pickleball coach and biomechanics expert. Analyze this video clip focusing on a {st.session_state.active_shot}. 
                Player skill level: DUPR {skill_level}.
                {target_clause}
                
                Provide feedback in a warm, simple, and natural conversational tone. Avoid rigid numerical angle commands (e.g. 'go to 45 degrees'). Instead, explain mechanical concepts simply and clearly, highlighting strengths and giving 2-3 practical tips for instant improvement.
                """
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[st.session_state.video_ref, prompt]
                )
                
                st.session_state.analysis_text = response.text
                
            except Exception as e:
                st.session_state.analysis_text = f"An error occurred during AI processing: {e}"

# Display AI Coaching Output in sleek card
st.markdown(f"""
    <div class="coaching-output">
        {st.session_state.analysis_text}
    </div>
""", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
c_f1, c_f2 = st.columns([3, 1])
with c_f1:
    st.markdown("© 2026 Shivansh Singla. All rights reserved.")
with c_f2:
    st.markdown("Privacy Policy | Terms")
