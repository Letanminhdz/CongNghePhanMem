"""
Disease lookup service.
Handles disease searches and retrievals.
"""

import logging
from typing import Any

from app.repositories.disease_repository import disease_repository
from app.schemas.disease import DiseaseResponse, DiseaseDetailResponse, DiseaseSearchResponse

logger = logging.getLogger(__name__)


class DiseaseLookupService:
    """Service for disease lookups and searches."""

    def __init__(self):
        self._repository = disease_repository

    def search_diseases(self, query: str, limit: int = 10) -> DiseaseSearchResponse:
        """
        Search for diseases by name or description.
        Returns a DiseaseSearchResponse with matching diseases.
        """
        logger.info(f"Searching diseases with query: '{query}', limit: {limit}")

        try:
            results = self._repository.search_diseases(query, limit=limit)

            diseases = [
                DiseaseResponse(
                    name=disease.get("name", ""),
                    description=disease.get("description"),
                )
                for disease in results
            ]

            logger.info(f"Found {len(diseases)} diseases matching query '{query}'")
            return DiseaseSearchResponse(total=len(diseases), limit=limit, items=diseases)

        except Exception as exc:
            logger.error(f"Error searching diseases: {exc}")
            return DiseaseSearchResponse(total=0, limit=limit, items=[])

    def get_disease_detail(self, disease_name: str) -> DiseaseDetailResponse | None:
        """
        Get full details of a disease including treating drugs.
        Returns DiseaseDetailResponse or None if not found.
        """
        logger.info(f"Fetching details for disease: '{disease_name}'")

        try:
            disease = self._repository.get_disease_by_name(disease_name)
            if not disease:
                logger.warning(f"Disease '{disease_name}' not found")
                return None

            detail = DiseaseDetailResponse(
                name=disease.get("name", ""),
                description=disease.get("description"),
            )

            logger.info(f"Successfully fetched details for disease '{disease_name}'")
            return detail

        except Exception as exc:
            logger.error(f"Error getting disease detail for '{disease_name}': {exc}")
            return None

    def get_treating_drugs(
        self, disease_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get drugs that treat a specific disease.
        """
        logger.info(f"Fetching treating drugs for disease: '{disease_name}'")

        try:
            drugs = self._repository.get_treating_drugs(disease_name, limit=limit)
            logger.info(f"Found {len(drugs)} treating drugs for disease '{disease_name}'")
            return drugs

        except Exception as exc:
            logger.error(
                f"Error getting treating drugs for disease '{disease_name}': {exc}"
            )
            return []


disease_lookup_service = DiseaseLookupService()
