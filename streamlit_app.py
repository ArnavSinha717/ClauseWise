import streamlit as st
import requests
import os
import time
from typing import Dict, Any, List

# --- Page Configuration ---
st.set_page_config(
    page_title="ClauseWise - Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for better UI ---
st.markdown("""
<style>
.stContainer > div {
    padding-top: 1rem;
}
.status-good {
    color: #00ff00;
}
.status-bad {
    color: #ff0000;
}
.chat-message {
    padding: 0.5rem;
    margin: 0.5rem 0;
    border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# --- API Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# --- Session State Initialization ---
def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        "document_id": None,
        "document_name": "",
        "simplified_text": None,
        "risk_assessment": None,
        "translated_text": None,
        "chat_history": [],
        "sources": [],
        "processing_complete": False,
        "last_backend_check": 0,
        "backend_status": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- API Communication Functions ---
@st.cache_data(ttl=30)  # Cache for 30 seconds
def check_backend_health() -> bool:
    """Check if backend is running with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except Exception as e:
        st.error(f"Backend connection error: {e}")
        return False

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_supported_languages() -> Dict[str, str]:
    """Get supported languages with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}/supported-languages", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.warning(f"Could not fetch languages: {e}")
    
    # Fallback languages
    return {
        "en": "English",
        "hi": "Hindi", 
        "bn": "Bengali",
        "te": "Telugu",
        "mr": "Marathi",
        "ta": "Tamil",
        "gu": "Gujarati"
    }

def upload_document(file) -> tuple[bool, Dict[str, Any]]:
    """Upload document to backend"""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(
            f"{API_BASE_URL}/upload-document", 
            files=files, 
            timeout=120  # Increased timeout for large files
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            return False, {"error": error_detail}
            
    except requests.exceptions.Timeout:
        return False, {"error": "Upload timeout - file may be too large"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Could not connect to backend server"}
    except Exception as e:
        return False, {"error": f"Upload failed: {str(e)}"}

def simplify_document(doc_id: str) -> tuple[bool, Dict[str, Any]]:
    """Simplify document"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/simplify", 
            json={"document_id": doc_id}, 
            timeout=120
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            return False, {"error": error_detail}
            
    except requests.exceptions.Timeout:
        return False, {"error": "Simplification timeout - document may be too long"}
    except Exception as e:
        return False, {"error": f"Simplification failed: {str(e)}"}

def assess_risk(doc_id: str) -> tuple[bool, Dict[str, Any]]:
    """Assess document risks"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/assess-risk", 
            json={"document_id": doc_id}, 
            timeout=120
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            return False, {"error": error_detail}
            
    except requests.exceptions.Timeout:
        return False, {"error": "Risk assessment timeout"}
    except Exception as e:
        return False, {"error": f"Risk assessment failed: {str(e)}"}

def chat_with_document(doc_id: str, question: str, lang: str) -> tuple[bool, Dict[str, Any]]:
    """Chat with document"""
    try:
        payload = {"document_id": doc_id, "question": question, "language": lang}
        response = requests.post(
            f"{API_BASE_URL}/chat", 
            json=payload, 
            timeout=120
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            return False, {"error": error_detail}
            
    except requests.exceptions.Timeout:
        return False, {"error": "Chat timeout - question may be too complex"}
    except Exception as e:
        return False, {"error": f"Chat failed: {str(e)}"}

def translate_text(text: str, lang: str) -> tuple[bool, Dict[str, Any]]:
    """Translate text"""
    try:
        payload = {"text": text, "target_language": lang}
        response = requests.post(
            f"{API_BASE_URL}/translate", 
            json=payload, 
            timeout=120
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            return False, {"error": error_detail}
            
    except Exception as e:
        return False, {"error": f"Translation failed: {str(e)}"}

# --- UI Components ---
def render_sidebar(language_options: Dict[str, str]):
    """Render sidebar with settings and status"""
    with st.sidebar:
        st.title("⚖️ ClauseWise")
        st.markdown("**Legal Document AI Assistant**")
        
        # Backend status check
        current_time = time.time()
        if current_time - st.session_state.last_backend_check > 30:  # Check every 30 seconds
            st.session_state.backend_status = check_backend_health()
            st.session_state.last_backend_check = current_time
        
        if st.session_state.backend_status:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Offline")
            st.warning("Start backend: `python run_backend.py`")
            if st.button("🔄 Retry Connection"):
                st.session_state.last_backend_check = 0  # Force recheck
                st.rerun()

        st.markdown("---")
        
        # Language selection
        st.header("🌐 Settings")
        selected_language = st.selectbox(
            "Select Language:",
            options=list(language_options.keys()),
            format_func=lambda x: language_options.get(x, x),
            index=0,
            help="Select your preferred language for analysis and chat"
        )
        
        # Rate limiting info
        st.info("💡 **Rate Limits**: Using Gemini Free Tier. Please wait 5-10 seconds between requests.")
        
        st.markdown("---")
        
        # Document status
        st.header("📄 Document Status")
        if st.session_state.document_id:
            st.success(f"**Active:** {st.session_state.document_name}")
            if st.button("🗑️ Clear Document"):
                # Reset session state
                for key in ["document_id", "document_name", "simplified_text", 
                           "risk_assessment", "translated_text", "chat_history"]:
                    st.session_state[key] = None if key in ["document_id", "simplified_text", "risk_assessment", "translated_text"] else [] if key == "chat_history" else ""
                st.rerun()
        else:
            st.warning("No document loaded")
        
        st.markdown("---")
        
        # Help section
        st.subheader("📚 Help")
        with st.expander("How to Use"):
            st.markdown("""
            1. **Upload PDF**: Upload a legal document
            2. **Analyze**: Click 'Simplify' or 'Assess Risks'
            3. **Chat**: Ask questions about the document
            4. **Translate**: Get results in your language
            """)
        
        with st.expander("Troubleshooting"):
            st.markdown("""
            - **Upload fails**: Check file size (<10MB) and format (PDF only)
            - **Backend offline**: Run `python run_backend.py`
            - **Slow responses**: Free Gemini tier has rate limits
            - **No text extracted**: PDF might be image-based
            """)
    
    return selected_language

def render_document_upload():
    """Render document upload section"""
    st.header("📄 Step 1: Upload Legal Document")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload a legal document (contracts, agreements, etc.) - Max 10MB",
            disabled=not st.session_state.backend_status
        )
        
        if uploaded_file:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.info(f"📁 **File**: {uploaded_file.name} ({file_size_mb:.1f} MB)")
            
            if file_size_mb > 10:
                st.error("❌ File too large! Maximum size is 10MB.")
                return
            
            col1, col2 = st.columns([1, 3])
            with col1:
                process_button = st.button(
                    "🚀 Process Document", 
                    type="primary",
                    disabled=not st.session_state.backend_status
                )
            
            if process_button:
                with st.spinner("📖 Processing document... This may take 30-60 seconds."):
                    # Add progress bar
                    progress_bar = st.progress(0)
                    progress_bar.progress(25)
                    
                    success, result = upload_document(uploaded_file)
                    progress_bar.progress(75)
                    
                    if success:
                        progress_bar.progress(100)
                        # Reset relevant state for new document
                        st.session_state.document_id = result["document_id"]
                        st.session_state.document_name = result["filename"]
                        st.session_state.simplified_text = None
                        st.session_state.risk_assessment = None
                        st.session_state.translated_text = None
                        st.session_state.chat_history = []
                        st.session_state.processing_complete = True
                        
                        st.success(f"✅ Document '{result['filename']}' processed successfully!")
                        st.info(f"📊 Created {result.get('num_chunks', 0)} text chunks for analysis")
                        time.sleep(1)  # Brief pause before rerun
                        st.rerun()
                    else:
                        progress_bar.progress(0)
                        st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

def render_analysis_section(selected_language: str, lang_name: str):
    """Render document analysis section"""
    st.header("🔍 Step 2: Analyze Document")
    
    if not st.session_state.document_id:
        st.info("👆 Please upload and process a document first.")
        return
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📖 Simplify Document", help="Get a plain-English summary"):
                with st.spinner("🤖 Generating simplified summary..."):
                    success, result = simplify_document(st.session_state.document_id)
                    if success:
                        st.session_state.simplified_text = result["simplified_text"]
                        st.success("✅ Document simplified!")
                    else:
                        st.error(f"❌ Error: {result.get('error')}")

        with col2:
            if st.button("⚠️ Assess Risks", help="Identify potential legal risks"):
                with st.spinner("🔍 Performing risk assessment..."):
                    success, result = assess_risk(st.session_state.document_id)
                    if success:
                        st.session_state.risk_assessment = result["risk_assessment"]
                        st.success("✅ Risk assessment complete!")
                    else:
                        st.error(f"❌ Error: {result.get('error')}")
        
        # Translation option
        if st.session_state.simplified_text and selected_language != "en":
            if st.button(f"🌐 Translate to {lang_name}"):
                with st.spinner(f"🔄 Translating to {lang_name}..."):
                    success, result = translate_text(st.session_state.simplified_text, selected_language)
                    if success:
                        st.session_state.translated_text = result["translated_text"]
                        st.success("✅ Translation complete!")
                    else:
                        st.error(f"❌ Translation Error: {result.get('error')}")

def render_results():
    """Render analysis results"""
    if not (st.session_state.simplified_text or st.session_state.risk_assessment):
        return
    
    st.header("📋 Analysis Results")
    
    with st.container(border=True):
        if st.session_state.simplified_text:
            with st.expander("📖 Simplified Summary", expanded=True):
                st.markdown(st.session_state.simplified_text)
        
        if st.session_state.risk_assessment:
            with st.expander("⚠️ Risk Assessment", expanded=True):
                st.markdown(st.session_state.risk_assessment)

        if st.session_state.translated_text:
            with st.expander(f"🌐 Translation", expanded=True):
                st.markdown(st.session_state.translated_text)

def render_chat_section(selected_language: str):
    """Render chat interface"""
    st.header("💬 Step 3: Chat with Document")
    
    if not st.session_state.document_id:
        st.info("👆 Please upload and process a document first.")
        return
    
    with st.container(border=True):
        # Sample questions
        st.subheader("💡 Try these questions:")
        sample_questions = [
            "What are the main obligations in this document?",
            "What are the payment terms?", 
            "Are there any penalties mentioned?",
            "What happens if the contract is breached?",
            "What are the termination conditions?"
        ]
        
        cols = st.columns(len(sample_questions))
        for i, question in enumerate(sample_questions):
            with cols[i % len(cols)]:
                if st.button(f"❓ {question[:20]}...", key=f"sample_{i}", help=question):
                    st.session_state.chat_history.append({"role": "user", "content": question})
                    # Process the question
                    with st.spinner("🤖 Thinking..."):
                        success, result = chat_with_document(st.session_state.document_id, question, selected_language)
                        if success:
                            response_text = result["answer"]
                            sources = result.get("sources", [])
                            if sources:
                                response_text += f"\n\n*📚 Sources: {', '.join(sources)}*"
                            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                        else:
                            error_msg = f"❌ Error: {result.get('error', 'Could not process question.')}"
                            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    st.rerun()
        
        st.markdown("---")
        
        # Chat history display
        if st.session_state.chat_history:
            st.subheader("💬 Conversation")
            for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about the document...", key="main_chat"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.spinner("🤖 Thinking..."):
                success, result = chat_with_document(st.session_state.document_id, prompt, selected_language)
                
                if success:
                    response_text = result["answer"]
                    sources = result.get("sources", [])
                    if sources:
                        response_text += f"\n\n*📚 Sources: {', '.join(sources)}*"
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                else:
                    error_msg = f"❌ Error: {result.get('error', 'Could not process question.')}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            
            st.rerun()

# --- Main Application ---
def main():
    """Main application function"""
    initialize_session_state()
    
    # Get language options
    language_options = get_supported_languages()
    selected_lang_code = render_sidebar(language_options)
    selected_lang_name = language_options.get(selected_lang_code, "Unknown")
    
    # Main content area
    st.title("⚖️ ClauseWise - Legal AI Assistant")
    st.markdown("**Simplify legal documents, assess risks, and get answers in plain language.**")
    
    if not st.session_state.backend_status:
        st.error("🚫 Backend server is not running. Please start it to use the application.")
        st.code("python run_backend.py", language="bash")
        st.stop()
    
    # Render main sections
    render_document_upload()
    
    # Only show analysis and chat if document is uploaded
    if st.session_state.document_id:
        st.markdown("---")
        render_analysis_section(selected_lang_code, selected_lang_name)
        
        if st.session_state.simplified_text or st.session_state.risk_assessment:
            st.markdown("---")
            render_results()
        
        st.markdown("---")
        render_chat_section(selected_lang_code)

if __name__ == "__main__":
    main()