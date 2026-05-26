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
        else:
            logger.warning(f"Failed to insert drug: {brand_name}")

    logger.info(f"Inserted {imported} Drug nodes into Neo4j")
    return imported
