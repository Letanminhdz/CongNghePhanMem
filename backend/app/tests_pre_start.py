import logging

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# max_tries: Số lần thử kết nối tối đa trước khi báo lỗi (5 phút)
max_tries = 60 * 5
# wait_seconds: Thời gian chờ giữa các lần thử kết nối (giây)
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    """
    Mục đích: Xác nhận cơ sở dữ liệu hoạt động bình thường trước khi chạy kiểm thử (tests).
    Cơ chế hoạt động: Tương tự như backend_pre_start, sử dụng `tenacity` để thử lại việc kết nối và chạy truy vấn `SELECT 1` đến DB SQL.
    """
    # db_engine: Đối tượng engine của SQLAlchemy dùng để kết nối cơ sở dữ liệu kiểm thử
    try:
        # Thử tạo Session để kiểm tra trạng thái hoạt động của cơ sở dữ liệu
        with Session(db_engine) as session: # session: Phiên làm việc với cơ sở dữ liệu kiểm thử
            session.execute(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    """
    Mục đích: Điểm bắt đầu để chuẩn bị và kiểm tra môi trường chạy test.
    Cơ chế hoạt động: Gọi hàm `init` để thực thi việc chờ và kiểm tra kết nối DB.
    """
    logger.info("Initializing service")
    init(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
