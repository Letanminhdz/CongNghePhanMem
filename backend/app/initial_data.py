import logging

from sqlalchemy.orm import Session

from app.core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    """
    Mục đích: Khởi tạo dữ liệu ban đầu cho cơ sở dữ liệu SQL (tạo tài khoản superuser đầu tiên).
    Cơ chế hoạt động: Mở một phiên làm việc (Session) kết nối tới DB và gọi hàm `init_db` của hệ thống để thực thi khởi tạo bảng và chèn dữ liệu mặc định.
    """
    with Session(engine) as session: # session: Phiên làm việc tạm thời với cơ sở dữ liệu
        init_db(session)


def main() -> None:
    """
    Mục đích: Điểm khởi chạy để thiết lập dữ liệu ban đầu cho hệ thống trước khi hoạt động.
    Cơ chế hoạt động: Gọi hàm `init` để thực thi việc tạo tài khoản quản trị hệ thống và kiểm tra cơ sở dữ liệu.
    """
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
