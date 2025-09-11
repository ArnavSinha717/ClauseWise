import os
import base64
import logging
import tempfile
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
import openai
from pydub import AudioSegment
import io

load_dotenv()

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        """Initialize both TTS and STT services with Indian language support"""
        # TTS Configuration (ElevenLabs)
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.tts_client = None
        if self.elevenlabs_api_key:
            try:
                self.tts_client = ElevenLabs(api_key=self.elevenlabs_api_key)
                logger.info("✅ ElevenLabs TTS service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ElevenLabs: {e}")
        
        # STT Configuration (OpenAI Whisper)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            logger.info("✅ OpenAI Whisper STT service initialized")
        else:
            logger.warning("OPENAI_API_KEY not found. STT functionality will be limited.")
        
        # Indian Language Support
        self.indian_language_support = {
            "hi": {"name": "Hindi", "whisper_code": "hi", "elevenlabs_supported": True},
            "bn": {"name": "Bengali", "whisper_code": "bn", "elevenlabs_supported": True},
            "te": {"name": "Telugu", "whisper_code": "te", "elevenlabs_supported": True},
            "ta": {"name": "Tamil", "whisper_code": "ta", "elevenlabs_supported": True},
            "mr": {"name": "Marathi", "whisper_code": "mr", "elevenlabs_supported": True},
            "gu": {"name": "Gujarati", "whisper_code": "gu", "elevenlabs_supported": True},
            "kn": {"name": "Kannada", "whisper_code": "kn", "elevenlabs_supported": True},
            "ml": {"name": "Malayalam", "whisper_code": "ml", "elevenlabs_supported": True},
            "pa": {"name": "Punjabi", "whisper_code": "pa", "elevenlabs_supported": True},
            "or": {"name": "Odia", "whisper_code": "or", "elevenlabs_supported": True},
            "as": {"name": "Assamese", "whisper_code": "as", "elevenlabs_supported": False},
            "ur": {"name": "Urdu", "whisper_code": "ur", "elevenlabs_supported": True},
            "en": {"name": "English", "whisper_code": "en", "elevenlabs_supported": True}
        }
        
        # Default settings
        self.default_voice_id = os.getenv("ELEVENLABS_DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.default_voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    
    def is_tts_available(self) -> bool:
        """Check if TTS service is available"""
        return self.tts_client is not None
    
    def is_stt_available(self) -> bool:
        """Check if STT service is available"""
        return bool(self.openai_api_key)
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """Get supported languages for both STT and TTS"""
        return self.indian_language_support
    
    def is_language_supported(self, language_code: str, service: str = "both") -> bool:
        """Check if a language is supported for STT, TTS, or both"""
        if language_code not in self.indian_language_support:
            return False
        
        lang_info = self.indian_language_support[language_code]
        
        if service == "stt":
            return bool(lang_info.get("whisper_code"))
        elif service == "tts":
            return lang_info.get("elevenlabs_supported", False)
        else:  # both
            return bool(lang_info.get("whisper_code")) and lang_info.get("elevenlabs_supported", False)
    
    async def speech_to_text(
        self, 
        audio_data: bytes, 
        audio_format: str = "webm", 
        language: str = "en"
    ) -> Optional[str]:
        """
        Convert speech to text using OpenAI Whisper with language support
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, mp3, wav, etc.)
            language: Language code for transcription
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.is_stt_available():
            logger.warning("STT service not available")
            return None
        
        if not audio_data:
            logger.warning("Empty audio data provided for STT")
            return None
        
        # Check language support
        if language not in self.indian_language_support:
            logger.warning(f"Language {language} not supported, defaulting to English")
            language = "en"
        
        whisper_language = self.indian_language_support[language]["whisper_code"]
        
        temp_audio_path = None
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
            
            # Convert to WAV if needed (Whisper prefers WAV/MP3)
            if audio_format.lower() in ['webm', 'ogg']:
                try:
                    audio = AudioSegment.from_file(temp_audio_path, format=audio_format)
                    wav_path = temp_audio_path.replace(f".{audio_format}", ".wav")
                    audio.export(wav_path, format="wav")
                    temp_audio_path = wav_path
                except Exception as e:
                    logger.warning(f"Audio conversion failed, using original: {e}")
            
            logger.info(f"Transcribing audio in {language} ({whisper_language})")
            
            # Transcribe with OpenAI Whisper
            with open(temp_audio_path, "rb") as audio_file:
                response = await asyncio.to_thread(
                    openai.audio.transcriptions.create,
                    model="whisper-1",
                    file=audio_file,
                    language=whisper_language
                )
            
            transcribed_text = response.text.strip()
            logger.info(f"✅ Successfully transcribed: {len(transcribed_text)} characters in {language}")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"❌ Error in speech-to-text for {language}: {e}")
            return None
        
        finally:
            # Clean up temporary files
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    # Also remove converted WAV if it exists
                    wav_path = temp_audio_path.replace(".webm", ".wav").replace(".ogg", ".wav")
                    if wav_path != temp_audio_path and os.path.exists(wav_path):
                        os.remove(wav_path)
                except Exception as e:
                    logger.warning(f"Could not remove temp audio file: {e}")
    
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Optional[str]:
        """
        Convert text to speech using ElevenLabs with Indian language support
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (optional)
            voice_settings: Voice configuration (optional)
            language: Language code for TTS
            
        Returns:
            Base64 encoded audio data or None if failed
        """
        if not self.is_tts_available():
            logger.warning("TTS service not available")
            return None
        
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for TTS")
            return None
        
        # Check language support for TTS
        if not self.is_language_supported(language, "tts"):
            logger.warning(f"TTS not supported for {language}, defaulting to English")
            language = "en"
        
        # Limit text length
        if len(text) > 5000:
            logger.warning(f"Text too long for TTS ({len(text)} chars), truncating")
            text = text[:4500] + "..."
        
        try:
            voice_id = voice_id or self.default_voice_id
            settings = voice_settings or self.default_voice_settings
            
            logger.info(f"Generating speech in {language} for {len(text)} characters")
            
            # Use multilingual model for Indian languages
            model = "eleven_multilingual_v2" if language != "en" else "eleven_monolingual_v1"
            
            # Generate speech
            audio_generator = self.tts_client.generate(
                text=text,
                voice=voice_id,
                voice_settings=settings,
                model=model
            )
            
            # Convert to bytes
            audio_bytes = b"".join(audio_generator)
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            logger.info(f"✅ Generated {len(audio_bytes)} bytes of audio in {language}")
            return audio_base64
            
        except Exception as e:
            logger.error(f"❌ Error in text-to-speech for {language}: {e}")
            return None
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get available TTS voices with language capabilities"""
        if not self.is_tts_available():
            return {"error": "TTS service not available", "voices": []}
        
        try:
            voices = self.tts_client.voices.get_all()
            
            voice_list = []
            for voice in voices.voices:
                voice_info = {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "description": getattr(voice, 'description', ''),
                    "category": getattr(voice, 'category', ''),
                    "labels": getattr(voice, 'labels', {}),
                    "preview_url": getattr(voice, 'preview_url', ''),
                    "supports_multilingual": True  # ElevenLabs multilingual model supports most voices
                }
                voice_list.append(voice_info)
            
            logger.info(f"Retrieved {len(voice_list)} available voices")
            return {
                "voices": voice_list, 
                "default_voice_id": self.default_voice_id,
                "supported_languages": self.indian_language_support
            }
            
        except Exception as e:
            logger.error(f"Error retrieving voices: {e}")
            return {"error": str(e), "voices": []}
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get voice service information with Indian language support"""
        return {
            "tts": {
                "service": "ElevenLabs",
                "available": self.is_tts_available(),
                "default_voice_id": self.default_voice_id if self.is_tts_available() else None,
                "max_text_length": 5000,
                "supported_formats": ["mp3"],
                "supported_languages": [
                    {
                        "code": code,
                        "name": info["name"],
                        "supported": info["elevenlabs_supported"]
                    }
                    for code, info in self.indian_language_support.items()
                    if info["elevenlabs_supported"]
                ]
            },
            "stt": {
                "service": "OpenAI Whisper",
                "available": self.is_stt_available(),
                "supported_formats": ["webm", "mp3", "wav", "m4a", "ogg"],
                "max_file_size_mb": 25,
                "supported_languages": [
                    {
                        "code": code,
                        "name": info["name"],
                        "whisper_code": info["whisper_code"]
                    }
                    for code, info in self.indian_language_support.items()
                    if info["whisper_code"]
                ]
            },
            "api_keys": {
                "elevenlabs_configured": bool(self.elevenlabs_api_key),
                "openai_configured": bool(self.openai_api_key)
            },
            "indian_languages": self.indian_language_support
        }