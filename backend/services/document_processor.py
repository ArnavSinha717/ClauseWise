import hashlib
import os
from typing import List, Tuple, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
import tempfile
import fitz  # PyMuPDF - alternative PDF reader
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        """Initializes the text splitter with optimized settings for legal documents."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def _extract_text_pypdf(self, file_path: str) -> str:
        """Extract text using PyPDFLoader (LangChain method)"""
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            full_text = "\n".join([page.page_content for page in pages])
            return full_text.strip()
        except Exception as e:
            logger.warning(f"PyPDFLoader failed: {e}")
            return ""
    
    def _extract_text_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF (alternative method)"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF with multiple fallback methods"""
        # Try PyPDFLoader first
        text = self._extract_text_pypdf(file_path)
        
        # If that fails, try PyMuPDF
        if not text:
            logger.info("Trying alternative PDF extraction method...")
            text = self._extract_text_pymupdf(file_path)
        
        return text
    
    def _validate_pdf_content(self, text: str) -> bool:
        """Validate that extracted text is meaningful"""
        if not text or len(text.strip()) < 50:
            return False
        
        # Check if text contains meaningful content (not just special characters)
        import re
        word_count = len(re.findall(r'\b\w+\b', text))
        return word_count >= 10
    
    def _generate_document_id(self, content: str, filename: str) -> str:
        """Generate a unique document ID based on content and filename"""
        combined = f"{filename}_{content[:1000]}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def process_uploaded_file(self, file_content: bytes, filename: str) -> Tuple[Optional[str], List[Document]]:
        """
        Processes an uploaded PDF file's content, returns a document ID and its text chunks.
        Enhanced with better error handling and multiple PDF extraction methods.
        """
        temp_file_path = None
        try:
            # Validate file content
            if not file_content or len(file_content) == 0:
                logger.error("Empty file content received")
                return None, []
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            logger.info(f"Processing PDF: {filename} ({len(file_content)} bytes)")
            
            # Extract text using multiple methods
            full_text = self._extract_text_from_pdf(temp_file_path)
            
            # Validate extracted content
            if not self._validate_pdf_content(full_text):
                logger.error(f"Could not extract meaningful text from {filename}")
                return None, []
            
            logger.info(f"Extracted {len(full_text)} characters from {filename}")
            
            # Generate unique document ID
            doc_id = self._generate_document_id(full_text, filename)
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(full_text)
            
            if not chunks:
                logger.error("No chunks created from document")
                return None, []
            
            # Create LangChain Document objects
            documents = []
            for i, chunk in enumerate(chunks):
                if chunk.strip():  # Only include non-empty chunks
                    metadata = {
                        "source": filename,
                        "chunk_id": i,
                        "document_id": doc_id,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk)
                    }
                    documents.append(Document(page_content=chunk, metadata=metadata))
            
            logger.info(f"Created {len(documents)} document chunks for {filename}")
            return doc_id, documents

        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            return None, []
        
        finally:
            # Always clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_file_path}: {e}")
    
    def get_document_info(self, documents: List[Document]) -> dict:
        """Get summary information about processed documents"""
        if not documents:
            return {"total_chunks": 0, "total_content_length": 0}
        
        total_length = sum(len(doc.page_content) for doc in documents)
        return {
            "total_chunks": len(documents),
            "total_content_length": total_length,
            "average_chunk_size": total_length // len(documents) if documents else 0,
            "source_file": documents[0].metadata.get("source", "unknown") if documents else "unknown"
        }