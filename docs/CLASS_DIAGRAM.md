# Class Diagram (Relational models)

Sơ đồ lớp cho các model SQLAlchemy trong `backend/app/models`.

```mermaid
classDiagram
    class User {
        +int id
        +string full_name
        +string email
        +string hashed_password
        +bool is_active
        +bool is_superuser
        +datetime created_at
    }

    class Bookmark {
        +int id
        +int user_id
        +string item_type
        +string item_neo4j_id
        +datetime created_at
    }

    class ChatHistory {
        +int id
        +int user_id
        +text message
        +text response
        +string intent
        +text entities
        +datetime created_at
    }

    class InteractionHistory {
        +int id
        +int user_id
        +string drugs
        +datetime created_at
    }

    class SearchHistory {
        +int id
        +int user_id
        +string query_text
        +string item_type
        +datetime created_at
    }

    %% Relationships (FK -> User.id)
    User "1" -- "0..*" Bookmark : has
    User "1" -- "0..*" ChatHistory : wrote
    User "1" -- "0..*" InteractionHistory : did
    User "1" -- "0..*" SearchHistory : searched

    %% Note: Neo4j graph entities (Drug, Disease, Symptom, Ingredient, Manufacturer, RELATIONSHIPS)
    %% are stored in Neo4j and are not represented here as SQLAlchemy classes.
```

---

## Neo4j Graph Model

Sơ đồ các node và quan hệ trong Neo4j graph database.

```mermaid
graph TB
    Drug["<b>Drug</b><br/>name<br/>description<br/>fda_id"]
    Disease["<b>Disease</b><br/>name<br/>description<br/>icd_code"]
    Symptom["<b>Symptom</b><br/>name<br/>description"]
    Ingredient["<b>Ingredient</b><br/>name<br/>description"]
    Manufacturer["<b>Manufacturer</b><br/>name<br/>country<br/>website"]

    Drug -->|TREATS<br/>effectiveness| Disease
    Drug -->|INTERACTS_WITH<br/>severity| Drug
    Drug -->|CONTAINS<br/>concentration| Ingredient
    Drug -->|MADE_BY<br/>production_year| Manufacturer
    Disease -->|HAS_SYMPTOM<br/>frequency| Symptom

    style Drug fill:#e1f5ff
    style Disease fill:#fff3e0
    style Symptom fill:#f3e5f5
    style Ingredient fill:#e8f5e9
    style Manufacturer fill:#fce4ec
```

---

## Chi tiết cấu trúc Neo4j

Xem file [NEO4J_GRAPH_STRUCTURE.md](./NEO4J_GRAPH_STRUCTURE.md) để hiểu rõ:
- Các node type và properties
- Các relationship type
- Ví dụ query Cypher
- Cách nạp dữ liệu từ CSV
