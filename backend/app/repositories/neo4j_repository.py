import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

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
            
        # Optimize driver for local container/bolt usage
        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=30,
            keep_alive=True
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
            raise ImportError("Neo4j driver is not installed.") from exc

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
            raise ImportError("Neo4j driver is not installed.") from exc

        try:
            self._ensure_driver()
            with self._driver.session() as session:
                result = session.run(query, **params)
                return [record.data() for record in result]
        except Neo4jError as error:
            logger.error(f"Neo4j write error: {error}")
            raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=False
    )
    def verify_connectivity(self) -> bool:
        """
        Verify connection to Neo4j with retries.
        Helpful during startup when Neo4j container might be booting.
        """
        try:
            self._ensure_driver()
            with self._driver.session() as session:
                result = session.run("RETURN 1 AS result")
                record = result.single()
                return record is not None and record["result"] == 1
        except Exception as error:
            # We log as warning because tenacity will retry
            logger.warning(f"Neo4j connectivity attempt failed: {error}")
            return False


neo4j_repository = Neo4jRepository()
