
---

# Medical Chatbot

Ứng dụng `Medical Chatbot` là dự án web quản lý dữ liệu thuốc - bệnh - tương tác, gồm:

* Backend Python với FastAPI.
* Lưu trữ người dùng và dữ liệu quan hệ bằng PostgreSQL.
* Cơ sở dữ liệu đồ thị Neo4j để lưu bệnh, thuốc, triệu chứng, nhà sản xuất và quan hệ giữa chúng.
* Frontend React + Vite cho giao diện người dùng.
* Docker Compose để chạy toàn bộ stack nhanh và nhất quán.

## Giới thiệu dự án

Dự án này xây dựng một hệ thống backend + frontend cho:

* Tìm kiếm thuốc và bệnh.
* Xây dựng đồ thị Neo4j cho các quan hệ: thuốc điều trị bệnh, bệnh có triệu chứng, thuốc chứa thành phần, thuốc do nhà sản xuất nào sản xuất, thuốc tương tác với thuốc khác.
* Xác thực người dùng và quản lý quyền.
* Chạy thử nhanh bằng Docker Compose.

## Cấu trúc thư mục (Source Code Structure)

Dự án được phân chia rõ ràng theo mô hình Client-Server:

```text
medical-chatbot/
├── backend/                  # Mã nguồn Backend (FastAPI, Python)
│   ├── alembic/              # Migration DB Postgres
│   ├── app/                  # Logic chính của Backend
│   │   ├── api/              # Định nghĩa các Route / Endpoints (Auth, Chat, Tra cứu)
│   │   ├── core/             # Cấu hình môi trường, bảo mật, AI Settings, CORS
│   │   ├── crud/             # Các hàm truy vấn CSDL Postgres (User, Lịch sử)
│   │   ├── models/           # Định nghĩa cấu trúc bảng Postgres (ORM)
│   │   ├── services/         # Xử lý nghiệp vụ lõi (LLM, NER, Graph Search, Wikipedia)
│   │   └── data/             # File CSV gốc chứa kiến thức y khoa (Thuốc, Bệnh, Triệu chứng...)
│   ├── scripts/              # Các file bash script tự động khởi tạo hệ thống
│   └── requirements.txt      # Danh sách các thư viện Python
├── frontend/                 # Mã nguồn Frontend (ReactJS, Vite)
│   ├── public/               # Tài nguyên public (Hình ảnh, Icons)
│   └── src/                  # Mã nguồn chính của giao diện
│       ├── components/       # Các UI Component dùng chung (Navbar, Sidebar, Footer)
│       ├── layouts/          # Bố cục giao diện (AdminLayout, PublicLayout, DashboardLayout)
│       ├── pages/            # Các trang cụ thể (AiChat, MedicineSearch, AdminDashboard, Login...)
│       └── utils/            # Các hàm tiện ích hỗ trợ
├── docs/                     # Thư mục lưu trữ tài liệu phân tích thiết kế, Sơ đồ UML
├── docker-compose.yml        # Tệp cấu hình khởi chạy toàn bộ 4 container (FE, BE, Postgres, Neo4j)
├── .env.example              # File mẫu chứa các biến môi trường
└── README.md                 # Tài liệu hướng dẫn cài đặt và sử dụng (Chính là file này)
```

## Yêu cầu

* Docker và Docker Compose
* Git để clone code

## Cấu hình môi trường (`.env`)

File `.env` nằm ở thư mục gốc dự án và chứa cấu hình cho cả Backend, PostgreSQL và Neo4j. Mặc định bạn có thể sử dụng file `.env.example` để làm mẫu.

```bash
cp .env.example .env

```

**Các biến quan trọng cần kiểm tra:**

* `DOMAIN`: Tên miền môi trường. Mặc định `localhost`.
* `FRONTEND_HOST`: URL frontend. Mặc định `http://localhost:5173`.
* `ENVIRONMENT`: Môi trường chạy, thường là `local`.

**Backend:**

* `SECRET_KEY`: Khóa bí mật cho JWT và bảo mật (Nên thay đổi).
* `FIRST_SUPERUSER`: Email tài khoản quản trị mặc định.
* `FIRST_SUPERUSER_PASSWORD`: Mật khẩu tài khoản quản trị mặc định.
* `FIRST_USER`: Email tài khoản thông thường mặc định.
* `FIRST_USER_PASSWORD`: Mật khẩu tài khoản thông thường mặc định.

**Emails (SMTP / Gửi link quên mật khẩu):**

Để hệ thống gửi được email thật chứa link đặt lại mật khẩu cho người dùng khi họ nhấn quên mật khẩu trên giao diện Frontend:
* `SMTP_HOST`: Địa chỉ máy chủ SMTP (Ví dụ Gmail: `smtp.gmail.com`).
* `SMTP_PORT`: Cổng máy chủ SMTP (Ví dụ Gmail: `587`).
* `SMTP_TLS`: Kích hoạt TLS (Ví dụ Gmail: `True`).
* `SMTP_SSL`: Kích hoạt SSL (Ví dụ Gmail: `False`).
* `SMTP_USER`: Tài khoản email gửi (Ví dụ Gmail: `email-cua-ban@gmail.com`).
* `SMTP_PASSWORD`: Mật khẩu hoặc Mật khẩu ứng dụng (App Password 16 ký tự của Google) dùng để đăng nhập gửi mail.
* `EMAILS_FROM_EMAIL`: Địa chỉ email hiển thị ở người gửi (Trùng với `SMTP_USER`).

*Lưu ý: Backend của ứng dụng đã được cấu hình tự động tìm và đọc file `.env` ở thư mục gốc của dự án này.*

**PostgreSQL:**

* `POSTGRES_SERVER`: Tên service DB, mặc định `db`.
* `POSTGRES_DB`: Tên database, mặc định `app`.
* `POSTGRES_USER`: Tên user DB, mặc định `postgres`.
* `POSTGRES_PASSWORD`: Mật khẩu DB.

**Neo4j:**

* `NEO4J_URI`: URI kết nối Neo4j, mặc định `bolt://neo4j:7687`.
* `NEO4J_USERNAME`: User Neo4j, mặc định `neo4j`.
* `NEO4J_PASSWORD`: Mật khẩu Neo4j.

> **Quan trọng:** Thay `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `POSTGRES_PASSWORD`, `NEO4J_PASSWORD` bằng giá trị an toàn trước khi chạy trên môi trường thực tế.

## Khởi động dự án

1. Clone repository về máy và di chuyển vào thư mục dự án:

```bash
git clone <url-cua-repo> medical-chatbot
cd medical-chatbot

```

2. Đảm bảo bạn đã cấu hình xong file `.env`. Sau đó chạy lệnh sau để khởi tạo stack:

```bash
docker compose build
docker compose up -d

```

> **Lưu ý:** Bạn không cần chạy trực tiếp các lệnh Python thủ công để khởi tạo ban đầu. Phần `prestart` trong `backend/scripts/prestart.sh` sẽ tự động chờ DB khởi động, chạy migration (`alembic upgrade head`) và tạo user mặc định.

## Nạp dữ liệu đồ thị Neo4j từ CSV

Trong dự án có sẵn script nạp dữ liệu Neo4j từ CSV tại `backend/app/scripts/seed_from_csv.py`. Sau khi stack đã khởi động thành công ở bước trên, hãy chạy lệnh sau để tạo các node và quan hệ (từ các file CSV trong `backend/app/data/`):

```bash
docker compose exec backend python app/scripts/seed_from_csv.py

```

## Chạy lại từ đầu (Reset toàn bộ dữ liệu)

Nếu bạn muốn xóa sạch cơ sở dữ liệu hiện tại và khởi tạo lại dự án từ đầu, hãy chạy chuỗi lệnh sau:

```bash
# 1. Dừng và xóa toàn bộ stack cùng volumes dữ liệu cũ
docker compose down --volumes --rmi all

# 2. Xây dựng lại và khởi động lại
docker compose build
docker compose up -d

# 3. Nạp lại dữ liệu đồ thị
docker compose exec backend python app/scripts/seed_from_csv.py

```

## Chạy lệnh thủ công bên trong Backend

Nếu bạn cần debug hoặc chạy lệnh thủ công, hãy truy cập vào bên trong container backend:

```bash
docker compose exec backend bash

```

Một số lệnh hữu ích có thể chạy bên trong:

```bash
python -m alembic current
python app/initial_data.py

```

## Truy cập dịch vụ

Sau khi dự án chạy thành công, bạn có thể truy cập các dịch vụ qua các địa chỉ sau:

* **Frontend:** `http://localhost:5173`
* **Backend API (Docs):** `http://localhost:8000/docs`
* **Kiểm tra sức khỏe Backend:** `http://localhost:8000/health`
* **Neo4j Browser:** `http://localhost:7474`
* **Adminer (Postgres UI):** `http://localhost:8080`

## Cấu hình IDE (Gợi ý code & Sửa lỗi gạch đỏ)

Mặc dù dự án đã chạy hoàn hảo trong Docker, nhưng nếu bạn dùng **VS Code** để code ở máy thật, IDE sẽ báo lỗi gạch đỏ (ví dụ: `Cannot find module`) do thiếu file thư viện nội bộ. 

Để khắc phục và bật tính năng gợi ý code (IntelliSense) mượt mà nhất, bạn hãy cài đặt thư viện ảo cho cả Backend và Frontend:

### 1. Dành cho Backend (Python)
Chạy lệnh sau tại thư mục gốc của dự án để tạo môi trường ảo:
```bash
python3 -m venv .venv
source .venv/bin/activate    # Hoặc .venv\Scripts\activate trên Windows
pip install -r requirements.txt
```
> **Tip:** Sau khi cài xong, trong VS Code nhấn `Ctrl + Shift + P` -> Gõ **Python: Select Interpreter** -> Chọn `./.venv/bin/python`. Các lỗi đỏ ở file Python sẽ biến mất!

### 2. Dành cho Frontend (React/Vite)
Chạy lệnh sau để tải thư viện Node.js cục bộ giúp VS Code nhận diện được React, Tailwind và các component:
```bash
cd frontend
bun install   # Hoặc npm install nếu bạn không dùng bun
```

## License

Dự án này sử dụng giấy phép MIT.

---

## Hướng dẫn Backend (FastAPI Project - Backend)

## Yêu cầu

* Python 3.10 trở lên
* [pip](https://pip.pypa.io/) (đi kèm với Python)
* [Docker](https://www.docker.com/) (tùy chọn, dành cho Docker Compose)

## Docker Compose

Khởi động môi trường phát triển cục bộ với Docker Compose theo hướng dẫn ở các phần trên.

## Quy trình làm việc chung

### Cài đặt (Lần đầu)

1. **Di chuyển vào thư mục backend:**
   ```console
   $ cd backend
   ```

2. **Tạo môi trường ảo Python:**
   
   **Windows:**
   ```console
   $ python -m venv .venv
   $ .venv\Scripts\activate
   ```
   
   **Linux/macOS:**
   ```console
   $ python3 -m venv .venv
   $ source .venv/bin/activate
   ```

3. **Cài đặt các thư viện phụ thuộc:**
   ```console
   $ pip install -r ../requirements.txt
   ```

4. **Cấu hình biến môi trường:**
   ```console
   $ cp ../.env.example .env  # Và cập nhật các cấu hình của bạn
   ```

### Phát triển

Đảm bảo trình soạn thảo (editor) của bạn đang sử dụng đúng môi trường ảo Python, với đường dẫn interpreter là `backend/.venv/bin/python`.

Chỉnh sửa hoặc thêm các model SQLModel cho dữ liệu và bảng SQL trong `./backend/app/models.py`, các API endpoint trong `./backend/app/api/`, và các tiện ích CRUD (Create, Read, Update, Delete) trong `./backend/app/crud.py`.

### Chạy server

```console
$ source .venv/bin/activate  # (hoặc .venv\Scripts\activate trên Windows)
$ fastapi run app/main.py --reload
```

API sẽ chạy tại địa chỉ `http://localhost:8000` với tài liệu Swagger (docs) tại `/docs`.

## VS Code

Đã có sẵn cấu hình để chạy backend thông qua trình gỡ lỗi (debugger) của VS Code, nhờ đó bạn có thể sử dụng breakpoint, tạm dừng và kiểm tra biến, v.v.

Cấu hình cũng đã sẵn sàng để bạn có thể chạy test thông qua tab Python tests của VS Code.

## Tùy chỉnh Docker Compose (Override)

Trong quá trình phát triển, bạn có thể thay đổi các cài đặt Docker Compose mà chỉ ảnh hưởng đến môi trường phát triển cục bộ thông qua file `compose.override.yml`.

Sự thay đổi ở file này không ảnh hưởng đến môi trường production. Do đó, bạn có thể thêm các thay đổi "tạm thời" để hỗ trợ luồng phát triển.

Ví dụ, thư mục chứa code backend được đồng bộ hóa vào trong Docker container, copy trực tiếp code bạn đang sửa vào thư mục bên trong container. Điều đó cho phép bạn test các thay đổi ngay lập tức mà không cần build lại Docker image. Việc này chỉ nên làm khi development, còn trên production, bạn nên build image với phiên bản code mới nhất.

Có một lệnh ghi đè chạy `fastapi run --reload` thay vì `fastapi run` mặc định. Nó khởi động một tiến trình server duy nhất và tự động reload lại mỗi khi code thay đổi. Lưu ý nếu bạn lưu file Python có lỗi cú pháp, nó sẽ bị crash và dừng container. Sau đó bạn có thể khởi động lại bằng lệnh:

```console
$ docker compose watch
```

## Kiểm thử Backend (Tests)

Để chạy test backend:

```console
$ bash ./scripts/test.sh
```

Test được chạy bằng Pytest, bạn có thể chỉnh sửa và thêm test ở `./backend/tests/`.

### Chạy test khi stack đang mở

Nếu stack (Docker) của bạn đang chạy và bạn chỉ muốn chạy test, bạn có thể dùng:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

Kịch bản này gọi `pytest` sau khi đảm bảo các phần khác của stack đang chạy. Để dừng ở lỗi đầu tiên:

```bash
docker compose exec backend bash scripts/tests-start.sh -x
```

### Độ bao phủ (Test Coverage)

Khi test chạy xong, file `htmlcov/index.html` sẽ được tạo ra, bạn có thể mở nó trên trình duyệt để xem độ phủ (coverage) của test.

## Migrations (Di chuyển CSDL)

Vì trong lúc development thư mục app của bạn được mount thành volume trong container, bạn có thể chạy các lệnh `alembic` bên trong container và code migration sẽ xuất hiện ở thư mục gốc của bạn.

* Mở terminal tương tác trong container backend:

```console
$ docker compose exec backend bash
```

* Tạo bản revision mới sau khi thay đổi model (ví dụ thêm cột):

```console
$ alembic revision --autogenerate -m "Add column last_name to User model"
```

* Cập nhật database:

```console
$ alembic upgrade head
```

## Mẫu Email (Email Templates)

Các mẫu email nằm trong `./backend/app/email-templates/`. Cần cài đặt extension [MJML](https://github.com/mjmlio/vscode-mjml) trong VS Code. Sau khi tạo file `.mjml` trong thư mục `src`, dùng lệnh `MJML: Export to HTML` để xuất ra HTML lưu vào thư mục `build`.

---

## Hướng dẫn Frontend (FastAPI Project - Frontend)

Frontend được xây dựng bằng [Vite](https://vitejs.dev/), [React](https://reactjs.org/), [TypeScript](https://www.typescriptlang.org/), [TanStack Query](https://tanstack.com/query), [TanStack Router](https://tanstack.com/router) và [Tailwind CSS](https://tailwindcss.com/).

## Yêu cầu

- [Bun](https://bun.sh/) (khuyên dùng) hoặc [Node.js](https://nodejs.org/)

## Khởi động nhanh

```bash
bun install
bun run dev
```

* Sau đó mở trình duyệt tại địa chỉ http://localhost:5173/.

Lưu ý rằng live server này không chạy trong Docker, nó dành cho môi trường phát triển cục bộ và đây là quy trình được khuyên dùng. 

### Xóa bỏ frontend

Nếu bạn chỉ muốn phát triển ứng dụng API-only và muốn xóa frontend:
* Xóa thư mục `./frontend`.
* Xóa service `frontend` trong `compose.yml` và `compose.override.yml`.

## Tạo Client (Generate Client)

### Tự động

* Kích hoạt môi trường ảo của backend.
* Từ thư mục gốc của project, chạy script:

```bash
bash ./scripts/generate-client.sh
```

### Thủ công

* Khởi động Docker Compose stack.
* Tải file OpenAPI JSON từ `http://localhost/api/v1/openapi.json` và lưu thành file `openapi.json` ở thư mục gốc của `frontend`.
* Chạy lệnh tạo client:

```bash
bun run generate-client
```

Lưu ý: Mỗi khi backend thay đổi schema OpenAPI, bạn cần làm lại các bước này.

## Sử dụng API từ xa

Bạn có thể cấu hình biến môi trường `VITE_API_URL` để trỏ tới URL của API từ xa trong file `frontend/.env`:

```env
VITE_API_URL=https://api.my-domain.example.com
```

## Cấu trúc Code

* `frontend/src` - Mã nguồn chính của frontend.
* `frontend/src/assets` - Tài nguyên tĩnh (ảnh, icon...).
* `frontend/src/client` - OpenAPI client được tự động tạo.
* `frontend/src/components` - Các component dùng chung.
* `frontend/src/hooks` - Các custom hooks.
* `frontend/src/routes` - Định tuyến (routes) và các trang (pages).

## Kiểm thử End-to-End với Playwright

Để chạy test E2E:

```bash
docker compose up -d --wait backend
bunx playwright test
```

Hoặc chạy với giao diện UI:

```bash
bunx playwright test --ui
```
