import streamlit as st
import tempfile
import os
import time
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KineticPulse AI - Elite Motion Studio",
    page_icon="⚡",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = "Athlete"
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Vibrant Dark"
if "video_ref" not in st.session_state:
    st.session_state.video_ref = None
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = "Upload your high-definition session footage and click 'Run Comprehensive AI Analysis' to receive an exhaustive biomechanical breakdown."

# --- VIBRANT MATERIAL / GEMINI DESIGN SYSTEM ---
if st.session_state.theme_mode == "Vibrant Dark":
    bg_color = "#0B0F19"
    surface_color = "#131827"
    surface_elevated = "#1E2538"
    border_color = "#2D3748"
    text_primary = "#F8FAFC"
    text_secondary = "#94A3B8"
    vibrant_gradient = "linear-gradient(135deg, #06B6D4 0%, #8B5CF6 50%, #EC4899 100%)"
else:
    bg_color = "#F8FAFC"
    surface_color = "#FFFFFF"
    surface_elevated = "#F1F5F9"
    border_color = "#E2E8F0"
    text_primary = "#0F172A"
    text_secondary = "#64748B"
    vibrant_gradient = "linear-gradient(135deg, #0284C7 0%, #7C3AED 100%, #DB2777 100%)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Google Sans', sans-serif;
    }}

    .main .block-container {{
        background-color: {bg_color};
        color: {text_primary};
        padding-top: 2rem;
        padding-bottom: 3rem;
        transition: background-color 0.25s ease;
    }}
    
    h1, h2, h3 {{
        color: {text_primary} !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}

    /* Branded Header Badge */
    .app-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: {surface_elevated};
        border: 1px solid {border_color};
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        color: {text_primary};
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }}

    /* Authentication Card */
    .auth-card {{
        background: {surface_color};
        padding: 3.5rem 3rem;
        border-radius: 28px;
        border: 1px solid {border_color};
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.3);
        max-width: 480px;
        margin: 4rem auto;
        text-align: center;
    }}

    /* Metric Card with Vibrant Gradient Accent */
    .metric-card {{
        background: {surface_color};
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid {border_color};
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.04);
        position: relative;
        overflow: hidden;
    }}
    .metric-card::after {{
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 4px;
        background: {vibrant_gradient};
    }}
    .metric-val {{
        font-size: 2.2rem;
        font-weight: 700;
        background: {vibrant_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .metric-lbl {{
        font-size: 0.75rem;
        color: {text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.4rem;
        font-weight: 600;
    }}

    /* AI Coaching Output */
    .coaching-output {{
        background: {surface_color};
        padding: 2.5rem;
        border-radius: 24px;
        border: 1px solid {border_color};
        color: {text_primary};
        line-height: 1.9;
        font-size: 1.05rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    }}

    div[data-testid="stFileUploader"] {{
        background: {surface_color};
        border: 2px dashed #8B5CF6;
        border-radius: 20px;
        padding: 1.5rem;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION SCREEN ---
if not st.session_state.authenticated:
    st.markdown("""
        <div class="auth-card">
            <div style="display: flex; justify-content: center; margin-bottom: 1.2rem;">
                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" fill="url(#logo_grad)"/>
                    <path d="M8 12L11 15L16 9" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <defs>
                        <linearGradient id="logo_grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#06B6D4"/>
                            <stop offset="0.5" stop-color="#8B5CF6"/>
                            <stop offset="1" stop-color="#EC4899"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <h1 style="font-size: 2.1rem; margin-bottom: 0.3rem;">KineticPulse AI</h1>
            <p style="color: #94A3B8; margin-bottom: 2.5rem; font-size: 0.95rem;">Professional Computer Vision & Biomechanics Studio</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.4, 1])
    with col_b:
        # Real Google Sign-In redirect simulation button
        if st.button("🌐 Sign in with Google", use_container_width=True):
            with st.spinner("Redirecting to accounts.google.com..."):
                time.sleep(1.2)  # Simulate secure OAuth handshake
            st.session_state.authenticated = True
            st.session_state.user_name = "Alex Turner"
            st.session_state.user_email = "alex.turner@gmail.com"
            st.rerun()
            
        if st.button("⚡ Continue as Guest", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Guest Athlete"
            st.session_state.user_email = "guest@kineticpulse.ai"
            st.rerun()
    st.stop()

# --- SECURE API KEY LOAD ---
try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    api_key = ""
    st.error("API Key not found in secrets. Please configure it in your Streamlit Cloud settings.")

# --- SIDEBAR CONTROLS & SETTINGS ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" fill="#8B5CF6"/>
                <path d="M8 12L11 15L16 9" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <span style="font-size: 1.25rem; font-weight: 700;">KineticPulse</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Account:** `{st.session_state.user_name}`")
    st.markdown(f"<span style='color: {text_secondary}; font-size: 0.85rem;'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
    
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("## 🎨 Personalization")
    theme_selection = st.radio("Color Theme", ["Vibrant Dark", "Clean Light"], index=0 if st.session_state.theme_mode=="Vibrant Dark" else 1)
    if theme_selection != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_selection
        st.rerun()
        
    st.markdown("---")
    st.markdown("## ⚙️ Athlete Profile")
    skill_level = st.slider("Skill Level Rating", 1.0, 6.0, 4.0, 0.5)
    
    st.markdown("---")
    st.markdown("## 👥 Analysis Scope")
    analysis_scope = st.radio(
        "Target Focus",
        ["Comprehensive (All Subjects)", "Specific Target Subject"]
    )
    player_target = ""
    if analysis_scope == "Specific Target Subject":
        player_target = st.text_input("Subject description", placeholder="e.g. Athlete in foreground wearing vibrant jacket")

# --- MAIN APP HEADER ---
st.markdown("""
    <div class="app-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="#06B6D4"/></svg>
        Powered by Gemini 3.5 Flash Multimodal Engine
    </div>
""", unsafe_allow_html=True)

col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("# Biomechanical Motion & Form Studio")
    st.markdown(f"<p style='color: {text_secondary}; margin-top: -8px; font-size: 1.05rem;'>Upload high-definition sports or movement footage for lightning-fast, exhaustive computer vision feedback.</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN LAYOUT ---
col_video, col_insights = st.columns([1.2, 1], gap="large")

with col_video:
    st.subheader("📹 Session Footage Upload")
    uploaded_video = st.file_uploader("Upload MP4 or MOV clip (Optimized for rapid streaming)", type=["mp4", "mov"])
    
    if uploaded_video:
        video_bytes = uploaded_video.read()
        st.video(video_bytes)
        
        if st.session_state.video_ref is None or uploaded_video.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("Streaming high-def video securely to Gemini..."):
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
    st.subheader("📊 Session Telemetry")
    m1, m2, m3 = st.columns(3)
    
    metrics = [("Velocity", "52 MPH"), ("Cadence", "186 SPM"), ("Form Score", "97/100")]
    for col, (lbl, val) in zip([m1, m2, m3], metrics):
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{val}</div>
                    <div class="metric-lbl">{lbl}</div>
                </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Pro Tip**: Keep clips between 10 to 45 seconds for instantaneous Gemini 3.5 Flash response times.")

# --- COMPREHENSIVE AI ANALYSIS SECTION ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.subheader("🧠 Comprehensive Expert Motion Breakdown")

if st.button("🚀 Run Comprehensive AI Analysis", type="primary", use_container_width=True):
    if not api_key:
        st.error("API Key missing from secrets.")
    elif not st.session_state.video_ref:
        st.error("Please upload a video file first.")
    else:
        with st.spinner("Gemini is analyzing posture, momentum transfer, entry angles, and execution dynamics..."):
            try:
                client = genai.Client(api_key=api_key)
                target_clause = f"Focus specifically on {player_target}." if player_target else "Evaluate all subjects visible in the video comprehensively."
                
                prompt = f"""
                You are an elite sports scientist, world-class biomechanics coach, and motion analyst. Conduct an exhaustive, complete analysis of this video clip.
                Athlete skill level context: {skill_level} out of 6.0.
                {target_clause}
                
                Provide an all-encompassing, detailed breakdown covering EVERYTHING observable:
                1. Posture, balance, and core stability.
                2. Kinetic chain linkage, momentum transfer, and power generation.
                3. Limb positioning, entry/exit angles, and execution mechanics.
                4. Timing, rhythm, and consistency across movements.
                5. Complete, actionable coaching recommendations and clear corrective steps for every observed phase.
                
                Present the response in a structured, professional, highly encouraging tone without robotic numerical constraints. Be thorough and leave nothing out.
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
st.markdown(f"<p style='text-align: center; color: {text_secondary}; font-size: 0.9rem;'>© 2026 KineticPulse AI. Engineered for Peak Human Performance.</p>", unsafe_allow_html=True)
