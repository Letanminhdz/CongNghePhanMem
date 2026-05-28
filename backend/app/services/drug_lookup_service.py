"""
Drug lookup service.
Handles drug searches and retrievals.
"""

import logging
from typing import Any

from app.repositories.drug_repository import drug_repository
from app.schemas.drug import DrugResponse, DrugDetailResponse, DrugSearchResponse

logger = logging.getLogger(__name__)


class DrugLookupService:
    """Service for drug lookups and searches."""

    def __init__(self):
        self._repository = drug_repository

    def search_drugs(self, query: str, limit: int = 10) -> DrugSearchResponse:
        """
        Search for drugs by name, brand name, or generic name.
        Returns a DrugSearchResponse with matching drugs.
        """
        logger.info(f"Searching drugs with query: '{query}', limit: {limit}")

        try:
            results = self._repository.search_drugs(query, limit=limit)
            
            drugs = [
                DrugResponse(
                    name=drug.get("name", ""),
                    generic_name=drug.get("generic_name"),
                    purpose=drug.get("purpose"),
                    indications=drug.get("indications"),
                    warnings=drug.get("warnings"),
                    dosage=drug.get("dosage"),
                )
                for drug in results
            ]

            logger.info(f"Found {len(drugs)} drugs matching query '{query}'")
            return DrugSearchResponse(total=len(drugs), limit=limit, items=drugs)

        except Exception as exc:
            logger.error(f"Error searching drugs: {exc}")
            return DrugSearchResponse(total=0, limit=limit, items=[])

    def get_drug_detail(self, drug_name: str) -> DrugDetailResponse | None:
        """
        Get full details of a drug including ingredients, manufacturers, and interactions.
        Returns DrugDetailResponse or None if not found.
        """
        logger.info(f"Fetching details for drug: '{drug_name}'")

        try:
            drug = self._repository.get_drug_by_name(drug_name)
            if not drug:
                logger.warning(f"Drug '{drug_name}' not found")
                return None

            # Transform ingredients
            ingredients = [
                {"name": ing, "description": None}
                for ing in (drug.get("ingredients") or [])
                if ing
            ]

            # Transform manufacturers
            manufacturers = [
                {"name": mfr, "country": None}
                for mfr in (drug.get("manufacturers") or [])
                if mfr
            ]

            # Transform interactions
            interactions = [
                {
                    "name": inter.get("name", ""),
                    "severity": inter.get("severity", "unknown"),
                }
                for inter in (drug.get("interactions") or [])
                if inter and inter.get("name")
            ]

            detail = DrugDetailResponse(
                name=drug.get("name", ""),
                generic_name=drug.get("generic_name"),
                purpose=drug.get("purpose"),
                indications=drug.get("indications"),
                warnings=drug.get("warnings"),
                dosage=drug.get("dosage"),
                ingredients=ingredients,
                manufacturers=manufacturers,
                interactions=interactions,
            )

            logger.info(f"Successfully fetched details for drug '{drug_name}'")
            return detail

        except Exception as exc:
            logger.error(f"Error getting drug detail for '{drug_name}': {exc}")
            return None

    def get_drug_ingredients(self, drug_name: str) -> list[dict[str, Any]]:
        """
        Get all ingredients in a drug.
        """
        logger.info(f"Fetching ingredients for drug: '{drug_name}'")

        try:
            ingredients = self._repository.get_drug_ingredients(drug_name)
            logger.info(f"Found {len(ingredients)} ingredients for drug '{drug_name}'")
            return ingredients

        except Exception as exc:
            logger.error(f"Error getting ingredients for drug '{drug_name}': {exc}")
            return []

    def get_drugs_by_disease(
        self, disease_name: str, limit: int = 10
    ) -> DrugSearchResponse:
        """
        Get drugs that treat a specific disease.
        """
        logger.info(f"Fetching drugs for disease: '{disease_name}'")

        try:
            results = self._repository.get_drugs_by_disease(disease_name, limit=limit)

            drugs = [
                DrugResponse(
                    name=drug.get("name", ""),
                    generic_name=drug.get("generic_name"),
                    dosage=drug.get("dosage"),
                )
                for drug in results
            ]

            logger.info(f"Found {len(drugs)} drugs for disease '{disease_name}'")
            return DrugSearchResponse(total=len(drugs), limit=limit, items=drugs)

        except Exception as exc:
            logger.error(f"Error getting drugs for disease '{disease_name}': {exc}")
            return DrugSearchResponse(total=0, limit=limit, items=[])


drug_lookup_service = DrugLookupService()
