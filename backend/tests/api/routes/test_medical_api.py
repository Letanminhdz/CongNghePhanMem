import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.config import settings

client = TestClient(app)

@patch("app.services.medicine_lookup_service.medicine_lookup_service.search_medicines")
def test_search_drugs_pagination(mock_search, superuser_token_headers):
    """Test drug search pagination validation."""
    mock_search.return_value = {"total": 0, "limit": 10, "items": []}
    
    # Test valid
    response = client.get(
        f"{settings.API_V1_STR}/medicines/search?q=aspirin&limit=20&skip=5",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    mock_search.assert_called_with(query="aspirin", limit=20, skip=5)

    # Test invalid limit
    response = client.get(
        f"{settings.API_V1_STR}/medicines/search?q=aspirin&limit=101",
        headers=superuser_token_headers
    )
    assert response.status_code == 422

@patch("app.services.disease_lookup_service.disease_lookup_service.search_diseases")
def test_search_diseases_pagination(mock_search, superuser_token_headers):
    """Test disease search pagination validation."""
    mock_search.return_value = {"total": 0, "limit": 10, "items": []}
    
    response = client.get(
        f"{settings.API_V1_STR}/diseases/search?q=flu&limit=5&skip=0",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    mock_search.assert_called_with(query="flu", limit=5, skip=0)

@patch("app.services.drug_interaction_service.drug_interaction_service.check_multiple_interactions")
def test_drug_interaction_api(mock_check, superuser_token_headers):
    """Test drug interaction API."""
    mock_check.return_value = {"results": []}
    
    response = client.post(
        f"{settings.API_V1_STR}/interactions/check",
        headers=superuser_token_headers,
        json={"drug_names": ["A", "B"]}
    )
    assert response.status_code == 200
    mock_check.assert_called_with(["A", "B"])

def test_cypher_injection_prevention_logic():
    """
    This test verifies that the repo uses parameters.
    We check the source code of the repository to ensure f-strings are not used for drug names.
    """
    from app.repositories.drug_repository import DrugRepository
    import inspect
    
    source = inspect.getsource(DrugRepository.check_multiple_drug_interactions)
    assert "IN $drug_names" in source
    assert "f\"" not in source or "drug_names" not in source # Basic check
