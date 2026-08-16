import streamlit as st
import tempfile
import os
from google import genai

# Page Configuration & Professional Styling
st.set_page_config(
    page_title="AI Pickleball Biomechanics Coach",
    page_icon="🏓",
    layout="centered"
)

st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0rem;
    }
    .subtitle {
        color: #4B5563;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    .stCard {
        background-color: #F8FAFC;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🏓 AI Pickleball Biomechanics Coach</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload high-definition gameplay footage up to 1 GB for expert-level coaching analysis.</p>', unsafe_allow_html=True)

# Securely load API key from Streamlit Cloud secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    api_key = ""

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Coaching Settings")
    shot_type = st.selectbox("Select Shot Type", ["Forehand Drive", "Backhand Slice", "Serve", "Dink", "Volley"])
    skill_level = st.slider("Player Skill Level (DUPR)", 1.0, 6.0, 3.5, 0.5)
    
    st.markdown("---")
    st.subheader("👥 Player Focus")
    analysis_scope = st.radio(
        "Who should the coach evaluate?",
        ["All players in the video", "Specific player (describe below)"]
    )
    
    player_target = ""
    if analysis_scope == "Specific player (describe below)":
        player_target = st.text_input("Player Description", placeholder="e.g. Player in the blue shirt on the near side")

# Initialize Session State to cache the uploaded video reference
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "video_file_ref" not in st.session_state:
    st.session_state.video_file_ref = None

# Main Uploader Section (Supports up to 1GB via config.toml)
uploaded_video = st.file_uploader("Upload your pickleball video (MP4 or MOV)", type=["mp4", "mov"])

if uploaded_video is not None:
    st.success("Video successfully loaded into memory!")
    st.video(uploaded_video)
    
    # Process and cache video with Gemini if it's a new upload
    if uploaded_video.name != st.session_state.uploaded_file_name:
        with st.spinner("Uploading video to Gemini AI..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tfile.write(uploaded_video.read())
                tfile.close()
                
                client = genai.Client(api_key=api_key)
                st.session_state.video_file_ref = client.files.upload(file=tfile.name)
                st.session_state.uploaded_file_name = uploaded_video.name
                os.unlink(tfile.name)
            except Exception as e:
                st.error(f"Error uploading video: {e}")

    # Instant re-analysis trigger (No re-upload wait when changing shot types)
    if st.button("🚀 Run AI Analysis", type="primary"):
        if not api_key:
            st.error("Gemini API key is missing from Streamlit secrets. Please configure it in your app settings.")
        elif not st.session_state.video_file_ref:
            st.error("Please wait for the video upload to finish processing.")
        else:
            with st.spinner("Analyzing movement and generating coaching feedback..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    # Target definition for multi-player scenarios
                    target_instruction = f"Focus specifically on: {player_target}." if player_target else "Evaluate all players visible in the clip and give feedback for each."
                    
                    # Natural, conversational prompt avoiding robotic angle commands
                    prompt = f"""
                    You are a friendly, encouraging, and expert pickleball coach. Review this video clip focusing on a {shot_type}. 
                    Player skill level context: DUPR {skill_level}.
                    {target_instruction}
                    
                    Provide feedback in a warm, natural coaching tone. Avoid rigid mechanical or numerical angle instructions. Instead, explain concepts simply and clearly, highlighting what is going well and giving 2-3 practical, easy-to-understand adjustments to improve consistency, footwork, and power.
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=[st.session_state.video_file_ref, prompt]
                    )
                    
                    st.markdown("---")
                    st.subheader("📊 Personalized Coaching Breakdown")
                    st.markdown(f'<div class="stCard">{response.text}</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"An error occurred during AI processing: {e}")
else:
    st.info("💡 Tip: Once your video is uploaded, you can instantly switch between shot types (like Forehand to Backhand) and click re-analyze without waiting to upload again.")
