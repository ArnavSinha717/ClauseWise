from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
import uvicorn
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStoreManager
from services.llm_service import EnhancedLLMService
from services.translator import TranslatorService
from models.schemas import SimplificationRequest, ChatRequest, SimplificationResponse, ChatResponse

app = FastAPI(title="Legal Document Simplifier API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
doc_processor = DocumentProcessor()
vector_manager = VectorStoreManager()
llm_service = EnhancedLLMService()
translator = TranslatorService()

# Create temp directory
os.makedirs("temp", exist_ok=True)

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a legal PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file temporarily
        temp_path = f"temp/temp_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document
        document_id = doc_processor.process_document(temp_path)
        
        # Create vector store
        chunks = doc_processor.get_chunks(document_id)
        vector_manager.create_vector_store(document_id, chunks)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "document_id": document_id, 
            "status": "processed", 
            "filename": file.filename,
            "chunks_created": len(chunks)
        }
        
    except Exception as e:
        # Clean up temp file on error
        temp_path = f"temp/temp_{file.filename}"
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/simplify", response_model=SimplificationResponse)
async def simplify_document(request: SimplificationRequest):
    """Simplify legal document and assess risks using Gemini"""
    try:
        chunks = doc_processor.get_chunks(request.document_id)
        if not chunks:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Use Gemini for simplification and risk assessment
        simplified_text = await llm_service.simplify_document(chunks)
        risk_assessment = await llm_service.assess_risks(chunks)
        
        # Translate if target language specified
        translated_text = None
        if request.target_language and request.target_language != "en":
            translated_text = await llm_service.translate_text(
                simplified_text, 
                request.target_language
            )
        
        return SimplificationResponse(
            simplified_text=simplified_text,
            risk_assessment=risk_assessment,
            translated_text=translated_text,
            document_id=request.document_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simplifying document: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    """Chat with the document using RAG and legal knowledge base"""
    try:
        vector_store = vector_manager.get_vector_store(request.document_id)
        if not vector_store:
            raise HTTPException(status_code=404, detail="Document not found")
        
        answer, sources = await llm_service.chat_with_document(
            vector_store, 
            request.question, 
            request.language
        )
        
        return ChatResponse(answer=answer, sources=sources)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Legal Document Simplifier API is running"}

@app.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages for translation"""
    return translator.get_supported_languages()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)