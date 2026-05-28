import logging
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.services.ner_service import ner_service
from app.services.llm_service import llm_service
from app.services.neo4j_service import neo4j_service
from app.models.chat import ChatHistory
from app.schemas.chat import ChatMessageResponse

logger = logging.getLogger(__name__)

class ChatService:
    """
    RAG Orchestrator:
    User Message -> Intent -> NER -> Neo4j -> Context -> LLM -> History -> API Response
    """

    def _detect_intent(self, message: str) -> str:
        message = message.lower()
        if any(word in message for word in ["tác dụng", "là gì", "what is", "effect"]):
            return "drug_info"
        if any(word in message for word in ["tương tác", "dùng chung", "interaction", "together"]):
            return "interaction_check"
        if any(word in message for word in ["bệnh", "triệu chứng", "symptom", "disease"]):
            return "disease_info"
        return "general_query"

    def _build_context(self, entities: dict) -> Tuple[str, List[str], List[str]]:
        context_parts = []
        sources = []
        warnings = []

        # Process Drugs
        for drug_name in entities.get("drugs", []):
            detail = neo4j_service.get_drug_detail(drug_name)
            if detail:
                sources.append(f"Drug: {drug_name}")
                desc = f"Drug {drug_name}: {detail.get('purpose', 'N/A')}. Indications: {detail.get('indications', 'N/A')}."
                if detail.get('warnings'):
                    warnings.append(f"Warning for {drug_name}: {detail['warnings']}")
                context_parts.append(desc)

        # Process Diseases
        for disease_name in entities.get("diseases", []):
            detail = neo4j_service.get_disease_symptoms(disease_name)
            if detail:
                sources.append(f"Disease: {disease_name}")
                desc = f"Disease {disease_name}: {detail.get('description', 'N/A')}. Symptoms: {', '.join([s['name'] for s in detail.get('symptoms', [])])}."
                context_parts.append(desc)

        return "\n".join(context_parts), sources, warnings

    async def process_chat(self, db: Session, user_id: int, message: str) -> ChatMessageResponse:
        try:
            # 1. NER
            entities = ner_service.extract_entities(message)
            all_entity_names = entities.get("drugs", []) + entities.get("diseases", [])
            
            # 2. Intent & Context
            intent = self._detect_intent(message)
            context, sources, warnings = self._build_context(entities)
            
            # 3. LLM Generation
            answer = await llm_service.generate_response(message, context)
            
            # 4. Save History
            chat_record = ChatHistory(
                user_id=user_id,
                message=message,
                response=answer,
                intent=intent,
                entities=",".join(all_entity_names)
            )
            db.add(chat_record)
            db.commit()
            
            return ChatMessageResponse(
                answer=answer,
                entities=all_entity_names,
                sources=sources,
                warnings=warnings
            )
        except Exception as e:
            logger.exception(f"Error in chat processing: {e}")
            return ChatMessageResponse(
                answer="I encountered an error while processing your request. Please try again later.",
                warnings=[str(e)]
            )

    def get_user_history(self, db: Session, user_id: int, limit: int = 20) -> List[ChatHistory]:
        return db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.created_at.desc()).limit(limit).all()

chat_service = ChatService()
