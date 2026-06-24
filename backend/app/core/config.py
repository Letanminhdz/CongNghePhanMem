import warnings
from typing import Annotated, Any, Literal

from pathlib import Path
from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    """
    Mục đích: Phân tích cấu hình CORS nguồn (origins) từ dạng chuỗi phân cách bằng dấu phẩy thành danh sách các chuỗi.
    Cơ chế hoạt động: Kiểm tra nếu là chuỗi chưa được chuyển đổi thì thực hiện tách bằng dấu phẩy và làm sạch khoảng trắng.
    """
    # v: Giá trị cấu hình CORS đầu vào (có thể là chuỗi hoặc danh sách)
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """
    Lớp lưu trữ cấu hình môi trường và cài đặt cấu hình hệ thống (Settings) của Backend.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1" # Tiền tố đường dẫn cho API phiên bản 1
    PROJECT_NAME: str = "Medical Chatbot" # Tên của dự án
    ENVIRONMENT: Literal["local", "staging", "production"] = "local" # Môi trường chạy ứng dụng (local, staging, production)
    DEBUG: bool = True # Chế độ debug phục vụ phát triển
    FRONTEND_HOST: str = "http://localhost:5173" # Địa chỉ máy chủ Frontend

    SECRET_KEY: str = "changethis" # Khóa bí mật dùng để mã hóa session và token JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # Thời hạn hết hạn của Access Token JWT (mặc định 8 ngày)

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """Tính toán danh sách toàn bộ các domain (origins) được phép truy cập CORS."""
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        """Kiểm tra và trả về xem tính năng gửi email qua SMTP có khả dụng hay không."""
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # Cấu hình kết nối PostgreSQL
    POSTGRES_SERVER: str = "localhost" # Địa chỉ máy chủ PostgreSQL
    POSTGRES_PORT: int = 5432 # Cổng kết nối PostgreSQL
    POSTGRES_USER: str = "postgres" # Tên tài khoản PostgreSQL
    POSTGRES_PASSWORD: str = "" # Mật khẩu tài khoản PostgreSQL
    POSTGRES_DB: str = "medical_chatbot" # Tên cơ sở dữ liệu PostgreSQL

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Tự động tính toán chuỗi URI kết nối PostgreSQL cho SQLAlchemy."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    SENTRY_DSN: HttpUrl | None = None # Đường dẫn DSN của Sentry phục vụ theo dõi lỗi (nếu có)

    # Cấu hình dịch vụ gửi Email SMTP (Tùy chọn)
    SMTP_TLS: bool = True # Sử dụng kết nối bảo mật TLS
    SMTP_SSL: bool = False # Sử dụng kết nối bảo mật SSL
    SMTP_PORT: int = 587 # Cổng gửi email SMTP
    SMTP_HOST: str | None = None # Máy chủ gửi email SMTP
    SMTP_USER: str | None = None # Tài khoản gửi email
    SMTP_PASSWORD: str | None = None # Mật khẩu tài khoản gửi email
    EMAILS_FROM_EMAIL: EmailStr | None = None # Địa chỉ email hiển thị người gửi
    EMAILS_FROM_NAME: str | None = None # Tên hiển thị người gửi

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48 # Thời hạn hết hạn của mã khôi phục mật khẩu (giờ)
    EMAIL_TEST_USER: EmailStr = "test@example.com" # Tài khoản email phục vụ kiểm thử gửi mail

    FIRST_SUPERUSER: EmailStr = "admin@example.com" # Tài khoản quản trị viên tối cao đầu tiên
    FIRST_SUPERUSER_PASSWORD: str = "changethis" # Mật khẩu mặc định của tài khoản quản trị viên đầu tiên
    
    FIRST_USER: EmailStr = "user@example.com" # Tài khoản người dùng mặc định đầu tiên
    FIRST_USER_PASSWORD: str = "user1234" # Mật khẩu mặc định của tài khoản người dùng đầu tiên

    # Cấu hình cơ sở dữ liệu đồ thị Neo4j
    NEO4J_URI: str = "" # Đường dẫn kết nối tới Neo4j (ví dụ: bolt://localhost:7687)
    NEO4J_USERNAME: str = "" # Tài khoản truy cập Neo4j
    NEO4J_PASSWORD: str = "" # Mật khẩu truy cập Neo4j
    NEO4J_DATABASE: str = "neo4j" # Tên cơ sở dữ liệu đồ thị hoạt động


    # Cấu hình mô hình ngôn ngữ lớn LLM (Chỉ sử dụng Google Gemini)
    GEMINI_API_KEY: str | None = None # Khóa API truy cập Google Gemini
    GEMINI_MODEL: str = "gemini-2.5-flash" # Tên mô hình Gemini được chọn sử dụng
    LLM_TIMEOUT_SECONDS: int = 30 # Hạn thời gian tối đa cho cuộc gọi API LLM
    LLM_MAX_RETRIES: int = 3 # Số lần thử lại tối đa khi gọi LLM lỗi

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        """
        Mục đích: Ngăn chặn việc sử dụng mật khẩu/khóa bảo mật mặc định yếu khi triển khai thực tế.
        Cơ chế hoạt động: Nếu phát hiện dùng mật khẩu mặc định (như "changethis"):
        - Ở môi trường cục bộ (local): Đưa ra cảnh báo (warning).
        - Ở môi trường sản xuất (staging/production): Ném lỗi ValueError dừng ứng dụng ngay lập tức để bảo mật.
        """
        # var_name: Tên biến cấu hình cần kiểm tra tính bảo mật
        # value: Giá trị hiện tại của biến cấu hình đó
        if value in ["changethis", "", None, "your-super-secret-key-change-in-production"]:
            message = (
                f'The value of {var_name} is "{value}", '
                "for security, please change it to a strong secret, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        """
        Mục đích: Hàm tự động chạy sau khi tải xong cấu hình nhằm bắt buộc kiểm tra tính an toàn của các khóa bảo mật quan trọng.
        """
        if not self.SECRET_KEY:
            self.SECRET_KEY = "changethis"
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret("NEO4J_PASSWORD", self.NEO4J_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )
        self._check_default_secret(
            "FIRST_USER_PASSWORD", self.FIRST_USER_PASSWORD
        )
        return self


settings = Settings()  # type: ignore
