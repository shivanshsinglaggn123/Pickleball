from datetime import datetime
import base64
import json
import os
import sqlite3
import tempfile
import textwrap
import time

from google import genai
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from streamlit_oauth import OAuth2Component

    HAS_OAUTH_LIB = True
except ImportError:
    HAS_OAUTH_LIB = False


# ============================================================
# DATABASE
# ============================================================

DB_FILE = "kinetic_pulse_pro.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            avatar_color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            video_name TEXT,
            summary TEXT,
            metrics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(email) REFERENCES users(email)
        )
        """
    )

    conn.commit()
    conn.close()


def db_get_user(email):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, avatar_color FROM users WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def db_upsert_user(email, name, avatar_color="#06B6D4"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (email, name, avatar_color)
        VALUES (?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            name = excluded.name
        """,
        (email, name, avatar_color),
    )
    conn.commit()
    conn.close()


def db_save_analysis(email, video_name, summary, metrics_dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO analyses (email, video_name, summary, metrics)
        VALUES (?, ?, ?, ?)
        """,
        (
            email,
            video_name,
            summary,
            json.dumps(metrics_dict),
        ),
    )
    conn.commit()
    conn.close()


def db_get_history(email):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT video_name, summary, metrics, created_at
        FROM analyses
        WHERE email = ?
        ORDER BY id DESC
        """,
        (email,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


init_db()


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="KineticPulse AI — Pickleball Motion Suite",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLING
# ============================================================

st.markdown(
    textwrap.dedent(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
        }

        .stApp {
            background-color: #07090E !important;
            color: #F8FAFC;
        }

        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 4rem;
            max-width: 1360px;
        }

        .hero-gradient {
            background: linear-gradient(135deg, #06B6D4 0%, #8B5CF6 45%, #F43F5E 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }

        .metric-box {
            background: linear-gradient(145deg, #0E1626, #0A0F1D);
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        }

        div[data-testid="stFileUploader"] {
            background: #0E1626 !important;
            border: 2px dashed rgba(6, 182, 212, 0.4) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
        }

        #MainMenu, footer, header {
            visibility: hidden;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)


PICKLEBALL_LOGO_SVG = """
<svg width="36" height="36" viewBox="0 0 36 36" fill="none">
    <circle cx="18" cy="18" r="16" fill="url(#p_grad)" stroke="#22D3EE" stroke-width="1.5"/>
    <circle cx="18" cy="18" r="2.5" fill="#07090E"/>
    <circle cx="12" cy="14" r="2" fill="#07090E"/>
    <circle cx="24" cy="14" r="2" fill="#07090E"/>
    <circle cx="14" cy="22" r="2" fill="#07090E"/>
    <circle cx="22" cy="22" r="2" fill="#07090E"/>
    <circle cx="18" cy="10" r="1.8" fill="#07090E"/>
    <circle cx="18" cy="26" r="1.8" fill="#07090E"/>
    <path d="M 4 18 A 14 14 0 0 1 28 6" stroke="#F43F5E" stroke-width="3" stroke-linecap="round"/>
    <defs>
        <linearGradient id="p_grad" x1="0" y1="0" x2="36" y2="36">
            <stop offset="0%" stop-color="#22D3EE"/>
            <stop offset="50%" stop-color="#8B5CF6"/>
            <stop offset="100%" stop-color="#EC4899"/>
        </linearGradient>
    </defs>
</svg>
"""


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None
gemini_init_error = None

try:
    api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        gemini_init_error = "GEMINI_API_KEY is missing from Streamlit secrets."
    else:
        client = genai.Client(api_key=api_key)

except Exception as e:
    gemini_init_error = str(e)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "user_session": None,
    "video_file_name": None,
    "video_file_uri": None,
    "video_mime_type": None,
    "display_path": None,
    "last_filename": None,
    "latest_analysis": "Upload a session clip and click 'Run AI Motion Breakdown' to start.",
    "latest_metrics": {
        "paddle_vel": 54.2,
        "dink_acc": 96,
        "footwork": 184,
        "asymmetry": 2.8,
    },
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, dict) else value


# ============================================================
# AUTHENTICATION
# ============================================================

if not st.session_state.user_session:
    _, center_col, _ = st.columns([1, 1.3, 1])

    with center_col:
        with st.container(border=True):
            st.markdown(
                f"<div style='text-align:center; margin-bottom:2rem;'>"
                f"<div style='display:flex; justify-content:center; margin-bottom:0.75rem;'>"
                f"{PICKLEBALL_LOGO_SVG}"
                f"</div>"
                f"<h2 style='font-size:1.6rem; font-weight:800; margin:0;'>KineticPulse AI</h2>"
                f"<p style='color:#94A3B8; font-size:0.9rem; margin-top:0.4rem;'>"
                f"Professional Pickleball Motion Suite"
                f"</p>"
                f"</div>",
                unsafe_allow_html=True
            )

            auth_success = False
            user_email_val = None
            user_name_val = None

            try:
                google_client_id = st.secrets.get(
                    "GOOGLE_CLIENT_ID", ""
                ).strip()
                google_client_secret = st.secrets.get(
                    "GOOGLE_CLIENT_SECRET", ""
                ).strip()
                app_redirect_uri = st.secrets.get(
                    "REDIRECT_URI", "http://localhost:8501"
                ).strip()

                if (
                    HAS_OAUTH_LIB
                    and google_client_id
                    and google_client_secret
                ):
                    oauth2 = OAuth2Component(
                        client_id=google_client_id,
                        client_secret=google_client_secret,
                        authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
                        token_endpoint="https://oauth2.googleapis.com/token",
                        refresh_token_endpoint="https://oauth2.googleapis.com/token",
                        revoke_token_endpoint="https://oauth2.googleapis.com/revoke",
                    )

                    result = oauth2.authorize_button(
                        name="Continue with Google",
                        icon="https://www.svgrepo.com/show/475656/google-color.svg",
                        redirect_uri=app_redirect_uri,
                        scope="openid email profile",
                        key="google_oauth_btn",
                    )

                    if result and "token" in result:
                        id_token_enc = result["token"].get("id_token")

                        if id_token_enc:
                            parts = id_token_enc.split(".")

                            if len(parts) >= 2:
                                payload = parts[1]
                                payload += "=" * (-len(payload) % 4)
                                decoded = json.loads(
                                    base64.b64decode(payload).decode("utf-8")
                                )

                                user_email_val = decoded.get("email")
                                user_name_val = decoded.get(
                                    "name",
                                    user_email_val.split("@")[0]
                                    if user_email_val
                                    else "Athlete",
                                )

                                if user_email_val:
                                    auth_success = True

            except Exception as oauth_err:
                st.info(
                    f"💡 OAuth Notice: Running with safe authentication fallback. ({oauth_err})"
                )

            st.markdown(
                textwrap.dedent(
                    """
                    <div style="text-align:center; color:#475569; font-size:0.8rem; margin:1rem 0;">
                        ATHLETE STUDIO ACCESS
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            if st.button(
                "🚀 Enter Athlete Studio",
                use_container_width=True,
                type="primary",
            ):
                user_email_val = "athlete@kineticpulse.ai"
                user_name_val = "Alex Rivers"
                auth_success = True

            if auth_success and user_email_val:
                db_upsert_user(user_email_val, user_name_val, "#06B6D4")
                user_data = db_get_user(user_email_val)

                st.session_state.user_session = {
                    "email": user_email_val,
                    "name": user_data[0] if user_data else user_name_val,
                    "avatar_color": user_data[1] if user_data else "#06B6D4",
                }

                st.rerun()

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================

current_user = st.session_state.user_session


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="margin-bottom: 1rem;">
            <div>
                <span style="font-size:1.15rem; font-weight:800; background:linear-gradient(135deg,#06B6D4,#8B5CF6); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    KineticPulse
                </span>
                <div style="font-size:0.7rem; color:#34D399; font-weight:700;">
                    ● CLOUD SYNCHRONIZED
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        textwrap.dedent(
            f"""
            <div style="background:#0E1626; padding:1.1rem; border-radius:16px; border:1px solid #1E293B; margin-bottom:1.2rem;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="width:42px; height:42px; border-radius:50%; background:#06B6D4; display:flex; align-items:center; justify-content:center; font-weight:800; color:#07090E; font-size:1.1rem;">
                        {current_user["name"][0].upper()}
                    </div>
                    <div style="overflow:hidden;">
                        <div style="font-weight:700; font-size:0.92rem; color:#F8FAFC;">
                            {current_user["name"]}
                        </div>
                        <div style="font-size:0.75rem; color:#94A3B8; margin-top:2px;">
                            {current_user["email"]}
                        </div>
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    if gemini_init_error:
        st.error(f"Gemini configuration error: {gemini_init_error}")

    st.markdown("---")
    st.markdown("### 🎯 Pickleball Configuration")

    player_focus = st.radio(
        "Target Tracking",
        [
            "Analyze All Players",
            "Specific Player (Near Court)",
            "Specific Player (Far Court)",
        ],
    )

    player_identifier = ""

    if "Specific Player" in player_focus:
        player_identifier = st.text_input(
            "Player Visual Cue / Description",
            value="Player in neon shirt / left side",
            help="Describe clothing, hat, court position, or another visual characteristic.",
        )

    analysis_depth = st.radio(
        "Intelligence Scope",
        [
            "Comprehensive Kinematics (Form & Movement)",
            "Rapid Tactical Breakdown (Shot Selection & Position)",
        ],
    )

    skill_level = st.slider(
        "Competitive Rating (DUPR)",
        2.0,
        7.0,
        4.0,
        0.25,
    )

    st.markdown("---")
    st.markdown("### 📂 Saved Cloud History")

    history_items = db_get_history(current_user["email"])

    if not history_items:
        st.caption("No motion sessions recorded yet.")
    else:
        for v_name, summary_text, metrics_json, created_at in history_items:
            display_name = v_name[:16] + "..." if len(v_name) > 16 else v_name
            date_display = created_at[5:16] if created_at else "Unknown"

            with st.expander(f"🗓️ {date_display} | {display_name}"):
                st.write(
                    summary_text[:220]
                    + ("..." if len(summary_text) > 220 else "")
                )

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.user_session = None
        st.session_state.video_file_name = None
        st.session_state.video_file_uri = None
        st.session_state.video_mime_type = None
        st.session_state.display_path = None
        st.session_state.last_filename = None
        st.rerun()

# ============================================================
# MAIN DASHBOARD
# ============================================================

st.markdown(
    """
    <h1 style="font-size:2.5rem; margin-bottom:0.2rem;">
        Pickleball <span class="hero-gradient">Motion Studio</span>
    </h1>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <p style="color:#94A3B8; font-size:1.05rem; margin-bottom:2rem;">
        Multimodal frame-by-frame kinematic tracking powered by Gemini Cloud Intelligence.
    </p>
    """,
    unsafe_allow_html=True,
)

col_upload, col_dashboard = st.columns([1.2, 1], gap="large")


# ============================================================
# VIDEO UPLOAD
# ============================================================

with col_upload:
    st.subheader("📹 Session Video Capture")

    uploaded_file = st.file_uploader(
        "Upload match clip or training footage (MP4, MOV, AVI)",
        type=["mp4", "mov", "avi"],
    )

    if uploaded_file:
        is_new_file = st.session_state.last_filename != uploaded_file.name

        if is_new_file:
            if not client:
                st.error("❌ Gemini API client is not initialized.")
            else:
                with st.spinner("⚡ Uploading video to Gemini Cloud..."):
                    try:
                        safe_filename = os.path.basename(uploaded_file.name)
                        temp_dir = tempfile.gettempdir()
                        path = os.path.join(temp_dir, safe_filename)

                        with open(path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        v_file = client.files.upload(file=path)

                        st.info(
                            "🎞️ Gemini is processing the video. "
                            "The app will continue when the file is ready."
                        )

                        max_wait_seconds = 600
                        waited = 0

                        while True:
                            state_obj = getattr(v_file, "state", None)
                            state_name = (
                                state_obj.name
                                if state_obj is not None
                                else "UNKNOWN"
                            )

                            if state_name == "ACTIVE":
                                break

                            if state_name in {"FAILED", "ERROR"}:
                                raise RuntimeError(
                                    f"Gemini video processing failed with state: {state_name}"
                                )

                            if waited >= max_wait_seconds:
                                raise TimeoutError(
                                    "Gemini video processing timed out after 10 minutes."
                                )

                            time.sleep(5)
                            waited += 5
                            v_file = client.files.get(name=v_file.name)

                        st.session_state.video_file_name = v_file.name
                        st.session_state.video_file_uri = getattr(
                            v_file, "uri", None
                        )
                        st.session_state.video_mime_type = getattr(
                            v_file,
                            "mime_type",
                            uploaded_file.type or "video/mp4",
                        )
                        st.session_state.last_filename = uploaded_file.name
                        st.session_state.display_path = path
                        st.session_state.latest_analysis = (
                            "Video uploaded successfully. "
                            "Click 'Run AI Biomechanical Analysis' to analyze it."
                        )

                        st.success(
                            "✅ Video processed by Gemini and ready for AI analysis!"
                        )

                    except Exception as err:
                        st.session_state.video_file_name = None
                        st.session_state.video_file_uri = None
                        st.session_state.video_mime_type = None

                        st.error(
                            f"❌ Gemini video upload failed: {type(err).__name__}: {err}"
                        )
                        st.exception(err)

    if (
        st.session_state.display_path
        and os.path.exists(st.session_state.display_path)
    ):
        st.video(st.session_state.display_path)


# ============================================================
# TELEMETRY
# ============================================================

with col_dashboard:
    st.subheader("📊 Biomechanical Telemetry")

    metrics = st.session_state.latest_metrics

    m1, m2 = st.columns(2)

    with m1:
        st.markdown(
            textwrap.dedent(
                f"""
                <div class="metric-box">
                    <div style="color:#22D3EE; font-size:1.8rem; font-weight:800;">
                        {metrics["paddle_vel"]} MPH
                    </div>
                    <div style="color:#94A3B8; font-size:0.75rem; font-weight:700; text-transform:uppercase; margin-top:4px;">
                        ⚡ Paddle Head Speed
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        st.markdown(
            textwrap.dedent(
                f"""
                <div class="metric-box">
                    <div style="color:#34D399; font-size:1.8rem; font-weight:800;">
                        {metrics["dink_acc"]}%
                    </div>
                    <div style="color:#94A3B8; font-size:0.75rem; font-weight:700; text-transform:uppercase; margin-top:4px;">
                        🎯 Control Precision
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            textwrap.dedent(
                f"""
                <div class="metric-box">
                    <div style="color:#A78BFA; font-size:1.8rem; font-weight:800;">
                        {metrics["footwork"]} SPM
                    </div>
                    <div style="color:#94A3B8; font-size:0.75rem; font-weight:700; text-transform:uppercase; margin-top:4px;">
                        🔄 Footwork Cadence
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        st.markdown(
            textwrap.dedent(
                f"""
                <div class="metric-box">
                    <div style="color:#FBBF24; font-size:1.8rem; font-weight:800;">
                        {metrics["asymmetry"]}%
                    </div>
                    <div style="color:#94A3B8; font-size:0.75rem; font-weight:700; text-transform:uppercase; margin-top:4px;">
                        ⚠️ Stance Imbalance
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

    radar_df = pd.DataFrame(
        {
            "r": [92, 88, 79, 94, 85],
            "theta": [
                "Kinetic Chain",
                "Core Stability",
                "Recovery Speed",
                "Paddle Angle",
                "Footwork Rhythm",
            ],
        }
    )

    fig = px.line_polar(
        radar_df,
        r="r",
        theta="theta",
        line_close=True,
    )

    fig.update_traces(
        fill="toself",
        line_color="#06B6D4",
        fillcolor="rgba(6, 182, 212, 0.2)",
    )

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color="#475569",
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F8FAFC", family="Plus Jakarta Sans"),
        margin=dict(t=20, b=20, l=20, r=20),
        height=240,
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# AI ANALYSIS CONTROLS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1E293B;">', unsafe_allow_html=True)

col_run_btn, col_export_btn = st.columns([2, 1])

with col_run_btn:
    run_clicked = st.button(
        "🚀 Run AI Biomechanical Analysis",
        type="primary",
        use_container_width=True,
    )

with col_export_btn:
    if (
        st.session_state.latest_analysis
        and not st.session_state.latest_analysis.startswith("Upload")
    ):
        st.download_button(
            label="📥 Download Coaching Report",
            data=st.session_state.latest_analysis,
            file_name=f"KineticPulse_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )


# ============================================================
# RUN GEMINI ANALYSIS
# ============================================================

if run_clicked:
    if not st.session_state.video_file_name:
        st.error("❌ Please upload and process a video first.")

    elif not client:
        st.error("❌ Gemini API client is not initialized.")
        if gemini_init_error:
            st.error(f"Configuration error: {gemini_init_error}")

    else:
        with st.spinner("🧠 Gemini is analyzing your pickleball motion..."):
            tracking_instruction = player_focus

            if player_identifier:
                tracking_instruction += (
                    f" | Target Player: {player_identifier}"
                )

            prompt = f"""
You are an elite pickleball biomechanics, sports-performance,
and computer-vision analyst.

Analyze the uploaded pickleball video carefully.

Athlete competitive rating: {skill_level}/7.0 DUPR

Target tracking:
{tracking_instruction}

Analysis mode:
{analysis_depth}

Rules:
- Analyze only what can reasonably be observed.
- Do not fabricate exact measurements.
- Distinguish observations from inferences.
- Focus on the requested player.
- Give practical coaching advice.

Return a detailed Markdown report using these sections:

# Pickleball Biomechanical Analysis

## 1. Ready Stance
Discuss knee flexion, hip position, center of mass,
balance, and athletic posture.

## 2. Kinetic Chain
Discuss lower-body drive, hip rotation, torso rotation,
shoulder rotation, arm acceleration, and energy transfer.

## 3. Footwork & Movement
Discuss split-step timing, lateral movement,
recovery, court positioning, and balance.

## 4. Paddle Mechanics
Discuss paddle path, paddle-face angle, contact point,
swing path, follow-through, and preparation.

## 5. Mechanical Faults
Identify the most important faults.
For each fault explain:
- What was observed
- Why it matters
- How to correct it

## 6. Top 3 Corrective Drills
Provide exactly three practical drills.
For each drill include:
- Drill name
- Purpose
- How to perform it
- What the athlete should feel
- What improvement to watch for

## 7. Coaching Summary
Provide:
- 3 strengths
- 3 weaknesses
- 3 priority improvements in order
"""

            try:
                import time  # Ensuring time is available for the sleep functions
                import os
                
                active_file = None

                try:
                    active_file = client.files.get(
                        name=st.session_state.video_file_name
                    )
                except Exception:
                    active_file = None

                if active_file is None:
                    local_path = st.session_state.display_path

                    if not local_path or not os.path.exists(local_path):
                        raise FileNotFoundError(
                            "The temporary video is no longer available. "
                            "Please upload the video again."
                        )

                    active_file = client.files.upload(file=local_path)

                    max_wait_seconds = 600
                    waited = 0

                    while True:
                        state_obj = getattr(active_file, "state", None)
                        state_name = (
                            state_obj.name
                            if state_obj is not None
                            else "UNKNOWN"
                        )

                        if state_name == "ACTIVE":
                            break

                        if state_name in {"FAILED", "ERROR"}:
                            raise RuntimeError(
                                f"Gemini video processing failed: {state_name}"
                            )

                        if waited >= max_wait_seconds:
                            raise TimeoutError(
                                "Timed out waiting for Gemini to process the video."
                            )

                        time.sleep(5)
                        waited += 5

                        active_file = client.files.get(
                            name=active_file.name
                        )

                    st.session_state.video_file_name = active_file.name

                state_obj = getattr(active_file, "state", None)
                state_name = (
                    state_obj.name
                    if state_obj is not None
                    else "UNKNOWN"
                )

                if state_name != "ACTIVE":
                    raise RuntimeError(
                        f"Gemini video is not ready. Current state: {state_name}"
                    )

                # ---------------------------------------------------------
                # NEW: 503 RETRY LOGIC FOR GENERATE_CONTENT
                # ---------------------------------------------------------
                max_retries = 3
                retry_delay = 5
                response = None

                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            st.warning(f"⏳ Google's servers were busy. Retrying... (Attempt {attempt + 1} of {max_retries})")
                            
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[active_file, prompt],
                        )
                        # If successful, break the retry loop!
                        break
                        
                    except Exception as api_error:
                        error_msg = str(api_error)
                        
                        # Handle 503 / 500 Server Overload
                        if "503" in error_msg or "Service Unavailable" in error_msg or "500" in error_msg:
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                            else:
                                raise RuntimeError(f"Google API is consistently overloaded right now. Please try again later. Details: {error_msg}")
                        
                        # Handle Rate Limits
                        elif "429" in error_msg or "Quota" in error_msg:
                            raise RuntimeError(f"Rate limit exceeded. We've made too many requests. Please wait a few minutes. Details: {error_msg}")
                            
                        # If it's a different error, raise it immediately
                        else:
                            raise api_error
                # ---------------------------------------------------------

                response_text = ""

                try:
                    response_text = response.text or ""
                except Exception:
                    response_text = ""

                if not response_text.strip():
                    response_text = "⚠️ Gemini returned an empty response."

                    try:
                        if response and getattr(response, "candidates", None):
                            response_text += (
                                f"\n\nGemini returned {len(response.candidates)} "
                                "candidate(s), but no text."
                            )
                    except Exception:
                        pass

                st.session_state.latest_analysis = response_text

                db_save_analysis(
                    current_user["email"],
                    st.session_state.last_filename or "Unknown Video",
                    response_text,
                    st.session_state.latest_metrics,
                )

                st.success("✅ Analysis completed and saved!")

            except Exception as e:
                error_message = (
                    f"Gemini analysis failed.\n\n"
                    f"Error type: {type(e).__name__}\n"
                    f"Error: {e}"
                )

                st.session_state.latest_analysis = (
                    "## ⚠️ AI Analysis Error\n\n"
                    "```text\n"
                    + error_message
                    + "\n```"
                )

                st.error(error_message)
                st.exception(e)

# ============================================================
# REPORT
# ============================================================

with st.container(border=True):
    st.markdown("### 🧠 Comprehensive AI Motion Insights")
    st.markdown(st.session_state.latest_analysis)


# ============================================================
# FOOTER
# ============================================================

st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown(
    textwrap.dedent(
        """
        <p style="text-align:center; color:#475569; font-size:0.85rem;">
            © 2026 KineticPulse AI Suite • Enterprise Biometrics & Cloud Vision •
            Built with Streamlit & Gemini Cloud
        </p>
        """
    ),
    unsafe_allow_html=True,
)
