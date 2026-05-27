from typing import Any
import logging
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings
from app.services.neo4j_service import neo4j_service
from app.services.openfda_neo4j_service import openfda_neo4j_service

logger = logging.getLogger(__name__)


def _create_session_with_retry() -> requests.Session:
    """Create a requests session with retry strategy."""
    session = requests.Session()
    
    # Retry strategy for transient failures
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def _extract_first(field_list: Any) -> str:
    """Extract first element from list or return string as-is."""
    if isinstance(field_list, list) and field_list:
        return str(field_list[0]).strip()
    if isinstance(field_list, str):
        return field_list.strip()
    return ""


def _extract_active_ingredients(item: dict) -> list[str]:
    """Extract active ingredients from drug item."""
    ingredients = []
    
    # Try to get from active_ingredient field
    if "active_ingredient" in item:
        active_ing = item.get("active_ingredient", [])
        if isinstance(active_ing, list):
            for ing in active_ing:
                if isinstance(ing, dict) and "activeIngredientName" in ing:
                    ing_name = ing.get("activeIngredientName", "").strip()
                    if ing_name:
                        ingredients.append(ing_name)
                elif isinstance(ing, str):
                    ing_name = ing.strip()
                    if ing_name:
                        ingredients.append(ing_name)
    
    # Try to get from openfda.substance_name
    openfda = item.get("openfda", {})
    substance_names = openfda.get("substance_name", [])
    if isinstance(substance_names, list):
        for sub in substance_names:
            sub_name = str(sub).strip()
            if sub_name and sub_name not in ingredients:
                ingredients.append(sub_name)
    
    return ingredients


def _extract_entities(text: str, keywords: list[str]) -> list[str]:
    """
    Extract entities from text following specific keywords using heuristics.
    Used for Symptoms, Side Effects, and Diseases.
    """
    if not text:
        return []
        
    entities = []
    # Normalize text
    text = text.replace("\n", " ").replace("\r", " ")
    
    for kw in keywords:
        # Case insensitive search
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        matches = pattern.finditer(text)
        
        for match in matches:
            start = match.end()
            # Extract next ~100 chars
            segment = text[start:start+100].strip()
            
            # Split by common delimiters (comma, semi-colon, period, 'and')
            parts = re.split(r'[,.;]|\band\b', segment)
            
            if parts:
                candidate = parts[0].strip()
                # Basic validation: not a single word (usually too generic) or too long
                if 2 < len(candidate) < 50:
                    # Further cleanup
                    candidate = re.sub(r'\(.*?\)', '', candidate).strip()
                    if candidate and candidate.lower() not in ["", "none", "unknown"]:
                        entities.append(candidate.title())
                        
    return list(set(entities))[:5] # Limit to 5 unique per keyword occurrence


def import_openfda_drugs(limit: int = 10, skip: int = 0) -> int:
    """
    Fetch drugs from openFDA API and import them into Neo4j.
    """
    url = settings.OPENFDA_DRUG_LABEL_URL
    params = {"limit": limit, "skip": skip}

    logger.info(f"Fetching openFDA drugs: limit={limit}, skip={skip}")

    session = _create_session_with_retry()
    
    try:
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error(f"Failed to fetch openFDA data: {exc}")
        return 0
    finally:
        session.close()

    try:
        data = response.json()
    except ValueError as exc:
        logger.error(f"Failed to parse openFDA response: {exc}")
        return 0

    results = data.get("results", [])
    logger.info(f"Fetched {len(results)} drugs from openFDA")

    imported = 0
    source_attr = "openFDA_import_v2"

    for idx, item in enumerate(results, start=1):
        try:
            openfda = item.get("openfda", {})
            brand_name = _extract_first(openfda.get("brand_name", []))
            generic_name = _extract_first(openfda.get("generic_name", []))
            manufacturer = _extract_first(openfda.get("manufacturer_name", []))
            
            indications = _extract_first(item.get("indications_and_usage", []))
            warnings = _extract_first(item.get("warnings", []))
            dosage = _extract_first(item.get("dosage_and_administration", []))
            adverse_reactions = _extract_first(item.get("adverse_reactions", []))

            # Drug identifier
            drug_name = brand_name or generic_name
            if not drug_name:
                continue

            # 1. Merge Drug
            success = neo4j_service.merge_drug({
                "name": drug_name,
                "generic_name": generic_name,
                "purpose": _extract_first(item.get("purpose", [])),
                "indications": indications,
                "warnings": warnings,
                "dosage": dosage,
            })

            if not success:
                continue
            imported += 1

            # 2. Ingredients
            for ing in _extract_active_ingredients(item):
                neo4j_service.merge_contains_relationship(drug_name, ing)

            # 3. Manufacturer
            if manufacturer:
                neo4j_service.merge_made_by_relationship(drug_name, manufacturer)

            # 4. Diseases (TREATS)
            disease_kws = ["treatment of", "indicated for", "relief of", "prevention of"]
            extracted_diseases = _extract_entities(indications, disease_kws)
            for disease in extracted_diseases:
                neo4j_service.merge_treats_relationship(drug_name, disease, source=source_attr)
                
                # 5. Symptoms (HAS_SYMPTOM) - experimental link from disease text
                symptom_kws = ["associated with", "characterized by", "symptoms include"]
                extracted_symptoms = _extract_entities(indications, symptom_kws)
                for symptom in extracted_symptoms:
                    neo4j_service.merge_has_symptom_relationship(disease, symptom, source=source_attr)

            # 6. Side Effects (HAS_SIDE_EFFECT)
            se_kws = ["common side effects", "may cause", "adverse reactions include"]
            extracted_se = _extract_entities(adverse_reactions or warnings, se_kws)
            for se in extracted_se:
                neo4j_service.merge_side_effect_relationship(drug_name, se, source=source_attr)

        except Exception as exc:
            logger.error(f"Error processing drug {idx}: {exc}")

    # Stats sync
    openfda_neo4j_service.verify_drug_count() 
    
    return imported


def _extract_diseases_from_indications(indications: str) -> list[str]:
    """
    Extract disease names from indications text using simple heuristics.
    
    This is a basic implementation. For production,
    consider using NLP or a disease name entity recognizer.
    """
    if not indications:
        return []

    diseases = []
    
    # Common disease patterns
    disease_keywords = [
        "treatment of",
        "treatment for",
        "used for",
        "indicated for",
        "indication:",
    ]

    lower_text = indications.lower()
    
    for keyword in disease_keywords:
        if keyword in lower_text:
            # Extract text after keyword
            parts = lower_text.split(keyword)
            if len(parts) > 1:
                text_after = parts[1].strip()
                # Get first sentence or up to 100 characters
                disease_text = (
                    text_after.split(".")[0]
                    .split(",")[0]
                    .strip()[:100]
                )
                if len(disease_text) > 3:  # Avoid very short matches
                    # Capitalize properly
                    disease_name = " ".join(
                        word.capitalize() for word in disease_text.split()
                    )
                    if disease_name not in diseases:
                        diseases.append(disease_name)
    
    return diseases[:5]  # Limit to 5 diseases per drug

