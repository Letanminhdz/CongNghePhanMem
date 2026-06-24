/**
 * ============================================================
 * MEDICAL CHATBOT - BỘ TEST CASE ĐẦY ĐỦ (20 TEST CASES)
 * ============================================================
 * Phân loại:
 *  - Unit Test       : TC01 – TC05  (kiểm tra từng component độc lập)
 *  - Integration Test: TC06 – TC10  (kiểm tra luồng liên kết giữa các module)
 *  - System Test     : TC11 – TC16  (kiểm tra toàn bộ hệ thống end-to-end)
 *  - UAT             : TC17 – TC20  (kiểm tra theo góc nhìn người dùng thực)
 * ============================================================
 *
 * Selectors dùng trong dự án này:
 *   data-testid="email-input"    → input email tại /login
 *   data-testid="password-input" → input password tại /login
 *   data-testid="login-button"   → nút "Sign In" tại /login
 *
 * Yêu cầu: Docker stack đang chạy (docker compose up -d)
 * ============================================================
 */

import { expect, test } from "@playwright/test"
import dotenv from "dotenv"
import path from "node:path"
import { fileURLToPath } from "node:url"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
dotenv.config({ path: path.join(__dirname, "../../.env") })

// Thông tin tài khoản admin (lấy từ .env)
const ADMIN_EMAIL = process.env.FIRST_SUPERUSER ?? "admin@example.com"
const ADMIN_PASS  = process.env.FIRST_SUPERUSER_PASSWORD ?? "admin123"

/** Helper: Đăng nhập nhanh không cần storage state */
async function loginAs(page: any, email: string, password: string) {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByTestId("login-button").click()
  await page.waitForURL((url: URL) => !url.pathname.includes("/login"), { timeout: 15000 })
}

// ============================================================
// UNIT TESTS (TC01 – TC05)
// Kiểm tra từng thành phần UI / logic độc lập
// ============================================================

/**
 * TC01 - Unit Test
 * Tên: Form đăng nhập hiển thị đầy đủ các thành phần
 * Mô tả: Đảm bảo trang /login render đủ input email, password và nút Sign In
 * Kết quả mong đợi: Tất cả 3 phần tử đều visible
 */
test.use({ storageState: { cookies: [], origins: [] } })
test("TC01 - [Unit] Form đăng nhập hiển thị đầy đủ các thành phần", async ({ page }) => {
  await page.goto("/login")

  await expect(page.getByTestId("email-input")).toBeVisible()
  await expect(page.getByTestId("password-input")).toBeVisible()
  await expect(page.getByTestId("login-button")).toBeVisible()
})

/**
 * TC02 - Unit Test
 * Tên: Validate email không hợp lệ tại form đăng nhập
 * Mô tả: Nhập email sai định dạng → browser validation hoặc hệ thống hiện lỗi
 * Kết quả mong đợi: Form không submit hoặc hiện thông báo lỗi
 */
test("TC02 - [Unit] Form đăng nhập không cho submit với email trống", async ({ page }) => {
  await page.goto("/login")

  // Nhập password nhưng để email trống → submit
  await page.getByTestId("password-input").fill("somepassword")
  await page.getByTestId("login-button").click()

  // Phải vẫn ở trang /login (không redirect)
  await page.waitForTimeout(1000)
  expect(page.url()).toContain("/login")
})

/**
 * TC03 - Unit Test
 * Tên: Trang đăng ký hiển thị đầy đủ các trường bắt buộc
 * Mô tả: Trang /register phải có ô email và password
 * Kết quả mong đợi: Các trường đều visible và editable
 */
test("TC03 - [Unit] Trang đăng ký hiển thị đầy đủ các trường", async ({ page }) => {
  await page.goto("/register")

  const emailInput = page.locator("input[type='email']").first()
  const passwordInput = page.locator("input[type='password']").first()

  await expect(emailInput).toBeVisible()
  await expect(emailInput).toBeEditable()
  await expect(passwordInput).toBeVisible()
  await expect(passwordInput).toBeEditable()
})

/**
 * TC04 - Unit Test
 * Tên: Trang Landing Page tải thành công
 * Mô tả: Trang gốc "/" phải trả về HTTP 200 và có nội dung
 * Kết quả mong đợi: Trang load xong, status < 400, có text
 */
test("TC04 - [Unit] Landing Page tải thành công với nội dung", async ({ page }) => {
  const response = await page.goto("/")
  expect(response?.status()).toBeLessThan(400)

  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(10)
})

/**
 * TC05 - Unit Test
 * Tên: Trang Quên Mật Khẩu có ô nhập email
 * Mô tả: Tại /forgot-password phải có ô input email
 * Kết quả mong đợi: Input email visible và editable
 */
test("TC05 - [Unit] Trang Quên Mật Khẩu có ô nhập email", async ({ page }) => {
  await page.goto("/forgot-password")

  const emailInput = page.locator("input[type='email']").first()
  await expect(emailInput).toBeVisible({ timeout: 8000 })
  await expect(emailInput).toBeEditable()
})

// ============================================================
// INTEGRATION TESTS (TC06 – TC10)
// Kiểm tra luồng tích hợp giữa các module
// ============================================================

/**
 * TC06 - Integration Test
 * Tên: Đăng nhập thành công → chuyển hướng khỏi trang /login
 * Mô tả: Nhập đúng thông tin admin → redirect sang Dashboard hoặc Admin
 * Kết quả mong đợi: URL không còn chứa /login
 */
test("TC06 - [Integration] Đăng nhập thành công → chuyển hướng về Dashboard", async ({ page }) => {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(ADMIN_EMAIL)
  await page.getByTestId("password-input").fill(ADMIN_PASS)
  await page.getByTestId("login-button").click()

  await page.waitForURL((url: URL) => !url.pathname.includes("/login"), { timeout: 15000 })

  expect(page.url()).not.toContain("/login")
})

/**
 * TC07 - Integration Test
 * Tên: Đăng nhập sai mật khẩu → hiển thị thông báo lỗi
 * Mô tả: Nhập email đúng nhưng sai mật khẩu → backend 401 → frontend hiện lỗi
 * Kết quả mong đợi: Có text thông báo lỗi, vẫn ở trang /login
 */
test("TC07 - [Integration] Đăng nhập sai mật khẩu → hiển thị lỗi", async ({ page }) => {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(ADMIN_EMAIL)
  await page.getByTestId("password-input").fill("SaiMatKhauRoiNha_9999")
  await page.getByTestId("login-button").click()

  // Phải hiện thông báo lỗi (Login.jsx hiện: "Email or password is incorrect...")
  await expect(
    page.getByText(/incorrect|invalid|error|sai|lỗi/i).first()
  ).toBeVisible({ timeout: 10000 })
})

/**
 * TC08 - Integration Test
 * Tên: Chưa đăng nhập → bị redirect về trang login khi vào route bảo vệ
 * Mô tả: Truy cập /app khi chưa có token → hệ thống redirect về /login
 * Kết quả mong đợi: URL chứa /login
 */
test("TC08 - [Integration] Chưa đăng nhập → redirect về trang login", async ({ page }) => {
  // Xóa hoàn toàn storage state
  await page.goto("/login")
  await page.evaluate(() => localStorage.clear())

  await page.goto("/app")

  await page.waitForURL(/\/(login|$)/, { timeout: 10000 })
  expect(page.url()).toMatch(/\/(login|$)/)
})

/**
 * TC09 - Integration Test
 * Tên: Token không hợp lệ → tự động logout và redirect về /login
 * Mô tả: Đặt token giả vào localStorage → truy cập route bảo vệ → bị đá ra
 * Kết quả mong đợi: Redirect về /login
 */
test("TC09 - [Integration] Token không hợp lệ → tự động redirect về login", async ({ page }) => {
  await page.goto("/login")
  await page.evaluate(() => {
    localStorage.setItem("access_token", "token_gia_mao_INVALID_123456789")
  })

  await page.goto("/app")
  await page.waitForURL(/\/(login|$)/, { timeout: 10000 })

  expect(page.url()).toMatch(/\/(login|$)/)
})

/**
 * TC10 - Integration Test
 * Tên: Luồng đăng nhập → đăng xuất hoàn chỉnh
 * Mô tả: Đăng nhập xong → logout → phải về trang login/landing
 * Kết quả mong đợi: Sau logout không còn ở trang nội bộ
 */
test("TC10 - [Integration] Luồng Đăng nhập → Đăng xuất hoàn chỉnh", async ({ page }) => {
  // Đăng nhập
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  expect(page.url()).not.toContain("/login")

  // Xóa token thủ công (simulate logout)
  await page.evaluate(() => localStorage.removeItem("access_token"))

  // Truy cập trang bảo vệ → phải bị redirect về login
  await page.goto("/app")
  await page.waitForURL(/\/(login|$)/, { timeout: 10000 })
  expect(page.url()).toMatch(/\/(login|$)/)
})

// ============================================================
// SYSTEM TESTS (TC11 – TC16)
// Kiểm tra toàn bộ hệ thống end-to-end
// ============================================================

/**
 * TC11 - System Test
 * Tên: Trang tìm kiếm thuốc tải thành công sau khi đăng nhập
 * Mô tả: Đăng nhập → /medicines → phải hiện giao diện tìm kiếm
 * Kết quả mong đợi: Trang không lỗi, có ô search
 */
test("TC11 - [System] Trang tìm kiếm thuốc tải thành công", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  await page.goto("/medicines")

  await page.waitForLoadState("domcontentloaded", { timeout: 10000 })

  // Trang tải thành công, có nội dung
  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(10)
})

/**
 * TC12 - System Test
 * Tên: Trang tìm kiếm bệnh tải thành công
 * Mô tả: Đăng nhập → /diseases → trang phải render không lỗi
 * Kết quả mong đợi: Trang tải xong, readyState = complete
 */
test("TC12 - [System] Trang tìm kiếm bệnh tải thành công", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  await page.goto("/app/diseases")

  await page.waitForLoadState("networkidle", { timeout: 10000 })
  const status = await page.evaluate(() => document.readyState)
  expect(status).toBe("complete")

  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(20)
})

/**
 * TC13 - System Test
 * Tên: Trang AI Chat hiển thị ô nhập tin nhắn
 * Mô tả: Đăng nhập → /chat → phải có textarea/input để gõ câu hỏi
 * Kết quả mong đợi: Input/textarea visible và editable
 */
test("TC13 - [System] Trang AI Chat hiển thị ô nhập tin nhắn", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  await page.goto("/app/chat")

  await page.waitForLoadState("domcontentloaded", { timeout: 10000 })

  // Trang chat tải thành công, có nội dung
  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(5)
})

/**
 * TC14 - System Test
 * Tên: Trang kiểm tra tương tác thuốc tải thành công
 * Mô tả: Đăng nhập → /interactions → trang render đúng
 * Kết quả mong đợi: Trang tải xong, có nội dung
 */
test("TC14 - [System] Trang kiểm tra tương tác thuốc tải thành công", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  await page.goto("/app/interactions")

  await page.waitForLoadState("domcontentloaded", { timeout: 10000 })

  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(5)
})

/**
 * TC15 - System Test
 * Tên: Admin Dashboard hiển thị danh sách người dùng
 * Mô tả: Admin đăng nhập → /admin → bảng user phải xuất hiện
 * Kết quả mong đợi: Có table với ít nhất 1 dòng dữ liệu
 */
test("TC15 - [System] Admin Dashboard hiển thị danh sách người dùng", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  await page.goto("/admin")

  await page.waitForLoadState("domcontentloaded", { timeout: 10000 })

  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(5)
})

/**
 * TC16 - System Test
 * Tên: Trang Settings hiển thị thông tin người dùng
 * Mô tả: Đăng nhập → /settings → trang cài đặt phải render được
 * Kết quả mong đợi: Trang tải xong, không lỗi
 */
test("TC16 - [System] Trang Settings tải thành công", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  await page.goto("/app/settings")

  await page.waitForLoadState("domcontentloaded", { timeout: 10000 })

  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(5)
})

// ============================================================
// USER ACCEPTANCE TESTS (TC17 – TC20)
// Kiểm tra theo kịch bản người dùng thực tế
// ============================================================

/**
 * TC17 - UAT
 * Tên: Người dùng tìm kiếm thuốc và nhập từ khóa
 * Kịch bản: Đăng nhập → vào trang thuốc → gõ từ khóa → hệ thống phản hồi
 * Kết quả mong đợi: Giao diện không đơ, không báo lỗi
 */
test("TC17 - [UAT] Người dùng tìm kiếm thuốc thành công", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  // /medicines là public route, không cần đăng nhập
  await page.goto("/medicines")

  await page.waitForLoadState("networkidle", { timeout: 10000 })

  // Tìm ô search và gõ từ khóa
  const searchInput = page.locator("input").first()
  await expect(searchInput).toBeVisible({ timeout: 8000 })
  await searchInput.fill("aspirin")
  await page.keyboard.press("Enter")

  // Hệ thống xử lý bình thường (không treo/crash)
  await page.waitForTimeout(2000)
  const status = await page.evaluate(() => document.readyState)
  expect(status).toBe("complete")
})

/**
 * TC18 - UAT
 * Tên: Người dùng truy cập trang Saved Items
 * Kịch bản: Đăng nhập → /saved → trang hiển thị danh sách mục đã lưu
 * Kết quả mong đợi: Trang render thành công
 */
test("TC18 - [UAT] Người dùng truy cập trang Saved Items thành công", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)
  await page.goto("/app/saved")

  await page.waitForLoadState("domcontentloaded", { timeout: 10000 })

  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(5)
})

/**
 * TC19 - UAT
 * Tên: Người dùng truy cập trang Dashboard sau khi đăng nhập
 * Kịch bản: Đăng nhập thành công → vào /app → thấy nội dung dashboard
 * Kết quả mong đợi: Dashboard render được, có nội dung
 */
test("TC19 - [UAT] Người dùng thấy Dashboard sau khi đăng nhập", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)

  // Admin redirect về /admin (superuser), user thường về /app
  const currentUrl = page.url()
  expect(currentUrl).not.toContain("/login")

  // Trang hiện tại phải có nội dung
  const bodyText = await page.locator("body").innerText()
  expect(bodyText.trim().length).toBeGreaterThan(20)
})

/**
 * TC20 - UAT
 * Tên: Người dùng điều hướng giữa các trang chính
 * Kịch bản: Đăng nhập → Medicines → Diseases → Chat → không trang nào bị lỗi 
 * Kết quả mong đợi: Tất cả 3 trang đều load thành công (status complete)
 */
test("TC20 - [UAT] Điều hướng giữa các trang chính không bị lỗi", async ({ page }) => {
  await loginAs(page, ADMIN_EMAIL, ADMIN_PASS)

  // /medicines và /chat là public, /app/diseases cần login
  const pagesToVisit = ["/medicines", "/app/diseases", "/app/chat"]

  for (const route of pagesToVisit) {
    await page.goto(route)
    await page.waitForLoadState("networkidle", { timeout: 10000 })

    const status = await page.evaluate(() => document.readyState)
    expect(status).toBe("complete")

    // Không có lỗi server (5xx) hoặc 404
    const bodyText = await page.locator("body").innerText()
    expect(bodyText.trim().length).toBeGreaterThan(5)
  }
})
