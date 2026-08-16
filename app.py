import streamlit as st
import tempfile
import os
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PaddlePulse AI - Biomechanics Coach",
    page_icon="🏓",
    layout="wide"
)

# --- ADVANCED VIBRANT ATHLETIC TECH CSS ---
st.markdown("""
    <style>
    .main .block-container {
        background-color: #0A0F1D;
        color: #F8FAFC;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 800;
    }

    .auth-container {
        background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
        padding: 3rem 2.5rem;
        border-radius: 20px;
        border: 1px solid #312E81;
        box-shadow: 0 20px 40px -15px rgba(99, 102, 241, 0.3);
        max-width: 480px;
        margin: 4rem auto;
        text-align: center;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        padding: 1.25rem;
        border-radius: 14px;
        border: 1px solid #334155;
        text-align: center;
        box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, #06B6D4, #8B5CF6, #F97316);
    }
    .metric-val {
        font-size: 1.9rem;
        font-weight: 800;
        background: linear-gradient(90deg, #06B6D4, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.3rem;
    }

    .coaching-output {
        background: #111827;
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid #374151;
        color: #F3F4F6;
        line-height: 1.8;
        font-size: 1.05rem;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
    }

    div[data-testid="stFileUploader"] {
        background: #111827;
        border: 2px dashed #4F46E5;
        border-radius: 16px;
        padding: 1.5rem;
    }
    
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
    st.session_state.analysis_text = "Upload your gameplay video and click 'Run Comprehensive AI Video Analysis' to receive expert biomechanical feedback."

# --- AUTHENTICATION SCREEN ---
if not st.session_state.authenticated:
    st.markdown("""
        <div class="auth-container">
            <div style="display: flex; justify-content: center; margin-bottom: 1rem;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#8B5CF6" stroke-width="2" fill="#1E1B4B"/>
                    <path d="M7 14L12 9L17 14" stroke="#06B6D4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h1 style="font-size: 2rem; margin-bottom: 0.2rem; color: #FFFFFF;">PaddlePulse AI</h1>
            <p style="color: #94A3B8; margin-bottom: 2rem; font-size: 0.95rem;">Elite Computer Vision & Biomechanics Coaching Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.4, 1])
    with col_b:
        if st.button("🔵 Continue with Google", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Google Athlete"
            st.rerun()
            
        if st.button("🟣 Continue with Meta", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Meta Athlete"
            st.rerun()

        if st.button("👤 Continue as Guest", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Guest Athlete"
            st.rerun()
            
        st.markdown("<p style='text-align: center; color: #64748B; margin: 1.2rem 0 0.8rem 0; font-size: 0.85rem;'>or sign in with email</p>", unsafe_allow_html=True)
        email_input = st.text_input("Email address", placeholder="athlete@paddlepulse.ai", label_visibility="collapsed")
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
    st.error("API Key not found in secrets. Please configure it in your Streamlit Cloud settings.")

# --- SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="#06B6D4" stroke-width="2" fill="#1E1B4B"/>
                <path d="M8 12H16M12 8V16" stroke="#F97316" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <span style="font-size: 1.3rem; font-weight: 800; color: #FFFFFF;">PaddlePulse</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Logged in as:** `{st.session_state.user_name}`")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("## ⚙️ Coaching Parameters")
    shot_type = st.selectbox("Select Shot Type", ["Forehand Drive", "Backhand Slice", "Serve", "Dink", "Volley"])
    skill_level = st.slider("DUPR Skill Level", 1.0, 6.0, 3.5, 0.5)
    
    st.markdown("---")
    st.markdown("## 👥 Multi-Player Scope")
    analysis_scope = st.radio(
        "Evaluation Target",
        ["All players in video", "Specific player target"]
    )
    player_target = ""
    if analysis_scope == "Specific player target":
        player_target = st.text_input("Player description", placeholder="e.g. Near side player in blue shirt")

# --- MAIN APP HEADER ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("# 🏓 PaddlePulse AI Biomechanics Coach")
    st.markdown("<p style='color: #94A3B8; margin-top: -10px; font-size: 1.05rem;'>Instant multimodal video breakdown powered by Gemini 3.5 Flash.</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN LAYOUT ---
col_video, col_insights = st.columns([1.2, 1], gap="large")

with col_video:
    st.subheader("📹 High-Definition Match Footage")
    uploaded_video = st.file_uploader("Upload MP4 or MOV clip (up to 1 GB)", type=["mp4", "mov"])
    
    if uploaded_video:
        # Read bytes immediately to prevent stream consumption issues
        video_bytes = uploaded_video.read()
        st.video(video_bytes)
        
        if st.session_state.video_ref is None or uploaded_video.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("Processing high-def video stream with Gemini..."):
                try:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(video_bytes)
                    tfile.close()
                    
                    client = genai.Client(api_key=api_key)
                    st.session_state.video_ref = client.files.upload(file=tfile.name)
                    st.session_state.last_uploaded_name = uploaded_video.name
                    os.unlink(tfile.name)
                    st.success("Video successfully processed and ready!")
                except Exception as e:
                    st.error(f"Error processing video: {e}")

with col_insights:
    st.subheader("📊 Performance Telemetry")
    m1, m2, m3 = st.columns(3)
    
    metrics = [("Velocity", "44 MPH"), ("Spin Rate", "1.9k RPM"), ("Form Rating", "93/100")]
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

st.markdown(f"""
    <div class="coaching-output">
        {st.session_state.analysis_text}
    </div>
""", unsafe_allow_html=True)

# --- CLEAN FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.9rem;'>© 2026 PaddlePulse AI. Engineered for Peak Athletic Performance.</p>", unsafe_allow_html=True)
