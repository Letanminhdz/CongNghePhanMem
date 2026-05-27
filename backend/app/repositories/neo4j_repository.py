"""
Neo4j repository layer.
"""

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jRepository:
    """Handles low-level Neo4j driver operations."""

    def __init__(self) -> None:
        self._driver = None

    def _ensure_driver(self) -> None:
        if self._driver is not None:
            return
        if not settings.NEO4J_URI:
            raise ValueError("NEO4J_URI is not configured")
        try:
            from neo4j import GraphDatabase  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "Neo4j support is unavailable because the neo4j driver is not installed. "
                "Install it with `pip install neo4j`."
            ) from exc
        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        )

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j repository closed")

    def execute_read(self, query: str, **params: Any) -> list[dict]:
        try:
            from neo4j.exceptions import Neo4jError  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "Neo4j support is unavailable because the neo4j driver is not installed. "
                "Install it with `pip install neo4j`."
            ) from exc

        try:
            self._ensure_driver()
            with self._driver.session() as session:
                result = session.run(query, **params)
                return [record.data() for record in result]
        except Neo4jError as error:
            logger.error(f"Neo4j read error: {error}")
            raise

    def execute_write(self, query: str, **params: Any) -> list[dict]:
        try:
            from neo4j.exceptions import Neo4jError  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "Neo4j support is unavailable because the neo4j driver is not installed. "
                "Install it with `pip install neo4j`."
            ) from exc

        try:
            self._ensure_driver()
            with self._driver.session() as session:
                result = session.run(query, **params)
                return [record.data() for record in result]
        except Neo4jError as error:
            logger.error(f"Neo4j write error: {error}")
            raise

    def verify_connectivity(self) -> bool:
        try:
            from neo4j.exceptions import Neo4jError  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "Neo4j support is unavailable because the neo4j driver is not installed. "
                "Install it with `pip install neo4j`."
            ) from exc

        try:
            self._ensure_driver()
            with self._driver.session() as session:
                result = session.run("RETURN 1 AS result")
                record = result.single()
                return record is not None and record["result"] == 1
        except Neo4jError as error:
            logger.error(f"Neo4j connectivity error: {error}")
            return False


neo4j_repository = Neo4jRepository()
