import os
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS  # Fixed import
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

class VectorStoreManager:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_stores: Dict[str, FAISS] = {}
        self.store_dir = "vector_stores"
        os.makedirs(self.store_dir, exist_ok=True)
    
    def create_vector_store(self, document_id: str, documents: List[Document]) -> None:
        """Create and store a vector store for the document"""
        try:
            if not documents:
                raise ValueError("No documents provided")
            
            # Create FAISS vector store
            vector_store = FAISS.from_documents(documents, self.embeddings)
            
            # Store in memory
            self.vector_stores[document_id] = vector_store
            
            # Save to disk for persistence
            store_path = os.path.join(self.store_dir, document_id)
            vector_store.save_local(store_path)
            
        except Exception as e:
            raise Exception(f"Error creating vector store: {str(e)}")
    
    def get_vector_store(self, document_id: str) -> Optional[FAISS]:
        """Get vector store by document ID"""
        if document_id in self.vector_stores:
            return self.vector_stores[document_id]
        
        # Try to load from disk
        store_path = os.path.join(self.store_dir, document_id)
        if os.path.exists(store_path):
            try:
                vector_store = FAISS.load_local(
                    store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self.vector_stores[document_id] = vector_store
                return vector_store
            except Exception as e:
                print(f"Error loading vector store: {e}")
        
        return None
    
    def search_similar(self, document_id: str, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents"""
        vector_store = self.get_vector_store(document_id)
        if not vector_store:
            return []
        
        try:
            return vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"Error searching similar documents: {e}")
            return []