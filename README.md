# 🏛️ ClauseWise - Legal Document AI Assistant

Transform complex legal documents into plain English with AI-powered analysis, risk assessment, and real-time chat.

## ✨ Features

- 📄 **PDF Document Processing** - Upload any legal document
- 🤖 **Plain English Summaries** - AI explains complex legal language  
- ⚠️ **Risk Assessment** - Identifies potential legal risks
- 💬 **Document Chat** - Ask questions about your document
- 🌐 **Multi-language Support** - 12+ Indian languages
- 🔒 **Privacy-First** - Documents processed locally, not stored

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd ClauseWise
```

### 2. Run Setup (One Command!)
```bash
python setup.py
```

This will:
- ✅ Create virtual environment
- ✅ Install all dependencies  
- ✅ Set up project structure
- ✅ Create configuration files

### 3. Get Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Update `.env` file:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

### 4. Start the Application

**Activate virtual environment:**
```bash
# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**Start Backend (Terminal 1):**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Start Frontend (Terminal 2):**
```bash
python -m streamlit run streamlit_app.py --server.port 8501
```

### 5. Access the Application
- 🌐 **Frontend**: http://localhost:8501
- 📚 **API Documentation**: http://localhost:8000/docs

## 🛠️ Manual Installation (Advanced)

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
cp .env.example .env
# Edit .env with your actual API key
```

## 🧪 Testing

```bash
# Test the complete system (if test file exists)
python test_clausewise.py

# Test individual components
curl http://localhost:8000/health
```

## 📁 Project Structure

```
ClauseWise/
├── setup.py                  # One-command setup script
├── requirements.txt          # Python dependencies
├── .env.example             # Configuration template
├── streamlit_app.py         # Frontend application
├── backend/
│   ├── main.py             # FastAPI application
│   ├── services/           # Core AI services
│   │   ├── llm_service.py        # AI/LLM integration
│   │   ├── document_processor.py # PDF processing
│   │   ├── vector_store.py       # Vector database
│   │   └── translator.py         # Language support
│   └── models/             # Data models
│       └── schemas.py
└── backend/legal_datasets/  # Legal knowledge base
```

## ⚙️ Configuration

Key settings in `.env`:
- `GOOGLE_API_KEY` - Your Gemini API key *(required)*
- `RATE_LIMIT_REQUESTS_PER_MINUTE=15` - API rate limiting
- `MAX_FILE_SIZE_MB=10` - Upload size limit
- `CHUNK_SIZE=1000` - Text processing chunk size

## 📚 Adding Legal Knowledge

Enhance the AI's legal understanding:

1. Add files to `backend/legal_datasets/`:
   - **PDF files**: Legal documents, case law, statutes
   - **CSV files**: With 'text', 'content', or 'judgment' columns
   - **JSON files**: Legal data in structured format

2. Restart the backend to load new data

## 🔧 Troubleshooting

**Setup Issues:**
- Ensure Python 3.8+ is installed
- Check internet connection for dependency downloads
- On Windows, install Microsoft Visual C++ if compilation fails

**Runtime Issues:**
- Verify Gemini API key is correct and has quota
- Check that ports 8000 and 8501 are available
- Review console logs for detailed error messages

**Document Processing:**
- PDF must contain actual text (not just images)
- File size limit is 10MB
- Scanned documents may need OCR preprocessing

## 🏗️ Architecture

**Frontend**: Streamlit web application  
**Backend**: FastAPI with async processing  
**AI Models**:
- **LLM**: Google Gemini 1.5 Flash (text generation)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (document search)

**Vector Database**: ChromaDB (local, privacy-preserving)  
**Document Processing**: PyPDF2 + PyMuPDF (multi-method extraction)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly: `python test_clausewise.py`
5. Submit a pull request

## 📄 License

[Your chosen license]

## 🆘 Support

- **Issues**: [GitHub Issues](link-to-issues)
- **Documentation**: Check `/docs` endpoint when backend is running
- **API Reference**: http://localhost:8000/docs

## 🌟 Features in Development

- OCR support for scanned documents
- Batch document processing
- Document comparison features
- Advanced legal clause detection
- Integration with legal databases

---

**Built with ❤️ for democratizing legal understanding**