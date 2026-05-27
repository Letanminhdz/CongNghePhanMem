"""
Script độc lập: đọc .env, gọi openFDA, import dữ liệu vào Neo4j.

Cách chạy (từ thư mục backend/):
    python -m app.scripts.import_openfda --limit 20 --skip 0
"""
import argparse
import logging
import os
import sys

from dotenv import load_dotenv

# Thêm backend/ vào path nếu chạy trực tiếp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

from app.services.import_openfda_service import import_openfda_drugs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import openFDA drug data into Neo4j")
    parser.add_argument("--limit", type=int, default=10, help="Số record lấy")
    parser.add_argument("--skip", type=int, default=0, help="Vị trí bắt đầu")
    args = parser.parse_args()

    logger.info("Đang import %d drugs từ openFDA (skip=%d)...", args.limit, args.skip)
    imported = import_openfda_drugs(limit=args.limit, skip=args.skip)
    logger.info("Import thành công: %d drugs", imported)


if __name__ == "__main__":
    main()
