import logging
import re
from typing import Set
from app.services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False

class NERService:
    """
    Dịch vụ nhận diện thực thể (NER) cho Medical Chatbot.
    Xác định Tên thuốc và Bệnh lý từ truy vấn của người dùng bằng Tìm kiếm Vector Ngữ cảnh.
    """
    
    def __init__(self):
        """
        Mục đích: Khởi tạo dịch vụ NER và nạp mô hình SentenceTransformer để tính toán embedding.
        Cơ chế hoạt động:
        - Khởi tạo danh sách trống cho thuốc và bệnh lý.
        - Nếu thư viện `sentence-transformers` được cài đặt thành công (`MODEL_AVAILABLE`), tải mô hình `all-MiniLM-L6-v2`.
        - Nếu không có thư viện, ghi cảnh báo và đặt model bằng None để sử dụng cơ chế so khớp chính xác dự phòng.
        """
        self.drug_names = [] # drug_names: Danh sách tên thuốc được tải từ Neo4j
        self.disease_names = [] # disease_names: Danh sách tên bệnh lý được tải từ Neo4j
        self.drug_embeddings = None # drug_embeddings: Tensor chứa vector embeddings của tên thuốc
        self.disease_embeddings = None # disease_embeddings: Tensor chứa vector embeddings của tên bệnh lý
        
        if MODEL_AVAILABLE:
            logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2') # model: Mô hình Transformer dùng để chuyển văn bản thành vector
        else:
            logger.warning("sentence-transformers not available. Falling back to exact match.")
            self.model = None
            
        self._last_refresh = 0 # _last_refresh: Thời gian chạy lần cập nhật bộ nhớ cache thực thể gần nhất
        self._refresh_interval = 3600  # _refresh_interval: Chu kỳ làm mới cache thực thể (mặc định 1 giờ)

    def _normalize_text(self, text: str) -> str:
        """
        Mục đích: Chuẩn hóa chuỗi văn bản đầu vào để so khớp không phân biệt hoa thường và dấu câu.
        Cơ chế hoạt động: Chuyển thành chữ thường và loại bỏ toàn bộ các ký tự đặc biệt/dấu câu bằng biểu thức chính quy (Regex).
        """
        # text: Chuỗi văn bản thô cần được chuẩn hóa
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Mục đích: Tính khoảng cách chỉnh sửa Levenshtein giữa hai chuỗi s1 và s2.
        Cơ chế hoạt động: Sử dụng thuật toán quy hoạch động tối ưu hóa bộ nhớ O(min(len(s1), len(s2))).
        """
        # s1: Chuỗi thứ nhất
        # s2: Chuỗi thứ hai
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def refresh_entities(self):
        """
        Mục đích: Cập nhật bộ nhớ đệm (cache) danh sách tên thuốc, bệnh lý và tính toán sẵn embeddings của chúng từ Neo4j.
        Cơ chế hoạt động:
        1. Gọi `neo4j_service` để lấy tối đa 1000 thuốc và 1000 bệnh lý hiện có trong đồ thị.
        2. Lưu tên của chúng vào list.
        3. Nếu mô hình AI SentenceTransformer khả dụng, tiến hành chuyển đổi toàn bộ danh sách tên thành vector embeddings và lưu vào bộ nhớ RAM.
        """
        try:
            logger.info("Refreshing NER entity cache from Neo4j...")
            self._last_refresh = datetime.now().timestamp()
            # drugs: Danh sách bản ghi thuốc lấy từ Neo4j
            drugs = neo4j_service.search_drugs("", limit=1000)
            # diseases: Danh sách bản ghi bệnh lý lấy từ Neo4j
            diseases = neo4j_service.search_diseases("", limit=1000)
            
            self.drug_names = [d["name"] for d in drugs]
            self.disease_names = [d["name"] for d in diseases]
            
            if self.model:
                logger.info("Computing Semantic Embeddings for entities...")
                if self.drug_names:
                    self.drug_embeddings = self.model.encode(self.drug_names, convert_to_tensor=True)
                if self.disease_names:
                    self.disease_embeddings = self.model.encode(self.disease_names, convert_to_tensor=True)
                    
            logger.info(f"NER cache refreshed: {len(self.drug_names)} drugs, {len(self.disease_names)} diseases.")
        except Exception as e:
            logger.error(f"Failed to refresh NER cache: {e}")

    def extract_entities(self, text: str) -> dict:
        """
        Mục đích: Nhận diện và trích xuất danh sách thuốc và bệnh lý xuất hiện trong một đoạn tin nhắn chat.
        Cơ chế hoạt động:
        1. Kiểm tra cache thực thể, nếu trống thì tự động tải từ Neo4j.
        2. Ưu tiên trích xuất các từ/cụm từ nằm trong dấu ngoặc kép trước.
        3. Nếu không có ngoặc kép, sử dụng thuật toán cửa sổ trượt (sliding window) từ 1 tới 3 từ liên tiếp để sinh danh sách các cụm từ cần kiểm tra.
        4. Nếu mô hình SentenceTransformer hoạt động, mã hóa các cụm từ này thành vector embeddings rồi tính Cosine Similarity với danh sách thực thể mẫu. Chấp nhận nếu độ tương đồng vượt ngưỡng 0.78.
        5. Nếu mô hình không hoạt động, thực hiện so khớp chính xác chuỗi sau khi chuẩn hóa.
        """
        # text: Tin nhắn đầu vào của người dùng cần trích xuất thực thể
        if not self.drug_names:
            self.refresh_entities()

        extracted_drugs = set() # extracted_drugs: Tập hợp các tên thuốc phát hiện được (để tránh trùng lặp)
        extracted_diseases = set() # extracted_diseases: Tập hợp các tên bệnh lý phát hiện được

        # 1. Trích xuất thực thể nằm trong dấu ngoặc kép (Ưu tiên cao nhất)
        # quoted_phrases: Danh sách các cụm từ được đặt trong ngoặc kép
        quoted_phrases = re.findall(r'["\'](.*?)["\']', text)
        if quoted_phrases:
            logger.info(f"Found quoted entities: {quoted_phrases}")
            words_to_check = quoted_phrases
        else:
            # Cửa sổ trượt từ 1-3 từ
            # normalized_query: Tin nhắn của người dùng sau khi đã chuẩn hóa loại bỏ dấu câu
            normalized_query = self._normalize_text(text)
            # words: Danh sách các từ riêng lẻ
            words = normalized_query.split()
            # words_to_check: Danh sách các cụm từ ghép (1-3 từ) sinh ra từ cửa sổ trượt
            words_to_check = []
            for n in range(1, 4):
                for i in range(len(words) - n + 1):
                    words_to_check.append(" ".join(words[i:i+n]))

        if not words_to_check:
            return {"drugs": [], "diseases": []}

        if self.model and self.drug_embeddings is not None and self.disease_embeddings is not None:
            # Tìm kiếm ngữ cảnh (Semantic Search)
            # phrase_embeddings: Vector embeddings của các cụm từ cần kiểm tra
            phrase_embeddings = self.model.encode(words_to_check, convert_to_tensor=True)
            
            if self.drug_names:
                # cos_scores_drugs: Ma trận độ tương đồng cosine giữa các cụm từ cần kiểm tra với danh sách thuốc
                cos_scores_drugs = util.cos_sim(phrase_embeddings, self.drug_embeddings)
                for i in range(len(words_to_check)):
                    best_score, best_idx = torch.max(cos_scores_drugs[i], dim=0)
                    if best_score.item() > 0.78:  # Ngưỡng tương đồng 0.78
                        extracted_drugs.add(self.drug_names[best_idx])
                        
            if self.disease_names:
                # cos_scores_diseases: Ma trận độ tương đồng cosine giữa các cụm từ kiểm tra với danh sách bệnh lý
                cos_scores_diseases = util.cos_sim(phrase_embeddings, self.disease_embeddings)
                for i in range(len(words_to_check)):
                    best_score, best_idx = torch.max(cos_scores_diseases[i], dim=0)
                    if best_score.item() > 0.78:
                        extracted_diseases.add(self.disease_names[best_idx])
        else:
            # Dự phòng sang So khớp Fuzzy sử dụng Levenshtein
            for phrase in words_to_check:
                # norm_phrase: Cụm từ kiểm tra được chuẩn hóa
                norm_phrase = self._normalize_text(phrase)
                for drug in self.drug_names:
                    norm_drug = self._normalize_text(drug)
                    # Cho phép sai khác tối đa 1 ký tự đối với cụm từ ngắn, 2 ký tự đối với cụm từ dài (>7 ký tự)
                    max_dist = 2 if len(norm_drug) > 7 else 1
                    if self._levenshtein_distance(norm_phrase, norm_drug) <= max_dist:
                        extracted_drugs.add(drug)
                for disease in self.disease_names:
                    norm_disease = self._normalize_text(disease)
                    # Cho phép sai khác tối đa 1 ký tự đối với cụm từ ngắn, 2 ký tự đối với cụm từ dài (>7 ký tự)
                    max_dist = 2 if len(norm_disease) > 7 else 1
                    if self._levenshtein_distance(norm_phrase, norm_disease) <= max_dist:
                        extracted_diseases.add(disease)

        return {
            "drugs": list(extracted_drugs),
            "diseases": list(extracted_diseases)
        }

ner_service = NERService()
