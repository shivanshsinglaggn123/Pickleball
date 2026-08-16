import streamlit as st
import tempfile
import os
import time
from google import genai

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KineticPulse AI — Elite Motion Studio",
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
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "main"
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Vibrant Obsidian"
if "video_ref" not in st.session_state:
    st.session_state.video_ref = None
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = "Upload your high-definition session footage and click 'Run Comprehensive AI Analysis' to receive an exhaustive, professional-grade biomechanical breakdown."

# --- PREMIUM DESIGN SYSTEM ---
if st.session_state.theme_mode == "Vibrant Obsidian":
    bg_color = "#070B14"
    surface_color = "#0F1626"
    surface_elevated = "#1A2338"
    border_color = "#2A3859"
    text_primary = "#F8FAFC"
    text_secondary = "#94A3B8"
    accent_gradient = "linear-gradient(135deg, #00F2FE 0%, #4FACFE 50%, #6366F1 100%)"
    card_shadow = "0 25px 50px -12px rgba(0, 0, 0, 0.7)"
else:
    bg_color = "#F8FAFC"
    surface_color = "#FFFFFF"
    surface_elevated = "#F1F5F9"
    border_color = "#E2E8F0"
    text_primary = "#0F172A"
    text_secondary = "#64748B"
    accent_gradient = "linear-gradient(135deg, #0284C7 0%, #7C3AED 50%, #DB2777 100%)"
    card_shadow = "0 20px 40px -10px rgba(0, 0, 0, 0.08)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Poppins', 'Google Sans', sans-serif;
    }}

    .main .block-container {{
        background-color: {bg_color};
        color: {text_primary};
        padding-top: 2.5rem;
        padding-bottom: 3.5rem;
        transition: background-color 0.3s ease;
    }}
    
    h1, h2, h3 {{
        color: {text_primary} !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}

    .auth-card {{
        background: {surface_color};
        padding: 3.5rem 3rem;
        border-radius: 32px;
        border: 1px solid {border_color};
        box-shadow: {card_shadow};
        max-width: 480px;
        margin: 3rem auto;
        text-align: center;
        backdrop-filter: blur(10px);
        animation: slideInUp 0.5s ease-out;
    }}

    @keyframes slideInUp {{
        from {{ transform: translateY(20px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}

    .app-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: {surface_elevated};
        border: 1px solid {border_color};
        padding: 10px 20px;
        border-radius: 32px;
        font-size: 0.85rem;
        font-weight: 600;
        color: {text_primary};
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }}

    .app-badge:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 28px rgba(99, 102, 241, 0.3);
    }}

    .metric-card {{
        background: {surface_color};
        padding: 2rem 1.5rem;
        border-radius: 24px;
        border: 1px solid {border_color};
        text-align: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0, 242, 254, 0.2);
    }}
    
    .metric-card::after {{
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 4px;
        background: {accent_gradient};
    }}
    
    .metric-val {{
        font-size: 2.5rem;
        font-weight: 700;
        background: {accent_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    .metric-lbl {{
        font-size: 0.75rem;
        color: {text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-top: 0.8rem;
        font-weight: 600;
    }}

    .coaching-output {{
        background: {surface_color};
        padding: 3rem;
        border-radius: 28px;
        border: 1px solid {border_color};
        color: {text_primary};
        line-height: 2;
        font-size: 1.05rem;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        animation: fadeIn 0.6s ease-out;
        white-space: pre-wrap;
        word-wrap: break-word;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    div[data-testid="stFileUploader"] {{
        background: {surface_color} !important;
        border: 2px dashed #6366F1 !important;
        border-radius: 24px !important;
        padding: 2rem !important;
        transition: all 0.3s ease;
    }}

    div[data-testid="stFileUploader"]:hover {{
        border-color: #00F2FE !important;
        box-shadow: 0 10px 25px rgba(0, 242, 254, 0.15);
    }}

    button {{
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }}

    button[kind="primary"] {{
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 50%, #6366F1 100%) !important;
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3) !important;
    }}

    button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 35px rgba(99, 102, 241, 0.4) !important;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION FLOW ---
if not st.session_state.authenticated:
    
    if st.session_state.auth_step == "google_modal":
        st.markdown("""
            <div class="auth-card">
                <div style="display: flex; justify-content: center; margin-bottom: 1rem;">
                    <svg width="36" height="36" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"/>
                        <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.19v3.15C3.17 21.32 7.23 24 12 24z"/>
                        <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.19C.43 8.12 0 9.87 0 12s.43 3.88 1.19 5.42l4.09-3.15z"/>
                        <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.23 0 3.17 2.68 1.19 6.58l4.09 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                    </svg>
                </div>
                <h2 style="font-size: 1.5rem; margin-bottom: 0.2rem;">Choose an account</h2>
                <p style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 2rem;">to continue to KineticPulse AI</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_m1, col_m2, col_m3 = st.columns([1, 1.6, 1])
        with col_m2:
            if st.button("👤 alex.turner.pro@gmail.com", use_container_width=True):
                with st.spinner("Authenticating..."):
                    time.sleep(1.0)
                st.session_state.authenticated = True
                st.session_state.user_name = "Alex Turner"
                st.session_state.user_email = "alex.turner.pro@gmail.com"
                st.rerun()
                
            if st.button("👤 athlete.elite@gmail.com", use_container_width=True):
                with st.spinner("Authenticating..."):
                    time.sleep(1.0)
                st.session_state.authenticated = True
                st.session_state.user_name = "Jordan Vance"
                st.session_state.user_email = "athlete.elite@gmail.com"
                st.rerun()
                
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Back", use_container_width=True):
                st.session_state.auth_step = "main"
                st.rerun()
        st.stop()

    st.markdown("""
        <div class="auth-card">
            <div style="display: flex; justify-content: center; margin-bottom: 1.2rem;">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" fill="url(#main_grad)"/>
                    <path d="M7 12L10 15L17 8" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <defs>
                        <linearGradient id="main_grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#00F2FE"/>
                            <stop offset="1" stop-color="#6366F1"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <h1 style="font-size: 2.2rem; margin-bottom: 0.4rem;">KineticPulse AI</h1>
            <p style="color: #94A3B8; margin-bottom: 2.5rem; font-size: 0.95rem;">Professional Computer Vision & Biomechanics Studio</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 1.4, 1])
    with col_b:
        if st.button("🌐 Sign in with Google", use_container_width=True):
            st.session_state.auth_step = "google_modal"
            st.rerun()
            
        if st.button("⚡ Continue as Guest", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Guest Athlete"
            st.session_state.user_email = "guest@kineticpulse.ai"
            st.rerun()
    st.stop()

# --- SECURE API KEY & CLIENT INITIALIZATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    client = genai.Client(api_key=api_key)
except Exception:
    api_key = ""
    client = None
    st.error("🔐 API Key not found in secrets.")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" fill="#6366F1"/>
                <path d="M7 12L10 15L17 8" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <span style="font-size: 1.25rem; font-weight: 700;">KineticPulse</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Account:** `{st.session_state.user_name}`")
    st.markdown(f"<span style='color: {text_secondary}; font-size: 0.85rem;'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
    
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.auth_step = "main"
        st.rerun()
        
    st.markdown("---")
    st.markdown("## 🎨 Personalization")
    theme_selection = st.radio("Color Theme", ["Vibrant Obsidian", "Clean Light"], index=0 if st.session_state.theme_mode=="Vibrant Obsidian" else 1)
    if theme_selection != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_selection
        st.rerun()
        
    st.markdown("---")
    st.markdown("## ⚙️ Athlete Profile")
    skill_level = st.slider("Skill Level Rating", 1.0, 6.0, 4.0, 0.5)
    
    st.markdown("---")
    st.markdown("## 👥 Analysis Scope")
    analysis_scope = st.radio("Target Focus", ["Comprehensive (All Subjects)", "Specific Target Subject"])
    player_target = ""
    if analysis_scope == "Specific Target Subject":
        player_target = st.text_input("Subject description", placeholder="e.g. Athlete in foreground wearing jacket")

# --- MAIN APP HEADER ---
st.markdown("""
    <div class="app-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="#00F2FE"/></svg>
        Powered by Gemini 3.5 Flash
    </div>
""", unsafe_allow_html=True)

col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("# Biomechanical Motion & Form Studio")
    st.markdown(f"<p style='color: {text_secondary}; margin-top: -8px; font-size: 1.05rem;'>Upload high-definition sports footage for lightning-fast AI analysis.</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN LAYOUT ---
col_video, col_insights = st.columns([1.2, 1], gap="large")

with col_video:
    st.subheader("📹 Session Footage Upload")
    uploaded_video = st.file_uploader("Upload MP4 or MOV", type=["mp4", "mov"])
    
    if uploaded_video:
        video_bytes = uploaded_video.read()
        st.video(video_bytes)
        
        if st.session_state.video_ref is None or uploaded_video.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("📤 Uploading video..."):
                try:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(video_bytes)
                    tfile.close()
                    
                    video_file = client.files.upload(file=tfile.name)
                    st.session_state.video_ref = video_file
                    st.session_state.last_uploaded_name = uploaded_video.name
                    os.unlink(tfile.name)
                    st.success("✅ Video ready!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

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
    st.info("💡 Keep clips 10-45 seconds for fastest results")

# --- ANALYSIS SECTION ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.subheader("🧠 AI Motion Breakdown")

if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
    if not api_key or not client:
        st.error("❌ API Key missing")
    elif not st.session_state.video_ref:
        st.error("❌ Upload a video first")
    else:
        with st.spinner("🧠 Analyzing..."):
            try:
                target_clause = f"Focus on {player_target}." if player_target else "Comprehensive analysis."
                
                prompt = f"""Elite sports biomechanics analysis:
                Skill level: {skill_level}/6
                {target_clause}
                
                Cover:
                1. Posture & balance
                2. Kinetic chain & power
                3. Positioning & mechanics
                4. Timing & consistency
                5. Coaching recommendations
                
                Be thorough and encouraging."""
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[st.session_state.video_ref, prompt]
                )
                st.session_state.analysis_text = response.text
                
            except Exception as e:
                st.session_state.analysis_text = f"❌ Error: {str(e)[:200]}"

st.markdown(f"""
    <div class="coaching-output">
        {st.session_state.analysis_text}
    </div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: {text_secondary}; font-size: 0.9rem;'>© 2026 KineticPulse AI</p>", unsafe_allow_html=True)
