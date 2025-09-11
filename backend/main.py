# Add these Pydantic models for language-aware voice operations
class DocumentUploadRequest(BaseModel):
    language: Optional[str] = "en"  # Document language

class VoiceTranscriptionRequest(BaseModel):
    audio_format: str = "webm"
    language: str = "en"  # Language for transcription

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    voice_settings: Optional[Dict[str, Any]] = None
    language: str = "en"  # Language for TTS

class ChatRequest(BaseModel):
    document_id: str
    question: str
    language: str = "en"
    use_document_language: bool = True  # Use document's original language

# Update the upload endpoint to store document language
@app.post("/upload-document", tags=["Document"])
async def upload_document(
    file: UploadFile = File(...),
    language: str = "en"  # Add language parameter
):
    """Upload and process a PDF document with language preference"""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    # Validate file size (10MB limit)
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > 10:
        raise HTTPException(status_code=400, detail=f"File too large ({file_size_mb:.1f}MB). Maximum size is 10MB.")
    
    logger.info(f"Processing uploaded file: {file.filename} ({file_size_mb:.1f}MB) in {language}")
    
    try:
        # Process the document
        doc_id, chunks = document_processor.process_uploaded_file(file_content, file.filename)

        if not doc_id or not chunks:
            logger.error(f"Failed to process {file.filename} - no content extracted")
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF. The file might be corrupted, password-protected, or contain only images.")
        
        logger.info(f"Successfully processed {file.filename}: {len(chunks)} chunks created")
        
        # Create vector store
        vector_store_manager.create_vector_store(doc_id, chunks)
        
        # Store document language preference in metadata
        doc_info = document_processor.get_document_info(chunks)
        doc_info["language"] = language
        doc_info["supports_voice"] = voice_service.is_language_supported(language)
        
        # Store language in vector store metadata if possible
        try:
            collection = vector_store_manager.get_vector_store(doc_id)
            if collection:
                # Update collection metadata with language info
                collection.modify(metadata={"language": language, "voice_supported": doc_info["supports_voice"]})
        except Exception as e:
            logger.warning(f"Could not store language metadata: {e}")
        
        return {
            "message": "Document processed successfully",
            "document_id": doc_id,
            "filename": file.filename,
            "num_chunks": len(chunks),
            "file_size_mb": round(file_size_mb, 2),
            "document_info": doc_info,
            "language": language,
            "voice_support": {
                "stt_supported": voice_service.is_language_supported(language, "stt"),
                "tts_supported": voice_service.is_language_supported(language, "tts")
            }
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

# Update voice transcription endpoint
@app.post("/voice/transcribe", tags=["Voice"])
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str = "en"
):
    """Convert speech to text using OpenAI Whisper with Indian language support"""
    try:
        if not voice_service.is_stt_available():
            raise HTTPException(
                status_code=503,
                detail="Speech-to-text service unavailable. Please check OpenAI API key."
            )
        
        # Check language support
        if not voice_service.is_language_supported(language, "stt"):
            raise HTTPException(
                status_code=400,
                detail=f"Speech-to-text not supported for language: {language}"
            )
        
        # Validate file size (25MB limit for Whisper)
        file_content = await audio_file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > 25:
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large ({file_size_mb:.1f}MB). Maximum size is 25MB."
            )
        
        logger.info(f"Transcribing audio in {language}: {audio_file.filename} ({file_size_mb:.1f}MB)")
        
        # Determine audio format from filename
        audio_format = "webm"
        if audio_file.filename:
            ext = audio_file.filename.split('.')[-1].lower()
            if ext in ['mp3', 'wav', 'm4a', 'ogg']:
                audio_format = ext
        
        # Transcribe audio
        transcribed_text = await voice_service.speech_to_text(file_content, audio_format, language)
        
        if not transcribed_text:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")
        
        return {
            "transcribed_text": transcribed_text,
            "language": language,
            "audio_format": audio_format,
            "file_size_mb": round(file_size_mb, 2),
            "text_length": len(transcribed_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

# Update TTS endpoint
@app.post("/voice/speak", tags=["Voice"])
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using ElevenLabs with Indian language support"""
    try:
        if not voice_service.is_tts_available():
            raise HTTPException(
                status_code=503,
                detail="Text-to-speech service unavailable. Please check ElevenLabs API key."
            )
        
        # Check language support
        if not voice_service.is_language_supported(request.language, "tts"):
            raise HTTPException(
                status_code=400,
                detail=f"Text-to-speech not supported for language: {request.language}"
            )
        
        logger.info(f"TTS request in {request.language}: {len(request.text)} characters")
        
        # Validate text
        if len(request.text) > 5000:
            raise HTTPException(
                status_code=400,
                detail="Text too long. Maximum 5000 characters allowed."
            )
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Generate speech
        audio_base64 = await voice_service.text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            voice_settings=request.voice_settings,
            language=request.language
        )
        
        if not audio_base64:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
        
        return {
            "audio_base64": audio_base64,
            "voice_id": request.voice_id or voice_service.default_voice_id,
            "language": request.language,
            "text_length": len(request.text),
            "format": "mp3"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

# Add endpoint to get supported Indian languages
@app.get("/voice/languages", tags=["Voice"])
async def get_supported_languages():
    """Get supported Indian languages for voice services"""
    try:
        languages = voice_service.get_supported_languages()
        return {
            "supported_languages": languages,
            "tts_languages": [
                code for code, info in languages.items() 
                if info.get("elevenlabs_supported", False)
            ],
            "stt_languages": [
                code for code, info in languages.items() 
                if info.get("whisper_code")
            ]
        }
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Update chat endpoint to handle document language
@app.post("/chat", tags=["Interaction"])
async def chat_with_document_endpoint(request: ChatRequest):
    """Chat with a document using AI with language-aware voice support"""
    try:
        logger.info(f"Chat request for document {request.document_id}: {request.question[:50]}...")
        
        # Get vector store
        vector_store = vector_store_manager.get_vector_store(request.document_id)
        if not vector_store:
            raise HTTPException(status_code=404, detail="Document vector store not found.")

        # Get document language if use_document_language is True
        document_language = request.language
        if request.use_document_language:
            try:
                # Try to get language from vector store metadata
                collection_info = vector_store_manager.get_collection_info(request.document_id)
                stored_language = collection_info.get("metadata", {}).get("language")
                if stored_language:
                    document_language = stored_language
                    logger.info(f"Using document language: {document_language}")
            except Exception as e:
                logger.warning(f"Could not retrieve document language: {e}")

        # Get answer from LLM
        answer, sources = await llm_service.chat_with_document(
            document_vector_store=vector_store,
            question=request.question,
            language=document_language
        )
        
        return {
            "answer": answer,
            "sources": sources,
            "question": request.question,
            "language": document_language,
            "document_id": request.document_id,
            "voice_support": {
                "can_speak_response": voice_service.is_language_supported(document_language, "tts"),
                "can_transcribe_input": voice_service.is_language_supported(document_language, "stt")
            }
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error in chat for document {request.document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# Get document language info
@app.get("/documents/{document_id}/language", tags=["Document"])
async def get_document_language(document_id: str):
    """Get language information for a specific document"""
    try:
        collection_info = vector_store_manager.get_collection_info(document_id)
        if not collection_info:
            raise HTTPException(status_code=404, detail="Document not found")
        
        language = collection_info.get("metadata", {}).get("language", "en")
        
        return {
            "document_id": document_id,
            "language": language,
            "language_name": voice_service.get_supported_languages().get(language, {}).get("name", "Unknown"),
            "voice_support": {
                "stt_supported": voice_service.is_language_supported(language, "stt"),
                "tts_supported": voice_service.is_language_supported(language, "tts")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document language: {e}")
        raise HTTPException(status_code=500, detail=str(e))