import os
import tempfile
import streamlit as st
from google import genai

# Page configuration
st.set_page_config(
    page_title="Gemini Streamlit App",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Gemini AI Assistant")
st.write("Powered by the official Google `google-genai` SDK.")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    
    # Check for environment variable first, allow manual override
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("Gemini API Key", value=env_api_key, type="password")
    
    api_key = api_key_input or env_api_key
    
    model_choice = st.selectbox(
        "Select Model",
        ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.7-flash"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### Instructions")
    st.markdown("1. Enter your API key.\n2. Type your prompt or upload a file.\n3. Click **Generate**.")

# Validation check for API key
if not api_key:
    st.warning("⚠️ Please enter your Gemini API Key in the sidebar or set your `GEMINI_API_KEY` environment variable to begin.")
    st.stop()

# Initialize the official google-genai client
client = genai.Client(api_key=api_key)

# Main input interface
user_prompt = st.text_area("Your Prompt:", placeholder="Ask something or give instructions...")

uploaded_file = st.file_uploader("Upload a file (optional)", type=["txt", "pdf", "png", "jpg", "jpeg", "csv"])

if st.button("Generate Response", type="primary"):
    if not user_prompt.strip():
        st.error("Please provide a prompt before generating.")
    else:
        with st.spinner("Generating response..."):
            try:
                contents = [user_prompt]
                
                # Handle file upload if provided
                if uploaded_file is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    # Upload using the modern client files API
                    file_ref = client.files.upload(file=tmp_path)
                    contents.append(file_ref)
                    
                    # Clean up temporary local file
                    os.unlink(tmp_path)

                # Generate content from the selected model
                response = client.models.generate_content(
                    model=model_choice,
                    contents=contents
                )
                
                st.markdown("### Output")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
