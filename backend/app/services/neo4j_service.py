"""
Neo4j Database Service.

Handles all Neo4j operations with proper session management,
error handling, and logging.
"""

import logging
from typing import Any, Optional

from app.repositories.neo4j_repository import neo4j_repository

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j database service with singleton pattern."""

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
    # DRUG OPERATIONS
    # ============================================

    def merge_drug(self, drug_data: dict[str, Any]) -> bool:
        try:
            query = """
            MERGE (d:Drug {name: $name})
            SET d.generic_name = $generic_name,
                d.purpose = $purpose,
                d.indications = $indications,
                d.warnings = $warnings,
                d.dosage = $dosage,
                d.updated_at = datetime()
            RETURN d.name AS name
            """
            results = self._repository.execute_write(
                query,
                name=drug_data.get("name", ""),
                generic_name=drug_data.get("generic_name"),
                purpose=drug_data.get("purpose"),
                indications=drug_data.get("indications"),
                warnings=drug_data.get("warnings"),
                dosage=drug_data.get("dosage"),
            )
            return bool(results)
        except Exception as e:
            logger.error(f"Error merging drug: {e}")
            return False

    def search_drugs(self, query_text: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Drug)
            WHERE toLower(d.name) CONTAINS toLower($search)
               OR toLower(coalesce(d.generic_name, "")) CONTAINS toLower($search)
               OR toLower(coalesce(d.purpose, "")) CONTAINS toLower($search)
            RETURN {
                id: id(d),
                name: d.name,
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

    def get_drug_detail(self, drug_name: str) -> Optional[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Drug)
            WHERE toLower(trim(d.name)) = toLower(trim($name))

            OPTIONAL MATCH (d)-[:CONTAINS]->(i:Ingredient)
            WITH d,
            collect(DISTINCT {
                id: id(i),
                name: i.name
            }) AS ingredients

            OPTIONAL MATCH (d)-[:MADE_BY]->(m:Manufacturer)
            WITH d, ingredients,
            collect(DISTINCT {
                id: id(m),
                name: m.name
            }) AS manufacturers

            OPTIONAL MATCH (d)-[r:INTERACTS_WITH]-(other:Drug)
            WITH d, ingredients, manufacturers,
            collect(DISTINCT {
                id: id(other),
                name: other.name,
                severity: r.severity,
                description: r.description
            }) AS interactions

            RETURN {
                id: id(d),
                name: d.name,
                generic_name: d.generic_name,
                purpose: d.purpose,
                indications: d.indications,
                warnings: d.warnings,
                dosage: d.dosage,
                ingredients: ingredients,
                manufacturers: manufacturers,
                interactions: interactions
            } AS detail
            """
            results = self._repository.execute_read(query, name=drug_name)
            
            logger.info(f"Neo4j query (drug) results count: {len(results)}")
            if not results:
                return None

            detail = dict(results[0]["detail"])
            logger.info(f"Neo4j detail keys: {list(detail.keys())}")
                
            detail["ingredients"] = [
                item for item in detail.get("ingredients", []) if item and item.get("name")
            ]
            detail["manufacturers"] = [
                item for item in detail.get("manufacturers", []) if item and item.get("name")
            ]
            detail["interactions"] = [
                item
                for item in detail.get("interactions", [])
                if item and item.get("name")
            ]
            return detail
        except Exception as e:
            logger.error(f"Error getting drug detail for '{drug_name}': {e}")
            return None

    # ============================================
    # DISEASE OPERATIONS
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

    def get_disease_symptoms(self, disease_name: str) -> Optional[dict[str, Any]]:
        try:
            query = """
            MATCH (d:Disease)
            WHERE toLower(trim(d.name)) = toLower(trim($name))
            OPTIONAL MATCH (d)-[:RELATED_TO]->(s:Symptom)
            RETURN {
                id: id(d),
                name: d.name,
                description: d.description,
                symptoms: collect(distinct {id: id(s), name: s.name})
            } AS disease
            """
            results = self._repository.execute_read(query, name=disease_name)
            
            logger.info(f"Neo4j query (disease) results count: {len(results)}")
            if not results:
                return None
                
            disease = results[0].get("disease")
            logger.info(f"Raw Neo4j disease type: {type(disease)}")
            
            # Robust conversion to dict
            if disease is not None:
                disease = dict(disease)
            else:
                return None
                
            disease["symptoms"] = [
                item for item in disease.get("symptoms", []) if item and item.get("name")
            ]
            return disease
        except Exception as e:
            logger.error(f"Error getting disease symptoms for '{disease_name}': {e}")
            return None

    # ============================================
    # INTERACTION OPERATIONS
    # ============================================

    def check_drug_interactions(self, drug_names: list[str]) -> list[dict[str, Any]]:
        """
        Check interactions between multiple drugs using a single efficient Cypher query.
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
    # RELATIONSHIP OPERATIONS
    # ============================================

    # ============================================
    # RELATIONSHIP OPERATIONS
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
        self, drug_name: str, disease_name: str, source: str = "openFDA_heuristic"
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
        self, disease_name: str, symptom_name: str, source: str = "openFDA_heuristic"
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

    def merge_side_effect_relationship(
        self, drug_name: str, side_effect_name: str, source: str = "openFDA_heuristic"
    ) -> bool:
        try:
            query = """
            MERGE (d:Drug {name: $drug_name})
            MERGE (s:SideEffect {name: $side_effect_name})
            MERGE (d)-[r:HAS_SIDE_EFFECT]->(s)
            SET r.source = $source,
                r.updated_at = datetime()
            """
            self._repository.execute_write(
                query,
                drug_name=drug_name.strip(),
                side_effect_name=side_effect_name.strip(),
                source=source
            )
            return True
        except Exception as e:
            logger.error(f"Error merging HAS_SIDE_EFFECT relationship: {e}")
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
    # MAINTENANCE & STATS
    # ============================================

    def rebuild_graph(self) -> bool:
        """Create constraints and indexes in Neo4j."""
        try:
            queries = [
                "CREATE CONSTRAINT drug_name IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
                "CREATE CONSTRAINT ingredient_name IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE",
                "CREATE CONSTRAINT manufacturer_name IF NOT EXISTS FOR (m:Manufacturer) REQUIRE m.name IS UNIQUE",
                "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
                "CREATE CONSTRAINT side_effect_name IF NOT EXISTS FOR (s:SideEffect) REQUIRE s.name IS UNIQUE",
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
        """Remove test/dummy nodes and relationships."""
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
        """Delete ALL nodes and relationships if confirmed."""
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
        """Get counts of labels, relationships, and isolated nodes."""
        try:
            # Count labels
            try:
                label_results = self._repository.execute_read("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count")
                labels = {r["label"] or "Unknown": r["count"] for r in label_results}
            except Exception:
                labels = {}

            # Count relationships
            rel_query = "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count"
            rel_results = self._repository.execute_read(rel_query)
            relationships = {r["type"]: r["count"] for r in rel_results}

            # Count isolated nodes
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
        """Fetch nodes and relationships for visualization."""
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
                # Process source node
                n = record.get("n")
                if n:
                    node_id = str(n.element_id) if hasattr(n, "element_id") else str(id(n))
                    if node_id not in nodes_set:
                        nodes_set[node_id] = {
                            "id": node_id,
                            "label": list(n.labels)[0] if n.labels else "Unknown",
                            "properties": dict(n)
                        }
                
                # Process relationship and target node
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
