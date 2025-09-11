from typing import Dict

class TranslatorService:
    """Simplified translator service - translation handled by Gemini in LLM service"""
    
    def __init__(self):
        self.language_codes = {
            "hi": "Hindi",
            "bn": "Bengali", 
            "te": "Telugu",
            "mr": "Marathi",
            "ta": "Tamil",
            "gu": "Gujarati",
            "kn": "Kannada",
            "ml": "Malayalam",
            "or": "Odia",
            "pa": "Punjabi",
            "as": "Assamese",
            "ur": "Urdu"
        }
    
    async def translate_text(self, text: str, target_language: str) -> str:
        """Placeholder - actual translation handled by LLM service to avoid extra API calls"""
        return f"Translation will be handled by main LLM service to optimize API usage."
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported language codes and names"""
        return self.language_codes