"""
Drug interaction service.
Handles drug interaction checks and retrievals.
"""

import logging
from typing import Any

from app.repositories.drug_repository import drug_repository
from app.schemas.interaction import InteractionCheckResponse, InteractionResult

logger = logging.getLogger(__name__)


class DrugInteractionService:
    """Service for checking drug interactions."""

    def __init__(self):
        self._repository = drug_repository

    def get_drug_interactions(self, drug_name: str) -> list[dict[str, Any]]:
        """
        Get all drugs that interact with a specific drug.
        Returns list of interactions with severity and description.
        """
        logger.info(f"Fetching interactions for drug: '{drug_name}'")

        try:
            interactions = self._repository.get_drug_interactions(drug_name)
            logger.info(
                f"Found {len(interactions)} drugs that interact with '{drug_name}'"
            )
            return interactions

        except Exception as exc:
            logger.error(f"Error getting interactions for drug '{drug_name}': {exc}")
            return []

    def check_multiple_interactions(
        self, drug_names: list[str]
    ) -> InteractionCheckResponse:
        """
        Check interactions between multiple drugs.
        Returns InteractionCheckResponse with all interaction pairs found.
        """
        logger.info(f"Checking interactions for drugs: {drug_names}")

        if not drug_names or len(drug_names) < 2:
            logger.warning(
                f"Invalid drug list for interaction check: {drug_names}"
            )
            return InteractionCheckResponse(results=[])

        try:
            interactions = self._repository.check_multiple_drug_interactions(drug_names)

            results = [
                InteractionResult(
                    drug_1=inter.get("drug_1", ""),
                    drug_2=inter.get("drug_2", ""),
                    has_interaction=True,
                    severity=inter.get("severity", "unknown"),
                    description=inter.get("description"),
                )
                for inter in interactions
            ]

            logger.info(f"Found {len(results)} interaction pairs")
            return InteractionCheckResponse(results=results)

        except Exception as exc:
            logger.error(f"Error checking multiple interactions: {exc}")
            return InteractionCheckResponse(results=[])

    def assess_interaction_severity(
        self, drug_1: str, drug_2: str
    ) -> dict[str, Any] | None:
        """
        Assess the severity of interaction between two specific drugs.
        Returns interaction details or None if no interaction.
        """
        logger.info(f"Assessing interaction between '{drug_1}' and '{drug_2}'")

        try:
            # Get interactions for first drug
            interactions = self._repository.get_drug_interactions(drug_1)

            for inter in interactions:
                if inter.get("name") == drug_2:
                    logger.info(
                        f"Found interaction: {drug_1} ↔ {drug_2} "
                        f"(severity: {inter.get('severity')})"
                    )
                    return inter

            logger.info(f"No interaction found between '{drug_1}' and '{drug_2}'")
            return None

        except Exception as exc:
            logger.error(
                f"Error assessing interaction between '{drug_1}' and '{drug_2}': {exc}"
            )
            return None

    def get_safe_drug_combinations(
        self, drug_names: list[str]
    ) -> dict[str, Any]:
        """
        Analyze a list of drugs to identify safe and unsafe combinations.
        Returns a summary of interactions found.
        """
        logger.info(f"Analyzing drug combinations: {drug_names}")

        try:
            interactions = self._repository.check_multiple_drug_interactions(drug_names)

            # Group by severity
            severe = [i for i in interactions if i.get("severity") == "severe"]
            moderate = [i for i in interactions if i.get("severity") == "moderate"]
            mild = [i for i in interactions if i.get("severity") == "mild"]

            result = {
                "total_drugs": len(drug_names),
                "total_interactions": len(interactions),
                "by_severity": {
                    "severe": len(severe),
                    "moderate": len(moderate),
                    "mild": len(mild),
                },
                "interactions": interactions,
                "is_safe": len(severe) == 0,
                "warnings": [],
            }

            if severe:
                result["warnings"].append(
                    f"⚠️  SEVERE: {len(severe)} severe interactions found"
                )
            if moderate:
                result["warnings"].append(
                    f"⚠️  MODERATE: {len(moderate)} moderate interactions found"
                )

            logger.info(f"Drug combination analysis: {result['total_interactions']} interactions found")
            return result

        except Exception as exc:
            logger.error(f"Error analyzing drug combinations: {exc}")
            return {
                "total_drugs": len(drug_names),
                "total_interactions": 0,
                "by_severity": {"severe": 0, "moderate": 0, "mild": 0},
                "interactions": [],
                "is_safe": True,
                "warnings": [],
            }


drug_interaction_service = DrugInteractionService()
