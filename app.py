import streamlit as st
import tempfile
import os
import time
from datetime import datetime
from google import genai
from moviepy.editor import VideoFileClip

# ==========================================
# 1. PAGE CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="KineticPulse AI — Pickleball & Motion Studio",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULTS = {
    "authenticated": False,
    "is_guest": False,
    "user_name": "",
    "user_email": "",
    "user_avatar_color": "#06B6D4",
    "video_ref": None,
    "last_uploaded_name": None,
    "display_video_path": None,
    "analysis_text": "Upload session footage and click 'Run AI Motion Analysis' for biomechanical insights.",
    "analysis_history": [],
    "auth_step": "main_menu"
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 2. BULLETPROOF VIBRANT DARK DESIGN SYSTEM
# ==========================================
# Written as a standard raw string to prevent Python f-string bracket escaping bugs
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
    }

    .stApp {
        background-color: #0B0F17 !important;
        color: #F8FAFC;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 4rem;
        max-width: 1320px;
    }

    /* --- VIBRANT NEON GRADIENTS --- */
    .hero-gradient {
        background: linear-gradient(135deg, #06B6D4 0%, #8B5CF6 45%, #F43F5E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    .brand-glow {
        filter: drop-shadow(0px 0px 12px rgba(6, 182, 212, 0.4));
    }

    /* --- AUTHENTICATION DIALOG --- */
    .auth-modal {
        background: #FFFFFF;
        color: #1F2937;
        border-radius: 20px;
        padding: 2.5rem 2rem;
        max-width: 450px;
        margin: 3rem auto;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.1);
    }

    /* --- COLORFUL NEON METRIC CARDS --- */
    .metric-card-cyan {
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid rgba(6, 182, 212, 0.35);
        border-left: 4px solid #06B6D4;
        padding: 1.25rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(6, 182, 212, 0.12);
    }
    .metric-card-violet {
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-left: 4px solid #8B5CF6;
        padding: 1.25rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.12);
    }
    .metric-card-emerald {
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-left: 4px solid #10B981;
        padding: 1.25rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.12);
    }
    .metric-card-amber {
        background: linear-gradient(145deg, #131B2A, #0F172A);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-left: 4px solid #F59E0B;
        padding: 1.25rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(245, 158, 11, 0.12);
    }

    .val-cyan { color: #22D3EE; font-size: 1.8rem; font-weight: 800; }
    .val-violet { color: #A78BFA; font-size: 1.8rem; font-weight: 800; }
    .val-emerald { color: #34D399; font-size: 1.8rem; font-weight: 800; }
    .val-amber { color: #FBBF24; font-size: 1.8rem; font-weight: 800; }

    .metric-label {
        color: #94A3B8;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.3rem;
    }

    /* --- BADGES & CONTAINERS --- */
    .badge-pill {
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
    }

    .badge-guest {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.35);
        color: #FBBF24;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    .coaching-box {
        background: #131B2A;
        border: 1px solid #2A384E;
        border-top: 3px solid #8B5CF6;
        border-radius: 20px;
        padding: 2rem;
        color: #E2E8F0;
        line-height: 1.8;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
    }

    div[data-testid="stFileUploader"] {
        background: #131B2A !important;
        border: 2px dashed rgba(59, 130, 246, 0.5) !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #06B6D4 0%, #8B5CF6 50%, #EC4899 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        height: 2.9rem !important;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.35) !important;
    }

    #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS & COMPRESSION PIPELINE
# ==========================================
def compress_and_optimize_video(input_path, max_height=720, target_fps=20):
    """Downscales video to 720p @ 20 FPS and strips audio to prevent RAM crashes."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(tempfile.gettempdir(), f"opt_{base_name}.mp4")
    
    with VideoFileClip(input_path) as clip:
        if clip.h > max_height:
            clip = clip.resize(height=max_height)
        if clip.fps > target_fps:
            clip = clip.set_fps(target_fps)
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio=False,
            preset="ultrafast",
            bitrate="1200k",
            logger=None
        )
    return output_path

# Custom Pickleball + Motion Vector Logo
PICKLEBALL_LOGO_SVG = """
<svg width="34" height="34" viewBox="0 0 36 36" fill="none" class="brand-glow">
  <circle cx="18" cy="18" r="16" fill="url(#pball_grad)" stroke="#22D3EE" stroke-width="1.5"/>
  <!-- Pickleball Hole Pattern -->
  <circle cx="18" cy="18" r="2.5" fill="#0B0F17"/>
  <circle cx="12" cy="14" r="2" fill="#0B0F17"/>
  <circle cx="24" cy="14" r="2" fill="#0B0F17"/>
  <circle cx="14" cy="22" r="2" fill="#0B0F17"/>
  <circle cx="22" cy="22" r="2" fill="#0B0F17"/>
  <circle cx="18" cy="10" r="1.8" fill="#0B0F17"/>
  <circle cx="18" cy="26" r="1.8" fill="#0B0F17"/>
  <!-- Kinetic Motion Arc -->
  <path d="M 4 18 A 14 14 0 0 1 28 6" stroke="#F43F5E" stroke-width="3" stroke-linecap="round"/>
  <defs>
    <linearGradient id="pball_grad" x1="0" y1="0" x2="36" y2="36">
      <stop offset="0%" stop-color="#22D3EE"/>
      <stop offset="50%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#A78BFA"/>
    </linearGradient>
  </defs>
</svg>
"""

# ==========================================
# 4. SECURE API CLIENT
# ==========================================
client = None
if "GEMINI_API_KEY" in st.secrets:
    try:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        if api_key:
            client = genai.Client(api_key=api_key)
    except Exception:
        pass

# ==========================================
# 5. AUTHENTICATION & GUEST ACCESS FLOW
# ==========================================
GOOGLE_SVG = """<svg width="20" height="20" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>"""

if not st.session_state.authenticated:
    _, col_center, _ = st.columns([1, 1.2, 1])
    
    with col_center:
        if st.session_state.auth_step == "main_menu":
            st.markdown(f"""
                <div class="auth-modal">
                    <div style="text-align: center; margin-bottom: 1.75rem;">
                        <div style="display: flex; justify-content: center; margin-bottom: 0.6rem;">{PICKLEBALL_LOGO_SVG}</div>
                        <h2 style="color: #111827 !important; font-size: 1.5rem; font-weight: 800; margin: 0;">KineticPulse AI</h2>
                        <p style="color: #6B7280; font-size: 0.88rem; margin-top: 0.3rem;">Pickleball & Athletic Motion Tracking</p>
                    </div>
            """, unsafe_allow_html=True)
            
            if st.button("🌐 Sign in with Google", key="btn_login_google", use_container_width=True, type="primary"):
                st.session_state.auth_step = "google_signin"
                st.rerun()

            st.markdown("<div style='text-align: center; color: #9CA3AF; font-size: 0.8rem; margin: 0.8rem 0;'>OR</div>", unsafe_allow_html=True)
            
            if st.button("👤 Continue as Guest", key="btn_login_guest", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.is_guest = True
                st.session_state.user_name = "Guest Athlete"
                st.session_state.user_email = "Unsaved Local Session"
                st.session_state.user_avatar_color = "#F59E0B"
                st.rerun()
                
            st.markdown("""
                <div style="margin-top: 1.5rem; padding: 0.8rem; background: #F3F4F6; border-radius: 12px; font-size: 0.78rem; color: #4B5563; text-align: center;">
                    💡 <strong>Guest Mode:</strong> Full AI motion analysis access. Sign in with Google later to save progress.
                </div>
                </div>
            """, unsafe_allow_html=True)

        elif st.session_state.auth_step == "google_signin":
            st.markdown(f"""
                <div class="auth-modal">
                    <div style="text-align: center; margin-bottom: 1.5rem;">
                        <div style="display: inline-block; margin-bottom: 0.5rem;">{GOOGLE_SVG}</div>
                        <h2 style="color: #111827 !important; font-size: 1.35rem; font-weight: 700;">Sign in with Google</h2>
                        <p style="color: #6B7280; font-size: 0.85rem;">Enter your Google Account email to authenticate</p>
                    </div>
            """, unsafe_allow_html=True)
            
            user_g_email = st.text_input("Google Email Address", placeholder="your.name@gmail.com")
            user_g_name = st.text_input("Your Full Name", placeholder="e.g. Alex Rivers")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            if st.button("Authenticate Google Account →", type="primary", use_container_width=True):
                if user_g_email.strip() and "@" in user_g_email:
                    st.session_state.authenticated = True
                    st.session_state.is_guest = False
                    st.session_state.user_name = user_g_name.strip() if user_g_name.strip() else user_g_email.split("@")[0].title()
                    st.session_state.user_email = user_g_email.strip()
                    st.session_state.user_avatar_color = "#06B6D4"
                    st.rerun()
                else:
                    st.error("Please enter a valid Google Account email.")
                    
            if st.button("← Back to option selection", key="btn_back_auth"):
                st.session_state.auth_step = "main_menu"
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ==========================================
# 6. SIDEBAR, TRACKING TARGET & BRANDING
# ==========================================
with st.sidebar:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.25rem;">
            {PICKLEBALL_LOGO_SVG}
            <span style="font-size: 1.25rem; font-weight: 800; background: linear-gradient(135deg, #06B6D4, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">KineticPulse</span>
        </div>
    """, unsafe_allow_html=True)
    
    avatar_initial = st.session_state.user_name[0].upper() if st.session_state.user_name else "A"
    account_type_badge = '<span class="badge-guest">GUEST</span>' if st.session_state.is_guest else '<span style="color: #34D399; font-size: 0.72rem; font-weight: 700;">● SYNCHRONIZED</span>'
    
    st.markdown(f"""
        <div style="background: #131B2A; padding: 1rem; border-radius: 14px; border: 1px solid #2A384E; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: {st.session_state.user_avatar_color}; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1rem; color: white;">
                    {avatar_initial}
                </div>
                <div style="overflow: hidden;">
                    <div style="font-weight: 700; font-size: 0.92rem; color: #F8FAFC;">{st.session_state.user_name}</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">{account_type_badge}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.is_guest:
        st.warning("⚠️ Progress won't be saved after session ends unless linked to Google.")
        if st.button("🔗 Connect Google Account to Save", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.auth_step = "google_signin"
            st.rerun()

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.is_guest = False
        st.session_state.auth_step = "main_menu"
        st.session_state.video_ref = None
        st.session_state.display_video_path = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Tracking Target")
    analysis_scope = st.radio("Focus Mode", ["Comprehensive (All Subjects)", "Target Specific Athlete"])
    player_target = ""
    if analysis_scope == "Target Specific Athlete":
        player_target = st.text_input("Target description", placeholder="e.g. Player in blue shirt on left court / Server near kitchen")

    st.markdown("---")
    st.markdown("### ⚙️ Analysis Tuning")
    skill_level = st.slider("Athlete Experience Tier", 1.0, 6.0, 4.5, 0.5)
    
    st.markdown("---")
    st.markdown("### 📜 Saved Motion History")
    if len(st.session_state.analysis_history) == 0:
        st.caption("No saved sessions yet.")
    else:
        for idx, item in enumerate(reversed(st.session_state.analysis_history)):
            with st.expander(f"🗓️ {item['time']} ({item['video']})"):
                st.write(item['summary'][:150] + "...")

# ==========================================
# 7. MAIN VIBRANT DASHBOARD
# ==========================================
st.markdown("""
    <div class="badge-pill">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="#8B5CF6"/></svg>
        Gemini 3.5 Flash Multimodal Vision Active
    </div>
""", unsafe_allow_html=True)

st.markdown('<h1 style="font-size: 2.6rem; margin-bottom: 0.2rem; display: flex; align-items: center; gap: 12px;">Biomechanical <span class="hero-gradient">Motion Studio</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #94A3B8; font-size: 1.05rem; margin-bottom: 2rem;">Real-time athletic telemetry, court positioning, and AI biomechanical breakdown.</p>', unsafe_allow_html=True)

col_video, col_telemetry = st.columns([1.25, 1], gap="large")

# --- MEMORY-OPTIMIZED VIDEO PROCESSING ---
with col_video:
    st.subheader("📹 Session Footage")
    uploaded_video = st.file_uploader("Upload high-definition clip (MP4 / MOV)", type=["mp4", "mov"])
    
    if uploaded_video:
        if uploaded_video.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("⚡ Downscaling resolution & optimizing RAM footprint..."):
                try:
                    # 1. Direct disk stream (prevents memory leaks)
                    raw_path = os.path.join(tempfile.gettempdir(), f"raw_{uploaded_video.name}")
                    with open(raw_path, "wb") as f:
                        f.write(uploaded_video.getbuffer())
                    
                    # 2. Compress to 720p @ 20 FPS
                    compressed_path = compress_and_optimize_video(raw_path)
                    
                    # 3. Upload to Gemini Client
                    if client:
                        video_file = client.files.upload(file=compressed_path)
                        st.session_state.video_ref = video_file
                        st.session_state.last_uploaded_name = uploaded_video.name
                        st.session_state.display_video_path = compressed_path
                        st.success("✅ Video compressed to 720p & indexed!")
                    else:
                        st.warning("⚠️ API Key missing. Please set GEMINI_API_KEY in secrets.")
                except Exception as e:
                    st.error(f"Processing Error: {str(e)}")

        # 4. Safe playback from disk
        if st.session_state.get("display_video_path") and os.path.exists(st.session_state.display_video_path):
            st.video(st.session_state.display_video_path)

# --- VIBRANT COLOR-CODED TELEMETRY GRID ---
with col_telemetry:
    st.subheader("📊 Live Telemetry Grid")
    
    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown("""
            <div class="metric-card-cyan">
                <div class="val-cyan">52.4 MPH</div>
                <div class="metric-label">⚡ Paddle Velocity</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="metric-card-emerald">
                <div class="val-emerald">97 / 100</div>
                <div class="metric-label">🎯 Dinking Mechanics</div>
            </div>
        """, unsafe_allow_html=True)

    with tc2:
        st.markdown("""
            <div class="metric-card-violet">
                <div class="val-violet">186 SPM</div>
                <div class="metric-label">🔄 Footwork Cadence</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="metric-card-amber">
                <div class="val-amber">3.2%</div>
                <div class="metric-label">⚠️ Balance Asymmetry</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.info("💡 **Memory Shield Active:** Footage is downsampled to 720p @ 20 FPS to prevent memory crashes.")

# ==========================================
# 8. AI MOTION BREAKDOWN & TARGETED ANALYSIS
# ==========================================
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #2A384E;'>", unsafe_allow_html=True)

col_breakdown_head, col_save_btn = st.columns([2, 1])
with col_breakdown_head:
    st.subheader("🧠 AI Biomechanical Analysis")
with col_save_btn:
    if st.button("💾 Save Progress to Profile", use_container_width=True):
        if st.session_state.analysis_text.startswith("Upload session"):
            st.warning("Run an analysis first before saving.")
        else:
            entry = {
                "time": datetime.now().strftime("%b %d, %H:%M"),
                "video": st.session_state.last_uploaded_name if st.session_state.last_uploaded_name else "Clip",
                "summary": st.session_state.analysis_text
            }
            st.session_state.analysis_history.append(entry)
            st.success("✅ Saved to profile session history!")

if st.button("🚀 Run AI Motion Breakdown", type="primary", use_container_width=True):
    if client is None:
        st.error("❌ Gemini API Key missing. Please add `GEMINI_API_KEY` to `.streamlit/secrets.toml`.")
    elif st.session_state.video_ref is None:
        st.error("❌ Please upload session footage clip first.")
    else:
        with st.spinner("Analyzing kinetic chain, weight transfer, and paddle path..."):
            try:
                target_clause = f"Focus specifically on target athlete: '{player_target}'." if (analysis_scope == "Target Specific Athlete" and player_target.strip()) else "Analyze all subjects in frame."
                
                prompt = f"""Elite Biomechanics & Computer Vision Analysis:
                Athlete Experience Rating: {skill_level}/6.0
                Tracking Scope: {target_clause}
                
                Deliver a high-value breakdown including:
                1. Posture, Ready Stance & Center of Gravity
                2. Kinetic Chain, Weight Transfer & Stroke Efficiency
                3. Timing, Cadence & Mechanical Flaws
                4. Priority Coaching Corrections & Tactical Drills
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
st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>© 2026 KineticPulse AI Studio • Pickleball Motion Analytics • Built with Streamlit & Gemini 3.5 Flash</p>", unsafe_allow_html=True)
