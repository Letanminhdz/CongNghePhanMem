"""
Dịch vụ kiểm tra tương tác thuốc.
Xử lý việc kiểm tra và truy xuất tương tác giữa các loại thuốc.
"""

import logging
from typing import Any

from app.repositories.drug_repository import drug_repository
from app.schemas.interaction import InteractionCheckResponse, InteractionResult

logger = logging.getLogger(__name__)


class DrugInteractionService:
    """Dịch vụ kiểm tra tương tác thuốc."""

    def __init__(self):
        self._repository = drug_repository

    def get_drug_interactions(self, drug_name: str, limit: int = 10, skip: int = 0) -> list[dict[str, Any]]:
        """
        Lấy tất cả các loại thuốc có tương tác với một thuốc cụ thể.
        Trả về danh sách các tương tác kèm theo mức độ nghiêm trọng và mô tả.
        """
        logger.info(f"Fetching interactions for drug: '{drug_name}', limit: {limit}, skip: {skip}")

        try:
            interactions = self._repository.get_drug_interactions(drug_name, limit=limit, skip=skip)
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
        Kiểm tra tương tác giữa nhiều loại thuốc với nhau.
        Trả về InteractionCheckResponse chứa tất cả các cặp tương tác tìm thấy.
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
        Đánh giá mức độ nghiêm trọng của tương tác giữa hai loại thuốc cụ thể.
        Trả về thông tin chi tiết về tương tác hoặc None nếu không có tương tác.
        """
        logger.info(f"Assessing interaction between '{drug_1}' and '{drug_2}'")

        try:
            # Lấy các tương tác của thuốc đầu tiên
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
        Phân tích danh sách các loại thuốc để xác định tổ hợp an toàn và không an toàn.
        Trả về tóm tắt các tương tác tìm thấy.
        """
        logger.info(f"Analyzing drug combinations: {drug_names}")

        try:
            interactions = self._repository.check_multiple_drug_interactions(drug_names)

            # Gom nhóm theo mức độ nghiêm trọng
            severe = [i for i in interactions if i.get("severity") == "severe"]
            moderate = [i for i in interactions if i.get("severity") == "moderate"]
            mild = [i for i in interactions if i.get("severity") == "mild"]

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

            result = {
                "drug_names": drug_names,
                "interactions": results,
                "is_safe": len(severe) == 0,
                "warnings": [],
                "summary": f"Found {len(interactions)} interactions between {len(drug_names)} drugs.",
            }

            if severe:
                result["warnings"].append(
                    f"⚠️ SEVERE: {len(severe)} severe interactions found"
                )
            if moderate:
                result["warnings"].append(
                    f"⚠️ MODERATE: {len(moderate)} moderate interactions found"
                )

            logger.info(f"Drug combination analysis: {len(interactions)} interactions found")
            return result

        except Exception as exc:
            logger.error(f"Error analyzing drug combinations: {exc}")
            return {
                "drug_names": drug_names,
                "interactions": [],
                "is_safe": True,
                "warnings": [],
                "summary": "Failed to analyze interactions",
            }


drug_interaction_service = DrugInteractionService()
