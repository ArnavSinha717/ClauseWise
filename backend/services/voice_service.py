import os
import base64
import logging
import tempfile
import asyncio
import io
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# ElevenLabs for both TTS and STT
try:
    from elevenlabs import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# Audio processing
try:
    from pydub import AudioSegment
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        """Initialize voice service with ElevenLabs for both TTS and STT"""
        
        # ElevenLabs Configuration
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.client = None
        
        if self.elevenlabs_api_key and ELEVENLABS_AVAILABLE:
            try:
                self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
                logger.info("✅ ElevenLabs TTS + STT service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ElevenLabs: {e}")
        else:
            logger.warning("ElevenLabs API key not found or package not installed")
        
        # Indian Language Support (based on ElevenLabs Scribe v1 documentation)
        self.indian_language_support = {
            "hi": {
                "name": "Hindi",
                "elevenlabs_code": "hin",  # ElevenLabs language code
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "excellent"  # ≤ 5% WER
            },
            "bn": {
                "name": "Bengali", 
                "elevenlabs_code": "ben",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "high"  # >5% to ≤10% WER
            },
            "te": {
                "name": "Telugu",
                "elevenlabs_code": "tel",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "high"
            },
            "ta": {
                "name": "Tamil",
                "elevenlabs_code": "tam",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "high"
            },
            "mr": {
                "name": "Marathi",
                "elevenlabs_code": "mar",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "high"
            },
            "gu": {
                "name": "Gujarati",
                "elevenlabs_code": "guj",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "good"  # >10% to ≤25% WER
            },
            "kn": {
                "name": "Kannada",
                "elevenlabs_code": "kan",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "excellent"
            },
            "ml": {
                "name": "Malayalam",
                "elevenlabs_code": "mal",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "excellent"
            },
            "pa": {
                "name": "Punjabi",
                "elevenlabs_code": "pan",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "good"
            },
            "or": {
                "name": "Odia",
                "elevenlabs_code": "ori",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "high"
            },
            "as": {
                "name": "Assamese",
                "elevenlabs_code": "asm",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "good"
            },
            "ur": {
                "name": "Urdu",
                "elevenlabs_code": "urd",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "good"
            },
            "en": {
                "name": "English",
                "elevenlabs_code": "eng",
                "tts_supported": True,
                "stt_supported": True,
                "accuracy": "excellent"
            }
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
        return self.client is not None
    
    def is_stt_available(self) -> bool:
        """Check if STT service is available"""
        return self.client is not None
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """Get supported languages for both STT and TTS"""
        return self.indian_language_support
    
    def is_language_supported(self, language_code: str, service: str = "both") -> bool:
        """Check if a language is supported for STT, TTS, or both"""
        if language_code not in self.indian_language_support:
            return False
        
        lang_info = self.indian_language_support[language_code]
        
        if service == "stt":
            return lang_info.get("stt_supported", False)
        elif service == "tts":
            return lang_info.get("tts_supported", False)
        else:  # both
            return lang_info.get("stt_supported", False) and lang_info.get("tts_supported", False)
    
    async def speech_to_text(
        self, 
        audio_data: bytes, 
        audio_format: str = "webm", 
        language: str = "en"
    ) -> Optional[str]:
        """
        Convert speech to text using ElevenLabs STT (Scribe v1)
        
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
        
        # Get ElevenLabs language code
        elevenlabs_lang_code = self.indian_language_support[language]["elevenlabs_code"]
        
        temp_audio_path = None
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
            
            # Convert to supported format if needed
            if audio_format.lower() in ['webm', 'ogg'] and AUDIO_PROCESSING_AVAILABLE:
                try:
                    audio = AudioSegment.from_file(temp_audio_path, format=audio_format)
                    wav_path = temp_audio_path.replace(f".{audio_format}", ".wav")
                    audio.export(wav_path, format="wav")
                    temp_audio_path = wav_path
                    audio_format = "wav"
                except Exception as e:
                    logger.warning(f"Audio conversion failed, using original: {e}")
            
            logger.info(f"Transcribing audio in {language} ({elevenlabs_lang_code}) using ElevenLabs Scribe v1")
            
            # ElevenLabs STT API call
            with open(temp_audio_path, "rb") as audio_file:
                # Using the correct ElevenLabs STT API method
                response = await asyncio.to_thread(
                    self.client.speech_to_text.transcribe,
                    audio_file,
                    model_id="scribe-v1"  # Scribe v1 model
                )
            
            # Extract transcribed text from response
            if hasattr(response, 'text'):
                transcribed_text = response.text
            elif isinstance(response, dict) and 'text' in response:
                transcribed_text = response['text']
            else:
                logger.error("Unexpected response format from ElevenLabs STT")
                return None
            
            logger.info(f"✅ Successfully transcribed: {len(transcribed_text)} characters in {language}")
            return transcribed_text.strip()
                
        except Exception as e:
            logger.error(f"❌ Error in speech-to-text for {language}: {e}")
            return None
        
        finally:
            # Clean up temporary files
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    # Also remove converted files
                    for ext in ['.wav', '.mp3']:
                        converted_path = temp_audio_path.replace(f".{audio_format}", ext)
                        if converted_path != temp_audio_path and os.path.exists(converted_path):
                            os.remove(converted_path)
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
        Convert text to speech using ElevenLabs TTS
        
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
        max_length = int(os.getenv("TTS_MAX_CHARACTERS", "5000"))
        if len(text) > max_length:
            logger.warning(f"Text too long for TTS ({len(text)} chars), truncating")
            text = text[:max_length-3] + "..."
        
        try:
            voice_id = voice_id or self.default_voice_id
            settings = voice_settings or self.default_voice_settings
            
            logger.info(f"Generating speech in {language} for {len(text)} characters")
            
            # Use multilingual model for Indian languages
            model = "eleven_multilingual_v2" if language != "en" else "eleven_monolingual_v1"
            
            # Generate speech
            audio_generator = self.client.generate(
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
            voices = self.client.voices.get_all()
            
            voice_list = []
            for voice in voices.voices:
                voice_info = {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "description": getattr(voice, 'description', ''),
                    "category": getattr(voice, 'category', ''),
                    "labels": getattr(voice, 'labels', {}),
                    "preview_url": getattr(voice, 'preview_url', ''),
                    "supports_multilingual": True
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
        """Get voice service information"""
        return {
            "tts": {
                "service": "ElevenLabs",
                "available": self.is_tts_available(),
                "default_voice_id": self.default_voice_id if self.is_tts_available() else None,
                "max_text_length": int(os.getenv("TTS_MAX_CHARACTERS", "5000")),
                "supported_formats": ["mp3"],
                "supported_languages": [
                    {
                        "code": code,
                        "name": info["name"],
                        "supported": info["tts_supported"]
                    }
                    for code, info in self.indian_language_support.items()
                ]
            },
            "stt": {
                "service": "ElevenLabs Scribe v1",
                "available": self.is_stt_available(),
                "supported_formats": ["webm", "mp3", "wav", "m4a", "ogg", "aac", "flac", "mp4"],
                "max_file_size_mb": int(os.getenv("STT_MAX_FILE_SIZE_MB", "3000")),  # 3GB limit
                "max_duration_hours": int(os.getenv("STT_MAX_DURATION_HOURS", "10")),
                "supported_languages": [
                    {
                        "code": code,
                        "name": info["name"],
                        "elevenlabs_code": info["elevenlabs_code"],
                        "accuracy": info["accuracy"]
                    }
                    for code, info in self.indian_language_support.items()
                ]
            },
            "api_keys": {
                "elevenlabs_configured": bool(self.elevenlabs_api_key)
            },
            "indian_languages": self.indian_language_support
        }