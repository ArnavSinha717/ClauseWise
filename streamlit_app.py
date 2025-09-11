import streamlit as st
import requests
import os  # <-- This line was missing
from typing import Dict, Any, List

# --- Page Configuration ---
st.set_page_config(
    page_title="ClauseWise - Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- API Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# --- Session State Initialization ---
# This ensures that variables persist across user interactions
def initialize_session_state():
    defaults = {
        "document_id": None,
        "document_name": "",
        "simplified_text": None,
        "risk_assessment": None,
        "translated_text": None,
        "chat_history": [],
        "sources": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- API Communication Functions ---
# These functions handle all requests to the backend API

def check_backend_health() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def get_supported_languages() -> Dict[str, str]:
    try:
        response = requests.get(f"{API_BASE_URL}/supported-languages", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        return {"en": "English", "hi": "Hindi"}
    return {"en": "English", "hi": "Hindi"}

def upload_document(file) -> tuple[bool, Dict[str, Any]]:
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{API_BASE_URL}/upload-document", files=files, timeout=60)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        return False, {"error": error_detail}

def simplify_document(doc_id: str) -> tuple[bool, Dict[str, Any]]:
    try:
        response = requests.post(f"{API_BASE_URL}/simplify", json={"document_id": doc_id}, timeout=90)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        return False, {"error": error_detail}

def assess_risk(doc_id: str) -> tuple[bool, Dict[str, Any]]:
    try:
        response = requests.post(f"{API_BASE_URL}/assess-risk", json={"document_id": doc_id}, timeout=90)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        return False, {"error": error_detail}

def chat_with_document(doc_id: str, question: str, lang: str) -> tuple[bool, Dict[str, Any]]:
    try:
        payload = {"document_id": doc_id, "question": question, "language": lang}
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=90)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        return False, {"error": error_detail}

def translate_text(text: str, lang: str) -> tuple[bool, Dict[str, Any]]:
    try:
        payload = {"text": text, "target_language": lang}
        response = requests.post(f"{API_BASE_URL}/translate", json=payload, timeout=90)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        return False, {"error": error_detail}

# --- UI Rendering Functions ---

def render_sidebar(language_options: Dict[str, str]):
    with st.sidebar:
        st.title("⚖️ ClauseWise")
        
        if check_backend_health():
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Offline")
            st.warning("Please start the backend server to use the app.")
            st.stop()

        st.header("Settings")
        selected_language = st.selectbox(
            "Select Language:",
            options=list(language_options.keys()),
            format_func=lambda x: language_options.get(x, x),
            index=0
        )
        
        st.info("💡 Using Gemini Free Tier. Please wait between requests to avoid rate limits.")
        st.markdown("---")
        st.subheader("📚 Legal Knowledge Base")
        st.markdown("""
        To enhance legal knowledge:
        1. Add PDF/CSV/JSON files to `backend/legal_datasets/`
        2. Restart the backend server.
        """)
    return selected_language

def render_main_content(selected_language: str, lang_name: str):
    st.title("Legal AI Assistant")
    st.markdown("Upload a legal document to simplify, assess risks, and ask questions.")

    # --- Document Upload Section ---
    with st.container(border=True):
        st.header("📄 1. Upload & Process Document")
        uploaded_file = st.file_uploader(
            "Upload a PDF legal document", type=["pdf"],
            help="Max file size 10MB"
        )
        
        if uploaded_file:
            if st.button("Process Document", type="primary"):
                with st.spinner("Processing document... This may take a moment."):
                    success, result = upload_document(uploaded_file)
                    if success:
                        # Reset state for new document
                        initialize_session_state() 
                        st.session_state.document_id = result["document_id"]
                        st.session_state.document_name = result["filename"]
                        st.success(f"✅ Document '{result['filename']}' processed successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown processing error')}")

    if not st.session_state.document_id:
        st.info("Please upload and process a document to begin analysis.")
        st.stop()

    st.success(f"**Active Document:** `{st.session_state.document_name}`")

    # --- Analysis & Chat Columns ---
    col1, col2 = st.columns(2)

    # --- Analysis Column ---
    with col1:
        with st.container(border=True):
            st.header("🔍 2. Analyze Document")
            
            if st.button("Simplify Document"):
                with st.spinner("Generating simplified summary..."):
                    success, result = simplify_document(st.session_state.document_id)
                    if success:
                        st.session_state.simplified_text = result["simplified_text"]
                    else:
                        st.error(f"❌ Simplification Error: {result.get('error')}")

            if st.button("Assess Risks"):
                with st.spinner("Performing risk assessment..."):
                    success, result = assess_risk(st.session_state.document_id)
                    if success:
                        st.session_state.risk_assessment = result["risk_assessment"]
                    else:
                        st.error(f"❌ Risk Assessment Error: {result.get('error')}")
            
            if st.session_state.simplified_text and selected_language != "en":
                if st.button(f"Translate Summary to {lang_name}"):
                    with st.spinner(f"Translating..."):
                        success, result = translate_text(st.session_state.simplified_text, selected_language)
                        if success:
                            st.session_state.translated_text = result["translated_text"]
                        else:
                            st.error(f"❌ Translation Error: {result.get('error')}")

        # --- Results Display ---
        if st.session_state.simplified_text or st.session_state.risk_assessment:
            with st.container(border=True):
                st.header("📋 Analysis Results")
                if st.session_state.simplified_text:
                    with st.expander("📖 Simplified Summary", expanded=True):
                        st.markdown(st.session_state.simplified_text)
                
                if st.session_state.risk_assessment:
                    with st.expander("⚠️ Risk Assessment", expanded=True):
                        st.markdown(st.session_state.risk_assessment)

                if st.session_state.translated_text:
                    with st.expander(f"🌐 Translation ({lang_name})", expanded=True):
                        st.markdown(st.session_state.translated_text)

    # --- Chat Column ---
    with col2:
        with st.container(border=True):
            st.header("💬 3. Chat with Document")
            
            # Display chat history
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input
            if prompt := st.chat_input("Ask a question about the document..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.spinner("Thinking..."):
                    success, result = chat_with_document(st.session_state.document_id, prompt, selected_language)
                    
                    if success:
                        response_text = result["answer"]
                        sources = result.get("sources", [])
                        if sources:
                            response_text += f"\n\n*Sources: {', '.join(sources)}*"
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                        st.rerun()
                    else:
                        error_message = f"❌ Error: {result.get('error', 'Could not get an answer.')}"
                        st.session_state.chat_history.append({"role": "assistant", "content": error_message})
                        st.rerun()

# --- Main Application ---
def main():
    initialize_session_state()
    language_options = get_supported_languages()
    selected_lang_code = render_sidebar(language_options)
    selected_lang_name = language_options.get(selected_lang_code, "Unknown")
    render_main_content(selected_lang_code, selected_lang_name)

if __name__ == "__main__":
    main()