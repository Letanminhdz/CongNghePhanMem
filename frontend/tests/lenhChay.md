# HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY TEST TỰ ĐỘNG - MEDICAL CHATBOT

Tài liệu này bao gồm các bước từ khi chưa có công cụ test cho đến khi chạy được toàn bộ kịch bản test tự động bằng Playwright.

---

## 1. CÀI ĐẶT CÔNG CỤ TEST TỪ ĐẦU (INSTALLATION)

Mở **PowerShell** hoặc **Terminal** và đi vào thư mục `frontend` của dự án để cài đặt Playwright và các trình duyệt đi kèm.

```powershell
cd D:\CNPM\CongNghePhanMem\frontend

# 1. Cài đặt các thư viện cần thiết (nếu chưa cài)
npm install

# 2. Tải và cài đặt Playwright cùng các trình duyệt (Chromium, Firefox, WebKit)
npx playwright install
```
*(Quá trình tải trình duyệt có thể mất vài phút tùy tốc độ mạng).*

---

## 2. KHỞI ĐỘNG HỆ THỐNG TRƯỚC KHI TEST

Để test chạy thành công, cả Backend và Frontend phải đang mở.

### Bật Backend và CSDL
Mở một cửa sổ PowerShell mới tại thư mục gốc của dự án:
```powershell
cd D:\CNPM\CongNghePhanMem
docker compose up -d db neo4j backend
```

### Bật Frontend (Dev Server)
Mở một cửa sổ PowerShell mới tại thư mục `frontend`:
```powershell
cd D:\CNPM\CongNghePhanMem\frontend
npm run dev
```
*(Giữ nguyên cửa sổ này, không được tắt).*

---

## 3. LỆNH CHẠY TEST CASE

Mở thêm một cửa sổ PowerShell mới tại thư mục `frontend` và chạy 1 trong 2 lệnh sau:

### Chạy hiển thị giao diện (Khuyên dùng để demo)
Lệnh này mở giao diện UI, cho phép bạn xem robot thao tác trên trình duyệt thật.
```powershell
cd D:\CNPM\CongNghePhanMem\frontend
npx playwright test tests/medical_chatbot.spec.ts --ui
```

### Chạy ngầm (Headless) trong Terminal
Chạy ngầm và in kết quả xanh/đỏ ra màn hình.
```powershell
cd D:\CNPM\CongNghePhanMem\frontend
npx playwright test tests/medical_chatbot.spec.ts --project=chromium
```

### Xem Báo Cáo HTML (Sau khi chạy ngầm xong)
```powershell
npx playwright show-report
```
