import streamlit as st
import tempfile
import os
from google import genai
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Pickleball Biomechanics Coach",
    page_icon="🏓",
    layout="wide"
)

# --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
    <style>
    /* Main Container Styling */
    .main .block-container {
        background-color: #FAFAFA;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #1E3A8A; /* Deep Blue */
        font-weight: 600;
    }
    
    /* KPI Card Styling */
    .kpi-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #E5E7EB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #6B7280;
        text-transform: uppercase;
    }

    /* Interactive Buttons Styling */
    .inactive-btn {
        background-color: #F3F4F6;
        color: #374151;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: 1px solid #D1D5DB;
        text-align: center;
        font-weight: 500;
    }
    .active-btn {
        background-color: #2563EB;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: 1px solid #2563EB;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }
    
    /* Coaching Breakdown Box */
    .coaching-box {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        color: #374151;
        line-height: 1.6;
        min-height: 150px;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- HEADER & USER PROFILE ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("AI Pickleball Biomechanics Coach")
with col_h2:
    st.markdown("""
        <div style='display: flex; align-items: center; justify-content: flex-end; gap: 10px; padding: 10px; background-color: white; border-radius: 50px; border: 1px solid #E5E7EB;'>
            <span style='font-weight: 600; color: #1E3A8A;'>Shivansh's Dashboard</span>
            <img src='https://api.dicebear.com/8.x/adventurer/svg?seed=Shivansh' style='width: 40px; height: 40px; border-radius: 50%; border: 2px solid #2563EB;'>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("📹 **Analyze Video**")
    st.markdown("📜 **History**")
    st.markdown("⚙️ **Settings**")
    
    st.markdown("---")
    st.markdown("## Player Profile")
    shot_type = st.selectbox("Shot Type", ["Forehand Drive", "Backhand Slice", "Serve", "Dink", "Volley"])
    st.markdown("## Coaching Settings")
    skill_level = st.slider("Skill Level (DUPR)", 1.0, 6.0, 3.5, 0.5)

# --- SECURE API KEY LOAD ---
try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    api_key = ""
    st.error("API Key not found in secrets. Please configure it.")

# --- SESSION STATE FOR CACHING ---
if "video_ref" not in st.session_state:
    st.session_state.video_ref = None
if "active_shot" not in st.session_state:
    st.session_state.active_shot = "Forehand Drive"
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = "Upload a video and click 'Run Analysis' to receive your personalized coaching breakdown here."

# --- MAIN LAYOUT (2 Columns) ---
col_video, col_insights = st.columns([2, 1])

with col_video:
    st.subheader("Uploaded Pickleball match clip")
    uploaded_video = st.file_uploader("Choose an MP4 or MOV video", type=["mp4", "mov"])
    
    if uploaded_video:
        st.video(uploaded_video)
        
        if st.session_state.video_ref is None or uploaded_video.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("Uploading video to Gemini AI..."):
                try:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(uploaded_video.read())
                    tfile.close()
                    
                    client = genai.Client(api_key=api_key)
                    st.session_state.video_ref = client.files.upload(file=tfile.name)
                    st.session_state.last_uploaded_name = uploaded_video.name
                    os.unlink(tfile.name)
                    st.success("Video processed successfully.")
                except Exception as e:
                    st.error(f"Error processing video: {e}")

with col_insights:
    st.subheader("Quick Insights")
    c1, c2, c3 = st.columns(3)
    
    kpi_data = [("Ball Speed", "42 MPH"), ("Spin RPM", "1800"), ("Footwork", "88/100")]
    for col, (label, value) in zip([c1, c2, c3], kpi_data):
        with col:
            st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-value'>{value}</div>
                    <div class='kpi-label'>{label}</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("### Analysis Focus")
    b_col1, b_col2 = st.columns(2)
    
    with b_col1:
        if st.button("Forehand Drive"):
            st.session_state.active_shot = "Forehand Drive"
            st.rerun()
            
    with b_col2:
        if st.button("Backhand Slice"):
            st.session_state.active_shot = "Backhand Slice"
            st.rerun()

    if st.session_state.active_shot == "Forehand Drive":
        b_col1.markdown("<div class='active-btn'>Forehand Drive</div>", unsafe_allow_html=True)
        b_col2.markdown("<div class='inactive-btn'>Backhand Slice</div>", unsafe_allow_html=True)
    else:
        b_col1.markdown("<div class='inactive-btn'>Forehand Drive</div>", unsafe_allow_html=True)
        b_col2.markdown("<div class='active-btn'>Backhand Slice</div>", unsafe_allow_html=True)


# --- EXPERT COACHING BREAKDOWN ---
st.markdown("<br>", unsafe_allow_html=True)
st.header("Expert Coaching Breakdown")

run_btn = st.button("🚀 Run Analysis", type="primary")

if run_btn:
    if not api_key:
        st.error("API Key missing.")
    elif not st.session_state.video_ref:
        st.error("Please upload a video first.")
    else:
        with st.spinner(f"Generating {st.session_state.active_shot} analysis with Gemini 3.5 Flash..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = f"""
                You are an elite pickleball coach providing feedback on a {st.session_state.active_shot}.
                The player's skill level is DUPR {skill_level}.
                
                Analyze the video clip for biomechanics, footwork, and technique.
                Provide feedback in a friendly, encouraging, and simple tone. 
                Avoid rigid angle instructions (e.g., "go to 45 degrees"). 
                Instead, explain concepts simply and give 2-3 practical adjustments.
                """
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[st.session_state.video_ref, prompt]
                )
                
                st.session_state.analysis_text = response.text
                
            except Exception as e:
                st.session_state.analysis_text = f"An error occurred during AI processing: {e}"

st.markdown(f"<div class='coaching-box'>{st.session_state.analysis_text}</div>", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
c_foot1, c_foot2 = st.columns([3, 1])
with c_foot1:
    st.markdown("© Copyright Shivansh Singla. Built for College Portfolio.")
with c_foot2:
    st.markdown("Contact Us")
