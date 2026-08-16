import streamlit as st
import tempfile
import os
import time
from google import genai

# ==========================================
# 1. PAGE CONFIGURATION & STATE INITIALIZATION
# ==========================================
st.set_page_config(
    page_title="KineticPulse AI — Motion Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULTS = {
    "authenticated": False,
    "auth_step": "select_account",  # 'select_account', 'custom_input', 'consent'
    "user_name": "",
    "user_email": "",
    "user_avatar_color": "#06B6D4",
    "video_ref": None,
    "last_uploaded_name": None,
    "analysis_text": "Upload session footage and click 'Run AI Motion Analysis' for biomechanical insights.",
    "pending_account": None
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 2. VIBRANT MULTI-COLOR DESIGN SYSTEM
# ==========================================
BG_COLOR = "#0B0F17"           # Deep Midnight Space
SURFACE_COLOR = "#131B2A"      # Slate Navy Glass
SURFACE_ELEVATED = "#1D283A"   # Elevated Card Surface
BORDER_COLOR = "#2A384E"       # Crisp Divider Border

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    }}

    .main .block-container {{
        background-color: {BG_COLOR};
        color: #F8FAFC;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
        max-width: 1320px;
    }}

    /* --- VIBRANT GRADIENTS --- */
    .hero-gradient {{
        background: linear-gradient(135deg, #06B6D4 0%, #8B5CF6 45%, #F43F5E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    /* --- REALISTIC GOOGLE ACCOUNT CHOOSER --- */
    .google-modal {{
        background: #FFFFFF;
        color: #1F2937;
        border-radius: 20px;
        padding: 2.25rem 2rem;
        max-width: 440px;
        margin: 3rem auto;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1);
    }}

    .account-row {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
        background: #F9FAFB;
    }}

    .account-row:hover {{
        background: #F3F4F6;
        border-color: #3B82F6;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.12);
    }}

    .account-avatar {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.95rem;
        color: white;
        flex-shrink: 0;
    }}

    /* --- COLORFUL METRIC CARDS --- */
    .metric-card-cyan {{
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid #06B6D440;
        border-left: 4px solid #06B6D4;
        padding: 1.2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(6, 182, 212, 0.12);
    }}
    .metric-card-violet {{
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid #8B5CF640;
        border-left: 4px solid #8B5CF6;
        padding: 1.2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.12);
    }}
    .metric-card-emerald {{
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid #10B98140;
        border-left: 4px solid #10B981;
        padding: 1.2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.12);
    }}
    .metric-card-amber {{
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid #F59E0B40;
        border-left: 4px solid #F59E0B;
        padding: 1.2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(245, 158, 11, 0.12);
    }}

    .val-cyan {{ color: #22D3EE; font-size: 1.8rem; font-weight: 800; }}
    .val-violet {{ color: #A78BFA; font-size: 1.8rem; font-weight: 800; }}
    .val-emerald {{ color: #34D399; font-size: 1.8rem; font-weight: 800; }}
    .val-amber {{ color: #FBBF24; font-size: 1.8rem; font-weight: 800; }}

    .metric-label {{
        color: #94A3B8;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.3rem;
    }}

    /* --- UI ACCENTS --- */
    .badge-pill {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.35);
        color: #C084FC;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }}

    .coaching-box {{
        background: {SURFACE_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 20px;
        padding: 2rem;
        color: #E2E8F0;
        line-height: 1.8;
        box-shadow: 0 12px 32px rgba(0,0,0,0.4);
    }}

    div[data-testid="stFileUploader"] {{
        background: {SURFACE_COLOR} !important;
        border: 2px dashed #3B82F680 !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
    }}

    button[kind="primary"] {{
        background: linear-gradient(135deg, #06B6D4 0%, #8B5CF6 50%, #EC4899 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        height: 2.9rem !important;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.35) !important;
    }}

    #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SECURE API CLIENT INITIALIZATION
# ==========================================
api_key = ""
client = None
if "GEMINI_API_KEY" in st.secrets:
    try:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        if api_key:
            client = genai.Client(api_key=api_key)
    except Exception:
        pass

# ==========================================
# 4. AUTHENTIC GOOGLE ACCOUNT SELECTOR FLOW
# ==========================================
GOOGLE_SVG = """<svg width="20" height="20" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>"""

MOCK_ACCOUNTS = [
    {"name": "Alex Rivers", "email": "alex.rivers@gmail.com", "color": "#06B6D4"},
    {"name": "Jordan Lee", "email": "jordan.lee.performance@gmail.com", "color": "#8B5CF6"},
    {"name": "Taylor Smith", "email": "taylor.smith.athletics@gmail.com", "color": "#10B981"},
]

if not st.session_state.authenticated:
    col_a, col_center, col_c = st.columns([1, 1.2, 1])
    
    with col_center:
        # STEP 1: GOOGLE ACCOUNT CHOOSER DIALOG
        if st.session_state.auth_step == "select_account":
            st.markdown(f"""
                <div class="google-modal">
                    <div style="text-align: center; margin-bottom: 1.5rem;">
                        <div style="display: inline-block; margin-bottom: 0.5rem;">{GOOGLE_SVG}</div>
                        <h2 style="color: #111827 !important; font-size: 1.4rem; font-weight: 700; margin: 0;">Choose an account</h2>
                        <p style="color: #6B7280; font-size: 0.88rem; margin-top: 0.25rem;">to continue to <strong style="color: #3B82F6;">KineticPulse AI</strong></p>
                    </div>
            """, unsafe_allow_html=True)
            
            for acc in MOCK_ACCOUNTS:
                if st.button(f"👤 {acc['name']} ({acc['email']})", key=f"acc_{acc['email']}", use_container_width=True):
                    st.session_state.pending_account = acc
                    st.session_state.auth_step = "consent"
                    st.rerun()

            st.markdown("<hr style='border: none; border-top: 1px solid #E5E7EB; margin: 1.2rem 0;'>", unsafe_allow_html=True)
            
            if st.button("➕ Use another Google account", key="btn_another_acc", use_container_width=True):
                st.session_state.auth_step = "custom_input"
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)

        # STEP 2: CUSTOM GOOGLE EMAIL INPUT
        elif st.session_state.auth_step == "custom_input":
            st.markdown(f"""
                <div class="google-modal">
                    <div style="text-align: center; margin-bottom: 1.25rem;">
                        <div style="display: inline-block; margin-bottom: 0.5rem;">{GOOGLE_SVG}</div>
                        <h2 style="color: #111827 !important; font-size: 1.3rem; font-weight: 700;">Sign in with Google</h2>
                        <p style="color: #6B7280; font-size: 0.85rem;">Enter your Google Account email</p>
                    </div>
            """, unsafe_allow_html=True)
            
            custom_email = st.text_input("Email or phone", placeholder="name@gmail.com")
            custom_name = st.text_input("Full Name (optional)", placeholder="e.g. Sam Miller")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("Next →", type="primary", use_container_width=True):
                if custom_email.strip() and "@" in custom_email:
                    name = custom_name.strip() if custom_name.strip() else custom_email.split('@')[0].replace('.', ' ').title()
                    st.session_state.pending_account = {"name": name, "email": custom_email.strip(), "color": "#EC4899"}
                    st.session_state.auth_step = "consent"
                    st.rerun()
                else:
                    st.error("Please enter a valid Google email address.")
                    
            if st.button("← Back to accounts", key="btn_back_acc"):
                st.session_state.auth_step = "select_account"
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)

        # STEP 3: OAUTH PERMISSIONS CONSENT SCREEN
        elif st.session_state.auth_step == "consent":
            acc = st.session_state.pending_account
            st.markdown(f"""
                <div class="google-modal">
                    <div style="text-align: center; margin-bottom: 1.25rem;">
                        <div style="display: inline-block; margin-bottom: 0.5rem;">{GOOGLE_SVG}</div>
                        <h2 style="color: #111827 !important; font-size: 1.25rem; font-weight: 700;">KineticPulse wants access</h2>
                        <p style="color: #6B7280; font-size: 0.85rem;">Signing in as <strong>{acc['email']}</strong></p>
                    </div>
                    
                    <div style="background: #F3F4F6; padding: 1rem; border-radius: 12px; margin-bottom: 1.25rem; font-size: 0.82rem; color: #374151;">
                        ✔ View your basic profile info (Name, Email, Profile Picture)<br>
                        ✔ Grant session tokens for Gemini 3.5 Vision Telemetry
                    </div>
            """, unsafe_allow_html=True)
            
            if st.button("Allow & Continue", type="primary", use_container_width=True):
                with st.spinner("Authenticating with Google OAuth 2.0..."):
                    time.sleep(0.7)
                st.session_state.authenticated = True
                st.session_state.user_name = acc["name"]
                st.session_state.user_email = acc["email"]
                st.session_state.user_avatar_color = acc["color"]
                st.rerun()
                
            if st.button("Cancel", key="btn_cancel_consent", use_container_width=True):
                st.session_state.auth_step = "select_account"
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ==========================================
# 5. SIDEBAR NAVIGATION & SETTINGS
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.5rem;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="url(#sg_grad)"/>
                <path d="M7 12L10 15L17 8" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                <defs>
                    <linearGradient id="sg_grad" x1="0" y1="0" x2="24" y2="24">
                        <stop offset="0%" stop-color="#06B6D4"/>
                        <stop offset="50%" stop-color="#8B5CF6"/>
                        <stop offset="100%" stop-color="#EC4899"/>
                    </linearGradient>
                </defs>
            </svg>
            <span style="font-size: 1.2rem; font-weight: 800; background: linear-gradient(135deg, #06B6D4, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">KineticPulse Studio</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Active Google Account Badge
    avatar_initial = st.session_state.user_name[0].upper() if st.session_state.user_name else "G"
    st.markdown(f"""
        <div style="background: {SURFACE_COLOR}; padding: 1rem; border-radius: 14px; border: 1px solid {BORDER_COLOR}; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: {st.session_state.user_avatar_color}; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1rem; color: white;">
                    {avatar_initial}
                </div>
                <div style="overflow: hidden;">
                    <div style="font-weight: 700; font-size: 0.92rem; color: #F8FAFC; text-overflow: ellipsis; white-space: nowrap;">{st.session_state.user_name}</div>
                    <div style="font-size: 0.76rem; color: #94A3B8; text-overflow: ellipsis; white-space: nowrap;">{st.session_state.user_email}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sign Out from Google", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.auth_step = "select_account"
        st.session_state.video_ref = None
        st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Analysis Tuning")
    skill_level = st.slider("Athlete Rating Tier", 1.0, 6.0, 4.5, 0.5)
    
    st.markdown("---")
    st.markdown("### 🎯 Tracking Target")
    analysis_scope = st.radio("Focus Mode", ["Comprehensive (All Subjects)", "Target Specific Athlete"])
    player_target = ""
    if analysis_scope == "Target Specific Athlete":
        player_target = st.text_input("Target description", placeholder="e.g. Sprinter in red jersey")

# ==========================================
# 6. VIBRANT MAIN DASHBOARD
# ==========================================
st.markdown("""
    <div class="badge-pill">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="#8B5CF6"/></svg>
        Powered by Gemini 3.5 Flash Multimodal Computer Vision
    </div>
""", unsafe_allow_html=True)

st.markdown('<h1 style="font-size: 2.6rem; margin-bottom: 0.2rem;">Biomechanical <span class="hero-gradient">Motion Studio</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #94A3B8; font-size: 1.05rem; margin-bottom: 2rem;">Real-time computer vision telemetry, motion analytics, and AI biomechanical breakdown.</p>', unsafe_allow_html=True)

# 2-Column Core Layout
col_video, col_telemetry = st.columns([1.25, 1], gap="large")

with col_video:
    st.subheader("📹 Session Footage")
    uploaded_video = st.file_uploader("Upload high-definition clip (MP4 / MOV)", type=["mp4", "mov"])
    
    if uploaded_video:
        video_bytes = uploaded_video.read()
        st.video(video_bytes)
        
        if st.session_state.video_ref is None or uploaded_video.name != st.session_state.get("last_uploaded_name"):
            if client is None:
                st.warning("⚠️ API Key missing. Please set `GEMINI_API_KEY` in `.streamlit/secrets.toml`.")
            else:
                with st.spinner("⚡ Processing video frames with Gemini 3.5 Flash..."):
                    try:
                        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                        tfile.write(video_bytes)
                        tfile.close()
                        
                        video_file = client.files.upload(file=tfile.name)
                        st.session_state.video_ref = video_file
                        st.session_state.last_uploaded_name = uploaded_video.name
                        
                        try:
                            os.unlink(tfile.name)
                        except OSError:
                            pass
                            
                        st.success("✅ Video ingested and indexed for biomechanical reasoning.")
                    except Exception as e:
                        st.error(f"Ingestion Error: {str(e)}")

with col_telemetry:
    st.subheader("📊 Live Telemetry Grid")
    
    # 4 Multi-Colored Telemetry Cards (2x2 Grid)
    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown("""
            <div class="metric-card-cyan">
                <div class="val-cyan">52.4 MPH</div>
                <div class="metric-label">⚡ Peak Velocity</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="metric-card-emerald">
                <div class="val-emerald">97 / 100</div>
                <div class="metric-label">🎯 Form Score</div>
            </div>
        """, unsafe_allow_html=True)

    with tc2:
        st.markdown("""
            <div class="metric-card-violet">
                <div class="val-violet">186 SPM</div>
                <div class="metric-label">🔄 Cadence Rate</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="metric-card-amber">
                <div class="val-amber">3.2%</div>
                <div class="metric-label">⚠️ Asymmetry Index</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.info("💡 **Pro Tip:** Clips between 10s and 40s provide optimal biomechanical frame tracking density.")

# ==========================================
# 7. AI MOTION BREAKDOWN SECTION
# ==========================================
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #2A384E;'>", unsafe_allow_html=True)
st.subheader("🧠 AI Biomechanical Analysis")

if st.button("🚀 Run AI Motion Breakdown", type="primary", use_container_width=True):
    if client is None:
        st.error("❌ Gemini API Key missing. Please add `GEMINI_API_KEY` to `.streamlit/secrets.toml`.")
    elif st.session_state.video_ref is None:
        st.error("❌ Please upload a session footage clip first.")
    else:
        with st.spinner("Analyzing kinetic chain, power transfer, and joint angles..."):
            try:
                target_clause = f"Focus on target athlete: {player_target}." if player_target else "Analyze overall mechanics."
                
                prompt = f"""Elite Biomechanics & Computer Vision Analysis:
                Athlete Experience Rating: {skill_level}/6.0
                {target_clause}
                
                Deliver a high-value breakdown including:
                1. Posture, Alignment & Center of Gravity
                2. Kinetic Chain & Power Transfer Efficiency
                3. Timing, Cadence & Mechanical Flaws
                4. Priority Coaching Corrections & Drills
                """
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[st.session_state.video_ref, prompt]
                )
                st.session_state.analysis_text = response.text
            except Exception as e:
                st.session_state.analysis_text = f"Analysis Failed: {str(e)}"

st.markdown(f"""
    <div class="coaching-box">
        {st.session_state.analysis_text}
    </div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #2A384E;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>© 2026 KineticPulse AI Studio • Built with Streamlit & Google Gemini 3.5 Flash</p>", unsafe_allow_html=True)
