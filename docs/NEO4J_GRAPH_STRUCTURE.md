# Neo4j Graph Database Structure

Cấu trúc dữ liệu lưu trong **Neo4j** của dự án Medical Chatbot.

## Tổng quan

Neo4j là một cơ sở dữ liệu đồ thị (Graph Database) được sử dụng để lưu trữ dữ liệu y tế với các mối quan hệ phức tạp giữa:
- **Thuốc** (Drug)
- **Bệnh** (Disease)
- **Triệu chứng** (Symptom)
- **Thành phần** (Ingredient)
- **Nhà sản xuất** (Manufacturer)

## Node Types (Các loại nút)

### 1. Drug (Thuốc)
**Mô tả**: Lưu thông tin về các loại thuốc.

**Properties**:
- `name` (String): Tên chung/Tên định danh (Primary Key)
- `brand_name` (String): Tên thương mại
- `generic_name` (String): Tên gốc
- `purpose` (String): Mục đích/Công dụng
- `dosage` (String): Liều lượng
- `indications` (String): Chỉ định
- `warnings` (String): Cảnh báo
- `contraindications` (String): Chống chỉ định
- `adverse_reactions` (String): Phản ứng có hại
- `manufacturer` (String): Nhà sản xuất

**Ví dụ**:
```
Drug {
  name: "Aspirin",
  brand_name: "Bayer Aspirin",
  purpose: "Thuốc giảm đau, hạ sốt",
  dosage: "500mg/ngày"
}
```

### 2. Disease (Bệnh)
**Mô tả**: Lưu thông tin về các bệnh lý.

**Properties**:
- `name` (String): Tên bệnh (Primary Key)
- `description` (String): Mô tả chi tiết bệnh
- `icd_code` (String): Mã ICD-10 nếu có
- `category` (String): Thể loại bệnh
- `severity` (String): Mức độ nghiêm trọng

**Ví dụ**:
```
Disease {
  name: "Headache",
  description: "Đau đầu",
  icd_code: "G89.29",
  category: "Thần kinh",
  severity: "Nhẹ"
}
```

### 3. Symptom (Triệu chứng)
**Mô tả**: Lưu các triệu chứng bệnh.

**Properties**:
- `name` (String): Tên triệu chứng (Primary Key)
- `description` (String): Mô tả triệu chứng

**Ví dụ**:
```
Symptom {
  name: "Fever",
  description: "Sốt cao"
}
```

### 4. Ingredient (Thành phần)
**Mô tả**: Lưu các thành phần hóa học trong thuốc.

**Properties**:
- `name` (String): Tên thành phần (Primary Key)
- `description` (String): Mô tả thành phần

**Ví dụ**:
```
Ingredient {
  name: "Acetylsalicylic Acid",
  description: "Hoạt chất chính của Aspirin"
}
```

### 5. Manufacturer (Nhà sản xuất)
**Mô tả**: Lưu thông tin nhà sản xuất thuốc.

**Properties**:
- `name` (String): Tên nhà sản xuất (Primary Key)
- `country` (String): Nước sản xuất
- `website` (String): Website của công ty

**Ví dụ**:
```
Manufacturer {
  name: "Bayer",
  country: "Germany",
  website: "https://www.bayer.com"
}
```

## Relationship Types (Các loại quan hệ)

### 1. TREATS (Thuốc điều trị bệnh)
**Từ**: Drug → Disease  
**Mô tả**: Thuốc này điều trị được bệnh nào.

**Properties**:
- `effectiveness` (String): Mức độ hiệu quả (e.g., "high", "medium", "low")
- `source` (String): Nguồn dữ liệu (e.g., "csv_seed", "openFDA")

**Ví dụ**:
```
(Aspirin) -[TREATS {effectiveness: "high"}]-> (Headache)
```

### 2. HAS_SYMPTOM (Bệnh có triệu chứng)
**Từ**: Disease → Symptom  
**Mô tả**: Bệnh này thường gặp triệu chứng nào.

**Properties**:
- `frequency` (String): Tần suất (e.g., "common", "rare")
- `source` (String): Nguồn dữ liệu

**Ví dụ**:
```
(Headache) -[HAS_SYMPTOM {frequency: "common"}]-> (Fever)
```

### 3. CONTAINS (Thuốc chứa thành phần)
**Từ**: Drug → Ingredient  
**Mô tả**: Thuốc này chứa thành phần gì.

**Properties**:
- `concentration` (String): Nồng độ (e.g., "500mg", "10%")

**Ví dụ**:
```
(Aspirin) -[CONTAINS {concentration: "500mg"}]-> (Acetylsalicylic Acid)
```

### 4. MADE_BY (Thuốc được sản xuất bởi)
**Từ**: Drug → Manufacturer  
**Mô tả**: Thuốc này được sản xuất bởi nhà sản xuất nào.

**Properties**:
- `production_year` (String): Năm sản xuất

**Ví dụ**:
```
(Aspirin) -[MADE_BY {production_year: "1897"}]-> (Bayer)
```

### 5. INTERACTS_WITH (Thuốc tương tác với thuốc)
**Từ**: Drug → Drug  
**Mô tả**: Thuốc này có thể tương tác (không tốt) với thuốc khác.

**Properties**:
- `severity` (String): Mức độ nguy hiểm ("severe", "moderate", "mild")
- `description` (String): Mô tả chi tiết tương tác

**Ví dụ**:
```
(Aspirin) -[INTERACTS_WITH {severity: "moderate", description: "May increase bleeding"}]-> (Warfarin)
```

## Biểu đồ cấu trúc

```
┌─────────────────────────────────────────────────────────┐
│                    NEO4J GRAPH STRUCTURE                │
└─────────────────────────────────────────────────────────┘

                           Drug
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    Ingredient         Manufacturer       Disease
                                           │
                                           ▼
                                        Symptom

Relationships:
• Drug -[CONTAINS]-> Ingredient
• Drug -[MADE_BY]-> Manufacturer
• Drug -[TREATS]-> Disease
• Disease -[HAS_SYMPTOM]-> Symptom
• Drug -[INTERACTS_WITH]-> Drug
```

## Ví dụ query trong Neo4j

### Tìm thuốc điều trị bệnh nào đó

```cypher
MATCH (drug:Drug)-[treats:TREATS]->(disease:Disease)
WHERE disease.name = "Headache"
RETURN drug.name, treats.effectiveness
```

### Tìm các thành phần trong thuốc

```cypher
MATCH (drug:Drug)-[contains:CONTAINS]->(ingredient:Ingredient)
WHERE drug.name = "Aspirin"
RETURN ingredient.name, contains.concentration
```

### Kiểm tra tương tác giữa hai thuốc

```cypher
MATCH (drug1:Drug)-[interacts:INTERACTS_WITH]->(drug2:Drug)
WHERE drug1.name = "Aspirin" OR drug2.name = "Aspirin"
RETURN drug1.name, drug2.name, interacts.severity
```

### Tìm triệu chứng của bệnh

```cypher
MATCH (disease:Disease)-[has:HAS_SYMPTOM]->(symptom:Symptom)
WHERE disease.name = "Headache"
RETURN symptom.name, has.frequency
```

## Cách nạp dữ liệu

Dữ liệu Neo4j được nạp từ các file CSV trong thư mục `backend/app/data/`:

| File CSV | Node Type | Mô tả |
|----------|-----------|-------|
| `drugs.csv` | Drug | Danh sách thuốc |
| `diseases.csv` | Disease | Danh sách bệnh |
| `symptoms.csv` | Symptom | Danh sách triệu chứng |
| `ingredients.csv` | Ingredient | Danh sách thành phần |
| `manufacturers.csv` | Manufacturer | Danh sách nhà sản xuất |
| `drug_disease.csv` | TREATS | Quan hệ thuốc ↔ bệnh |
| `disease_symptom.csv` | HAS_SYMPTOM | Quan hệ bệnh ↔ triệu chứng |
| `drug_ingredient.csv` | CONTAINS | Quan hệ thuốc ↔ thành phần |
| `drug_manufacturer.csv` | MADE_BY | Quan hệ thuốc ↔ nhà sản xuất |
| `drug_interaction.csv` | INTERACTS_WITH | Quan hệ thuốc ↔ thuốc |

## Để nạp dữ liệu Neo4j từ CSV

```bash
docker compose exec backend python app/scripts/seed_from_csv.py
```

## Truy cập Neo4j Browser

Neo4j Browser là giao diện để viết query và xem dữ liệu trực tiếp:

```
http://localhost:7474
```

**Đăng nhập**:
- Username: `neo4j`
- Password: (giá trị `NEO4J_PASSWORD` trong `.env`)
