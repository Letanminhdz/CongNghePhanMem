import os
import sys
from pathlib import Path

# Add the backend directory to sys.path
backend_path = Path(__file__).parent.absolute()
sys.path.append(str(backend_path))

def audit_imports():
    print("Starting import audit...")
    modules_to_test = [
        "app.main",
        "app.api.v1.api",
        "app.api.v1.endpoints.deps",
        "app.api.v1.endpoints.auth",
        "app.api.v1.endpoints.debug",
        "app.api.v1.endpoints.chat",
        "app.api.v1.endpoints.users",
        "app.api.v1.endpoints.medicines",
        "app.api.v1.endpoints.diseases",
        "app.api.v1.endpoints.bookmarks",
        "app.repositories.user_repository",
        "app.repositories.drug_repository",
        "app.repositories.disease_repository",
        "app.services.llm_service",
        "app.services.chat_service",
        "app.models.user",
    ]

    success_count = 0
    failures = []

    for module_name in modules_to_test:
        try:
            print(f"Testing import: {module_name}...", end=" ")
            __import__(module_name)
            print("OK")
            success_count += 1
        except Exception as e:
            print("FAILED")
            failures.append((module_name, str(e), type(e).__name__))
            # We continue even after failure to find more errors if they aren't blocking
            # but usually an import error blocks subsequent imports if they depend on it

    print(f"\nAudit finished. Success: {success_count}/{len(modules_to_test)}")
    if failures:
        print("\nFailures:")
        for mod, err, err_type in failures:
            print(f"  - {mod}: [{err_type}] {err}")
        return False
    return True

if __name__ == "__main__":
    # Mock environment variables if needed
    os.environ["SECRET_KEY"] = "test_secret"
    os.environ["POSTGRES_SERVER"] = "localhost"
    os.environ["POSTGRES_USER"] = "postgres"
    os.environ["POSTGRES_PASSWORD"] = "password"
    os.environ["POSTGRES_DB"] = "db"
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    
    if audit_imports():
        sys.exit(0)
    else:
        sys.exit(1)
