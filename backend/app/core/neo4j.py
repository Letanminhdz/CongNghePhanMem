from collections.abc import Generator

from neo4j import Driver, GraphDatabase, Session

from app.core.config import settings

driver: Driver = GraphDatabase.driver(
    settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
)


def get_neo4j_session() -> Generator[Session, None, None]:
    with driver.session() as session:
        yield session
