import logging
import json
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
        context_data = []
        sources = []
        warnings = []
        
        found_data = False

        # Process Drugs
        for drug_name in entities.get("drugs", []):
            drug_name = drug_name.strip()
            detail = neo4j_service.get_drug_detail(drug_name)
            if detail:
                found_data = True
                context_data.append({
                    "type": "drug",
                    "name": detail.get("name"),
                    "indications": detail.get("indications"),
                    "dosage": detail.get("dosage"),
                    "warnings": detail.get("warnings"),
                    "ingredients": [i["name"] for i in detail.get("ingredients", [])],
                    "manufacturers": [m["name"] for m in detail.get("manufacturers", [])]
                })
                if detail.get('warnings'):
                    warnings.append(f"Warning for {drug_name}: {detail['warnings']}")

        # Process Diseases
        for disease_name in entities.get("diseases", []):
            disease_name = disease_name.strip()
            detail = neo4j_service.get_disease_symptoms(disease_name)
            if detail:
                found_data = True
                context_data.append({
                    "type": "disease",
                    "name": detail.get("name"),
                    "description": detail.get("description"),
                    "symptoms": [s["name"] for s in detail.get("symptoms", [])]
                })

        if found_data:
            sources.append("Neo4j Knowledge Graph")
            # Use JSON for structured context
            context_str = json.dumps(context_data, indent=2, ensure_ascii=False)
            return context_str, sources, warnings
        
        return "", [], []

    async def process_chat(self, db: Session, user_id: int, message: str) -> ChatMessageResponse:
        try:
            # 1. NER
            entities = ner_service.extract_entities(message)
            all_entity_names = entities.get("drugs", []) + entities.get("diseases", [])
            logger.info(f"Detected entities: {entities}")
            
            # 2. Intent & Context
            intent = self._detect_intent(message)
            context, sources, warnings = self._build_context(entities)
            logger.info(f"Retrieved graph context: {context}")
            
            # 3. Prompt Construction
            llm_prompt = message
            if context:
                logger.info(f"Final RAG context JSON: {context}")
                llm_prompt = (
                    f"Use the following medical knowledge graph context:\n\n"
                    f"{context}\n\n"
                    f"Answer the user's medical question accurately.\n"
                    f"If data exists in the graph, use it.\n"
                    f"Mention warnings and dosage if available.\n\n"
                    f"User question:\n{message}"
                )
            
            # 4. LLM Generation
            answer = await llm_service.generate_response(llm_prompt, context)
            
            # 5. Save History
            chat_record = ChatHistory(
                user_id=user_id,
                message=message,
                response=answer,
                intent=intent,
                entities=",".join(all_entity_names)
            )
            db.add(chat_record)
            db.commit()
            
            llm_sources = sources if sources else ["Offline Data"]
            logger.info(f"LLM sources: {llm_sources}")

            return ChatMessageResponse(
                answer=answer,
                entities=all_entity_names,
                sources=llm_sources,
                warnings=warnings
            )
        except Exception as e:
            logger.exception(f"Error in chat processing: {e}")
            return ChatMessageResponse(
                answer="I encountered an error while processing your request. Please try again later.",
                warnings=[str(e)],
                sources=["Offline Data"]
            )

    def get_user_history(self, db: Session, user_id: int, limit: int = 20) -> List[ChatHistory]:
        return db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.created_at.desc()).limit(limit).all()

chat_service = ChatService()
