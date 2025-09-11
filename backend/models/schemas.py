from pydantic import BaseModel
from typing import Optional, List

class SimplificationRequest(BaseModel):
    document_id: str
    target_language: Optional[str] = "en"

class SimplificationResponse(BaseModel):
    simplified_text: str
    risk_assessment: str
    translated_text: Optional[str] = None
    document_id: str

class ChatRequest(BaseModel):
    document_id: str
    question: str
    language: Optional[str] = "en"

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

class HealthResponse(BaseModel):
    status: str
    message: str
    legal_kb_info: Optional[dict] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    filename: str
    chunks_created: int
    collection_info: Optional[dict] = None