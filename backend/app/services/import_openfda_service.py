from typing import Any
import logging

import requests

from app.core.config import settings
from app.services.openfda_neo4j_service import openfda_neo4j_service

logger = logging.getLogger(__name__)


def _extract_first(field_list: Any) -> str:
    """Lấy phần tử đầu tiên của list hoặc trả về chuỗi rỗng."""
    if isinstance(field_list, list) and field_list:
        return field_list[0]
    if isinstance(field_list, str):
        return field_list
    return ""


def import_openfda_drugs(limit: int = 10, skip: int = 0) -> int:
    """
    Gọi openFDA drug label API, parse dữ liệu và import vào Neo4j.
    Trả về số lượng bản ghi đã import.
    """
    url = settings.OPENFDA_DRUG_LABEL_URL
    params = {"limit": limit, "skip": skip}

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    logger.info(f"Fetched {len(results)} drugs from openFDA")

    imported = 0
    for item in results:
        openfda = item.get("openfda", {})

        brand_name = _extract_first(openfda.get("brand_name", []))
        generic_name = _extract_first(openfda.get("generic_name", []))
        manufacturer = _extract_first(openfda.get("manufacturer_name", []))
        purpose = _extract_first(item.get("purpose", []))
        indications = _extract_first(item.get("indications_and_usage", []))
        warnings = _extract_first(item.get("warnings", []))
        dosage = _extract_first(item.get("dosage_and_administration", []))

        if not brand_name:
            continue

        # 1. Merge Drug node
        success = openfda_neo4j_service.merge_drug_to_neo4j(
            name=brand_name,
            brand_name=brand_name,
            generic_name=generic_name,
            manufacturer=manufacturer,
            purpose=purpose,
            indications=indications,
            warnings=warnings,
            dosage=dosage,
        )
        
        if success:
            imported += 1
            # 2. Extract potential Diseases from indications/purpose
            # Simple extraction: look for common patterns or just use the first few words of indications
            # For a more robust solution, we'd use NLP, but for now we'll take keywords
            potential_diseases = []
            if indications:
                # Basic heuristic: if it contains "treatment of", extract what follows
                if "treatment of" in indications.lower():
                    part = indications.lower().split("treatment of")[1].split(".")[0].split(",")[0].strip()
                    if len(part) < 50: # avoid long sentences
                        potential_diseases.append(part.capitalize())
            
            # 3. Merge Disease nodes and create TREATS relationship
            for disease_name in potential_diseases:
                if disease_name:
                    openfda_neo4j_service.merge_disease_to_neo4j(name=disease_name)
                    openfda_neo4j_service.merge_treats_relationship(
                        drug_name=brand_name, 
                        disease_name=disease_name
                    )
                    logger.info(f"Connected Drug({brand_name}) -[:TREATS]-> Disease({disease_name})")
        else:
            logger.warning(f"Failed to insert drug: {brand_name}")

    total_drugs = openfda_neo4j_service.verify_drug_count()
    total_diseases = openfda_neo4j_service.verify_disease_count()
    logger.info("="*60)
    logger.info(f"GRAPH IMPORT COMPLETED:")
    logger.info(f" - New Drugs: {imported}")
    logger.info(f" - Total Drugs: {total_drugs}")
    logger.info(f" - Total Diseases: {total_diseases}")
    logger.info("="*60)
    return imported
