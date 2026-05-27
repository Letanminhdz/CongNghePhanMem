import pytest
import httpx
from app.services.llm_service import llm_service
from app.core.config import settings

@pytest.mark.asyncio
async def test_llm_fallback_no_api_key():
    # Force keys to None
    settings.OPENAI_API_KEY = None
    settings.GEMINI_API_KEY = None
    settings.GROQ_API_KEY = None
    
    context = "Reference drug: Paracetamol is for pain relief."
    response = await llm_service.generate_response("What is paracetamol?", context)
    
    assert "Based on my internal records" in response
    assert "pain relief" in response
    assert "consult a doctor" in response

@pytest.mark.asyncio
async def test_llm_safety_prompt_inclusion():
    # This is more an integration test, but we can check if the prompt exists
    assert "not medical advice" in llm_service.MEDICAL_SAFETY_PROMPT
    assert "diagnosis" in llm_service.MEDICAL_SAFETY_PROMPT
