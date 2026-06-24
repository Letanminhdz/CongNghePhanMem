"""
Dịch vụ cơ sở dữ liệu Neo4j.

Xử lý tất cả các thao tác Neo4j với quản lý session chính xác,
xử lý lỗi và ghi log.
"""

import logging
from typing import Any, Optional

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class Neo4jService:
    """Dịch vụ cơ sở dữ liệu Neo4j với mẫu singleton."""

    _instance: Optional["Neo4jService"] = None

    def __new__(cls) -> "Neo4jService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._repository = neo4j_repository

    def verify_connectivity(self) -> bool:
        return self._repository.verify_connectivity()

    # ============================================
    # THAO TÁC TRÊN THUỐC (DRUGS)
    # ============================================

    def merge_drug(self, drug_data: dict[str, Any]) -> bool:
        try:
            # Cơ chế dự phòng cho tên: brand_name -> generic_name -> "Unknown"
            name = drug_data.get("name") or drug_data.get("brand_name") or drug_data.get("generic_name") or "Unknown"
            
            query = """
            MERGE (d:Drug {name: $name})
            SET d.brand_name = $brand_name,
                d.generic_name = $generic_name,
                d.purpose = $purpose,
                d.indications = $indications,
                d.warnings = $warnings,
                d.dosage = $dosage,
                d.contraindications = $contraindications,
                d.adverse_reactions = $adverse_reactions,
                d.updated_at = datetime()
            RETURN d.name AS name
            """
            results = self._repository.execute_write(
                query,
                name=name,
                brand_name=drug_data.get("brand_name"),
                generic_name=drug_data.get("generic_name"),
                purpose=drug_data.get("purpose"),
                indications=drug_data.get("indications"),
                warnings=drug_data.get("warnings"),
                dosage=drug_data.get("dosage"),
                contraindications=drug_data.get("contraindications"),
                adverse_reactions=drug_data.get("adverse_reactions"),
            )
            return bool(results)
        except Exception as e:
            logger.error(f"Error merging drug: {e}")
            return False

    def merge_disease(self, disease_data: dict[str, Any]) -> bool:
        try:
            name = disease_data.get("name")
            if not name:
                return False
            query = """
            MERGE (d:Disease {name: $name})
            SET d.description = $description,
                d.updated_at = datetime()
            RETURN d.name AS name
            """
            results = self._repository.execute_write(
                query,
                name=name,
                description=disease_data.get("description"),
            )
            return bool(results)
        except Exception as e:
            logger.error(f"Error merging disease: {e}")
            return False

    def merge_symptom(self, symptom_data: dict[str, Any]) -> bool:
        try:
            name = symptom_data.get("name")
            if not name:
                return False
            query = """
            MERGE (s:Symptom {name: $name})
            SET s.updated_at = datetime()
            RETURN s.name AS name
            """
            results = self._repository.execute_write(query, name=name)
            return bool(results)
        except Exception as e:
            logger.error(f"Error merging symptom: {e}")
            return False

    def merge_ingredient(self, ingredient_data: dict[str, Any]) -> bool:
        try:
            name = ingredient_data.get("name")
            if not name:
                return False
            query = """
            MERGE (i:Ingredient {name: $name})
            SET i.updated_at = datetime()
            RETURN i.name AS name
            """
            results = self._repository.execute_write(query, name=name)
            return bool(results)
        except Exception as e:
            logger.error(f"Error merging ingredient: {e}")
            return False

    def merge_manufacturer(self, manufacturer_data: dict[str, Any]) -> bool:
        try:
            name = manufacturer_data.get("name")
            if not name:
                return False
            query = """
            MERGE (m:Manufacturer {name: $name})
            SET m.updated_at = datetime()
            RETURN m.name AS name
            """
            results = self._repository.execute_write(query, name=name)
            return bool(results)
        except Exception as e:
            logger.error(f"Error merging manufacturer: {e}")
            return False

    def search_drugs(self, query_text: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Drug)
            WHERE toLower(coalesce(d.name, "")) CONTAINS toLower($search)
               OR toLower(coalesce(d.brand_name, "")) CONTAINS toLower($search)
               OR toLower(coalesce(d.generic_name, "")) CONTAINS toLower($search)
               OR toLower(coalesce(d.purpose, "")) CONTAINS toLower($search)
            RETURN {
                id: id(d),
                name: d.name,
                brand_name: d.brand_name,
                generic_name: d.generic_name,
                purpose: d.purpose
            } AS drug
            LIMIT $limit
            """
            results = self._repository.execute_read(
                query, search=query_text, limit=limit
            )
            return [record["drug"] for record in results]
        except Exception as e:
            logger.error(f"Error searching drugs: {e}")
            return []



    # ============================================
    # THAO TÁC TRÊN BỆNH LÝ (DISEASES)
    # ============================================

    def search_diseases(self, query_text: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Disease)
            WHERE toLower(d.name) CONTAINS toLower($search)
               OR toLower(coalesce(d.description, "")) CONTAINS toLower($search)
            RETURN {
                id: id(d),
                name: d.name,
                description: d.description
            } AS disease
            LIMIT $limit
            """
            results = self._repository.execute_read(
                query, search=query_text, limit=limit
            )
            return [record["disease"] for record in results]
        except Exception as e:
            logger.error(f"Error searching diseases: {e}")
            return []



    def get_subgraph_context(self, drug_names: list[str], disease_names: list[str]) -> list[dict[str, Any]]:
        """
        Tìm kiếm tối ưu hóa 'Graph-First'.
        Lấy tất cả các nút và mối quan hệ liên quan cho nhiều thực thể trong một lần truy vấn duy nhất.
        """
        if not drug_names and not disease_names:
            return []
            
        try:
            logger.info(f"Neo4j subgraph context lookup for drugs={drug_names}, diseases={disease_names}")
            query = """
            MATCH (n)
            WHERE (n:Drug AND (
                toLower(trim(n.name)) IN $drugs
                OR toLower(trim(coalesce(n.brand_name, ''))) IN $drugs
                OR toLower(trim(coalesce(n.generic_name, ''))) IN $drugs
            ))
            OR (n:Disease AND toLower(trim(n.name)) IN $diseases)
            
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE type(r) IN ['TREATS', 'HAS_SYMPTOM', 'CONTAINS', 'MADE_BY', 'INTERACTS_WITH']
            
            RETURN n, labels(n) AS node_labels, collect({
                rel: type(r),
                neighbor_label: labels(m)[0],
                neighbor_name: m.name,
                rel_props: properties(r)
            }) AS connections
            """
            results = self._repository.execute_read(
                query,
                drugs=[d.lower().strip() for d in drug_names],
                diseases=[d.lower().strip() for d in disease_names]
            )
            
            context_data = []
            for record in results:
                node = record["n"]
                node_labels = record.get("node_labels", [])
                conns = record["connections"]
                
                node_data = dict(node)
                node_data["type"] = node_labels[0].lower() if node_labels else "unknown"
                
                # Group connections
                if node_data["type"] == "drug":
                    node_data["ingredients"] = [c["neighbor_name"] for c in conns if c["rel"] == "CONTAINS"]
                    node_data["manufacturers"] = [c["neighbor_name"] for c in conns if c["rel"] == "MADE_BY"]
                    node_data["treated_diseases"] = [c["neighbor_name"] for c in conns if c["rel"] == "TREATS"]
                    node_data["interactions"] = [
                        {"name": c["neighbor_name"], "severity": c["rel_props"].get("severity"), "description": c["rel_props"].get("description")} 
                        for c in conns if c["rel"] == "INTERACTS_WITH"
                    ]
                elif node_data["type"] == "disease":
                    node_data["symptoms"] = [c["neighbor_name"] for c in conns if c["rel"] == "HAS_SYMPTOM"]
                    node_data["treating_drugs"] = [c["neighbor_name"] for c in conns if c["rel"] == "TREATS" and c["neighbor_label"] == "Drug"]
                
                context_data.append(node_data)
            
            return context_data
        except Exception as e:
            logger.error(f"Error getting subgraph context: {e}")
            return []

    # ============================================
    # THAO TÁC TRÊN TƯƠNG TÁC (INTERACTION)
    # ============================================

    def check_drug_interactions(self, drug_names: list[str]) -> list[dict[str, Any]]:
        """
        Kiểm tra tương tác giữa nhiều loại thuốc bằng cách sử dụng một truy vấn Cypher hiệu quả duy nhất.
        """
        if not drug_names or len(drug_names) < 2:
            return []
            
        try:
            query = """
            MATCH (d1:Drug)-[r:INTERACTS_WITH]-(d2:Drug)
            WHERE d1.name IN $names AND d2.name IN $names
              AND id(d1) < id(d2)
            RETURN {
                drug_1: d1.name,
                drug_2: d2.name,
                has_interaction: true,
                severity: r.severity,
                description: r.description
            } AS interaction
            """
            results = self._repository.execute_read(query, names=drug_names)
            return [record["interaction"] for record in results]
        except Exception as e:
            logger.error(f"Error checking interactions: {e}")
            return []

    # ============================================
    # THAO TÁC TRÊN MỐI QUAN HỆ (RELATIONSHIP)
    # ============================================

    def merge_contains_relationship(
        self, drug_name: str, ingredient_name: str
    ) -> bool:
        try:
            query = """
            MERGE (d:Drug {name: $drug_name})
            MERGE (i:Ingredient {name: $ingredient_name})
            MERGE (d)-[:CONTAINS]->(i)
            """
            self._repository.execute_write(
                query,
                drug_name=drug_name.strip(),
                ingredient_name=ingredient_name.strip(),
            )
            return True
        except Exception as e:
            logger.error(f"Error merging CONTAINS relationship: {e}")
            return False

    def merge_made_by_relationship(
        self, drug_name: str, manufacturer_name: str
    ) -> bool:
        try:
            query = """
            MERGE (d:Drug {name: $drug_name})
            MERGE (m:Manufacturer {name: $manufacturer_name})
            MERGE (d)-[:MADE_BY]->(m)
            """
            self._repository.execute_write(
                query,
                drug_name=drug_name.strip(),
                manufacturer_name=manufacturer_name.strip(),
            )
            return True
        except Exception as e:
            logger.error(f"Error merging MADE_BY relationship: {e}")
            return False

    def merge_treats_relationship(
        self, drug_name: str, disease_name: str, source: str = "database_first"
    ) -> bool:
        try:
            query = """
            MERGE (d:Drug {name: $drug_name})
            MERGE (dis:Disease {name: $disease_name})
            MERGE (d)-[r:TREATS]->(dis)
            SET r.source = $source,
                r.updated_at = datetime()
            """
            self._repository.execute_write(
                query,
                drug_name=drug_name.strip(),
                disease_name=disease_name.strip(),
                source=source
            )
            return True
        except Exception as e:
            logger.error(f"Error merging TREATS relationship: {e}")
            return False

    def merge_has_symptom_relationship(
        self, disease_name: str, symptom_name: str, source: str = "database_first"
    ) -> bool:
        try:
            query = """
            MERGE (d:Disease {name: $disease_name})
            MERGE (s:Symptom {name: $symptom_name})
            MERGE (d)-[r:HAS_SYMPTOM]->(s)
            SET r.source = $source,
                r.updated_at = datetime()
            """
            self._repository.execute_write(
                query,
                disease_name=disease_name.strip(),
                symptom_name=symptom_name.strip(),
                source=source
            )
            return True
        except Exception as e:
            logger.error(f"Error merging HAS_SYMPTOM relationship: {e}")
            return False


    def create_interacts_relationship(
        self,
        drug_name_1: str,
        drug_name_2: str,
        severity: str = "moderate",
        description: str = "",
    ) -> bool:
        try:
            query = """
            MERGE (d1:Drug {name: $drug_name_1})
            MERGE (d2:Drug {name: $drug_name_2})
            MERGE (d1)-[r:INTERACTS_WITH]-(d2)
            SET r.severity = $severity,
                r.description = $description,
                r.updated_at = datetime()
            """
            self._repository.execute_write(
                query,
                drug_name_1=drug_name_1.strip(),
                drug_name_2=drug_name_2.strip(),
                severity=severity,
                description=description,
            )
            return True
        except Exception as e:
            logger.error(f"Error creating INTERACTS_WITH relationship: {e}")
            return False

    # ============================================
    # BẢO TRÌ & THỐNG KÊ
    # ============================================

    def rebuild_graph(self) -> bool:
        """Tạo các ràng buộc (constraints) và chỉ mục (indexes) trong Neo4j."""
        try:
            queries = [
                "CREATE CONSTRAINT drug_name IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT ingredient_name IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE",
                "CREATE CONSTRAINT manufacturer_name IF NOT EXISTS FOR (m:Manufacturer) REQUIRE m.name IS UNIQUE",
                "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
                "CREATE INDEX drug_brand_name IF NOT EXISTS FOR (d:Drug) ON (d.brand_name)",
                "CREATE INDEX drug_generic_name IF NOT EXISTS FOR (d:Drug) ON (d.generic_name)",
            ]
            for q in queries:
                self._repository.execute_write(q)
            logger.info("Neo4j constraints and indexes rebuilt successfully.")
            return True
        except Exception as e:
            logger.error(f"Error rebuilding graph: {e}")
            return False

    def cleanup_test_data(self) -> dict[str, int]:
        """Xóa các nút và mối quan hệ thử nghiệm/nháp."""
        try:
            query = """
            MATCH (n)
            WHERE n.name CONTAINS 'test' 
               OR n.name CONTAINS 'demo' 
               OR n.name CONTAINS 'hello'
               OR labels(n)[0] IN ['Test', 'Demo']
            DETACH DELETE n
            RETURN count(*) AS deleted_count
            """
            results = self._repository.execute_write(query)
            count = results[0]["deleted_count"] if results else 0
            logger.info(f"Cleaned up {count} test nodes.")
            return {"deleted_nodes": count}
        except Exception as e:
            logger.error(f"Error cleaning test data: {e}")
            return {"error": str(e)}

    def reset_graph(self, confirm: bool = False) -> dict[str, Any]:
        """Xóa TẤT CẢ các nút và mối quan hệ nếu được xác nhận."""
        if not confirm:
            return {"error": "Confirmation required to reset graph"}
        try:
            query = "MATCH (n) DETACH DELETE n RETURN count(*) AS deleted_count"
            results = self._repository.execute_write(query)
            count = results[0]["deleted_count"] if results else 0
            logger.warning(f"FULL GRAPH RESET: Deleted {count} nodes.")
            return {"success": True, "deleted_nodes": count}
        except Exception as e:
            logger.error(f"Error resetting graph: {e}")
            return {"error": str(e)}

    def get_graph_stats(self) -> dict[str, Any]:
        """Lấy số lượng nhãn, mối quan hệ và các nút cô lập."""
        try:
            # Đếm các nhãn
            try:
                label_results = self._repository.execute_read("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count")
                labels = {r["label"] or "Unknown": r["count"] for r in label_results}
            except Exception:
                labels = {}

            # Đếm các mối quan hệ
            rel_query = "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count"
            rel_results = self._repository.execute_read(rel_query)
            relationships = {r["type"]: r["count"] for r in rel_results}

            # Đếm các nút cô lập
            isolated_query = "MATCH (n) WHERE NOT (n)--() RETURN count(n) AS count"
            isolated_results = self._repository.execute_read(isolated_query)
            isolated_count = isolated_results[0]["count"] if isolated_results else 0

            return {
                "label_counts": labels,
                "relationship_counts": relationships,
                "isolated_nodes_count": isolated_count
            }
        except Exception as e:
            logger.error(f"Error getting graph stats: {e}")
            return {"error": str(e)}

    def get_graph_data(self, limit: int = 100) -> dict[str, list[dict[str, Any]]]:
        """Lấy các nút và mối quan hệ để phục vụ hiển thị trực quan (visualization)."""
        try:
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            WITH n, r, m
            LIMIT $limit
            RETURN n, r, m
            """
            results = self._repository.execute_read(query, limit=limit)
            
            nodes_set = {}
            links = []
            
            for record in results:
                # Xử lý nút nguồn
                n = record.get("n")
                if n:
                    node_id = str(n.element_id) if hasattr(n, "element_id") else str(id(n))
                    if node_id not in nodes_set:
                        nodes_set[node_id] = {
                            "id": node_id,
                            "label": list(n.labels)[0] if n.labels else "Unknown",
                            "properties": dict(n)
                        }
                
                # Xử lý mối quan hệ và nút đích
                r = record.get("r")
                m = record.get("m")
                if r and m:
                    target_id = str(m.element_id) if hasattr(m, "element_id") else str(id(m))
                    if target_id not in nodes_set:
                        nodes_set[target_id] = {
                            "id": target_id,
                            "label": list(m.labels)[0] if m.labels else "Unknown",
                            "properties": dict(m)
                        }
                    links.append({
                        "source": node_id,
                        "target": target_id,
                        "type": r.type,
                        "properties": dict(r)
                    })
            
            return {
                "nodes": list(nodes_set.values()),
                "links": links
            }
        except Exception as e:
            logger.error(f"Error fetching graph data: {e}")
            return {"nodes": [], "links": []}


neo4j_service = Neo4jService()
