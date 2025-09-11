import PyPDF2
import hashlib
import os
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class DocumentProcessor:
    def __init__(self):
        self.documents: Dict[str, List[Document]] = {}
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def process_document(self, file_path: str) -> str:
        """Process PDF document and return document ID"""
        try:
            # Extract text from PDF
            text = self._extract_pdf_text(file_path)
            
            # Generate unique document ID
            doc_id = hashlib.md5(text.encode()).hexdigest()
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            documents = [Document(page_content=chunk) for chunk in chunks]
            
            # Store documents
            self.documents[doc_id] = documents
            
            return doc_id
        
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def get_chunks(self, document_id: str) -> List[Document]:
        """Get document chunks by ID"""
        return self.documents.get(document_id, [])
    
    def get_full_text(self, document_id: str) -> str:
        """Get full document text by ID"""
        chunks = self.get_chunks(document_id)
        return "\n".join([chunk.page_content for chunk in chunks])