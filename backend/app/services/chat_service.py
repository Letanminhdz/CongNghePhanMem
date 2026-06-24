import logging
import json
import time
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.ner_service import ner_service
from app.services.llm_service import llm_service
from app.services.neo4j_service import neo4j_service
from app.services.wikipedia_service import wikipedia_service
from app.models.chat import ChatHistory
from app.schemas.chat import ChatMessageResponse

logger = logging.getLogger(__name__)

class ChatService:
    """
    Bộ điều phối RAG:
    Tin nhắn người dùng -> Ý định -> NER -> Neo4j -> Ngữ cảnh -> LLM -> Lịch sử -> Phản hồi API
    """

    def _detect_intent(self, message: str) -> str:
        """
        Mục đích: Phân tích và phát hiện ý định (intent) của người dùng từ tin nhắn gửi lên.
        Cơ chế hoạt động: Chuyển tin nhắn thành chữ thường và quét qua các từ khóa phổ biến để phân loại thành:
        - "interaction_check": Kiểm tra tương tác thuốc.
        - "drug_info": Tra cứu thông tin chi tiết về thuốc.
        - "disease_info": Tra cứu thông tin bệnh lý/triệu chứng.
        - "general_query": Các câu hỏi chung khác.
        """
        # message: Chuỗi tin nhắn đầu vào của người dùng cần phân tích ý định
        message = message.lower() # Chuyển đổi toàn bộ tin nhắn thành chữ thường để so khớp không phân biệt hoa thường
        if any(word in message for word in ["tương tác", "dùng chung", "interaction", "together", "kết hợp"]):
            return "interaction_check"
        if any(word in message for word in ["tác dụng", "là gì", "what is", "effect", "công dụng"]):
            return "drug_info"
        if any(word in message for word in ["bệnh", "triệu chứng", "symptom", "disease", "đau", "sốt"]):
            return "disease_info"
        return "general_query"

    def _build_context(self, entities: Dict[str, List[str]], intent: str = "general_query") -> Tuple[str, List[str], List[str]]:
        """
        Mục đích: Truy xuất và xây dựng ngữ cảnh y tế từ cơ sở dữ liệu đồ thị Neo4j dựa trên các thực thể (thuốc/bệnh lý) đã nhận diện.
        Cơ chế hoạt động:
        1. Lấy ra danh sách thuốc và bệnh lý từ danh sách thực thể đầu vào.
        2. Nếu không có thực thể nào, trả về kết quả rỗng.
        3. Gọi `neo4j_service.get_subgraph_context` để truy vấn một đồ thị con chứa các thực thể này trong Neo4j.
        4. Lọc thông tin, lấy ra các nguồn (sources), các cảnh báo y tế (warnings), đặc biệt là cảnh báo tương tác thuốc nếu ý định là "interaction_check".
        """
        # entities: Từ điển chứa các thực thể y tế đã được nhận diện (phân loại thành "drugs" và "diseases")
        # intent: Ý định của người dùng dùng để tối ưu hóa quá trình xây dựng ngữ cảnh
        drugs = entities.get("drugs", []) # Danh sách tên thuốc được nhận diện
        diseases = entities.get("diseases", []) # Danh sách tên bệnh lý được nhận diện
        
        if not drugs and not diseases:
            return "", [], []

        # Tìm kiếm Graph-First: gộp tất cả thực thể vào một truy vấn đồ thị con
        # context_data: Dữ liệu đồ thị con lấy từ Neo4j chứa thông tin chi tiết của thuốc và bệnh lý
        context_data = neo4j_service.get_subgraph_context(drugs, diseases)
        
        sources = [] # Danh sách nguồn dữ liệu từ Neo4j
        warnings = [] # Danh sách các cảnh báo y tế liên quan
        
        for item in context_data:
            name = item.get("name") # Tên thực thể trong Neo4j
            label = item.get("type", "unknown").capitalize() # Nhãn thực thể (ví dụ: Drug, Disease)
            sources.append(f"Neo4j: {label}({name})")
            
            if item.get("warnings"):
                warnings.append(f"Cảnh báo cho {name}: {item['warnings']}")
                
            # Nếu có nhiều thuốc, kiểm tra các tương tác cụ thể trong các mục
            if intent == "interaction_check" and item.get("type") == "drug":
                # Đảm bảo các tương tác được làm nổi bật nếu đó là ý định kiểm tra tương tác
                for inter in item.get("interactions", []):
                    warnings.append(f"Tương tác ({inter.get('severity')}): {name} và {inter.get('name')}")

        if context_data:
            unique_sources = sorted(list(set(sources))) # Loại bỏ các nguồn trùng lặp và sắp xếp
            context_str = json.dumps(context_data, indent=2, ensure_ascii=False) # Chuyển dữ liệu ngữ cảnh thành chuỗi JSON
            return context_str, unique_sources, list(set(warnings))
        
        return "", [], []

    async def _fetch_wikipedia_context(
        self, 
        entities: Dict[str, List[str]], 
        language: str = "en"
    ) -> Tuple[str, List[str]]:
        """
        Mục đích: Lấy thông tin y tế bổ sung từ Wikipedia tiếng Anh hoặc tiếng Việt cho các thực thể được phát hiện.
        Cơ chế hoạt động:
        1. Gộp danh sách thuốc và bệnh lý lại thành danh sách các thuật ngữ cần tìm kiếm.
        2. Nếu ngôn ngữ không phải tiếng Anh, thực hiện dịch thuật ngữ bệnh lý sang ngôn ngữ đó trước khi tìm kiếm để tăng độ chính xác trên Wikipedia.
        3. Gọi `wikipedia_service.extract_medical_context` để lấy thông tin tóm tắt.
        4. Trích xuất tóm tắt và nguồn tương ứng, trả về định dạng chuỗi JSON và danh sách nguồn.
        """
        # entities: Từ điển chứa danh sách các thực thể thuốc và bệnh lý
        # language: Ngôn ngữ hội thoại để xác định Wikipedia vùng miền tương ứng (ví dụ: "vi" hoặc "en")
        drugs = entities.get("drugs", []) # Danh sách thuốc
        diseases = entities.get("diseases", []) # Danh sách bệnh lý
        all_terms = drugs + diseases # Tổng hợp tất cả thuật ngữ y tế cần tìm kiếm
        
        if not all_terms:
            return "", []
        
        try:
            # Chuyển đổi tên ngôn ngữ thành mã ngôn ngữ cho Wikipedia
            # lang_code: Mã ngôn ngữ viết tắt cho Wikipedia (ví dụ: "vi", "en")
            lang_code = "vi" if language.lower() in ["vietnamese", "vi"] else "en"
            
            search_terms = [] # Danh sách thuật ngữ thực tế sau khi đã xử lý dịch (nếu cần)
            if lang_code != "en":
                from deep_translator import GoogleTranslator
                try:
                    # translator: Bộ dịch từ Google Translator dùng để dịch thuật ngữ bệnh lý
                    translator = GoogleTranslator(source='en', target=lang_code)
                    for term in all_terms:
                        # Chỉ dịch tên bệnh. Việc dịch tên thuốc (ví dụ: Advil) có thể gây ảo giác cho LLM
                        if term in diseases:
                            search_terms.append(translator.translate(term))
                        else:
                            search_terms.append(term)
                    logger.info(f"Translated terms for Wikipedia search: {search_terms}")
                except Exception as e:
                    logger.error(f"Failed to translate terms for Wikipedia: {e}")
                    search_terms = all_terms
            else:
                search_terms = all_terms

            # Lấy tóm tắt Wikipedia cho tất cả các thuật ngữ
            # wiki_data: Từ điển chứa tóm tắt Wikipedia thu thập được ứng với mỗi thuật ngữ
            wiki_data = await wikipedia_service.extract_medical_context(search_terms, language=lang_code)
            
            sources = [] # Danh sách các nguồn Wikipedia
            context_entries = [] # Danh sách các bản ghi dữ liệu Wikipedia
            
            for term, summary in wiki_data.items():
                if summary:
                    context_entries.append({
                        "term": term,
                        "source": "Wikipedia",
                        "summary": summary
                    })
                    sources.append(f"Wikipedia: {term}")
            
            if context_entries:
                context_str = json.dumps(context_entries, indent=2, ensure_ascii=False) # Chuỗi JSON chứa ngữ cảnh Wikipedia
                return context_str, sources
            
            return "", []
            
        except Exception as e:
            logger.error(f"Error fetching Wikipedia context: {e}")
            return "", []

    async def process_chat(self, db: Session, user_id: Optional[int], message: str) -> ChatMessageResponse:
        """
        Mục đích: Xử lý tin nhắn chat của người dùng theo quy trình RAG hoàn chỉnh và trả về phản hồi từ AI.
        Cơ chế hoạt động:
        1. Nhận diện ngôn ngữ tin nhắn bằng LLM.
        2. Dịch tin nhắn sang tiếng Anh (nếu cần) để nâng cao độ chính xác của NER.
        3. Dùng NER trích xuất thực thể thuốc và bệnh lý.
        4. Nhận diện ý định và truy xuất thông tin đồ thị từ Neo4j làm ngữ cảnh chính.
        5. Lấy ngữ cảnh bổ sung từ Wikipedia.
        6. Gộp ngữ cảnh gửi tới LLM (Gemini) để sinh phản hồi cuối cùng.
        7. Lưu lịch sử chat vào DB nếu người dùng đã đăng nhập.
        8. Trả về phản hồi đầy đủ kèm thực thể, nguồn và cảnh báo.
        """
        # db: Phiên làm việc với cơ sở dữ liệu SQLAlchemy để lưu lịch sử
        # user_id: ID của người dùng thực hiện chat (None nếu là khách ẩn danh)
        # message: Nội dung tin nhắn người dùng gửi lên
        start_time = time.time() # start_time: Ghi lại thời điểm bắt đầu xử lý để tính toán hiệu năng
        try:
            # lang: Ngôn ngữ được phát hiện của tin nhắn người dùng
            lang = await llm_service.detect_language(message)
            logger.info(f"Detected language: {lang}")

            # Dịch sang tiếng Anh để nhận diện thực thể (NER)
            process_message = message # process_message: Nội dung tin nhắn được xử lý (đã dịch sang tiếng Anh nếu cần)
            if lang != "English":
                from deep_translator import GoogleTranslator
                try:
                    process_message = GoogleTranslator(source='auto', target='en').translate(message)
                    logger.info(f"Translated message for NER: {process_message}")
                except Exception as e:
                    logger.error(f"Translation failed: {e}")

            # 2. Nhận diện thực thể (NER)
            # entities: Từ điển chứa các thực thể đã trích xuất từ tin nhắn
            entities = ner_service.extract_entities(process_message)
            # all_entity_names: Danh sách phẳng tất cả tên các thực thể nhận diện được
            all_entity_names = entities.get("drugs", []) + entities.get("diseases", [])
            logger.info(f"NER Entities: {entities}")
            
            # 3. Nhận diện ý định & Truy xuất ngữ cảnh
            # intent: Ý định của người dùng (ví dụ: drug_info, interaction_check, ...)
            intent = self._detect_intent(message)
            
            # Lấy ngữ cảnh Neo4j (chính)
            # neo4j_context: Chuỗi JSON chứa ngữ cảnh lấy từ Neo4j
            # neo4j_sources: Danh sách các thực thể đồ thị được lấy làm nguồn tham khảo
            # warnings: Danh sách cảnh báo y tế được lọc ra
            neo4j_context, neo4j_sources, warnings = self._build_context(entities, intent)
            
            # Lấy ngữ cảnh Wikipedia (phụ) - không chặn
            # wiki_context: Chuỗi JSON chứa ngữ cảnh Wikipedia
            # wiki_sources: Danh sách các nguồn Wikipedia được dùng làm tham khảo
            wiki_context, wiki_sources = await self._fetch_wikipedia_context(entities, language=lang)
            
            # Kết hợp ngữ cảnh: Neo4j trước (ưu tiên cao hơn), sau đó đến Wikipedia
            # combined_context: Ngữ cảnh y tế tổng hợp cuối cùng để gửi cho LLM
            # all_sources: Danh sách tổng hợp toàn bộ các nguồn tham khảo
            combined_context = neo4j_context
            all_sources = neo4j_sources.copy()
            
            # Thêm Wikipedia nếu không có dữ liệu từ Neo4j
            if not neo4j_context and wiki_context:
                combined_context = wiki_context
                all_sources.extend(wiki_sources)
            elif wiki_context:
                # Thêm Wikipedia làm ngữ cảnh bổ sung
                if combined_context:
                    combined_context += f"\n\nWIKIPEDIA_CONTEXT:\n{wiki_context}"
                all_sources.extend(wiki_sources)
            
            logger.info(f"RAG Context length: {len(combined_context)} chars | Sources: {all_sources}")
            
            # 4. LLM tạo câu trả lời
            # answer: Phản hồi văn bản y khoa sinh ra bởi LLM dựa trên câu hỏi và ngữ cảnh đã cung cấp
            answer = await llm_service.generate_response(message, combined_context, language=lang)
            
            # 5. Cập nhật lịch sử
            if user_id is not None:
                # chat_record: Thực thể model ChatHistory dùng để lưu thông tin cuộc trò chuyện vào cơ sở dữ liệu
                chat_record = ChatHistory(
                    user_id=user_id,
                    message=message,
                    response=answer,
                    intent=intent,
                    entities=",".join(all_entity_names)
                )
                db.add(chat_record)
                db.commit()
            
            # process_time: Thời gian xử lý toàn bộ quy trình RAG tính bằng giây
            process_time = time.time() - start_time
            logger.info(f"Chat processing completed in {process_time:.2f}s | Lang: {lang} | Sources: {all_sources or 'LLM Knowledge'}")

            return ChatMessageResponse(
                answer=answer,
                entities=all_entity_names,
                sources=all_sources if all_sources else ["AI Base Knowledge"],
                warnings=warnings
            )
        except Exception as e:
            logger.exception(f"Error in chat processing: {e}")
            return ChatMessageResponse(
                answer="Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.",
                warnings=[str(e)],
                sources=["Error Fallback"]
            )

    def get_user_history(self, db: Session, user_id: int, limit: int = 20) -> List[Any]:
        """
        Mục đích: Lấy danh sách lịch sử chat của một người dùng cụ thể.
        Cơ chế hoạt động: Truy vấn từ bảng chathistory theo `user_id`, sắp xếp giảm dần theo thời gian tạo, giới hạn số lượng kết quả trả về.
        """
        # db: Phiên làm việc cơ sở dữ liệu
        # user_id: ID người dùng cần lấy lịch sử
        # limit: Giới hạn số lượng bản ghi lịch sử chat muốn lấy
        return db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.created_at.desc()).limit(limit).all()

    def get_chat_detail(self, db: Session, chat_id: int, user_id: int) -> Optional[ChatHistory]:
        """
        Mục đích: Lấy thông tin chi tiết một lượt chat cụ thể.
        Cơ chế hoạt động: Truy vấn bản ghi `ChatHistory` theo ID của cuộc chat và ID của người dùng sở hữu để bảo mật thông tin.
        """
        # db: Phiên làm việc cơ sở dữ liệu
        # chat_id: ID của bản ghi lịch sử chat cần xem chi tiết
        # user_id: ID người dùng sở hữu lượt chat để kiểm tra quyền truy cập
        return db.query(ChatHistory).filter(ChatHistory.id == chat_id, ChatHistory.user_id == user_id).first()

    def get_all_chat_logs(
        self, db: Session, user_id: Optional[int] = None, limit: int = 20, skip: int = 0
    ) -> List[ChatHistory]:
        """
        Mục đích: Lấy tất cả nhật ký trò chuyện (dành cho Admin quản lý hệ thống).
        Cơ chế hoạt động: Truy vấn danh sách lịch sử chat, có thể lọc theo `user_id` cụ thể, hỗ trợ phân trang qua `skip` và `limit`.
        """
        # db: Phiên làm việc cơ sở dữ liệu
        # user_id: Bộ lọc theo ID người dùng (tùy chọn)
        # limit: Số lượng log tối đa lấy ra trên trang
        # skip: Số lượng bản ghi cần bỏ qua để phân trang
        # query: Đối tượng truy vấn SQLAlchemy được xây dựng dần
        query = db.query(ChatHistory)
        if user_id:
            query = query.filter(ChatHistory.user_id == user_id)
        return query.order_by(ChatHistory.created_at.desc()).offset(skip).limit(limit).all()

    def get_chat_logs_count(self, db: Session, user_id: Optional[int] = None) -> int:
        """
        Mục đích: Lấy tổng số lượng bản ghi nhật ký trò chuyện (dành cho Admin).
        Cơ chế hoạt động: Đếm số dòng dữ liệu trong bảng chathistory, có thể lọc theo `user_id`.
        """
        # db: Phiên làm việc cơ sở dữ liệu
        # user_id: Bộ lọc theo ID người dùng (tùy chọn)
        # query: Đối tượng truy vấn SQLAlchemy
        query = db.query(ChatHistory)
        if user_id:
            query = query.filter(ChatHistory.user_id == user_id)
        return query.count()

    def get_chat_topic_stats(self, db: Session) -> Dict[str, Any]:
        """
        Mục đích: Lấy số liệu thống kê về các chủ đề (ý định) trò chuyện của người dùng (dành cho Admin).
        Cơ chế hoạt động: Nhóm dữ liệu trong bảng chathistory theo trường `intent` và đếm số lượng bản ghi của mỗi nhóm.
        """
        # db: Phiên làm việc cơ sở dữ liệu
        from sqlalchemy import func
        # stats: Kết quả truy vấn nhóm theo ý định và đếm số lượng tương ứng
        stats = db.query(ChatHistory.intent, func.count(ChatHistory.id)).group_by(ChatHistory.intent).all()
        # topic_counts: Từ điển lưu trữ số lượng lượt chat ứng với từng chủ đề/ý định
        topic_counts = {item[0] or "unknown": item[1] for item in stats}
        # total: Tổng số lượt chat trong hệ thống
        total = sum(topic_counts.values()) or 1
        
        return {
            "counts": topic_counts,
            "total": sum(topic_counts.values())
        }

    def get_monthly_ai_usage(self, db: Session) -> int:
        """
        Mục đích: Đếm số lượng cuộc trò chuyện sử dụng AI trong tháng hiện tại (dành cho Admin giám sát hạn mức).
        Cơ chế hoạt động: Truy vấn và đếm tất cả các bản ghi có trường thời gian `created_at` nằm trong tháng và năm hiện tại.
        """
        # db: Phiên làm việc cơ sở dữ liệu
        from sqlalchemy import extract
        from datetime import datetime
        # current_month: Số tháng hiện tại (1-12)
        current_month = datetime.now().month
        # current_year: Số năm hiện tại
        current_year = datetime.now().year
        return db.query(ChatHistory).filter(
            extract('month', ChatHistory.created_at) == current_month,
            extract('year', ChatHistory.created_at) == current_year
        ).count()

chat_service = ChatService()

