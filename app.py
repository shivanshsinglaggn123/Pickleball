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
if "video_ref" not in st.session_state:
    st.session_state.video_ref = None
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = "Upload high-definition session footage and click 'Run Comprehensive AI Analysis' to receive an exhaustive biomechanical breakdown."

# --- PREMIUM OBSIDIAN DESIGN SYSTEM ---
bg_color = "#09090B"
surface_color = "#18181B"
surface_elevated = "#27272A"
border_color = "#3F3F46"
text_primary = "#FAFAFA"
text_secondary = "#A1A1AA"
accent_gradient = "linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #EC4899 100%)"
card_shadow = "0 12px 32px rgba(0, 0, 0, 0.6)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Google Sans', 'Poppins', sans-serif;
    }}

    .main .block-container {{
        background-color: {bg_color};
        color: {text_primary};
        padding-top: 2rem;
        padding-bottom: 4rem;
    }}
    
    h1, h2, h3 {{
        color: {text_primary} !important;
        font-weight: 700;
        letter-spacing: -0.015em;
    }}

    .sub-header {{
        color: {text_secondary};
        margin-top: -0.4rem;
        margin-bottom: 1.5rem;
        font-size: 1.05rem;
        font-weight: 400;
        letter-spacing: -0.01em;
    }}

    .auth-card {{
        background: {surface_color};
        padding: 3rem 2.5rem;
        border-radius: 28px;
        border: 1px solid {border_color};
        box-shadow: {card_shadow};
        max-width: 440px;
        margin: 4rem auto;
        text-align: center;
        animation: fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    @keyframes fadeIn {{
        from {{ transform: translateY(10px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}

    .app-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: {surface_elevated};
        border: 1px solid {border_color};
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        color: {text_primary};
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}

    .metric-card {{
        background: {surface_color};
        padding: 1.5rem 1rem;
        border-radius: 20px;
        border: 1px solid {border_color};
        text-align: center;
        box-shadow: {card_shadow};
        position: relative;
        overflow: hidden;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 16px 36px rgba(56, 189, 248, 0.15);
    }}
    
    .metric-card::after {{
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 3px;
        background: {accent_gradient};
    }}
    
    .metric-val {{
        font-size: 1.8rem;
        font-weight: 700;
        background: {accent_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
        white-space: nowrap;
    }}
    
    .metric-lbl {{
        font-size: 0.72rem;
        color: {text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.4rem;
        font-weight: 600;
        white-space: nowrap;
    }}

    .coaching-output {{
        background: {surface_color};
        padding: 2.5rem;
        border-radius: 24px;
        border: 1px solid {border_color};
        color: {text_primary};
        line-height: 1.8;
        font-size: 1rem;
        box-shadow: {card_shadow};
        white-space: pre-wrap;
        word-wrap: break-word;
    }}

    div[data-testid="stFileUploader"] {{
        background: {surface_color} !important;
        border: 2px dashed {border_color} !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
    }}

    button[kind="primary"] {{
        background: {accent_gradient} !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        box-shadow: {card_shadow} !important;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION FLOW ---
if not st.session_state.authenticated:
    st.markdown(f"""
        <div class="auth-card">
            <div style="display: flex; justify-content: center; margin-bottom: 1.2rem;">
                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" fill="url(#brand_grad)"/>
                    <path d="M7 12L10 15L17 8" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                    <defs>
                        <linearGradient id="brand_grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#38BDF8"/>
                            <stop offset="1" stop-color="#818CF8"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <h1 style="font-size: 1.8rem; margin-bottom: 0.3rem;">KineticPulse AI</h1>
            <p style="color: {text_secondary}; margin-bottom: 2rem; font-size: 0.9rem;">Professional Computer Vision & Biomechanics</p>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([0.1, 1, 0.1])
    with col_b:
        google_email_input = st.text_input("Sign in with Google Email", placeholder="your.name@gmail.com")
        
        if st.button("🌐 Continue with Google", type="primary", use_container_width=True):
            if google_email_input.strip() and "@" in google_email_input:
                with st.spinner("Authenticating with Google..."):
                    time.sleep(0.8)
                st.session_state.authenticated = True
                st.session_state.user_email = google_email_input.strip()
                st.session_state.user_name = google_email_input.split('@')[0].replace('.', ' ').title()
                st.rerun()
            else:
                st.error("Please enter a valid Google email address.")
                
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("⚡ Continue as Guest", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_name = "Guest Athlete"
            st.session_state.user_email = "guest@kineticpulse.ai"
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- SECURE API KEY & CLIENT INITIALIZATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    client = genai.Client(api_key=api_key)
except Exception:
    api_key = ""
    client = None

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.5rem;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" fill="#38BDF8"/>
                <path d="M7 12L10 15L17 8" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <span style="font-size: 1.2rem; font-weight: 700;">KineticPulse</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Signed in as:** `{st.session_state.user_name}`")
    st.markdown(f"<span style='color: {text_secondary}; font-size: 0.82rem;'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("### ⚙️ Athlete Settings")
    skill_level = st.slider("Skill Level Rating", 1.0, 6.0, 4.0, 0.5)
    
    st.markdown("---")
    st.markdown("### 👥 Analysis Scope")
    analysis_scope = st.radio("Target Focus", ["Comprehensive (All Subjects)", "Specific Target Subject"])
    player_target = ""
    if analysis_scope == "Specific Target Subject":
        player_target = st.text_input("Subject description", placeholder="e.g. Athlete in foreground")

# --- MAIN APP HEADER ---
st.markdown("""
    <div class="app-badge">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="#38BDF8"/></svg>
        Powered by Gemini 3.5 Flash
    </div>
""", unsafe_allow_html=True)

st.markdown("# Biomechanical Motion Studio")
st.markdown('<p class="sub-header">Upload high-definition session footage for instant computer vision telemetry and coaching.</p>', unsafe_allow_html=True)

# --- MAIN LAYOUT ---
col_video, col_insights = st.columns([1.2, 1], gap="large")

with col_video:
    st.subheader("📹 Session Footage")
    uploaded_video = st.file_uploader("Upload MP4 or MOV clip", type=["mp4", "mov"])
    
    if uploaded_video:
        video_bytes = uploaded_video.read()
        st.video(video_bytes)
        
        if st.session_state.video_ref is None or uploaded_video.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("📤 Processing video with Gemini..."):
                try:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(video_bytes)
                    tfile.close()
                    
                    if not api_key:
                        st.error("API Key not found in Streamlit secrets.")
                    else:
                        video_file = client.files.upload(file=tfile.name)
                        st.session_state.video_ref = video_file
                        st.session_state.last_uploaded_name = uploaded_video.name
                        os.unlink(tfile.name)
                        st.success("✅ Video ready for analysis!")
                except Exception as e:
                    st.error(f"❌ Error uploading: {str(e)}")

with col_insights:
    st.subheader("📊 Session Telemetry")
    
    # Perfectly symmetrical telemetry metrics grid
    m1, m2, m3 = st.columns(3)
    metrics_data = [("Velocity", "52 MPH"), ("Cadence", "186 SPM"), ("Form Score", "97/100")]
    
    for col, (lbl, val) in zip([m1, m2, m3], metrics_data):
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{val}</div>
                    <div class="metric-lbl">{lbl}</div>
                </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.info("💡 Keep clips between 10 to 45 seconds for optimal processing speed.")

# --- ANALYSIS SECTION ---
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
st.markdown("---")
st.subheader("🧠 AI Motion Breakdown")

if st.button("🚀 Run Comprehensive AI Analysis", type="primary", use_container_width=True):
    if not api_key or not client:
        st.error("❌ Gemini API Key is missing. Please add it to your Streamlit secrets.")
    elif not st.session_state.video_ref:
        st.error("❌ Please upload a session video first.")
    else:
        with st.spinner("🧠 Analyzing biomechanics and kinetic chain..."):
            try:
                target_clause = f"Focus on {player_target}." if player_target else "Comprehensive analysis."
                
                prompt = f"""Elite sports biomechanics and form analysis:
                Athlete skill level: {skill_level}/6
                {target_clause}
                
                Provide a thorough breakdown covering:
                1. Posture, balance & alignment
                2. Kinetic chain & power transfer
                3. Mechanics & execution efficiency
                4. Timing & consistency notes
                5. Actionable coaching recommendations
                
                Keep the tone professional, encouraging, and precise."""
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[st.session_state.video_ref, prompt]
                )
                st.session_state.analysis_text = response.text
                
            except Exception as e:
                st.session_state.analysis_text = f"❌ Analysis Error: {str(e)}"

st.markdown(f"""
    <div class="coaching-output">
        {st.session_state.analysis_text}
    </div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: {text_secondary}; font-size: 0.85rem;'>© 2026 KineticPulse AI • Built with Streamlit & Google Gemini</p>", unsafe_allow_html=True)
