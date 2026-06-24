# Wikipedia Integration Guide 📚

## Tổng Quan

Chatbot hiện đã tích hợp **Wikipedia API** để lấy dữ liệu y tế từ internet **hoàn toàn miễn phí**, không cần API key hoặc card ngân hàng.

**Ưu điểm Wikipedia Integration:**
- ✅ Hoàn toàn miễn phí (không cần API key)
- ✅ Dữ liệu y tế đáng tin cậy (Wikipedia Medical)
- ✅ Hỗ trợ 300+ ngôn ngữ (bao gồm Tiếng Việt)
- ✅ Real-time data mới nhất
- ✅ Không cần liên kết tài khoản hay thẻ ngân hàng

---

## 🏗️ Kiến Trúc

```
User Question (English/Vietnamese)
    ↓
NER (Named Entity Recognition) - Trích xuất thuốc, bệnh
    ↓
├─ Neo4j (Database nội bộ) → Tìm quan hệ
├─ Wikipedia API (Online) → Tìm thông tin y tế
    ↓
Kết hợp Context từ cả 2 nguồn
    ↓
Gemini LLM → Tạo câu trả lời
    ↓
Response (Same language as input)
```

---

## 📖 Cách Wikipedia API Hoạt Động

### 1. **Search**
Tìm kiếm bài viết trên Wikipedia:

```bash
curl "https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch=aspirin&srlimit=5"
```

Kết quả:
```json
{
  "query": {
    "search": [
      {
        "title": "Aspirin",
        "snippet": "Aspirin is a medication used to reduce pain, fever, or inflammation..."
      }
    ]
  }
}
```

### 2. **Get Article Summary**
Lấy phần intro của bài viết:

```bash
curl "https://en.wikipedia.org/w/api.php?action=query&format=json&titles=Aspirin&prop=extracts&explaintext=true&exintro=true&exchars=500"
```

### 3. **Get Full Article**
Lấy toàn bộ nội dung bài viết:

```bash
curl "https://en.wikipedia.org/w/api.php?action=query&format=json&titles=Aspirin&prop=extracts&explaintext=true"
```

### 4. **Vietnamese Wikipedia**
Chỉ cần thay đổi URL:

```bash
# Thay vì: https://en.wikipedia.org/w/api.php
# Dùng:   https://vi.wikipedia.org/w/api.php
```

---

## 🔧 Service Methods

### `WikipediaService.search()`
Tìm kiếm bài viết trên Wikipedia

```python
results = await wikipedia_service.search(
    query="aspirin",          # Từ khóa tìm kiếm
    language="en",            # "en" hoặc "vi"
    limit=5                   # Số kết quả trả về
)
# Trả về: List[Dict] với title, snippet, size, timestamp
```

### `WikipediaService.get_article_summary()`
Lấy phần intro/tóm tắt của bài viết

```python
summary = await wikipedia_service.get_article_summary(
    article_title="Aspirin",
    language="en",
    chars=500                 # Số ký tự tối đa
)
# Trả về: str hoặc None
```

### `WikipediaService.get_full_article()`
Lấy toàn bộ nội dung bài viết (tối đa 3000 ký tự)

```python
content = await wikipedia_service.get_full_article(
    article_title="Aspirin",
    language="en"
)
```

### `WikipediaService.search_and_summarize()`
Tìm kiếm + lấy tóm tắt bài viết tốt nhất

```python
result = await wikipedia_service.search_and_summarize(
    query="drug interaction",
    language="en"
)
# Trả về: str (summary + link) hoặc None
```

### `WikipediaService.extract_medical_context()`
Trích xuất thông tin y tế cho nhiều thuật ngữ cùng lúc

```python
results = await wikipedia_service.extract_medical_context(
    terms=["Aspirin", "Ibuprofen", "Drug interaction"],
    language="en",
    max_results=3
)
# Trả về: Dict[str, Optional[str]]
# {"Aspirin": "summary...", "Ibuprofen": "summary...", ...}
```

---

## 🚀 Test Wikipedia Integration

### 1. **Chạy Test Script**

```bash
cd backend
python test_wikipedia.py
```

Kết quả sẽ hiển thị:
- ✅ TEST 1: Wikipedia Search
- ✅ TEST 2: Get Article Summary  
- ✅ TEST 3: Search + Summarize
- ✅ TEST 4: Medical Context Extraction
- ✅ TEST 5: Vietnamese Wikipedia

### 2. **Test Thủ Công Trong Python**

```python
import asyncio
from app.services.wikipedia_service import wikipedia_service

async def test():
    # Search
    results = await wikipedia_service.search("aspirin", language="en")
    print(results)
    
    # Get summary
    summary = await wikipedia_service.get_article_summary("Aspirin", language="en")
    print(summary)

asyncio.run(test())
```

---

## 🤖 Integration Trong Chat Service

Khi user hỏi câu hỏi, hệ thống sẽ:

1. **Detect Language** - Xác định user hỏi bằng tiếng gì
2. **Extract Entities (NER)** - Tìm thuốc, bệnh trong câu hỏi
3. **Query Neo4j** - Lấy dữ liệu từ database nội bộ
4. **Query Wikipedia** - Lấy dữ liệu từ Wikipedia online
5. **Combine Context** - Kết hợp cả 2 nguồn (Neo4j + Wikipedia)
6. **Generate Response** - Dùng Gemini LLM tạo câu trả lời

### Example: User hỏi "Aspirin có gây tương tác với Ibuprofen không?"

```
Query: "Aspirin có gây tương tác với Ibuprofen không?"
↓
Language: Vietnamese
Entities: drugs=["Aspirin", "Ibuprofen"]
↓
Neo4j: Tìm quan hệ trong cơ sở dữ liệu
Wikipedia: Lấy thông tin về Aspirin, Ibuprofen, drug interaction
↓
Context: 
  Neo4j: {...drug interaction data...}
  Wikipedia: 
    - Aspirin summary
    - Ibuprofen summary
    - Drug interaction information
↓
Gemini: Tạo câu trả lời bằng TIẾNG VIỆT
↓
Response: "Aspirin và Ibuprofen có thể tương tác..."
```

---

## ⚙️ Configuration

Hiện tại không cần cấu hình gì thêm. Wikipedia service hoạt động out-of-box.

Nếu muốn tuỳ chỉnh, mở file `backend/app/services/wikipedia_service.py`:

```python
# Endpoints
EN_WIKI_API = "https://en.wikipedia.org/w/api.php"
VI_WIKI_API = "https://vi.wikipedia.org/w/api.php"

# Timeout
TIMEOUT = 10  # 10 seconds

# Max context length
3000  # characters (trong get_full_article)
```

---

## 🌐 Supported Languages

Wikipedia hỗ trợ 300+ ngôn ngữ, bao gồm:

- 🇬🇧 English (`en`)
- 🇻🇳 Vietnamese (`vi`)
- 🇪🇸 Spanish (`es`)
- 🇫🇷 French (`fr`)
- 🇩🇪 German (`de`)
- 🇮🇹 Italian (`it`)
- 🇷🇺 Russian (`ru`)
- 🇵🇹 Portuguese (`pt`)
- ... và nhiều ngôn ngữ khác

Cách dùng:
```python
# Vietnamese
await wikipedia_service.search("aspirin", language="vi")

# Spanish
await wikipedia_service.search("aspirin", language="es")

# French
await wikipedia_service.search("aspirin", language="fr")
```

---

## 📊 Performance

**Response Time:**
- Search: ~500ms - 1s
- Get Summary: ~300-600ms
- Medical Context (5 terms): ~2-3s

**Rate Limiting:**
- Wikipedia cho phép ~200 requests/second
- No registration needed
- No API key required
- No quota limits

---

## 🐛 Troubleshooting

### Problem: "Connection timeout"
```
Solution: Tăng TIMEOUT trong wikipedia_service.py
TIMEOUT = 15  # Tăng từ 10 lên 15 seconds
```

### Problem: "Article not found"
```
Solution: Wikipedia search không always perfect
- Thử dùng search() trước để tìm đúng title
- Hoặc thử dùng language khác
```

### Problem: "No results từ Wikipedia"
```
Solution: 
1. Check internet connection
2. Verify term name (phải chính xác)
3. Thử search() để debug
```

---

## 🎯 Use Cases

### 1. **Drug Information**
```
User: "Paracetamol là gì?"
Response: Kết hợp Neo4j + Wikipedia → Thông tin chi tiết
```

### 2. **Drug Interactions**
```
User: "Aspirin tương tác với Warfarin không?"
Response: Neo4j interaction data + Wikipedia medical info
```

### 3. **Disease Symptoms**
```
User: "Triệu chứng của viêm họng là gì?"
Response: Wikipedia disease info + Neo4j symptom data
```

### 4. **Side Effects**
```
User: "Aspirin có tác dụng phụ gì?"
Response: Wikipedia side effects + Neo4j warnings
```

---

## 📝 Example Chat Conversation

```
User: "Có thể dùng Aspirin và Ibuprofen cùng nhau không? Tôi đau đầu."

System Flow:
1. Language Detection: Vietnamese ✅
2. NER: drugs=["Aspirin", "Ibuprofen"], intent="interaction_check"
3. Neo4j Query: Tìm interaction giữa Aspirin - Ibuprofen
4. Wikipedia Query: Lấy info về Aspirin, Ibuprofen, drug safety
5. LLM Generation: Tạo câu trả lời bằng Tiếng Việt

Response:
"Không nên dùng Aspirin và Ibuprofen cùng nhau vì:

1. **Tương tác thuốc**: Cả hai đều là NSAIDs, có thể làm tăng nguy 
   hiểm ra máu dạ dày

2. **Tác dụng phụ**: Có thể gây buồn nôn, khó tiêu, hoặc chảy máu 
   trong dạ dày

3. **Khuyến nghị**: Chỉ chọn một trong hai. Nếu đau đầu, bạn nên:
   - Uống đủ nước
   - Nghỉ ngơi
   - Tư vấn với bác sĩ nếu đau kéo dài

Lưu ý: Đây không phải là lời khuyên y tế chuyên môn. Vui lòng 
tham khảo ý kiến bác sĩ."

Sources: Neo4j, Wikipedia: Aspirin, Wikipedia: Ibuprofen, 
Wikipedia: NSAID
```

---

## 🔒 Privacy & Safety

- ✅ Wikipedia là open-source, không lưu trữ dữ liệu cá nhân
- ✅ Không cần login hay authentication
- ✅ Không thu thập dữ liệu người dùng
- ✅ Requests từ backend → Wikipedia (không qua người thứ ba)

---

## 📚 More Resources

- Wikipedia API Docs: https://www.mediawiki.org/wiki/API/REST_v1
- Medical Topics: https://en.wikipedia.org/wiki/Category:Medicine
- Drugs: https://en.wikipedia.org/wiki/Category:Drugs

---

**Ngày tạo**: 2024
**Version**: 1.0
**Status**: ✅ Production Ready
