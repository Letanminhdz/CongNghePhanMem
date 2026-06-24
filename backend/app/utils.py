import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore[import-untyped]
import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    """Định nghĩa cấu trúc dữ liệu của một Email gửi đi bao gồm tiêu đề và nội dung HTML."""
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """
    Mục đích: Đọc và dựng (render) giao diện nội dung email HTML từ tệp mẫu (template) bằng công cụ Jinja2.
    Cơ chế hoạt động: Đọc tệp template HTML trong thư mục `email-templates/build/` rồi sử dụng Jinja2 để điền các biến ngữ cảnh (`context`) vào template đó.
    """
    # template_name: Tên của tệp mẫu email (ví dụ: test_email.html)
    # context: Từ điển chứa dữ liệu cần truyền vào mẫu để hiển thị
    # template_str: Chuỗi văn bản thô đọc từ tệp mẫu
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text()
    # html_content: Nội dung HTML hoàn chỉnh sau khi dựng
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    """
    Mục đích: Gửi một email tới địa chỉ đích thông qua máy chủ SMTP.
    Cơ chế hoạt động: 
    1. Kiểm tra xem các biến môi trường cấu hình email SMTP có bật hay không.
    2. Tạo đối tượng `emails.Message`.
    3. Cấu hình thông số kết nối SMTP (host, port, TLS/SSL, tài khoản/mật khẩu) và gửi thư.
    """
    # email_to: Địa chỉ email người nhận
    # subject: Tiêu đề của thư
    # html_content: Nội dung email định dạng HTML
    assert settings.emails_enabled, "no provided configuration for email variables"
    # message: Đối tượng email được đóng gói
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    # smtp_options: Các tùy chọn kết nối tới máy chủ SMTP
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    # response: Kết quả phản hồi từ máy chủ SMTP sau khi gửi
    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"send email result: {response}")


def generate_test_email(email_to: str) -> EmailData:
    """
    Mục đích: Sinh nội dung email kiểm thử hệ thống gửi nhận email.
    Cơ chế hoạt động: Sử dụng mẫu `test_email.html` và điền tên dự án cùng email nhận.
    """
    # email_to: Địa chỉ nhận email kiểm thử
    # project_name: Tên dự án lấy từ cấu hình hệ thống
    project_name = settings.PROJECT_NAME
    # subject: Tiêu đề email kiểm thử
    subject = f"{project_name} - Test email"
    # html_content: Nội dung email đã được dựng mẫu
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    """
    Mục đích: Sinh nội dung email hướng dẫn khôi phục mật khẩu kèm theo token xác thực bảo mật.
    Cơ chế hoạt động: Xây dựng liên kết khôi phục trỏ tới Frontend kèm token, sau đó dựng mẫu email `reset_password.html`.
    """
    # email_to: Địa chỉ nhận mail
    # email: Tên đăng nhập/email của tài khoản cần lấy lại mật khẩu
    # token: Mã xác thực bảo mật JWT cho việc đặt lại mật khẩu
    # project_name: Tên dự án
    project_name = settings.PROJECT_NAME
    # subject: Tiêu đề email khôi phục mật khẩu
    subject = f"{project_name} - Password recovery for user {email}"
    # link: Đường dẫn tới giao diện đặt lại mật khẩu của Frontend kèm token
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    # html_content: Nội dung HTML chứa thông tin khôi phục mật khẩu
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
    """
    Mục đích: Sinh nội dung email chào mừng và thông báo thông tin đăng nhập của tài khoản mới được tạo.
    Cơ chế hoạt động: Dựng mẫu email `new_account.html` và điền tên tài khoản, mật khẩu tạm thời.
    """
    # email_to: Địa chỉ nhận mail đăng ký
    # username: Tên đăng nhập tài khoản mới tạo
    # password: Mật khẩu tạm thời cấp cho tài khoản mới
    # project_name: Tên dự án
    project_name = settings.PROJECT_NAME
    # subject: Tiêu đề email tài khoản mới
    subject = f"{project_name} - New account for user {username}"
    # html_content: Nội dung email đã dựng mẫu
    html_content = render_email_template(
        template_name="new_account.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": username,
            "password": password,
            "email": email_to,
            "link": settings.FRONTEND_HOST,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    """
    Mục đích: Sinh mã JWT dùng cho luồng khôi phục mật khẩu của một tài khoản cụ thể.
    Cơ chế hoạt động: Tạo payload chứa email (`sub`), thời điểm bắt đầu hiệu lực (`nbf`), và thời điểm hết hạn (`exp`) tính bằng giờ từ cài đặt. Mã hóa thông tin này bằng SECRET_KEY.
    """
    # email: Email cần cấp mã khôi phục mật khẩu
    # delta: Thời hạn hiệu lực của mã thông báo
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    # now: Thời gian UTC hiện tại
    now = datetime.now(timezone.utc)
    # expires: Thời điểm hết hạn của mã thông báo
    expires = now + delta
    # exp: Timestamp thời điểm hết hạn
    exp = expires.timestamp()
    # encoded_jwt: Chuỗi mã hóa JWT hoàn chỉnh làm token khôi phục mật khẩu
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    """
    Mục đích: Giải mã và kiểm tra tính hợp lệ của mã khôi phục mật khẩu JWT.
    Cơ chế hoạt động: Dùng `jwt.decode` để giải mã token. Nếu thành công và chưa hết hạn, trả về email của người dùng. Nếu lỗi token không hợp lệ/hết hạn, trả về None.
    """
    # token: Chuỗi JWT cần giải mã và xác thực
    try:
        # decoded_token: Dữ liệu payload sau khi giải mã JWT thành công
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None
