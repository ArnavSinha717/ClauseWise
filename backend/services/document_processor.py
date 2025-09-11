import hashlib
import os
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
import tempfile

class DocumentProcessor:
    def __init__(self):
        """Initializes the text splitter."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def process_uploaded_file(self, file_content: bytes, filename: str) -> Tuple[str, List[Document]]:
        """
        Processes an uploaded PDF file's content, returns a document ID and its text chunks.
        """
        try:
            # Use a temporary file to hold the uploaded content for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            # Use PyPDFLoader to extract text
            loader = PyPDFLoader(temp_file_path)
            pages = loader.load()
            full_text = "\n".join([page.page_content for page in pages])

            if not full_text.strip():
                return None, []

            # Generate a unique document ID based on the content
            doc_id = hashlib.md5(full_text.encode()).hexdigest()
            
            # Split the text into chunks
            chunks = self.text_splitter.split_text(full_text)
            
            # Create LangChain Document objects for each chunk
            documents = []
            for i, chunk in enumerate(chunks):
                metadata = {"source": filename, "chunk_id": i, "document_id": doc_id}
                documents.append(Document(page_content=chunk, metadata=metadata))
            
            # Clean up the temporary file
            os.remove(temp_file_path)
            
            return doc_id, documents

        except Exception as e:
            # Ensure temp file is cleaned up on error
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise Exception(f"Error processing document: {str(e)}")