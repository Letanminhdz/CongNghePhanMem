"""
OpenFDA to Neo4j integration service.
Handles merging drug data into Neo4j with detailed logging.
"""

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenFDANeo4jService:
    """Service for importing OpenFDA drugs into Neo4j with proper session management."""

    def __init__(self) -> None:
        self._driver = None

    def _ensure_driver(self) -> None:
        """Lazily initialize Neo4j driver."""
        if self._driver is not None:
            return
        if not settings.NEO4J_URI:
            raise ValueError("NEO4J_URI is not configured")
        try:
            from neo4j import GraphDatabase  # type: ignore[import]

        except ImportError as exc:
            raise ImportError(
                "Neo4j driver is not installed. Install with `pip install neo4j`."
            ) from exc

        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        )
        logger.info("Neo4j driver initialized")

    def merge_drug_to_neo4j(
        self,
        name: str,
        brand_name: str = "",
        generic_name: str = "",
        manufacturer: str = "",
        purpose: str = "",
        indications: str = "",
        warnings: str = "",
        dosage: str = "",
    ) -> bool:
        """
        Merge a drug node into Neo4j using MERGE to avoid duplicates.
        Returns True if successful, False otherwise.
        """
        try:
            self._ensure_driver()

            # Use 'name' as unique identifier for the drug
            query = """
            MERGE (d:Drug {name: $name})
            SET
                d.brand_name = $brand_name,
                d.generic_name = $generic_name,
                d.manufacturer = $manufacturer,
                d.purpose = $purpose,
                d.indications = $indications,
                d.warnings = $warnings,
                d.dosage = $dosage,
                d.updated_at = datetime()
            RETURN d.name AS name
            """

            with self._driver.session() as session:
                result = session.run(
                    query,
                    name=name,
                    brand_name=brand_name or "",
                    generic_name=generic_name or "",
                    manufacturer=manufacturer or "",
                    purpose=purpose or "",
                    indications=indications or "",
                    warnings=warnings or "",
                    dosage=dosage or "",
                )
                # Consume result to ensure execution
                record = result.single()
                if record:
                    logger.debug(f"Merged drug node: {record['name']}")
                    return True
                return False

        except Exception as exc:
            logger.error(f"Neo4j write error for drug '{name}': {exc}")
            return False

    def verify_drug_count(self) -> int:
        """Query Neo4j to count total Drug nodes."""
        try:
            self._ensure_driver()

            with self._driver.session() as session:
                result = session.run("MATCH (d:Drug) RETURN COUNT(d) AS count")
                record = result.single()
                if record:
                    count = record["count"]
                    logger.info(f"Total Drug nodes in Neo4j: {count}")
                    return count
                return 0

        except Exception as exc:
            logger.error(f"Failed to count Drug nodes: {exc}")
            return 0

    def merge_disease_to_neo4j(
        self,
        name: str,
        description: str = "",
        icd_code: str = "",
    ) -> bool:
        """
        Merge a disease node into Neo4j.
        Returns True if successful, False otherwise.
        """
        try:
            self._ensure_driver()

            query = """
            MERGE (d:Disease {name: $name})
            SET
                d.description = $description,
                d.icd_code = $icd_code,
                d.updated_at = datetime()
            RETURN d.name AS name
            """

            with self._driver.session() as session:
                result = session.run(
                    query,
                    name=name,
                    description=description or "",
                    icd_code=icd_code or "",
                )
                record = result.single()
                if record:
                    logger.debug(f"Merged disease node: {record['name']}")
                    return True
                return False

        except Exception as exc:
            logger.error(f"Neo4j write error for disease '{name}': {exc}")
            return False

    def merge_treats_relationship(self, drug_name: str, disease_name: str) -> bool:
        """
        Create a TREATS relationship: (Drug)-[:TREATS]->(Disease).
        Returns True if successful, False otherwise.
        """
        try:
            self._ensure_driver()

            query = """
            MATCH (drug:Drug {name: $drug_name})
            MATCH (disease:Disease {name: $disease_name})
            MERGE (drug)-[r:TREATS]->(disease)
            SET r.created_at = datetime()
            RETURN r
            """

            with self._driver.session() as session:
                result = session.run(query, drug_name=drug_name, disease_name=disease_name)
                record = result.single()
                if record:
                    logger.debug(f"Created TREATS relationship: {drug_name} -> {disease_name}")
                    return True
                return False

        except Exception as exc:
            logger.error(f"Failed to create TREATS relationship: {exc}")
            return False

    def verify_disease_count(self) -> int:
        """Query Neo4j to count total Disease nodes."""
        try:
            self._ensure_driver()

            with self._driver.session() as session:
                result = session.run("MATCH (d:Disease) RETURN COUNT(d) AS count")
                record = result.single()
                if record:
                    count = record["count"]
                    logger.info(f"Total Disease nodes in Neo4j: {count}")
                    return count
                return 0

        except Exception as exc:
            logger.error(f"Failed to count Disease nodes: {exc}")
            return 0

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed")


openfda_neo4j_service = OpenFDANeo4jService()
