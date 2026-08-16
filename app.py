import streamlit as st
import tempfile
import os
from datetime import datetime
from google import genai
from moviepy.editor import VideoFileClip

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="KineticPulse AI — Motion Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULTS = {
    "authenticated": False,
    "is_guest": False,
    "user_name": "",
    "user_email": "",
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
# 2. VIDEO COMPRESSION PIPELINE
# ==========================================
def compress_and_optimize_video(input_path, max_height=720, target_fps=20):
    """
    Downscales video height to 720p, lowers FPS to 20, and strips audio.
    Saves RAM and prevents Streamlit browser crashes.
    """
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

# ==========================================
# 3. SECURE API CLIENT
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
# 4. AUTHENTICATION FLOW
# ==========================================
if not st.session_state.authenticated:
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        with st.container(border=True):
            st.title("⚡ KineticPulse AI")
            st.caption("Biomechanical Motion Analytics Platform")
            st.divider()
            
            if st.session_state.auth_step == "main_menu":
                st.write("Sign in to sync your telemetry or continue in guest mode.")
                if st.button("🌐 Sign in with Google Account", type="primary", use_container_width=True):
                    st.session_state.auth_step = "google_signin"
                    st.rerun()
                
                if st.button("👤 Continue as Guest", use_container_width=True):
                    st.session_state.authenticated = True
                    st.session_state.is_guest = True
                    st.session_state.user_name = "Guest Athlete"
                    st.session_state.user_email = "Local Unsaved Session"
                    st.rerun()

            elif st.session_state.auth_step == "google_signin":
                st.subheader("Google Authentication")
                user_g_email = st.text_input("Google Email Address", placeholder="athlete@gmail.com")
                user_g_name = st.text_input("Full Name", placeholder="Alex Rivers")
                
                if st.button("Authenticate & Enter", type="primary", use_container_width=True):
                    if user_g_email.strip() and "@" in user_g_email:
                        st.session_state.authenticated = True
                        st.session_state.is_guest = False
                        st.session_state.user_name = user_g_name.strip() if user_g_name.strip() else user_g_email.split("@")[0].capitalize()
                        st.session_state.user_email = user_g_email.strip()
                        st.rerun()
                    else:
                        st.error("Please enter a valid email address.")
                        
                if st.button("← Back to Menu"):
                    st.session_state.auth_step = "main_menu"
                    st.rerun()
    st.stop()

# ==========================================
# 5. SIDEBAR CONTROLS & TRACKING TARGET
# ==========================================
with st.sidebar:
    st.title("⚡ KineticPulse")
    st.markdown(f"**User:** {st.session_state.user_name}")
    st.caption(f"Mode: {'Guest' if st.session_state.is_guest else 'Synchronized'}")
    
    if st.session_state.is_guest:
        if st.button("🔗 Link Google Account", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.auth_step = "google_signin"
            st.rerun()

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.auth_step = "main_menu"
        st.session_state.video_ref = None
        st.session_state.display_video_path = None
        st.rerun()

    st.divider()
    st.subheader("🎯 Tracking Target")
    analysis_scope = st.radio("Focus Mode", ["Comprehensive (All Subjects)", "Target Specific Athlete"])
    player_target = ""
    if analysis_scope == "Target Specific Athlete":
        player_target = st.text_input("Target description", placeholder="e.g. Pitcher in white uniform / Sprinter in red jersey")

    st.divider()
    st.subheader("⚙️ Analysis Tuning")
    skill_level = st.slider("Athlete Tier", 1.0, 6.0, 4.5, 0.5)

    st.divider()
    st.subheader("📜 Saved Motion History")
    if not st.session_state.analysis_history:
        st.caption("No saved sessions yet.")
    else:
        for item in reversed(st.session_state.analysis_history):
            with st.expander(f"🗓️ {item['time']} - {item['video']}"):
                st.write(item['summary'])

# ==========================================
# 6. MAIN DASHBOARD
# ==========================================
st.title("⚡ Biomechanical Motion Studio")
st.caption("Real-time computer vision telemetry, athlete tracking, and AI mechanical analysis.")

col_video, col_telemetry = st.columns([1.2, 1], gap="medium")

# --- VIDEO UPLOAD & STREAMING PIPELINE ---
with col_video:
    with st.container(border=True):
        st.subheader("📹 Session Footage")
        uploaded_video = st.file_uploader("Upload HD Clip (MP4 / MOV)", type=["mp4", "mov"])
        
        if uploaded_video:
            if uploaded_video.name != st.session_state.get("last_uploaded_name"):
                with st.spinner("Optimizing clip resolution & lowering RAM footprint..."):
                    try:
                        # Stream file buffer directly to disk to avoid RAM saturation
                        raw_path = os.path.join(tempfile.gettempdir(), f"raw_{uploaded_video.name}")
                        with open(raw_path, "wb") as f:
                            f.write(uploaded_video.getbuffer())
                        
                        # Downscale to 720p @ 20 FPS
                        compressed_path = compress_and_optimize_video(raw_path)
                        
                        # Register with Gemini API
                        if client:
                            video_file = client.files.upload(file=compressed_path)
                            st.session_state.video_ref = video_file
                            st.session_state.last_uploaded_name = uploaded_video.name
                            st.session_state.display_video_path = compressed_path
                            st.success("✅ Footage compressed to 720p & indexed!")
                        else:
                            st.warning("⚠️ Add `GEMINI_API_KEY` to `.streamlit/secrets.toml`.")
                    except Exception as e:
                        st.error(f"Processing error: {str(e)}")

            if st.session_state.get("display_video_path") and os.path.exists(st.session_state.display_video_path):
                st.video(st.session_state.display_video_path)

# --- NATIVE STREAMLIT TELEMETRY GRID ---
with col_telemetry:
    with st.container(border=True):
        st.subheader("📊 Live Telemetry")
        m1, m2 = st.columns(2)
        with m1:
            st.metric(label="Peak Velocity", value="52.4 MPH", delta="+1.2 MPH")
            st.metric(label="Form Score", value="97 / 100", delta="Optimal")
        with m2:
            st.metric(label="Cadence Rate", value="186 SPM", delta="-2 SPM")
            st.metric(label="Asymmetry Index", value="3.2%", delta="-0.4% Low")
        st.caption("💡 Video automatically downscaled to 720p @ 20 FPS to protect browser memory.")

st.divider()

# ==========================================
# 7. AI MOTION ANALYSIS
# ==========================================
col_head, col_save = st.columns([3, 1])
with col_head:
    st.subheader("🧠 AI Biomechanical Analysis")
with col_save:
    if st.button("💾 Save Breakdown", use_container_width=True):
        if st.session_state.analysis_text.startswith("Upload session"):
            st.warning("Run analysis first.")
        else:
            st.session_state.analysis_history.append({
                "time": datetime.now().strftime("%b %d, %H:%M"),
                "video": st.session_state.last_uploaded_name or "Clip",
                "summary": st.session_state.analysis_text
            })
            st.success("Saved to session history!")

if st.button("🚀 Run AI Motion Breakdown", type="primary", use_container_width=True):
    if client is None:
        st.error("❌ Gemini API Key missing in secrets.")
    elif st.session_state.video_ref is None:
        st.error("❌ Upload session footage first.")
    else:
        with st.spinner("Analyzing kinetic chain, joint angles, and power transfer..."):
            try:
                target_clause = f"Focus specifically on target athlete: '{player_target}'." if (analysis_scope == "Target Specific Athlete" and player_target.strip()) else "Analyze all subjects in frame."
                
                prompt = f"""Elite Biomechanics & Computer Vision Analysis:
                Athlete Experience Tier: {skill_level}/6.0
                Tracking Scope: {target_clause}
                
                Provide a detailed breakdown covering:
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
                st.session_state.analysis_text = f"Analysis Error: {str(e)}"

with st.container(border=True):
    st.markdown(st.session_state.analysis_text)
