import logging
import httpx
import asyncio
from typing import Optional, Dict
from app.core.config import settings
from app.core.ai_settings_store import get_ai_settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Dịch vụ tương tác với các nhà cung cấp LLM (OpenAI, Gemini, Groq).
    Bao gồm các quy tắc an toàn, logic thử lại (retry) và cơ chế dự phòng cho AI y tế.
    """

    SYSTEM_PROMPT = (
        "You are an expert Doctor of Pharmacy. Your goal is to provide accurate, "
        "evidence-based information using the provided Knowledge Graph context.\n\n"
        "STRICT RULES:\n"
        "1. LANGUAGE CONSISTENCY: You MUST respond in the EXACT same language as the user's question. "
        "If the user asks in Vietnamese, respond in Vietnamese. If English, respond in English. "
        "This applies to Spanish, French, German, and any other language.\n"
        "2. PRIORITIZE CONTEXT: Base your answer primarily on the provided Knowledge Graph (Neo4j) context. "
        "If Neo4j context is missing or incomplete, use the provided Google Search context as a secondary source. "
        "The context might be in English; you MUST translate and interpret it into the user's language.\n"
        "3. MEDICAL DISCLAIMER: Every response MUST end with a disclaimer in the SAME language as the response:\n"
        "   - Vietnamese: 'Lưu ý: Đây không phải là lời khuyên y tế chuyên môn. Vui lòng tham khảo ý kiến bác sĩ.'\n"
        "   - English: 'Note: This is not professional medical advice. Please consult a doctor.'\n"
        "   - Spanish: 'Nota: Este no es un consejo médico profesional. Por favor, consulte a un médico.'\n"
        "   - French: 'Note : Ceci ne constitue pas un avis médical professionnel. Veuillez consulter un médecin.'\n"
        "   - German: 'Hinweis: Dies ist kein professioneller medizinischer Rat. Bitte konsultieren Sie einen Arzt.'\n"
        "4. NO FINAL DIAGNOSIS: Never give a definitive diagnosis.\n"
        "5. TERMINOLOGY: Keep drug names and active ingredients accurate, using standard medical terms in the target language.\n"
        "6. NO HALLUCINATION: If the provided Knowledge Graph context does not contain enough information, "
        "you may still answer based on your general medical knowledge, but clearly note when exact context is unavailable. "
        "Do not invent facts or medical advice.\n"
        "7. STRICT DOMAIN RESTRICTION: You MUST ONLY answer questions related to medicine, diseases, drugs, health, and medical symptoms. "
        "If the user asks about anything outside of the medical domain (e.g., coding, math, general chatting, jokes, history, physics), "
        "politely decline to answer and state that you are a specialized medical AI and can only answer health-related queries.\n"
    )

    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    async def detect_language(self, text: str) -> str:
        """
        Nhận diện ngôn ngữ của văn bản đầu vào.
        Sử dụng nhận diện theo luật cho tiếng Việt/tiếng Anh trước, sau đó chuyển sang dùng Gemini làm phương án dự phòng.
        """
        if not text:
            return "Unknown"

        normalized = text.strip().lower()

        # Quy tắc nhanh cho các từ tiếng Việt phổ biến.
        vietnamese_keywords = [
            "tôi", "bạn", "thuốc", "triệu chứng", "đau", "đau bụng", "uống", "không", "là gì",
            "một", "có", "và", "họ", "đừng", "có thể", "vì", "nhiều", "đổ mồ hôi"
        ]
        if any(word in normalized for word in vietnamese_keywords):
            return "Vietnamese"

        # Quy tắc nhanh cho các từ khóa tiếng Anh.
        english_keywords = [
            "what", "is", "drug", "symptom", "pain", "aspirin", "ibuprofen", "please", "do not", "how"
        ]
        if any(word in normalized for word in english_keywords):
            return "English"

        prompt = f"Detect the language of the following text and return ONLY the language name (e.g., 'Vietnamese', 'English', 'Spanish', 'French', 'German'):\n\n{text}"

        try:
            # Gọi ngắn để tăng tốc độ
            result = await self._call_gemini(prompt, "Language Detection Task")
            return result.strip() if result else "English"
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "English"

    async def _call_gemini(self, prompt: str, context: str) -> Optional[str]:
        """Gọi Google Gemini API (v1beta) với prompt và ngữ cảnh (context) được cung cấp.

        Sử dụng settings.GEMINI_MODEL (mặc định: gemini-2.5-flash).
        Định dạng endpoint chính thức:
          POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=API_KEY
        """
        ai_config = get_ai_settings()
        api_key = ai_config["api_key"]
        
        if not api_key:
            logger.warning("GEMINI_API_KEY is not configured – skipping Gemini call")
            return None

        model = ai_config["model"]
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )

        logger.debug(f"[Gemini] Model : {model}")
        logger.debug(
            f"[Gemini] Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=***"
        )
        logger.info(
            f"[Gemini] Calling model={model}, prompt_len={len(prompt)}, context_len={len(context)}"
        )

        # Xây dựng payload – system_instruction được hỗ trợ từ v1beta
        prompt_text = (
            f"KNOWLEDGE GRAPH CONTEXT (JSON):\n{context}\n\n"
            f"USER QUESTION: {prompt}"
        )

        if not context.strip():
            prompt_text = f"USER QUESTION: {prompt}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt_text
                        }
                    ],
                }
            ],
            "system_instruction": {"parts": [{"text": self.SYSTEM_PROMPT}]},
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "topK": 40,
                "maxOutputTokens": 8192,
            },
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    endpoint,
                    json=payload,
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                )

                # ── Debug: luôn ghi log trạng thái HTTP ──────────────────────────
                logger.debug(f"[Gemini] HTTP status: {response.status_code}")

                if response.status_code != 200:
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = response.text
                    logger.error(
                        f"[Gemini] Non-200 response – status={response.status_code}, "
                        f"model={model}, body={error_body}"
                    )
                    return None

                data = response.json()

                # Kiểm tra việc chặn ở cấp độ prompt (bộ lọc an toàn, v.v.)
                if data.get("promptFeedback", {}).get("blockReason"):
                    block_reason = data["promptFeedback"]["blockReason"]
                    logger.warning(f"[Gemini] Prompt blocked – reason: {block_reason}")
                    return None

                candidates = data.get("candidates")
                if not candidates:
                    logger.error(f"[Gemini] Response has no candidates: {data}")
                    return None

                # Xử lý các lý do kết thúc khác ngoài STOP
                finish_reason = candidates[0].get("finishReason", "STOP")
                if finish_reason not in ("STOP", "MAX_TOKENS"):
                    logger.warning(
                        f"[Gemini] Unexpected finishReason={finish_reason} for model={model}"
                    )

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    logger.error(f"[Gemini] No text part in response: {data}")
                    return None

                text = parts[0]["text"]
                logger.info(
                    f"[Gemini] Success – model={model}, response_len={len(text)}"
                )
                return text

            except httpx.TimeoutException:
                logger.error(
                    f"[Gemini] Request timed out after {settings.LLM_TIMEOUT_SECONDS}s "
                    f"(model={model})"
                )
                return None
            except Exception as e:
                logger.error(
                    f"[Gemini] Unexpected error (model={model}): {e}", exc_info=True
                )
                return None

    def _get_fallback_messages_by_language(self, language: str) -> Dict[str, str]:
        """Lấy tin nhắn dự phòng cho các ngôn ngữ khác nhau."""
        fallbacks = {
            "vietnamese": {
                "no_context": "Rất tiếc, tôi hiện không thể kết nối với dịch vụ trí tuệ nhân tạo và không tìm thấy thông tin cụ thể trong cơ sở dữ liệu nội bộ. Vui lòng thử lại sau hoặc hỏi bác sĩ của bạn.",
                "context_available": "Hiện tại dịch vụ AI đang bận, sau đây là thông tin thô từ cơ sở dữ liệu y khoa của chúng tôi:",
                "fallback_help": "Vui lòng tự tra cứu kỹ hoặc hỏi ý kiến chuyên môn từ bác sĩ.",
                "disclaimer": "Lưu ý: Đây không phải là lời khuyên y tế chuyên môn. Vui lòng tham khảo ý kiến bác sĩ."
            },
            "english": {
                "no_context": "I apologize, I am currently unable to connect to the AI service and could not find specific information in the database. Please try again later or ask your doctor.",
                "context_available": "The AI service is currently busy. Here is the raw information from our medical database:",
                "fallback_help": "Please research this carefully or ask a medical professional for advice.",
                "disclaimer": "Note: This is not professional medical advice. Please consult a doctor."
            },
            "spanish": {
                "no_context": "Disculpe, actualmente no puedo conectarme al servicio de IA y no pude encontrar información específica en la base de datos. Por favor, inténtelo más tarde o consulte a su médico.",
                "context_available": "El servicio de IA está ocupado actualmente. Aquí está la información sin procesar de nuestra base de datos médica:",
                "fallback_help": "Por favor, investigue esto cuidadosamente o consulte a un profesional médico.",
                "disclaimer": "Nota: Este no es un consejo médico profesional. Por favor, consulte a un médico."
            },
            "french": {
                "no_context": "Je m'excuse, je ne peux actuellement pas me connecter au service IA et je n'ai pas pu trouver d'informations spécifiques dans la base de données. Veuillez réessayer plus tard ou consulter votre médecin.",
                "context_available": "Le service IA est actuellement occupé. Voici les informations brutes de notre base de données médicale :",
                "fallback_help": "Veuillez étudier cela attentivement ou consulter un professionnel de la santé.",
                "disclaimer": "Note : Ceci ne constitue pas un avis médical professionnel. Veuillez consulter un médecin."
            },
            "german": {
                "no_context": "Entschuldigung, ich kann derzeit keine Verbindung zum KI-Dienst herstellen und konnte keine spezifischen Informationen in der Datenbank finden. Bitte versuchen Sie es später noch einmal oder fragen Sie Ihren Arzt.",
                "context_available": "Der KI-Dienst ist derzeit beschäftigt. Hier sind die Rohinformationen aus unserer medizinischen Datenbank:",
                "fallback_help": "Bitte untersuchen Sie dies sorgfältig oder konsultieren Sie einen medizinischen Fachmann.",
                "disclaimer": "Hinweis: Dies ist kein professioneller medizinischer Rat. Bitte konsultieren Sie einen Arzt."
            }
        }
        
        # Chuẩn hóa tên ngôn ngữ
        lang_key = language.lower() if language else "english"
        if lang_key not in fallbacks:
            lang_key = "english"
        
        return fallbacks[lang_key]

    def _get_safe_fallback_answer(self, context: str, language: str = "english") -> str:
        """Câu trả lời dự phòng nếu Gemini lỗi, bằng ngôn ngữ của người dùng."""
        messages = self._get_fallback_messages_by_language(language)
        
        if not context:
            return f"{messages['no_context']}\n\n{messages['disclaimer']}"

        # Thử định dạng ngữ cảnh JSON thô thành định dạng markdown dễ đọc hơn
        formatted_context = ""
        try:
            import json
            # Ngữ cảnh có thể có nhiều khối JSON được phân tách bằng WIKIPEDIA_CONTEXT:
            parts = context.split("WIKIPEDIA_CONTEXT:")
            
            # Định dạng Neo4j
            if parts[0].strip():
                try:
                    neo4j_data = json.loads(parts[0].strip())
                    for item in neo4j_data:
                        formatted_context += f"- **{item.get('name', 'Unknown')}** ({item.get('type', 'Info')}): "
                        details = []
                        if item.get("indications"): details.append(f"Chỉ định: {item.get('indications')}")
                        if item.get("dosage"): details.append(f"Liều lượng: {item.get('dosage')}")
                        if item.get("adverse_reactions"): details.append(f"Tác dụng phụ: {item.get('adverse_reactions')}")
                        if item.get("contraindications"): details.append(f"Chống chỉ định: {item.get('contraindications')}")
                        formatted_context += " | ".join(details) + "\n"
                except:
                    pass

            # Định dạng Wikipedia
            if len(parts) > 1 and parts[1].strip():
                try:
                    wiki_data = json.loads(parts[1].strip())
                    for item in wiki_data:
                        formatted_context += f"- **Wikipedia ({item.get('term', '')})**: {item.get('summary', '')}\n"
                except:
                    pass
            
            if not formatted_context:
                formatted_context = context
        except Exception:
            formatted_context = context

        return (
            f"{messages['context_available']}\n\n"
            f"{formatted_context}\n\n"
            f"{messages['fallback_help']}\n\n"
            f"{messages['disclaimer']}"
        )

    async def generate_response(self, prompt: str, context: str, language: str = "english") -> str:
        """
        Tạo câu trả lời sử dụng Gemini với cơ chế thử lại và logic dự phòng.
        Tham số ngôn ngữ đảm bảo các thông báo dự phòng hiển thị đúng ngôn ngữ.
        """
        ai_config = get_ai_settings()
        if not ai_config.get("api_key"):
            logger.warning("GEMINI_API_KEY is not configured – returning fallback immediately")
            return self._get_safe_fallback_answer(context, language)

        max_retries = settings.LLM_MAX_RETRIES
        response = None

        for attempt in range(max_retries):
            try:
                response = await self._call_gemini(prompt, context)
                if response:
                    break

                logger.warning(f"Lần thử {attempt + 1} thất bại cho Gemini, đang thử lại...")
                await asyncio.sleep(1 * (attempt + 1))  # Giãn cách lũy thừa (Exponential backoff)
            except Exception as e:
                logger.error(f"Lỗi trong lần thử generate_response {attempt + 1}: {e}")

        if response:
            return response

        return self._get_safe_fallback_answer(context, language)


llm_service = LLMService()
