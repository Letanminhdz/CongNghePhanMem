import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.config import settings

client = TestClient(app)

@patch("app.services.llm_service.llm_service.generate_response")
def test_chat_interaction_no_auth(mock_llm):
    """Test that chat works without authentication (anonymous)."""
    mock_llm.return_value = "Phản hồi cho người dùng ẩn danh."
    response = client.post(
        f"{settings.API_V1_STR}/chat/",
        json={"message": "Paradol có tác dụng gì?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()

@patch("app.services.llm_service.llm_service.generate_response")
@patch("app.services.ner_service.ner_service.extract_entities")
@patch("app.services.neo4j_service.neo4j_service.get_subgraph_context")
def test_chat_drug_lookup(
    mock_subgraph, 
    mock_ner, 
    mock_llm, 
    client: TestClient, 
    superuser_token_headers: dict
):
    """Test looking up a drug with mock entities and context."""
    # Mock NER
    mock_ner.return_value = {"drugs": ["Paracetamol"], "diseases": []}
    
    # Mock Neo4j Subgraph
    mock_subgraph.return_value = [{
        "name": "Paracetamol",
        "type": "drug",
        "generic_name": "Acetaminophen",
        "purpose": "Giảm đau, hạ sốt",
        "indications": "Đau đầu, sốt",
        "dosage": "500mg mỗi 4-6 giờ",
        "warnings": "Không dùng quá 4g mỗi ngày",
        "ingredients": ["Paracetamol"],
        "manufacturers": ["Generic"]
    }]
    
    # Mock LLM
    mock_llm.return_value = "Paracetamol là thuốc giảm đau hạ sốt phổ biến."

    response = client.post(
        f"{settings.API_V1_STR}/chat/",
        headers=superuser_token_headers,
        json={"message": "Paracetamol dùng để làm gì?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Paracetamol" in data["entities"]
    assert "Neo4j: Drug(Paracetamol)" in data["sources"]
    assert "Paracetamol" in data["answer"]

@patch("app.services.llm_service.llm_service.generate_response")
@patch("app.services.ner_service.ner_service.extract_entities")
def test_chat_unknown_entity(
    mock_ner, 
    mock_llm, 
    client: TestClient, 
    superuser_token_headers: dict
):
    """Test identifying when no entities are found."""
    mock_ner.return_value = {"drugs": [], "diseases": []}
    mock_llm.return_value = "Tôi không tìm thấy thông tin về thực thể bạn hỏi."

    response = client.post(
        f"{settings.API_V1_STR}/chat/",
        headers=superuser_token_headers,
        json={"message": "Blahblah kjsadhf?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["entities"] == []
    assert "AI Base Knowledge" in data["sources"]

@patch("app.services.llm_service.llm_service.generate_response")
@patch("app.services.ner_service.ner_service.extract_entities")
@patch("app.services.neo4j_service.neo4j_service.get_subgraph_context")
def test_chat_drug_interaction(
    mock_subgraph,
    mock_ner, 
    mock_llm, 
    client: TestClient, 
    superuser_token_headers: dict
):
    """Test interaction check between two drugs."""
    mock_ner.return_value = {"drugs": ["DrugA", "DrugB"], "diseases": []}
    
    mock_subgraph.return_value = [
        {
            "name": "DrugA",
            "type": "drug",
            "interactions": [{
                "name": "DrugB",
                "severity": "High",
                "description": "Serious interaction"
            }]
        },
        {
            "name": "DrugB",
            "type": "drug",
            "interactions": [{
                "name": "DrugA",
                "severity": "High",
                "description": "Serious interaction"
            }]
        }
    ]
    
    mock_llm.return_value = "DrugA and DrugB have a high severity interaction."

    response = client.post(
        f"{settings.API_V1_STR}/chat/",
        headers=superuser_token_headers,
        json={"message": "Dùng chung DrugA và DrugB được không?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Neo4j: Drug(DrugA)" in data["sources"]
    assert any("Tương tác (High)" in w for w in data["warnings"])

@patch("app.services.llm_service.llm_service.detect_language")
@patch("app.services.llm_service.llm_service.generate_response")
@patch("app.services.ner_service.ner_service.extract_entities")
def test_chat_multilingual_vi(mock_ner, mock_llm, mock_lang, client: TestClient, superuser_token_headers: dict):
    mock_lang.return_value = "Vietnamese"
    mock_ner.return_value = {"drugs": [], "diseases": []}
    mock_llm.return_value = "Xin chào, tôi là trợ lý y tế."
    
    response = client.post(f"{settings.API_V1_STR}/chat/", headers=superuser_token_headers, json={"message": "Chào bạn"})
    assert "Xin chào" in response.json()["answer"]

@patch("app.services.llm_service.llm_service.detect_language")
@patch("app.services.llm_service.llm_service.generate_response")
def test_chat_multilingual_en(mock_llm, mock_lang, client: TestClient, superuser_token_headers: dict):
    mock_lang.return_value = "English"
    mock_llm.return_value = "Hello, I am your medical assistant."
    
    response = client.post(f"{settings.API_V1_STR}/chat/", headers=superuser_token_headers, json={"message": "Hello"})
    assert "Hello" in response.json()["answer"]

@patch("app.services.llm_service.llm_service.detect_language")
@patch("app.services.llm_service.llm_service.generate_response")
def test_chat_multilingual_fr(mock_llm, mock_lang, client: TestClient, superuser_token_headers: dict):
    mock_lang.return_value = "French"
    mock_llm.return_value = "Bonjour, je suis votre assistant médical."
    
    response = client.post(f"{settings.API_V1_STR}/chat/", headers=superuser_token_headers, json={"message": "Bonjour"})
    assert "Bonjour" in response.json()["answer"]

@patch("app.services.llm_service.llm_service.detect_language")
@patch("app.services.llm_service.llm_service.generate_response")
def test_chat_multilingual_es(mock_llm, mock_lang, client: TestClient, superuser_token_headers: dict):
    mock_lang.return_value = "Spanish"
    mock_llm.return_value = "Hola, soy su asistente médico."
    
    response = client.post(f"{settings.API_V1_STR}/chat/", headers=superuser_token_headers, json={"message": "Hola"})
    assert "Hola" in response.json()["answer"]
@patch("app.services.llm_service.llm_service.generate_response")
def test_chat_anonymous_no_history(mock_llm, db: Session):
    """Test that anonymous chat does not save history."""
    from app.models.chat import ChatHistory
    
    mock_llm.return_value = "Anonymous response"
    count_before = db.query(ChatHistory).count()
    
    response = client.post(
        f"{settings.API_V1_STR}/chat/",
        json={"message": "Anonymous question"}
    )
    
    assert response.status_code == 200
    count_after = db.query(ChatHistory).count()
    assert count_before == count_after

@patch("app.services.llm_service.llm_service.generate_response")
def test_chat_authenticated_saves_history(
    mock_llm, 
    client: TestClient, 
    superuser_token_headers: dict, 
    db: Session
):
    """Test that authenticated chat saves history."""
    from app.models.chat import ChatHistory
    
    mock_llm.return_value = "Authenticated response"
    count_before = db.query(ChatHistory).count()
    
    response = client.post(
        f"{settings.API_V1_STR}/chat/",
        headers=superuser_token_headers,
        json={"message": "Authenticated question"}
    )
    
    assert response.status_code == 200
    count_after = db.query(ChatHistory).count()
    assert count_after == count_before + 1
