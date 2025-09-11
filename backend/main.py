import os
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv

from .services.document_processor import DocumentProcessor
from .services.vector_store import VectorStoreManager
from .services.llm_service import EnhancedLLMService 
from .services.translator import Translator

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ClauseWise - Legal Document Demystifier API",
    description="An API to simplify, analyze, and chat with legal documents.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    document_processor = DocumentProcessor()
    vector_store_manager = VectorStoreManager()
    llm_service = EnhancedLLMService()
    translator = Translator()
    logger.info("✅ All services initialized successfully")
except Exception as e:
    logger.error(f"❌ Service initialization failed: {e}")
    raise

# Pydantic models
class DocumentRequest(BaseModel):
    document_id: str

class TranslateRequest(BaseModel):
    text: str
    target_language: str = "hi"

class ChatRequest(BaseModel):
    document_id: str
    question: str
    language: str = "en"

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

@app.get("/", tags=["Status"])
async def read_root():
    """Root endpoint with basic API information"""
    return {
        "message": "Welcome to the ClauseWise Legal API!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Status"])
async def health_check():
    """Enhanced health check with service status"""
    try:
        # Check if services are working
        legal_kb_info = llm_service.get_legal_kb_info()
        
        return {
            "status": "healthy",
            "services": {
                "document_processor": "active",
                "vector_store": "active",
                "llm_service": "active",
                "legal_kb": legal_kb_info.get("status", "unknown")
            },
            "legal_kb_documents": legal_kb_info.get("count", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/supported-languages", tags=["Utilities"])
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        return translator.get_supported_languages()
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-document", tags=["Document"])
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a PDF document"""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    # Validate file size (10MB limit)
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > 10:
        raise HTTPException(status_code=400, detail=f"File too large ({file_size_mb:.1f}MB). Maximum size is 10MB.")
    
    logger.info(f"Processing uploaded file: {file.filename} ({file_size_mb:.1f}MB)")
    
    try:
        # Process the document
        doc_id, chunks = document_processor.process_uploaded_file(file_content, file.filename)

        if not doc_id or not chunks:
            logger.error(f"Failed to process {file.filename} - no content extracted")
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF. The file might be corrupted, password-protected, or contain only images.")
        
        logger.info(f"Successfully processed {file.filename}: {len(chunks)} chunks created")
        
        # Create vector store
        vector_store_manager.create_vector_store(doc_id, chunks)
        
        # Get additional info
        doc_info = document_processor.get_document_info(chunks)
        
        return {
            "message": "Document processed successfully",
            "document_id": doc_id,
            "filename": file.filename,
            "num_chunks": len(chunks),
            "file_size_mb": round(file_size_mb, 2),
            "document_info": doc_info
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.post("/simplify", tags=["Analysis"])
async def simplify_document(request: DocumentRequest):
    """Simplify a legal document into plain language"""
    try:
        logger.info(f"Simplifying document {request.document_id}")
        
        # Get document chunks
        full_text_chunks = vector_store_manager.get_all_chunks(request.document_id)
        if not full_text_chunks:
            raise HTTPException(status_code=404, detail="Document not found or has no content.")
        
        logger.info(f"Found {len(full_text_chunks)} chunks for simplification")
        
        # Simplify using LLM
        simplified_text = await llm_service.simplify_document(full_text_chunks)
        
        return {
            "simplified_text": simplified_text,
            "document_id": request.document_id,
            "chunks_processed": len(full_text_chunks)
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error simplifying document {request.document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Simplification failed: {str(e)}")

@app.post("/assess-risk", tags=["Analysis"])
async def assess_risk_in_document(request: DocumentRequest):
    """Assess legal risks in a document"""
    try:
        logger.info(f"Assessing risks for document {request.document_id}")
        
        # Get document chunks
        full_text_chunks = vector_store_manager.get_all_chunks(request.document_id)
        if not full_text_chunks:
            raise HTTPException(status_code=404, detail="Document not found or has no content.")
        
        logger.info(f"Found {len(full_text_chunks)} chunks for risk assessment")
        
        # Assess risks using LLM
        risk_assessment = await llm_service.assess_risks(full_text_chunks)
        
        return {
            "risk_assessment": risk_assessment,
            "document_id": request.document_id,
            "chunks_processed": len(full_text_chunks)
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error assessing risks for document {request.document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@app.post("/chat", tags=["Interaction"])
async def chat_with_document_endpoint(request: ChatRequest):
    """Chat with a document using AI"""
    try:
        logger.info(f"Chat request for document {request.document_id}: {request.question[:50]}...")
        
        # Get vector store
        vector_store = vector_store_manager.get_vector_store(request.document_id)
        if not vector_store:
            raise HTTPException(status_code=404, detail="Document vector store not found.")

        # Get answer from LLM
        answer, sources = await llm_service.chat_with_document(
            document_vector_store=vector_store,
            question=request.question,
            language=request.language
        )
        
        return {
            "answer": answer,
            "sources": sources,
            "question": request.question,
            "language": request.language,
            "document_id": request.document_id
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error in chat for document {request.document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/translate", tags=["Utilities"])
async def translate_text_endpoint(request: TranslateRequest):
    """Translate text to specified language"""
    try:
        logger.info(f"Translating text to {request.target_language}")
        
        # Validate text length
        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long for translation (max 5000 characters)")
        
        # Translate using LLM
        translated_text = await llm_service.translate_text(request.text, request.target_language)
        
        return {
            "translated_text": translated_text,
            "language": request.target_language,
            "original_length": len(request.text),
            "translated_length": len(translated_text)
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.get("/legal-kb-info", tags=["Knowledge Base"])
async def get_legal_kb_status():
    """Get information about the legal knowledge base"""
    try:
        info = llm_service.get_legal_kb_info()
        return {
            "legal_kb_info": info,
            "datasets_path": info.get("datasets_path", "unknown"),
            "status": info.get("status", "unknown"),
            "document_count": info.get("count", 0)
        }
    except Exception as e:
        logger.error(f"Error getting legal KB info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", tags=["Document"])
async def list_documents():
    """List all processed documents"""
    try:
        documents = vector_store_manager.list_documents()
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}", tags=["Document"])
async def delete_document(document_id: str):
    """Delete a processed document"""
    try:
        success = vector_store_manager.delete_document(document_id)
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)