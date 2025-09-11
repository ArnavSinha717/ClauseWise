import os
import json
import pandas as pd
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import asyncio
import glob
import time

load_dotenv()

class EnhancedLLMService:
    def __init__(self):
        # Initialize Gemini with free tier optimizations
        self.gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
            max_tokens=1024,  # Reduced for free tier
            rate_limiter={
                "requests_per_minute": 15,  # Free tier limit
                "tokens_per_minute": 32000
            }
        )
        
        # Initialize embeddings for vector store
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Legal knowledge base
        self.legal_knowledge_base = None
        self.knowledge_base_path = "backend/legal_datasets"
        self.last_request_time = 0
        self.min_request_interval = 4  # 4 seconds between requests for free tier
        
        # Try to load existing knowledge base first
        if not self._load_existing_knowledge_base():
            self._initialize_legal_knowledge_base()
    
    async def _rate_limit_check(self):
        """Ensure we don't exceed free tier rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            print(f"Rate limiting: waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _load_existing_knowledge_base(self):
        """Load existing legal knowledge base"""
        try:
            knowledge_base_store_path = "backend/legal_knowledge_store"
            if os.path.exists(knowledge_base_store_path):
                self.legal_knowledge_base = FAISS.load_local(
                    knowledge_base_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("Loaded existing legal knowledge base")
                return True
        except Exception as e:
            print(f"Could not load existing knowledge base: {e}")
        return False
    
    def _initialize_legal_knowledge_base(self):
        """Initialize the legal knowledge base from datasets"""
        try:
            legal_documents = []
            
            # Check if legal datasets directory exists
            if not os.path.exists(self.knowledge_base_path):
                print(f"Legal datasets directory not found at {self.knowledge_base_path}")
                print("Creating directory. Please add your legal datasets (CSV/JSON files) here.")
                os.makedirs(self.knowledge_base_path, exist_ok=True)
                return
            
            # Load different types of legal documents
            csv_files = glob.glob(os.path.join(self.knowledge_base_path, "*.csv"))
            json_files = glob.glob(os.path.join(self.knowledge_base_path, "*.json"))
            
            # Process CSV files (like Supreme Court judgments)
            for csv_file in csv_files:
                try:
                    print(f"Processing {csv_file}...")
                    df = pd.read_csv(csv_file, nrows=1000)  # Limit rows for free tier
                    
                    for _, row in df.iterrows():
                        text_content = None
                        metadata = {}
                        
                        # Common column names for legal datasets
                        text_columns = ['text', 'content', 'judgment', 'case_text', 'full_text', 'description', 'summary']
                        for col in text_columns:
                            if col in df.columns and pd.notna(row.get(col)):
                                text_content = str(row[col])
                                break
                        
                        if text_content and len(text_content) > 100:  # Only meaningful content
                            # Add metadata
                            for col in df.columns:
                                if col not in text_columns and pd.notna(row.get(col)):
                                    metadata[col] = str(row[col])[:100]  # Limit metadata size
                            
                            legal_documents.append(Document(
                                page_content=text_content[:1500],  # Limit size for free tier
                                metadata=metadata
                            ))
                    
                    print(f"Loaded {len(legal_documents)} documents from {csv_file}")
                except Exception as e:
                    print(f"Error loading CSV {csv_file}: {e}")
            
            # Process JSON files
            for json_file in json_files:
                try:
                    print(f"Processing {json_file}...")
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for i, item in enumerate(data[:500]):  # Limit for free tier
                            if isinstance(item, dict):
                                text_content = item.get('text') or item.get('content') or item.get('description')
                                if text_content and len(text_content) > 100:
                                    legal_documents.append(Document(
                                        page_content=str(text_content)[:1500],
                                        metadata={k: str(v)[:100] for k, v in item.items() if k != text_content}
                                    ))
                    
                    print(f"Processed documents from {json_file}")
                except Exception as e:
                    print(f"Error loading JSON {json_file}: {e}")
            
            # Create vector store if we have documents
            if legal_documents:
                print(f"Creating legal knowledge base with {len(legal_documents)} documents...")
                self.legal_knowledge_base = FAISS.from_documents(legal_documents, self.embeddings)
                
                # Save the knowledge base
                knowledge_base_store_path = "backend/legal_knowledge_store"
                os.makedirs(knowledge_base_store_path, exist_ok=True)
                self.legal_knowledge_base.save_local(knowledge_base_store_path)
                print("Legal knowledge base created and saved successfully!")
            else:
                print("No legal documents found to create knowledge base")
                
        except Exception as e:
            print(f"Error initializing legal knowledge base: {e}")
    
    async def simplify_document(self, documents: List[Document]) -> str:
        """Use Gemini to simplify the legal document - optimized for free tier"""
        try:
            await self._rate_limit_check()
            
            # Combine documents but limit size for free tier
            combined_text = ""
            for doc in documents:
                if len(combined_text) + len(doc.page_content) > 3000:  # Limit total input
                    break
                combined_text += doc.page_content + "\n"
            
            prompt = f"""Simplify this legal document for a regular person in India:

DOCUMENT:
{combined_text}

Please provide:
1. Main purpose in simple words
2. Key rights and obligations
3. Important deadlines or conditions
4. What this means for the person involved

Keep response under 500 words and use simple English:"""
            
            result = await asyncio.to_thread(self.gemini_llm.predict, prompt)
            return result
            
        except Exception as e:
            raise Exception(f"Error simplifying document: {str(e)}")
    
    async def assess_risks(self, documents: List[Document]) -> str:
        """Use Gemini to assess legal risks - optimized for free tier"""
        try:
            await self._rate_limit_check()
            
            # Limit input size for free tier
            combined_text = ""
            for doc in documents:
                if len(combined_text) + len(doc.page_content) > 2500:
                    break
                combined_text += doc.page_content + "\n"
            
            prompt = f"""Analyze legal risks in this document:

{combined_text}

Identify:
1. Financial risks or penalties
2. Unfavorable terms
3. Important deadlines
4. Termination risks
5. Overall risk level (Low/Medium/High)

Keep response focused and under 400 words:"""
            
            result = await asyncio.to_thread(self.gemini_llm.predict, prompt)
            return result
            
        except Exception as e:
            raise Exception(f"Error assessing risks: {str(e)}")
    
    async def translate_text(self, text: str, target_language: str) -> str:
        """Use Gemini for translation - optimized for free tier"""
        try:
            await self._rate_limit_check()
            
            language_names = {
                "hi": "Hindi (हिंदी)",
                "bn": "Bengali (বাংলা)", 
                "te": "Telugu (తెలుగు)",
                "mr": "Marathi (मराठी)",
                "ta": "Tamil (தமிழ்)",
                "gu": "Gujarati (ગુજરાતી)",
                "kn": "Kannada (ಕನ್ನಡ)",
                "ml": "Malayalam (മലയാളം)",
                "or": "Odia (ଓଡ଼ିଆ)",
                "pa": "Punjabi (ਪੰਜਾਬੀ)",
                "ur": "Urdu (اردو)"
            }
            
            target_lang_name = language_names.get(target_language, "Hindi")
            
            # Limit text size for free tier
            limited_text = text[:2000] if len(text) > 2000 else text
            
            prompt = f"""Translate to {target_lang_name}:

{limited_text}

Translation:"""
            
            result = await asyncio.to_thread(self.gemini_llm.predict, prompt)
            return result
            
        except Exception as e:
            print(f"Translation error: {e}")
            return f"Translation not available. Original: {text[:500]}..."
    
    async def chat_with_document(self, document_vector_store: FAISS, question: str, language: str = "en") -> Tuple[str, List[str]]:
        """Enhanced chat using both document and legal knowledge base"""
        try:
            await self._rate_limit_check()
            
            # Get relevant context from the uploaded document
            doc_similar = document_vector_store.similarity_search(question, k=2)
            doc_context = "\n".join([doc.page_content[:500] for doc in doc_similar])
            
            # Get context from legal knowledge base if available
            legal_context = ""
            if self.legal_knowledge_base:
                legal_similar = self.legal_knowledge_base.similarity_search(question, k=1)
                legal_context = legal_similar[0].page_content[:300] if legal_similar else ""
            
            # Determine language instruction
            lang_instruction = ""
            if language != "en":
                language_names = {
                    "hi": "Hindi", "bn": "Bengali", "te": "Telugu", "mr": "Marathi",
                    "ta": "Tamil", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam",
                    "or": "Odia", "pa": "Punjabi", "ur": "Urdu"
                }
                lang_name = language_names.get(language, "Hindi")
                lang_instruction = f"Answer in {lang_name}."
            
            prompt = f"""Based on this legal document and Indian legal context, answer the question.

DOCUMENT CONTEXT:
{doc_context}

LEGAL KNOWLEDGE:
{legal_context}

QUESTION: {question}

{lang_instruction}

Provide a clear, helpful answer based on the context:"""
            
            response = await asyncio.to_thread(self.gemini_llm.predict, prompt)
            
            # Prepare sources
            sources = []
            if doc_similar:
                sources.extend([doc.page_content[:100] + "..." for doc in doc_similar])
            if legal_context:
                sources.append("Legal Knowledge Base")
            
            return response, sources
            
        except Exception as e:
            print(f"Chat error: {e}")
            return f"I apologize, but I couldn't process your question at the moment. Please try again.", []