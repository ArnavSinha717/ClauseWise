import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv

from .services.document_processor import DocumentProcessor
from .services.vector_store import VectorStoreManager
from .services.llm_service import EnhancedLLMService 
from .services.translator import Translator

load_dotenv()

app = FastAPI(
    title="ClauseWise - Legal Document Demystifier API",
    description="An API to simplify, analyze, and chat with legal documents.",
    version="1.0.0"
)

document_processor = DocumentProcessor()
vector_store_manager = VectorStoreManager()
llm_service = EnhancedLLMService()
translator = Translator()

class DocumentRequest(BaseModel):
    document_id: str

class TranslateRequest(BaseModel):
    text: str
    target_language: str = "hi"

class ChatRequest(BaseModel):
    document_id: str
    question: str
    language: str = "en"

@app.get("/", tags=["Status"])
async def read_root():
    return {"message": "Welcome to the ClauseWise Legal API!"}

@app.get("/health", tags=["Status"])
async def health_check():
    return {"status": "ok"}

@app.get("/supported-languages", tags=["Utilities"])
async def get_supported_languages():
    return translator.get_supported_languages()

@app.post("/upload-document", tags=["Document"])
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        file_content = await file.read()
        
        # --- THIS IS THE FIX ---
        # Call the single, correct method from the updated DocumentProcessor
        doc_id, chunks = document_processor.process_uploaded_file(file_content, file.filename)

        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")
            
        vector_store_manager.create_vector_store(doc_id, chunks)
        
        return {
            "message": "Document processed successfully",
            "document_id": doc_id,
            "filename": file.filename,
            "num_chunks": len(chunks)
        }
    except Exception as e:
        print(f"Error in /upload-document: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/simplify", tags=["Analysis"])
async def simplify_document(request: DocumentRequest):
    try:
        # Use the get_all_chunks method from the new vector_store.py
        full_text_chunks = vector_store_manager.get_all_chunks(request.document_id)
        if not full_text_chunks:
            raise HTTPException(status_code=404, detail="Document not found or has no content.")
            
        simplified_text = await llm_service.simplify_document(full_text_chunks)
        return {"simplified_text": simplified_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assess-risk", tags=["Analysis"])
async def assess_risk_in_document(request: DocumentRequest):
    try:
        full_text_chunks = vector_store_manager.get_all_chunks(request.document_id)
        if not full_text_chunks:
            raise HTTPException(status_code=404, detail="Document not found or has no content.")
            
        risk_assessment = await llm_service.assess_risks(full_text_chunks)
        return {"risk_assessment": risk_assessment}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", tags=["Interaction"])
async def chat_with_document_endpoint(request: ChatRequest):
    try:
        vector_store = vector_store_manager.get_vector_store(request.document_id)
        if not vector_store:
            raise HTTPException(status_code=404, detail="Document vector store not found.")

        answer, sources = await llm_service.chat_with_document(
            document_vector_store=vector_store,
            question=request.question,
            language=request.language
        )
        return {"answer": answer, "sources": sources}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate", tags=["Utilities"])
async def translate_text_endpoint(request: TranslateRequest):
    try:
        translated_text = await llm_service.translate_text(request.text, request.target_language)
        return {"translated_text": translated_text, "language": request.target_language}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/legal-kb-info", tags=["Knowledge Base"])
async def get_legal_kb_status():
    info = llm_service.get_legal_kb_info()
    return info