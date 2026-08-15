import streamlit as st
import cv2
import tempfile

st.set_page_config(page_title="Pickleball Analytics Engine", layout="centered")
st.title("🏓 AI Pickleball Physics & Biomechanics Coach")
st.write("Upload a video of your pickleball serve to analyze your mechanics and ball trajectory.")

uploaded_video = st.file_uploader("Upload an MP4 video", type=["mp4", "mov"])

if uploaded_video is not None:
    st.success("Video successfully uploaded!")
    
    # Save temporarily to read video properties
    tfile = tempfile.NamedTemporaryFile(delete=False) 
    tfile.write(uploaded_video.read())
    
    # Open with OpenCV to get basic stats
    cap = cv2.VideoCapture(tfile.name)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    st.video(tfile.name)
    
    # Display quick diagnostic stats
    st.markdown("### 📊 Video Diagnostics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Framerate", f"{fps:.1f} FPS")
    col2.metric("Total Frames", frame_count)
    col3.metric("Duration", f"{duration:.2f} sec")
    
    cap.release()
else:
    st.warning("Please upload a video to begin analysis.")
