import os
import json
import pandas as pd
import time
import asyncio
import glob
from typing import List, Tuple, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader # <-- Import added for PDF handling

load_dotenv()

class EnhancedLLMService:
    def __init__(self):
        # Initialize Gemini with optimized settings
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.3,
            max_tokens=2048,
            top_k=40,
            top_p=0.95
        )
        
        # Rate limiting for free tier
        self.rate_limit = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "15"))
        self.last_request_time = 0
        self.min_request_interval = 60 / self.rate_limit  # seconds between requests
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Legal knowledge base setup
        self.legal_kb_collection = None
        self.chroma_client = None
        self.legal_datasets_path = os.getenv("LEGAL_DATASETS_PATH", "./backend/legal_datasets")
        self.enable_legal_kb = os.getenv("ENABLE_LEGAL_KB", "true").lower() == "true"
        
        if self.enable_legal_kb:
            self._initialize_legal_knowledge_base()
        
        print("✅ Enhanced LLM Service initialized")
    
    async def _rate_limit_check(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            print(f"⏰ Rate limiting: waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _initialize_legal_knowledge_base(self):
        """Initialize ChromaDB-based legal knowledge base"""
        try:
            chroma_path = os.path.join(os.getenv("CHROMA_DB_PATH", "./chroma_db"), "legal_kb")
            os.makedirs(chroma_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self.legal_kb_collection = self.chroma_client.get_or_create_collection(
                name="legal_knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            
            if self.legal_kb_collection.count() == 0:
                print("📚 New legal knowledge base detected. Loading datasets...")
                legal_documents = self._load_legal_datasets()
                
                if legal_documents:
                    print(f"📚 Creating legal knowledge base with {len(legal_documents)} documents...")
                    
                    texts = [doc.page_content for doc in legal_documents]
                    metadatas = [doc.metadata for doc in legal_documents]
                    ids = [f"legal_{i}" for i in range(len(legal_documents))]
                    
                    batch_size = 100
                    for i in range(0, len(texts), batch_size):
                        batch_texts = texts[i:i + batch_size]
                        batch_metadatas = metadatas[i:i + batch_size]
                        batch_ids = ids[i:i + batch_size]
                        
                        embeddings = self.embeddings.embed_documents(batch_texts)
                        
                        self.legal_kb_collection.add(
                            embeddings=embeddings,
                            documents=batch_texts,
                            metadatas=batch_metadatas,
                            ids=batch_ids
                        )
                        print(f"📊 Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                    
                    print("✅ Legal knowledge base created successfully!")
                else:
                    print("📂 No legal datasets found. Please add files to backend/legal_datasets/")
            else:
                print(f"✅ Loaded existing legal knowledge base with {self.legal_kb_collection.count()} documents")

        except Exception as e:
            print(f"❌ Error initializing legal knowledge base: {e}")
            self.legal_kb_collection = None
    
    def _load_legal_datasets(self) -> List[Document]:
        """Load legal datasets from files (CSV, JSON, and PDF)"""
        legal_documents = []
        
        if not os.path.exists(self.legal_datasets_path):
            print(f"📂 Creating legal datasets directory: {self.legal_datasets_path}")
            os.makedirs(self.legal_datasets_path, exist_ok=True)
            return []
        
        # --- NEW: Process PDF files ---
        pdf_files = glob.glob(os.path.join(self.legal_datasets_path, "*.pdf"))
        for pdf_file in pdf_files:
            try:
                print(f"📄 Processing PDF: {os.path.basename(pdf_file)}")
                loader = PyPDFLoader(pdf_file)
                pages = loader.load()
                for page in pages:
                    page.metadata["source"] = os.path.basename(pdf_file)
                legal_documents.extend(pages)
                print(f"✅ Loaded {len(pages)} pages from {os.path.basename(pdf_file)}")
            except Exception as e:
                print(f"❌ Error processing {pdf_file}: {e}")

        # Process CSV files
        csv_files = glob.glob(os.path.join(self.legal_datasets_path, "*.csv"))
        for csv_file in csv_files:
            try:
                print(f"📄 Processing CSV: {os.path.basename(csv_file)}")
                df = pd.read_csv(csv_file, nrows=2000)
                
                text_columns = ['text', 'content', 'judgment', 'case_text', 'full_text', 'description', 'summary']
                
                for idx, row in df.iterrows():
                    text_content = None
                    for col in text_columns:
                        if col in df.columns and pd.notna(row.get(col)):
                            text_content = str(row[col])
                            break
                    
                    if text_content and len(text_content) > 100:
                        metadata = { "source": os.path.basename(csv_file), "type": "csv", "row_id": idx }
                        for col in df.columns:
                            if col not in text_columns and pd.notna(row.get(col)):
                                metadata[col] = str(row[col])[:200]
                        
                        legal_documents.append(Document(
                            page_content=text_content[:2000],
                            metadata=metadata
                        ))
                
                print(f"✅ Loaded documents from {os.path.basename(csv_file)}")
                
            except Exception as e:
                print(f"❌ Error processing {csv_file}: {e}")
        
        # Process JSON files
        json_files = glob.glob(os.path.join(self.legal_datasets_path, "*.json"))
        for json_file in json_files:
            try:
                print(f"📄 Processing JSON: {os.path.basename(json_file)}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for i, item in enumerate(data[:1000]):
                        if isinstance(item, dict):
                            text_content = (item.get('text') or item.get('content') or 
                                          item.get('description') or item.get('judgment'))
                            
                            if text_content and len(str(text_content)) > 100:
                                metadata = { "source": os.path.basename(json_file), "type": "json", "item_id": i }
                                for key, value in item.items():
                                    if key not in ['text', 'content']:
                                        metadata[key] = str(value)[:200]
                                
                                legal_documents.append(Document(
                                    page_content=str(text_content)[:2000],
                                    metadata=metadata
                                ))
                
                print(f"✅ Loaded documents from {os.path.basename(json_file)}")
                
            except Exception as e:
                print(f"❌ Error processing {json_file}: {e}")
        
        return legal_documents
    
    async def simplify_document(self, documents: List[Document]) -> str:
        """Simplify legal document using Gemini"""
        try:
            await self._rate_limit_check()
            
            combined_text = ""
            for doc in documents:
                if len(combined_text) + len(doc.page_content) > 4000: break
                combined_text += doc.page_content + "\n\n"
            
            prompt = f"""You are a legal expert helping ordinary people understand legal documents in India. 
DOCUMENT TO SIMPLIFY:
{combined_text}
Please provide a clear, simple explanation that includes:
1. **MAIN PURPOSE**: What is this document for? (in 2-3 sentences)
2. **KEY POINTS**: What are the most important things to know? (3-5 bullet points)
3. **YOUR RIGHTS**: What rights do you have under this document?
4. **YOUR OBLIGATIONS**: What must you do or pay?
5. **IMPORTANT DATES**: Any deadlines or time limits mentioned?
6. **WHAT TO WATCH OUT FOR**: Any concerning clauses or conditions?
Use simple English that a person with basic education can understand. Explain legal terms in plain language."""
            
            result = await asyncio.to_thread(self.gemini_llm.invoke, prompt)
            return result.content
            
        except Exception as e:
            raise Exception(f"Error simplifying document: {str(e)}")
    
    async def assess_risks(self, documents: List[Document]) -> str:
        """Assess legal risks in the document"""
        try:
            await self._rate_limit_check()
            
            combined_text = ""
            for doc in documents:
                if len(combined_text) + len(doc.page_content) > 3500: break
                combined_text += doc.page_content + "\n\n"
            
            prompt = f"""As a legal risk analyst, evaluate the following document for potential risks:
DOCUMENT:
{combined_text}
Provide a comprehensive risk assessment:
**🔴 HIGH RISK AREAS:**
- List any high-risk clauses or terms
- Financial liabilities or penalties
**🟡 MEDIUM RISK AREAS:**
- Potentially problematic terms
- Unclear obligations
**🟢 OVERALL RISK LEVEL:** [Low/Medium/High]
**⚠️ IMMEDIATE ACTION REQUIRED:**
- Any urgent deadlines
- Critical decisions needed
**💡 RECOMMENDATIONS:**
- Suggestions to reduce risks
- When to consult a lawyer
Be specific and practical in your assessment."""
            
            result = await asyncio.to_thread(self.gemini_llm.invoke, prompt)
            return result.content
            
        except Exception as e:
            raise Exception(f"Error assessing risks: {str(e)}")
    
    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target Indian language"""
        try:
            await self._rate_limit_check()
            
            language_names = { "hi": "Hindi (हिंदी)", "bn": "Bengali (বাংলা)", "te": "Telugu (తెలుగు)", "mr": "Marathi (मराठी)", "ta": "Tamil (தமிழ்)", "gu": "Gujarati (ગુજરાતી)", "kn": "Kannada (ಕನ್ನಡ)", "ml": "Malayalam (മലയാളം)", "or": "Odia (ଓଡ଼ିଆ)", "pa": "Punjabi (ਪੰਜਾਬੀ)", "ur": "Urdu (اردو)", "as": "Assamese (অসমীয়া)" }
            target_lang_name = language_names.get(target_language, "Hindi")
            text_to_translate = text[:3000]
            
            prompt = f"""Translate the following legal document explanation to {target_lang_name}. Maintain the structure and formatting.
{text_to_translate}
Translation in {target_lang_name}:"""
            
            result = await asyncio.to_thread(self.gemini_llm.invoke, prompt)
            return result.content
            
        except Exception as e:
            print(f"Translation error: {e}")
            return f"Translation unavailable. Original text: {text[:300]}..."
    
    async def chat_with_document(self, document_vector_store, question: str, language: str = "en") -> Tuple[str, List[str]]:
        """Enhanced chat using document and legal knowledge base"""
        try:
            await self._rate_limit_check()
            
            doc_context = ""
            if hasattr(document_vector_store, 'query'):
                query_embedding = self.embeddings.embed_query(question)
                doc_results = document_vector_store.query(query_embeddings=[query_embedding], n_results=3)
                if doc_results['documents'] and doc_results['documents'][0]:
                    doc_context = "\n".join([doc[:400] for doc in doc_results['documents'][0]])
            
            legal_context = ""
            if self.legal_kb_collection:
                try:
                    legal_query_embedding = self.embeddings.embed_query(question)
                    legal_results = self.legal_kb_collection.query(query_embeddings=[legal_query_embedding], n_results=2)
                    if legal_results['documents'] and legal_results['documents'][0]:
                        legal_context = "\n".join([doc[:300] for doc in legal_results['documents'][0]])
                except Exception as e:
                    print(f"Legal KB query error: {e}")
            
            lang_instruction = ""
            if language != "en":
                language_names = { "hi": "Hindi", "bn": "Bengali", "te": "Telugu", "mr": "Marathi", "ta": "Tamil", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "or": "Odia", "pa": "Punjabi", "ur": "Urdu", "as": "Assamese" }
                lang_name = language_names.get(language, "Hindi")
                lang_instruction = f"Please answer in {lang_name}."
            
            prompt = f"""You are a helpful legal assistant for Indian legal documents. Answer the user's question based on the provided context.
DOCUMENT CONTEXT:
{doc_context}
LEGAL KNOWLEDGE CONTEXT:
{legal_context}
USER QUESTION: {question}
{lang_instruction}
Provide a helpful, accurate answer based on the context. If you cannot find relevant information, say so clearly."""
            
            response = await asyncio.to_thread(self.gemini_llm.invoke, prompt)
            
            sources = []
            if doc_context: sources.append("Your uploaded document")
            if legal_context: sources.append("Legal knowledge base")
            
            return response.content, sources
            
        except Exception as e:
            print(f"Chat error: {e}")
            return ("I apologize, but I couldn't process your question at the moment."), []
    
    def get_legal_kb_info(self) -> Dict[str, Any]:
        """Get information about the legal knowledge base"""
        if not self.legal_kb_collection:
            return {"status": "not_initialized", "count": 0}
        
        try:
            return {
                "status": "active",
                "count": self.legal_kb_collection.count(),
                "datasets_path": self.legal_datasets_path
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "count": 0}