import pytest
from app.services.ner_service import ner_service

def test_normalization():
    assert ner_service._normalize_text("Paracetamol, 500mg!") == "paracetamol 500mg"
    assert ner_service._normalize_text("Đau đầu chóng mặt?") == "dau dau chong mat"

def test_levenshtein():
    # Exact match
    assert ner_service._levenshtein_distance("paracetamol", "paracetamol") == 0
    # 1 typo
    assert ner_service._levenshtein_distance("paracetamon", "paracetamol") == 1
    # 2 typos
    assert ner_service._levenshtein_distance("paracetamox", "paracetamol") == 2

def test_extract_entities_fuzzy():
    # Mock some data in ner_service
    ner_service.drug_names = {"Paracetamol", "Aspirin", "Ibuprofen"}
    ner_service.disease_names = {"Headache", "Flu", "Sốt xuất huyết"}
    
    # Test English fuzzy
    result = ner_service.extract_entities("I have a paracetamon")
    assert "Paracetamol" in result["drugs"]
    
    # Test Vietnamese fuzzy (simple)
    ner_service.disease_names.add("Sot")
    result = ner_service.extract_entities("Tôi bị sot")
    assert "Sot" in result["diseases"]

def test_accent_insensitive_and_exact_extract():
    ner_service.drug_names = {"Paracetamol", "Aspirin", "Ibuprofen"}
    ner_service.disease_names = {"Đau đầu", "Cảm cúm", "Sốt xuất huyết"}
    
    # Accent-insensitive and exact match
    result = ner_service.extract_entities("Tôi bị dau dau va muon uong paracetamol")
    assert "Paracetamol" in result["drugs"]
    assert "Đau đầu" in result["diseases"]
