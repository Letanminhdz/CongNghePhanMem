# BÁO CÁO KIẾN TRÚC DỮ LIỆU VÀ THIẾT KẾ API DỰ ÁN MEDICHAT

Dựa trên toàn bộ cấu trúc giao diện Frontend (React) của hệ thống, dưới đây là tài liệu mô tả chi tiết về các Class dữ liệu, chiến lược lưu trữ giữa Neo4j và PostgreSQL, cùng với danh sách các API cần thiết cho từng trang.

---

## 1. MÔ TẢ TOÀN BỘ CLASS DỮ LIỆU (DATA MODELS)

Hệ thống được thiết kế theo mô hình lai (Hybrid Database), sử dụng ưu điểm của **Neo4j** (Graph Database) cho các dữ liệu y tế có tính liên kết chéo phức tạp, và **PostgreSQL** (Relational Database) cho dữ liệu người dùng và lịch sử hoạt động.

### 1.1. Các Bảng (Node) lưu trong Neo4j (Dữ liệu y tế)
1. **Medicine (Thuốc):**
   - Thuộc tính: `id`, `name`, `sub_description` (dạng bào chế/hàm lượng), `category`, `description`, `dosage` (liều lượng), `sideEffects` (tác dụng phụ), `contraindications` (chống chỉ định).
2. **Disease (Bệnh lý):**
   - Thuộc tính: `id`, `name`, `category`, `severity` (mức độ nghiêm trọng), `description`, `treatments` (phác đồ điều trị).
3. **Ingredient (Thành phần hóa học):**
   - Thuộc tính: `id`, `name`.
4. **Manufacturer (Nhà sản xuất):**
   - Thuộc tính: `id`, `name`, `country`.
5. **Symptom (Triệu chứng):**
   - Thuộc tính: `id`, `name`.

**Mô hình quan hệ (Edges) trong Neo4j:**
- `(Medicine) -[CONTAINS]-> (Ingredient)`
- `(Medicine) -[MANUFACTURED_BY]-> (Manufacturer)`
- `(Disease) -[HAS_SYMPTOM]-> (Symptom)`
- `(Medicine) -[TREATS]-> (Disease)`
- `(Medicine) -[INTERACTS_WITH {severity, description}]-> (Medicine)`

### 1.2. Các Bảng lưu trong PostgreSQL
Chỉ gồm 4 bảng chính phục vụ cho hoạt động của User và ứng dụng:
1. **User (Người dùng):**
   - Thuộc tính: `id`, `full_name`, `email`, `password_hash`, `role` (User/Admin), `status` (Active/Locked), `created_at`.
2. **ChatHistory (Lịch sử Chat AI):**
   - Thuộc tính: `id`, `user_id`, `session_title`, `messages` (Mảng JSON chứa nội dung người dùng hỏi và AI đáp), `total_tokens`, `created_at`, `updated_at`.
3. **Bookmark (Mục đã lưu):**
   - Thuộc tính: `id`, `user_id`, `item_type` (Medicine/Disease), `item_neo4j_id` (ID của dữ liệu trong Neo4j), `created_at`.
4. **SearchHistory (Lịch sử tìm kiếm):**
   - Thuộc tính: `id`, `user_id`, `query_text` (Từ khóa tìm kiếm), `item_type` (Phân loại tìm kiếm thuốc/bệnh), `created_at`.

---

## 2. LUỒNG DỮ LIỆU TỪNG TRANG GIAO DIỆN

### 2.1. Phân hệ Public & Auth (PostgreSQL)
- **Login / Register / ForgotPassword:**
  - **Lấy/Thêm/Sửa dữ liệu:** Tương tác trực tiếp với bảng `User` (PostgreSQL) để đăng nhập và tạo tài khoản.

### 2.2. Phân hệ User Dashboard (`/app`)
- **Dashboard (Trang chủ User):**
  - **Lấy dữ liệu:** 
    - Bảng `SearchHistory` (PostgreSQL) cho phần "Recent Searches".
    - Bảng `ChatHistory` và `Bookmark` (PostgreSQL) để đếm số liệu thống kê tổng quan.
    - Lấy thông tin hiển thị của thuốc/bệnh đã lưu từ Neo4j dựa trên ID lấy từ `Bookmark`.
- **AiChat (Chat với AI):**
  - **Lấy/Thêm dữ liệu:** Lưu và tải lịch sử đoạn chat từ bảng `ChatHistory` (PostgreSQL). AI engine xử lý ngầm sẽ truy vấn Neo4j.
- **Medicine Search & Detail (Tra cứu Thuốc):**
  - **Lấy dữ liệu:** Truy vấn hoàn toàn từ Neo4j (bảng `Medicine`, `Manufacturer`, `Ingredient`).
  - **Thêm dữ liệu:** Khi người dùng tra cứu, lưu từ khóa vào `SearchHistory` (PostgreSQL).
- **Disease Search & Detail (Tra cứu Bệnh):**
  - **Lấy dữ liệu:** Truy vấn hoàn toàn từ Neo4j (bảng `Disease`, `Symptom`).
  - **Thêm dữ liệu:** Ghi lại lịch sử vào `SearchHistory` (PostgreSQL).
- **Interaction Checker (Kiểm tra tương tác thuốc):**
  - **Lấy dữ liệu:** Truy vấn các Node `Medicine` và relation `INTERACTS_WITH` từ Neo4j.
- **Saved Items (Mục đã lưu):**
  - **Lấy/Thêm dữ liệu:** Bảng `Bookmark` (PostgreSQL). Backend tự động map với Neo4j để lấy tên chi tiết.
- **Settings (Cài đặt tài khoản):**
  - **Lấy/Sửa dữ liệu:** Bảng `User` (PostgreSQL).

### 2.3. Phân hệ Admin Dashboard (`/admin`)
- **Admin Dashboard & Reports (Thống kê):**
  - **Lấy dữ liệu:** Thống kê dựa trên bảng `User`, `ChatHistory`, và `SearchHistory` (PostgreSQL) để vẽ biểu đồ và phân tích (Ví dụ: Số phiên chat, thống kê chủ đề search).
- **Admin User Management (Quản lý người dùng):**
  - **Lấy/Sửa dữ liệu:** Truy vấn bảng `User` (PostgreSQL) để phân quyền (Role) và Khóa/Mở khóa tài khoản (Status).
- **Admin Medicines (Quản lý Thuốc):**
  - **Lấy/Thêm/Sửa/Xóa:** Tương tác trực tiếp bằng các Node/Edge trong Neo4j (`Medicine`, `Manufacturer`).
- **Admin Diseases (Quản lý Bệnh):**
  - **Lấy/Thêm/Sửa/Xóa:** Tương tác trực tiếp bằng các Node/Edge trong Neo4j (`Disease`, `Symptom`).
- **Admin AI Logs (Nhật ký AI):**
  - **Lấy dữ liệu:** Xem chi tiết các đoạn hội thoại của user từ bảng `ChatHistory` (PostgreSQL).

---

## 3. DANH SÁCH API CẦN THIẾT

### 3.1. Auth & User API (PostgreSQL: Bảng User)
* **POST /api/auth/register**
  - **Input:** `{ full_name, email, password }`
  - **Output:** `{ message, token, user }`
* **POST /api/auth/login**
  - **Input:** `{ email, password }`
  - **Output:** `{ token, user }`
* **PUT /api/users/me**
  - **Input:** `{ full_name, email }`
  - **Output:** Trạng thái tài khoản sau cập nhật.

### 3.2. Medicine API (Neo4j)
* **GET /api/medicines**
  - **Input (Query):** `?search=xyz&category=abc`
  - **Output:** Danh sách các loại thuốc.
* **GET /api/medicines/{id}**
  - **Output:** Chi tiết thuốc, thành phần, tương tác.
* **POST / PUT / DELETE /api/admin/medicines** (Dành cho Admin)
  - **Thao tác:** Thêm mới, cập nhật, xóa thuốc trong Neo4j.

### 3.3. Disease API (Neo4j)
* **GET /api/diseases** & **GET /api/diseases/{id}**
* **POST / PUT / DELETE /api/admin/diseases** (Dành cho Admin)

### 3.4. Search History API (PostgreSQL: Bảng SearchHistory)
* **GET /api/search-history**
  - **Output:** Danh sách từ khóa người dùng vừa tìm kiếm (`[{ query_text, item_type, created_at }]`).
* **POST /api/search-history**
  - **Input:** `{ query_text, item_type }` (gọi ngầm khi tra cứu bệnh/thuốc).

### 3.5. AI Chat API (PostgreSQL: Bảng ChatHistory)
* **GET /api/chat/history**
  - **Output:** Danh sách các đoạn chat trước đây (`[{ id, session_title, created_at }]`).
* **GET /api/chat/history/{id}**
  - **Output:** Lấy nội dung chi tiết của phiên chat (`messages` JSON).
* **POST /api/chat/message**
  - **Input:** `{ session_id, message }`
  - **Output:** `{ reply: "AI Response", tokens_used: 120 }` (Lưu lịch sử vào Postgres, AI engine tự query Neo4j).

### 3.6. Bookmark API (PostgreSQL: Bảng Bookmark)
* **GET /api/bookmarks**
  - **Output:** Trả về list `{ id, item_type, item_data }` (join Postgres với Neo4j).
* **POST /api/bookmarks**
  - **Input:** `{ item_type: "Medicine", item_neo4j_id: "uuid-123" }`
* **DELETE /api/bookmarks/{id}**

### 3.7. Admin Management API (PostgreSQL)
* **GET /api/admin/users** (Lấy danh sách người dùng)
* **PUT /api/admin/users/{id}/role** (Phân quyền User/Admin)
* **PUT /api/admin/users/{id}/status** (Khóa tài khoản)
* **GET /api/admin/stats** (Lấy tổng số User, tổng số Chat, Bookmark)
* **GET /api/admin/ai-logs** (Xem dữ liệu từ `ChatHistory` để kiểm tra độ chính xác AI)
