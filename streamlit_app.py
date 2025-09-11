import streamlit as st
import requests
import json
from typing import Dict, Any

# Configure the page
st.set_page_config(
    page_title="Legal Document Simplifier",
    page_icon="⚖️",
    layout="wide"
)

# API base URL
API_BASE_URL = "http://localhost:8000"

def main():
    st.title("⚖️ Legal Document Simplifier")
    st.markdown("Upload a legal PDF document and get simplified explanations in your preferred Indian language!")
    
    # Initialize session state
    if "document_id" not in st.session_state:
        st.session_state.document_id = None
    if "simplified_text" not in st.session_state:
        st.session_state.simplified_text = None
    if "risk_assessment" not in st.session_state:
        st.session_state.risk_assessment = None
    if "translated_text" not in st.session_state:
        st.session_state.translated_text = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Sidebar for language selection
    st.sidebar.title("Settings")
    
    # Check API connection
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ Backend Connected")
        else:
            st.sidebar.error("❌ Backend Error")
    except:
        st.sidebar.error("❌ Backend Offline")
        st.error("Please make sure the backend is running on http://localhost:8000")
        return
    
    # Get supported languages
    try:
        lang_response = requests.get(f"{API_BASE_URL}/supported-languages")
        if lang_response.status_code == 200:
            language_options = lang_response.json()
        else:
            language_options = {"hi": "Hindi", "en": "English"}
    except:
        language_options = {"hi": "Hindi", "en": "English"}
    
    # Add display names for better UX
    display_options = {}
    for code, name in language_options.items():
        if code == "hi":
            display_options[code] = f"{name} (हिंदी)"
        elif code == "bn":
            display_options[code] = f"{name} (বাংলা)"
        elif code == "te":
            display_options[code] = f"{name} (తెలుగు)"
        elif code == "mr":
            display_options[code] = f"{name} (मराठी)"
        elif code == "ta":
            display_options[code] = f"{name} (தமிழ்)"
        elif code == "gu":
            display_options[code] = f"{name} (ગુજરાતી)"
        elif code == "kn":
            display_options[code] = f"{name} (ಕನ್ನಡ)"
        elif code == "ml":
            display_options[code] = f"{name} (മലയാളം)"
        else:
            display_options[code] = name
    
    selected_language = st.sidebar.selectbox(
        "Select Translation Language:",
        options=list(display_options.keys()),
        format_func=lambda x: display_options[x],
        index=0
    )

    # Free tier warning
    st.sidebar.info("💡 Using Gemini Free Tier\n\nPlease wait between requests to avoid rate limits.")

    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📄 Document Upload & Processing")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload a PDF legal document",
            type=["pdf"],
            help="Upload a legal contract, agreement, or other legal document (max 10MB)"
        )
        
        if uploaded_file is not None:
            st.info(f"File: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            if st.button("Process Document", type="primary"):
                with st.spinner("Processing document... This may take a moment."):
                    success, result = upload_document(uploaded_file)
                    
                    if success:
                        st.session_state.document_id = result["document_id"]
                        st.success(f"✅ Document processed successfully!")
                        st.info(f"📄 Created {result.get('chunks_created', 0)} text chunks")
                        st.info(f"🆔 Document ID: {result['document_id'][:8]}...")
                    else:
                        st.error(f"❌ Error processing document: {result}")
        
        # Simplification section
        if st.session_state.document_id:
            st.subheader("🔍 Document Analysis")
            
            col_simplify, col_translate = st.columns(2)
            
            with col_simplify:
                if st.button("📋 Simplify Document", type="secondary"):
                    with st.spinner("Analyzing document... (Using Gemini AI)"):
                        success, result = simplify_document(st.session_state.document_id, "en")
                        
                        if success:
                            st.session_state.simplified_text = result["simplified_text"]
                            st.session_state.risk_assessment = result["risk_assessment"]
                            st.success("✅ Document simplified!")
                        else:
                            st.error(f"❌ Error: {result}")
            
            with col_translate:
                if st.button("🌐 Get Translation", type="secondary"):
                    if st.session_state.simplified_text:
                        with st.spinner(f"Translating to {display_options[selected_language]}..."):
                            success, result = simplify_document(st.session_state.document_id, selected_language)
                            
                            if success:
                                st.session_state.translated_text = result.get("translated_text")
                                st.success("✅ Translation complete!")
                            else:
                                st.error(f"❌ Translation error: {result}")
                    else:
                        st.warning("Please simplify the document first")

    with col2:
        st.header("📋 Results")
        
        # Display simplified text
        if st.session_state.simplified_text:
            with st.expander("📖 Simplified Summary", expanded=True):
                st.write(st.session_state.simplified_text)
            
            # Display translated text if available
            if st.session_state.translated_text:
                with st.expander(f"🌐 Translation ({display_options[selected_language]})", expanded=True):
                    st.write(st.session_state.translated_text)
            
            # Display risk assessment
            if st.session_state.risk_assessment:
                with st.expander("⚠️ Risk Assessment", expanded=False):
                    st.write(st.session_state.risk_assessment)
        else:
            st.info("Upload and process a document to see results here")

    # Chat section (full width)
    if st.session_state.document_id:
        st.header("💬 Chat with Your Document")
        st.caption("Ask questions about your document or get legal guidance")
        
        # Display chat history
        if st.session_state.chat_history:
            with st.container():
                for i, (question, answer) in enumerate(st.session_state.chat_history):
                    with st.chat_message("user"):
                        st.write(f"**Q:** {question}")
                    with st.chat_message("assistant"):
                        st.write(f"**A:** {answer}")
        
        # Chat input
        question = st.text_input(
            "Ask a question about your document:",
            placeholder="e.g., What are my main obligations in this contract?",
            key="chat_input"
        )
        
        col_ask, col_clear = st.columns([3, 1])
        
        with col_ask:
            if st.button("Ask Question", type="primary"):
                if question.strip():
                    with st.spinner("Getting answer... (This may take a few seconds)"):
                        success, result = chat_with_document(
                            st.session_state.document_id, 
                            question.strip(), 
                            selected_language if selected_language != "en" else "en"
                        )
                        
                        if success:
                            st.session_state.chat_history.append((question.strip(), result["answer"]))
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {result}")
                else:
                    st.warning("Please enter a question")
        
        with col_clear:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    # Instructions for adding legal datasets
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Legal Knowledge Base")
    st.sidebar.markdown("""
    **To enhance legal knowledge:**
    
    1. Create folder: `backend/legal_datasets/`
    2. Add CSV/JSON files with legal data
    3. Restart the backend
    
    **Supported formats:**
    - CSV with 'text', 'content', or 'judgment' columns
    - JSON with text content
    
    **Datasets you mentioned:**
    - Laws and Acts of India
    - SC Judgments 1950-2024
    - Legal Documents dataset
    """)

def upload_document(file) -> tuple[bool, Dict[str, Any]]:
    """Upload document to the API"""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{API_BASE_URL}/upload-document", files=files, timeout=30)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Unknown error")
    except Exception as e:
        return False, str(e)

def simplify_document(document_id: str, target_language: str) -> tuple[bool, Dict[str, Any]]:
    """Simplify document using the API"""
    try:
        payload = {
            "document_id": document_id,
            "target_language": target_language
        }
        response = requests.post(f"{API_BASE_URL}/simplify", json=payload, timeout=60)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Unknown error")
    except Exception as e:
        return False, str(e)

def chat_with_document(document_id: str, question: str, language: str = "en") -> tuple[bool, Dict[str, Any]]:
    """Chat with document using the API"""
    try:
        payload = {
            "document_id": document_id,
            "question": question,
            "language": language
        }
        response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=45)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Unknown error")
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    main()