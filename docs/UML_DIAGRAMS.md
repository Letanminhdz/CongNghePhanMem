# BỘ UML DIAGRAMS CHO HỆ THỐNG MEDICAL CHATBOT

Dưới đây là bộ UML hoàn chỉnh bao gồm các Use Case (Tổng quan & Phân rã), cùng với Activity Diagram (có Swimlane) và Sequence Diagram cho các chức năng cốt lõi.

---

## PHẦN 1: USE CASE DIAGRAM

### 1.1. Use Case Tổng Quan (Overall System)
```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle

actor "Guest" as guest
actor "User (Bệnh nhân)" as user
actor "Admin" as admin

rectangle "Medical AI Chatbot System" {
  usecase "Đăng ký/Đăng nhập" as UC1
  usecase "Chat với AI Y tế" as UC2
  usecase "Tra cứu Thuốc & Bệnh" as UC3
  usecase "Quản lý Hồ sơ" as UC4
  usecase "Quản lý Dữ liệu Y khoa" as UC5
  usecase "Xem Nhật ký AI & Báo cáo" as UC6
}

guest --> UC1
user --> UC2
user --> UC3
user --> UC4
admin --> UC5
admin --> UC6
admin --> UC1

user -up-|> guest
@enduml
```

### 1.2. Use Case Phân rã: Quá trình Chat với AI
```plantuml
@startuml
left to right direction
actor "User" as user

rectangle "Chức năng Chat với AI" {
  usecase "Chat với AI Y tế" as UC_Chat
  
  usecase "Dịch ngôn ngữ (Translate)" as UC_Trans
  usecase "Trích xuất Thực thể (NER)" as UC_NER
  usecase "Truy vấn Knowledge Graph" as UC_Graph
  usecase "Lấy tóm tắt Wikipedia" as UC_Wiki
  usecase "Lưu lịch sử Chat" as UC_History
}

user --> UC_Chat

UC_Chat ..> UC_Trans : <<include>>
UC_Chat ..> UC_NER : <<include>>
UC_Chat ..> UC_History : <<include>>

UC_NER ..> UC_Graph : <<extend>> (Nếu có từ khóa)
UC_NER ..> UC_Wiki : <<extend>> (Nếu có từ khóa)
@enduml
```

### 1.3. Use Case Phân rã: Quá trình Tra cứu (Thuốc & Bệnh lý)
```plantuml
@startuml
left to right direction
actor "User" as user

rectangle "Hệ thống Tra cứu (Neo4j)" {
  usecase "Tra cứu Thuốc (Medicine)" as UC_Drug
  usecase "Tra cứu Bệnh lý (Disease)" as UC_Disease
  
  usecase "Nhập từ khóa tìm kiếm" as UC_Input
  usecase "Lọc/Sắp xếp kết quả" as UC_Filter
  usecase "Xem danh sách kết quả" as UC_List
  
  usecase "Xem Chi tiết Bệnh lý" as UC_DetailDis
  usecase "Xem Triệu chứng (Symptoms)" as UC_Symp
  usecase "Xem Thuốc đặc trị (Treatments)" as UC_Treat
  
  usecase "Xem Chi tiết Thuốc" as UC_DetailDrug
  usecase "Xem Tác dụng phụ (Side Effects)" as UC_SideEffect
  usecase "Xem Tương tác thuốc (Interactions)" as UC_Interact
  usecase "Xem Thành phần (Ingredients)" as UC_Ingred
  
  usecase "Lưu vào Mục yêu thích (Bookmark)" as UC_Bookmark
}

user --> UC_Drug
user --> UC_Disease

UC_Drug ..> UC_Input : <<include>>
UC_Disease ..> UC_Input : <<include>>

UC_Input ..> UC_List : <<include>>

UC_List <.. UC_Filter : <<extend>> (Tùy chọn lọc)
UC_List <.. UC_DetailDis : <<extend>> (Click vào Bệnh)
UC_List <.. UC_DetailDrug : <<extend>> (Click vào Thuốc)

UC_DetailDis ..> UC_Symp : <<include>>
UC_DetailDis ..> UC_Treat : <<include>>

UC_DetailDrug ..> UC_SideEffect : <<include>>
UC_DetailDrug ..> UC_Interact : <<include>>
UC_DetailDrug ..> UC_Ingred : <<include>>

UC_DetailDis <.. UC_Bookmark : <<extend>>
UC_DetailDrug <.. UC_Bookmark : <<extend>>

@enduml
```

---

## PHẦN 2: QUÁ TRÌNH CHAT VỚI AI

### 2.1. Activity Diagram (Có Swimlane)
```plantuml
@startuml
|Người dùng|
start
:Nhập câu hỏi bệnh lý/thuốc;
:Nhấn nút Gửi;

|Frontend (React)|
:Gửi HTTP POST Request;

|Backend (FastAPI)|
:Phát hiện ngôn ngữ (Detect Language);
if (Ngôn ngữ != Tiếng Anh?) then (Có)
  |External Services|
  :Dịch sang Tiếng Anh (Google Translator);
else (Không)
endif

|Backend (FastAPI)|
:Trích xuất thực thể NER (Bệnh/Thuốc);

if (Tìm thấy thực thể?) then (Có)
  |Neo4j DB|
  :Tìm kiếm thông tin Graph Data;
  :Trả về dữ liệu;
  
  |External Services|
  :Tìm kiếm tóm tắt Wikipedia;
  :Trả về Wikipedia Summary;
  
  |Backend (FastAPI)|
  :Gộp Graph Data và Wikipedia thành Context;
else (Không)
  |Backend (FastAPI)|
  :Sử dụng AI Base Knowledge;
endif

|Backend (FastAPI)|
:Ghép Câu hỏi + Context thành Prompt;

|External Services|
:Gửi Prompt cho Gemini API;
:Trả về kết quả (AI Response);

|Backend (FastAPI)|
:Lưu lịch sử Chat vào PostgresDB;
:Gửi HTTP Response về Frontend;

|Frontend (React)|
:Hiển thị câu trả lời & Nguồn trích dẫn;

|Người dùng|
:Đọc kết quả;
stop
@enduml
```

### 2.2. Sequence Diagram
```plantuml
@startuml
autonumber
skinparam maxMessageSize 150

actor "Người dùng" as User
participant "Frontend" as FE
participant "Backend" as BE
participant "NER Service" as NER
database "Neo4j DB" as Neo4j
boundary "Gemini API" as Gemini

User -> FE: Gõ câu hỏi & Nhấn Gửi
activate FE
FE -> BE: POST /api/v1/chat/ask
activate BE

BE -> NER: extract_entities(message)
activate NER
NER --> BE: [Diseases, Drugs]
deactivate NER

opt Nếu tìm thấy Bệnh/Thuốc
    BE -> Neo4j: Cypher Query tìm Graph Data
    activate Neo4j
    Neo4j --> BE: Dữ liệu đồ thị
    deactivate Neo4j
end

BE -> BE: Xây dựng Prompt (Question + Context)
BE -> Gemini: Gửi Prompt (generateContent)
activate Gemini
Gemini --> BE: Trả về câu trả lời
deactivate Gemini

BE -> FE: JSON Response {answer, sources}
deactivate BE

FE --> User: Hiển thị câu trả lời AI
deactivate FE
@enduml
```

---

## PHẦN 3: QUÁ TRÌNH TRA CỨU THÔNG TIN Y KHOA (Thuốc & Bệnh)
*(Để tránh lặp lại, sơ đồ này bao quát chung cho luồng tìm kiếm và xem chi tiết của cả Thuốc và Bệnh do kiến trúc xử lý tương đồng nhau)*

### 3.1. Activity Diagram (Có Swimlane)
```plantuml
@startuml
|Người dùng|
start
:Mở trang Tra cứu (Thuốc/Bệnh);
:Nhập từ khóa vào ô tìm kiếm;

|Frontend (React)|
:Gửi HTTP GET Request (Search query);

|Backend (FastAPI)|
:Nhận query tìm kiếm;

|Neo4j DB|
:Thực thi MATCH (Node) CONTAINS query;
note right: Node có thể là Drug hoặc Disease
:Trả về danh sách các Node;

|Backend (FastAPI)|
:Format dữ liệu thành JSON;
:Gửi Response danh sách;

|Frontend (React)|
:Hiển thị danh sách kết quả;

|Người dùng|
:Chọn một mục cụ thể để xem chi tiết;

|Frontend (React)|
:Gửi HTTP GET Request (Details by ID);

|Backend (FastAPI)|
:Nhận ID;

|Neo4j DB|
:Thực thi Cypher truy xuất các Node liên kết;
note right: Tác dụng phụ (nếu là Thuốc)\nTriệu chứng (nếu là Bệnh)
:Trả về Graph Detail;

|Backend (FastAPI)|
:Gửi Response chi tiết;

|Frontend (React)|
:Hiển thị giao diện Chi tiết;

|Người dùng|
:Đọc thông tin;
stop
@enduml
```

### 3.2. Sequence Diagram
```plantuml
@startuml
autonumber
skinparam maxMessageSize 150

actor "Người dùng" as User
participant "Frontend" as FE
participant "Backend" as BE
database "Neo4j DB" as Neo4j

User -> FE: Gõ từ khóa tìm kiếm
activate FE
FE -> BE: GET /api/v1/neo4j/search?query=...
activate BE

BE -> Neo4j: MATCH (n) ... RETURN n
activate Neo4j
Neo4j --> BE: Danh sách Nodes (Thuốc/Bệnh)
deactivate Neo4j

BE --> FE: JSON List
deactivate BE
FE --> User: Hiển thị danh sách kết quả

User -> FE: Click xem chi tiết
FE -> BE: GET /api/v1/neo4j/details/{id}
activate BE

BE -> Neo4j: MATCH (n {id})-[r]-(other) RETURN n, r, other
activate Neo4j
Neo4j --> BE: Chi tiết Graph (Các mối quan hệ)
deactivate Neo4j

BE --> FE: JSON Details
deactivate BE

FE --> User: Hiển thị giao diện Chi tiết
deactivate FE
@enduml
```

---

## PHẦN 4: CLASS DIAGRAM (Sơ đồ Lớp & Sơ đồ Đồ thị)

Dưới đây là sơ đồ cấu trúc cơ sở dữ liệu của toàn bộ hệ thống, được chia làm 2 phần: Dữ liệu quan hệ (PostgreSQL) để quản lý người dùng và Dữ liệu đồ thị (Neo4j) để lưu trữ kiến thức y khoa.

### 4.1. Sơ đồ Lớp Quan hệ (PostgreSQL Models)
Quản lý tài khoản, lịch sử tra cứu và lịch sử trò chuyện của người dùng.

```plantuml
@startuml
skinparam classAttributeIconSize 0
skinparam classBackgroundColor #E1F5FE

class User {
  + id: Integer
  + full_name: String
  + email: String
  + hashed_password: String
  + is_active: Boolean
  + is_superuser: Boolean
  + created_at: DateTime
}

class Bookmark {
  + id: Integer
  + user_id: Integer
  + item_type: String
  + item_neo4j_id: String
  + created_at: DateTime
}

class ChatHistory {
  + id: Integer
  + user_id: Integer
  + message: Text
  + response: Text
  + intent: String
  + entities: Text
  + created_at: DateTime
}

class InteractionHistory {
  + id: Integer
  + user_id: Integer
  + drugs: String
  + created_at: DateTime
}

class SearchHistory {
  + id: Integer
  + user_id: Integer
  + query_text: String
  + item_type: String
  + created_at: DateTime
}

' Relationships (One-to-Many)
User "1" -- "0..*" Bookmark : "has >"
User "1" -- "0..*" ChatHistory : "wrote >"
User "1" -- "0..*" InteractionHistory : "did >"
User "1" -- "0..*" SearchHistory : "searched >"

@enduml
```

### 4.2. Sơ đồ Đồ thị Tri thức (Neo4j Graph Models)
Lưu trữ thông tin chuyên sâu về Thuốc, Bệnh lý và các mối quan hệ y khoa.

```plantuml
@startuml
skinparam classAttributeIconSize 0

class "Drug (Thuốc)" as Drug #e1f5ff {
  + name: String
  + brand_name: String
  + generic_name: String
  + purpose: String
  + dosage: String
  + indications: String
  + warnings: String
  + contraindications: String
  + adverse_reactions: String
  + manufacturer: String
}

class "Disease (Bệnh lý)" as Disease #fff3e0 {
  + name: String
  + description: String
  + icd_code: String
  + category: String
  + severity: String
}

class "Symptom (Triệu chứng)" as Symptom #f3e5f5 {
  + name: String
  + description: String
}

class "Ingredient (Thành phần)" as Ingredient #e8f5e9 {
  + name: String
  + description: String
}

class "Manufacturer (Nhà SX)" as Manufacturer #fce4ec {
  + name: String
  + country: String
  + website: String
}

' Neo4j Relationships
Drug "0..*" --> "0..*" Disease : "TREATS >\n(Chữa trị)"
Drug "0..*" --> "0..*" Drug : "INTERACTS_WITH >\n(Tương tác thuốc)"
Drug "0..*" --> "0..*" Ingredient : "CONTAINS >\n(Chứa thành phần)"
Drug "0..*" --> "1" Manufacturer : "MADE_BY >\n(Sản xuất bởi)"
Disease "0..*" --> "0..*" Symptom : "HAS_SYMPTOM >\n(Có triệu chứng)"

@enduml
```
