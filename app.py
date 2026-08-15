import streamlit as st

st.set_page_config(page_title="Pickleball Analytics Engine", layout="centered")
st.title("🏓 AI Pickleball Physics & Biomechanics Coach")
st.write("Upload a video of your pickleball serve to analyze your mechanics and ball trajectory.")

uploaded_video = st.file_uploader("Upload an MP4 video", type=["mp4", "mov"])

if uploaded_video is not None:
    st.success("Video successfully uploaded! (AI Processing module active...)")
    st.video(uploaded_video)
else:
    st.warning("Please upload a video to begin analysis.")
