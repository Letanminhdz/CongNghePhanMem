# MEDICHAT CLASS DIAGRAM

Dưới đây là Sơ đồ lớp (Class Diagram) thể hiện cấu trúc các thực thể và mối quan hệ giữa chúng, được phân chia theo 2 hệ quản trị cơ sở dữ liệu (PostgreSQL và Neo4j) dựa trên kiến trúc của hệ thống.

```mermaid
classDiagram
    %% PostgreSQL Database Classes
    namespace PostgreSQL {
        class User {
            +UUID id
            +String full_name
            +String email
            +String password_hash
            +String role
            +String status
            +DateTime created_at
        }

        class ChatHistory {
            +UUID id
            +UUID user_id
            +String session_title
            +JSON messages
            +Integer total_tokens
            +DateTime created_at
            +DateTime updated_at
        }

        class Bookmark {
            +UUID id
            +UUID user_id
            +String item_type
            +String item_neo4j_id
            +DateTime created_at
        }

        class SearchHistory {
            +UUID id
            +UUID user_id
            +String query_text
            +String item_type
            +DateTime created_at
        }
    }

    %% PostgreSQL Relationships
    User "1" -- "0..*" ChatHistory : có
    User "1" -- "0..*" Bookmark : có
    User "1" -- "0..*" SearchHistory : thực hiện

    %% Neo4j Database Classes (Graph)
    namespace Neo4j_GraphDB {
        class Medicine {
            +String id
            +String name
            +String sub_description
            +String category
            +String description
            +String dosage
            +String sideEffects
            +String contraindications
        }

        class Disease {
            +String id
            +String name
            +String category
            +String severity
            +String description
            +String treatments
        }

        class Ingredient {
            +String id
            +String name
        }

        class Manufacturer {
            +String id
            +String name
            +String country
        }

        class Symptom {
            +String id
            +String name
        }
    }

    %% Neo4j Relationships (Edges)
    Medicine "0..*" --> "1..*" Ingredient : [CONTAINS]
    Medicine "0..*" --> "1" Manufacturer : [MANUFACTURED_BY]
    Disease "0..*" --> "1..*" Symptom : [HAS_SYMPTOM]
    Medicine "0..*" --> "0..*" Disease : [TREATS]
    Medicine "0..*" --> "0..*" Medicine : [INTERACTS_WITH]

    %% Logical Relationships (Cross-DB)
    Bookmark "0..*" ..> "1" Medicine : ánh xạ qua item_neo4j_id
    Bookmark "0..*" ..> "1" Disease : ánh xạ qua item_neo4j_id
```
