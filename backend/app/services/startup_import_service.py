"""
Startup import service for automatic openFDA data initialization.
Handles non-blocking import with proper error handling and logging.
"""

import logging
from typing import Optional

from app.core.config import settings
from app.services.import_openfda_service import import_openfda_drugs
from app.services.openfda_neo4j_service import openfda_neo4j_service

logger = logging.getLogger(__name__)


def should_perform_startup_import() -> bool:
    """
    Check if we should perform startup import.
    Skip if Neo4j already has enough drug nodes to avoid redundant queries.
    """
    try:
        existing_count = openfda_neo4j_service.verify_drug_count()
        if existing_count >= settings.OPENFDA_MIN_EXISTING_NODES:
            logger.info(
                f"Neo4j already populated with {existing_count} drugs "
                f"(threshold: {settings.OPENFDA_MIN_EXISTING_NODES}), skipping startup import"
            )
            return False
        return True
    except Exception as exc:
        logger.warning(f"Could not check existing drug count: {exc}, proceeding with import")
        return True


def perform_startup_import() -> Optional[int]:
    """
    Perform automatic import of openFDA drugs on startup.
    Returns number of imported drugs, or None if import failed/skipped.
    """
    logger.info("=" * 60)
    logger.info("Starting automatic openFDA import...")
    logger.info(f"Import limit: {settings.OPENFDA_IMPORT_LIMIT}")

    try:
        if not should_perform_startup_import():
            logger.info("=" * 60)
            return None

        imported_count = import_openfda_drugs(
            limit=settings.OPENFDA_IMPORT_LIMIT,
            skip=0,
        )
        
        total_drugs = openfda_neo4j_service.verify_drug_count()
        logger.info(f"✓ Automatic openFDA import completed")
        logger.info(f"  - Imported/Updated: {imported_count}")
        logger.info(f"  - Total Drug nodes: {total_drugs}")
        logger.info("=" * 60)
        
        return imported_count

    except TimeoutError as exc:
        logger.error(f"✗ OpenFDA API timeout during startup import: {exc}")
        logger.info("Backend will continue without startup import. Manual import available via API.")
        logger.info("=" * 60)
        return None
    
    except Exception as exc:
        logger.exception(f"✗ Startup import failed: {exc}")
        logger.info("Backend will continue without startup import. Manual import available via API.")
        logger.info("=" * 60)
        return None
