from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings


def test_search_drugs_route_returns_items(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.medicines.medicine_lookup_service.search_medicines",
        return_value={
            "query": "aspirin",
            "limit": 5,
            "skip": 0,
            "total": 1,
            "items": [
                {
                    "name": "Aspirin",
                    "generic_name": "Acetylsalicylic Acid",
                    "purpose": "Pain relief",
                }
            ]
        },
    ):
        response = client.get(
            f"{settings.API_V1_STR}/medicines/search",
            params={"q": "aspirin", "limit": 5},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["name"] == "Aspirin"


def test_get_drug_detail_route_returns_404_when_missing(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.medicines.medicine_lookup_service.get_medicine_detail",
        return_value=None,
    ):
        response = client.get(f"{settings.API_V1_STR}/medicines/UnknownDrug/detail")
    assert response.status_code == 404
    assert response.json()["detail"] == "Medicine 'UnknownDrug' not found"


def test_check_interactions_route_returns_results(client: TestClient) -> None:
    from app.schemas.interaction import InteractionCheckResponse, InteractionResult
    with patch(
        "app.api.v1.endpoints.interactions.drug_interaction_service.check_multiple_interactions",
        return_value=InteractionCheckResponse(
            results=[
                InteractionResult(
                    drug_1="Aspirin",
                    drug_2="Ibuprofen",
                    has_interaction=True,
                    severity="high",
                    description="Increased bleeding risk",
                )
            ]
        ),
    ):
        response = client.post(
            f"{settings.API_V1_STR}/interactions/check",
            json={"drug_names": ["Aspirin", "Ibuprofen"]},
        )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 1
    assert payload["results"][0]["has_interaction"] is True
    assert payload["results"][0]["severity"] == "high"
