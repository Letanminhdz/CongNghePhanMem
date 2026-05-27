import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with LLM providers (OpenAI, Gemini, Groq).
    Includes safety rules and fallback logic.
    """
    
    MEDICAL_SAFETY_PROMPT = (
        "You are a professional medical assistant. "
        "Rules for safety:\n"
        "1. Never claim a final diagnosis. Always say 'based on the information provided, this could be...'.\n"
        "2. Always include a disclaimer: 'This is not medical advice. Please consult a professional doctor.'.\n"
        "3. If severe symptoms are mentioned (e.g., chest pain, difficulty breathing), warn the user to seek emergency care immediately.\n"
        "4. Do not suggest specific dosages if they could be dangerous. Stick to general information.\n"
        "5. Be concise and empathetic."
    )

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json"
        }

    async def _call_openai(self, prompt: str, context: str) -> Optional[str]:
        if not settings.OPENAI_API_KEY:
            return None
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {**self.headers, "Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        payload = {
            "model": settings.LLM_MODEL or "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": f"{self.MEDICAL_SAFETY_PROMPT}\n\nContext:\n{context}"},
                {"role": "user", "content": prompt}
            ]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=settings.LLM_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenAI call failed: {e}")
                return None

    async def _call_gemini(self, prompt: str, context: str) -> Optional[str]:
        if not settings.GEMINI_API_KEY:
            return None
        
        model = settings.LLM_MODEL or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
        
        full_prompt = f"{self.MEDICAL_SAFETY_PROMPT}\n\nContext:\n{context}\n\nUser Question: {prompt}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=settings.LLM_TIMEOUT_SECONDS)
                response.raise_for_status()
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.error(f"Gemini call failed: {e}")
                return None

    async def _call_groq(self, prompt: str, context: str) -> Optional[str]:
        if not settings.GROQ_API_KEY:
            return None
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {**self.headers, "Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        payload = {
            "model": settings.LLM_MODEL or "mixtral-8x7b-32768",
            "messages": [
                {"role": "system", "content": f"{self.MEDICAL_SAFETY_PROMPT}\n\nContext:\n{context}"},
                {"role": "user", "content": prompt}
            ]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=settings.LLM_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Groq call failed: {e}")
                return None

    def _get_safe_fallback_answer(self, context: str) -> str:
        """Fallback answer if LLM fails or keys are missing."""
        if not context:
            return "I'm sorry, I couldn't find specific information regarding your request in my database. Please consult a doctor for professional advice. (Source: Offline Data)"
        
        return (
            f"Based on my internal records:\n{context}\n\n"
            "This is a pre-formatted answer because the AI connection is currently unavailable. "
            "Please consult a doctor for a professional diagnosis."
        )

    async def generate_response(self, prompt: str, context: str) -> str:
        """
        Generate response using the configured provider with fallbacks.
        """
        provider = settings.LLM_PROVIDER
        response = None

        if provider == "openai":
            response = await self._call_openai(prompt, context)
        elif provider == "gemini":
            response = await self._call_gemini(prompt, context)
        elif provider == "groq":
            response = await self._call_groq(prompt, context)

        # Fallback logic if primary provider fails
        if response is None:
            # Try others if configured, else fallback
            logger.info("Primary provider failed, attempting fallbacks if available...")
            if not response and settings.GEMINI_API_KEY and provider != "gemini":
                response = await self._call_gemini(prompt, context)
            if not response and settings.GROQ_API_KEY and provider != "groq":
                response = await self._call_groq(prompt, context)
            if not response and settings.OPENAI_API_KEY and provider != "openai":
                response = await self._call_openai(prompt, context)

        if response:
            return response
        
        return self._get_safe_fallback_answer(context)

llm_service = LLMService()
