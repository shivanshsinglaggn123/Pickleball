import streamlit as st
import tempfile
import os
from google import genai

# Page Configuration
st.set_page_config(
    page_title="AI Pickleball Physics & Biomechanics Coach",
    page_icon="🏓",
    layout="centered"
)

st.title("🏓 AI Pickleball Biomechanics Coach")
st.write("Upload your gameplay video for real multimodal AI video analysis.")

# Securely load and clean API key from Streamlit Cloud secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    api_key = ""

# Sidebar for Additional Settings
with st.sidebar:
    st.header("⚙️ Configuration")
    shot_type = st.selectbox("Select Shot Type", ["Forehand Drive", "Backhand Slice", "Serve", "Dink"])
    skill_level = st.slider("Player Skill Level (DUPR)", 1.0, 6.0, 3.5, 0.5)

# Main Uploader Section
uploaded_video = st.file_uploader("Upload your pickleball video (MP4 or MOV)", type=["mp4", "mov"])

if uploaded_video is not None:
    st.success("Video successfully uploaded!")
    st.video(uploaded_video)
    
    if st.button("🚀 Run Real-Time AI Video Analysis", type="primary"):
        if not api_key:
            st.error("Gemini API key is missing from Streamlit secrets. Please configure it in your app settings.")
        else:
            with st.spinner("Uploading video to Gemini AI and analyzing biomechanics..."):
                try:
                    # Save uploaded video temporarily
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(uploaded_video.read())
                    tfile.close()
                    
                    # Initialize Modern GenAI Client (supports AQ. keys)
                    client = genai.Client(api_key=api_key)
                    
                    # Upload file to Gemini Files API
                    video_file = client.files.upload(file=tfile.name)
                    
                    # Craft prompt for Gemini
                    prompt = f"""
                    You are an elite pickleball coach and biomechanics expert. Analyze this video of a player executing a {shot_type}. 
                    The player's self-assessed skill level is DUPR {skill_level}.
                    
                    Provide your response structured with:
                    1. Peak Velocity Estimate (e.g. 38.5 MPH)
                    2. Knee Bend Angle Estimate (e.g. 135°)
                    3. Form Score (out of 100)
                    4. Specific, highly tailored coaching feedback detailing what they did right and what exact mechanical adjustments they need to make based directly on what you observe in this video file.
                    """
                    
                    # Generate response using Gemini Flash via modern SDK
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[video_file, prompt]
                    )
                    
                    st.markdown("---")
                    st.subheader("📊 AI Biomechanics & Performance Report")
                    st.write(response.text)
                    
                    # Clean up local temp file
                    os.unlink(tfile.name)
                    
                except Exception as e:
                    st.error(f"An error occurred during AI processing: {e}")
else:
    st.warning("Awaiting video upload. Drop an MP4 clip above to begin.")
