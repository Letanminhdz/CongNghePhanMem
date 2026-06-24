from app.repositories.neo4j_repository import neo4j_repository
print(neo4j_repository.execute_read("MATCH (n) RETURN count(n) as c"))
