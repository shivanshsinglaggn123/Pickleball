import streamlit as st
import tempfile
import os
import google.generativeai as genai

# Page Configuration
st.set_page_config(
    page_title="AI Pickleball Physics & Biomechanics Coach",
    page_icon="🏓",
    layout="centered"
)

st.title("🏓 AI Pickleball Biomechanics Coach")
st.write("Upload your gameplay video for real multimodal AI video analysis.")

# Sidebar for API Key & Settings
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", value=st.secrets.get("GEMINI_API_KEY", ""))
    shot_type = st.selectbox("Select Shot Type", ["Forehand Drive", "Backhand Slice", "Serve", "Dink"])
    skill_level = st.slider("Player Skill Level (DUPR)", 1.0, 6.0, 3.5, 0.5)

# Main Uploader Section
uploaded_video = st.file_uploader("Upload your pickleball video (MP4 or MOV)", type=["mp4", "mov"])

if uploaded_video is not None:
    st.success("Video successfully uploaded!")
    st.video(uploaded_video)
    
    if st.button("🚀 Run Real-Time AI Video Analysis", type="primary"):
        if not api_key:
            st.error("Please enter your Gemini API key in the sidebar to run the analysis.")
        else:
            with st.spinner("Uploading video to Gemini AI and analyzing biomechanics..."):
                try:
                    # Save uploaded video temporarily
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(uploaded_video.read())
                    tfile.close()
                    
                    # Configure Gemini API
                    genai.configure(api_key=api_key)
                    
                    # Upload file to Gemini Files API
                    video_file = genai.upload_file(path=tfile.name)
                    
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
                    
                    # Use gemini-1.5-flash for stable multimodal video analysis
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                    response = model.generate_content([video_file, prompt])
                    
                    st.markdown("---")
                    st.subheader("📊 AI Biomechanics & Performance Report")
                    st.write(response.text)
                    
                    # Clean up local temp file
                    os.unlink(tfile.name)
                    
                except Exception as e:
                    st.error(f"An error occurred during AI processing: {e}")
else:
    st.warning("Awaiting video upload. Drop an MP4 clip above to begin.")
