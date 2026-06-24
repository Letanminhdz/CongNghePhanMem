import logging

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# max_tries: Số lần thử kết nối tối đa (5 phút)
max_tries = 60 * 5
# wait_seconds: Khoảng thời gian chờ giữa các lần thử (giây)
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    """
    Mục đích: Kiểm tra và xác nhận cơ sở dữ liệu SQL đã khởi động và sẵn sàng kết nối.
    Cơ chế hoạt động: Sử dụng thư viện `tenacity` để tự động thử lại nhiều lần việc mở một Session SQL và thực thi câu lệnh truy vấn cơ bản `SELECT 1`.
    """
    # db_engine: Đối tượng SQLAlchemy Engine dùng để kết nối cơ sở dữ liệu SQL
    try:
        with Session(db_engine) as session: # session: Phiên làm việc tạm thời với cơ sở dữ liệu
            # Cố gắng thực thi câu lệnh đơn giản SELECT 1 để kiểm tra DB có phản hồi hay không
            session.execute(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    """
    Mục đích: Điểm khởi chạy của script để kiểm tra trạng thái cơ sở dữ liệu trước khi khởi động FastAPI.
    Cơ chế hoạt động: Gọi hàm `init` cùng với đối tượng `engine` toàn cục của ứng dụng.
    """
    logger.info("Initializing service")
    init(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
