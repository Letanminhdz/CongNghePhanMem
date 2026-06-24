import csv
import logging
import os
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.neo4j_service import neo4j_service

# Cấu hình logging để ghi nhận thông tin trong quá trình chạy script seed dữ liệu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DATA_DIR: Đường dẫn tuyệt đối tới thư mục chứa các file dữ liệu CSV cần nạp (seeding)
DATA_DIR = Path(__file__).parent.parent / "data"

def seed_nodes(file_path: Path, label: str, merge_func: Any):
    """
    Mục đích: Nạp (seed) các nút (nodes) từ một file CSV vào cơ sở dữ liệu đồ thị Neo4j.
    Cơ chế hoạt động: 
    1. Kiểm tra xem file CSV có tồn tại hay không, nếu không thì bỏ qua.
    2. Đọc từng dòng của file CSV bằng `csv.DictReader`.
    3. Gọi hàm hợp nhất (`merge_func`) được cung cấp để chèn hoặc cập nhật nút vào Neo4j mà không tạo trùng lặp.
    """
    # file_path: Đường dẫn tới file CSV chứa thông tin các nút cần seed
    # label: Nhãn của nút (ví dụ: "Drug", "Disease") để ghi log
    # merge_func: Hàm callback dùng để hợp nhất nút vào cơ sở dữ liệu đồ thị
    if not file_path.exists():
        logger.warning(f"File {file_path} không tồn tại, bỏ qua việc seed cho nhãn {label}.")
        return

    logger.info(f"Đang seed các nút {label} từ file {file_path}...")
    count = 0 # count: Biến đếm số lượng nút đã được seed thành công
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f) # reader: Trình đọc file CSV định dạng dòng dưới dạng từ điển (dictionary)
        for row in reader:
            # row: Một dòng dữ liệu trong file CSV (tương ứng với một bản ghi thực thể)
            if merge_func(row):
                count += 1
    logger.info(f"✓ Đã seed {count} nút {label}.")

def seed_relationships(file_path: Path, rel_type: str, merge_func: Any):
    """
    Mục đích: Nạp (seed) các mối quan hệ (relationships) giữa các nút từ file CSV vào Neo4j.
    Cơ chế hoạt động:
    1. Kiểm tra sự tồn tại của file CSV.
    2. Đọc dữ liệu CSV và xác định loại mối quan hệ để gọi hàm `merge_func` phù hợp với các tham số tương ứng (như tên thuốc, tên bệnh lý, triệu chứng, mức độ tương tác, v.v.).
    3. Thực hiện tạo hoặc cập nhật mối quan hệ trong đồ thị Neo4j.
    """
    # file_path: Đường dẫn tới file CSV chứa dữ liệu mối quan hệ
    # rel_type: Loại mối quan hệ trong Neo4j (ví dụ: "TREATS", "HAS_SYMPTOM", "CONTAINS", "INTERACTS_WITH")
    # merge_func: Hàm callback dùng để tạo/hợp nhất mối quan hệ trong cơ sở dữ liệu đồ thị
    if not file_path.exists():
        logger.warning(f"File {file_path} không tồn tại, bỏ qua việc seed mối quan hệ {rel_type}.")
        return

    logger.info(f"Đang seed mối quan hệ {rel_type} từ file {file_path}...")
    count = 0 # count: Biến đếm số lượng mối quan hệ đã được tạo thành công
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f) # reader: Đối tượng đọc file CSV
        for row in reader:
            # row: Một dòng chứa mối liên kết giữa 2 thực thể
            try:
                success = False # success: Cờ đánh dấu tạo mối quan hệ thành công hay không
                if rel_type == "TREATS":
                    success = merge_func(row['drug_name'], row['disease_name'], source="csv_seed")
                elif rel_type == "HAS_SYMPTOM":
                    success = merge_func(row['disease_name'], row['symptom_name'], source="csv_seed")
                elif rel_type == "CONTAINS":
                    success = merge_func(row['drug_name'], row['ingredient_name'])
                elif rel_type == "MADE_BY":
                    success = merge_func(row['drug_name'], row['manufacturer_name'])
                elif rel_type == "INTERACTS_WITH":
                    success = merge_func(
                        row['drug_1'], 
                        row['drug_2'], 
                        severity=row.get('severity', 'moderate'),
                        description=row.get('description', '')
                    )
                else:
                    success = False
                
                if success:
                    count += 1
            except Exception as e:
                logger.error(f"Lỗi khi seed dòng dữ liệu mối quan hệ {rel_type} {row}: {e}")
                
    logger.info(f"✓ Đã seed {count} mối quan hệ {rel_type}.")

def seed():
    """
    Mục đích: Hàm khởi chạy chính (main seed) thực hiện nạp toàn bộ cơ sở dữ liệu đồ thị Neo4j từ các file CSV.
    Cơ chế hoạt động:
    1. Xóa và khởi dựng lại cấu trúc đồ thị (chỉ mục/ràng buộc) thông qua `neo4j_service.rebuild_graph`.
    2. Thực hiện seed các nút trước theo thứ tự ưu tiên (Thuốc, Bệnh lý, Triệu chứng, Thành phần, Nhà sản xuất).
    3. Thực hiện seed các mối quan hệ liên kết các nút lại với nhau sau khi các nút đã được tạo.
    """
    logger.info("Bắt đầu chạy Neo4j CSV Seeding...")
    
    # Đảm bảo các chỉ mục và ràng buộc khóa đã tồn tại trong đồ thị Neo4j
    neo4j_service.rebuild_graph()
    
    # 1. Seed các Nút (Nodes) - Ưu tiên tạo các nút thực thể trước
    seed_nodes(DATA_DIR / "drugs.csv", "Drug", neo4j_service.merge_drug)
    seed_nodes(DATA_DIR / "diseases.csv", "Disease", neo4j_service.merge_disease)
    seed_nodes(DATA_DIR / "symptoms.csv", "Symptom", neo4j_service.merge_symptom)
    seed_nodes(DATA_DIR / "ingredients.csv", "Ingredient", neo4j_service.merge_ingredient)
    seed_nodes(DATA_DIR / "manufacturers.csv", "Manufacturer", neo4j_service.merge_manufacturer)
    
    # 2. Seed các Mối quan hệ (Relationships) - Liên kết các thực thể lại với nhau
    seed_relationships(DATA_DIR / "drug_disease.csv", "TREATS", neo4j_service.merge_treats_relationship)
    seed_relationships(DATA_DIR / "disease_symptom.csv", "HAS_SYMPTOM", neo4j_service.merge_has_symptom_relationship)
    seed_relationships(DATA_DIR / "drug_ingredient.csv", "CONTAINS", neo4j_service.merge_contains_relationship)
    seed_relationships(DATA_DIR / "drug_manufacturer.csv", "MADE_BY", neo4j_service.merge_made_by_relationship)
    seed_relationships(DATA_DIR / "drug_interaction.csv", "INTERACTS_WITH", neo4j_service.create_interacts_relationship)

    logger.info("Quá trình Neo4j Seeding đã hoàn tất thành công.")

if __name__ == "__main__":
    seed()
