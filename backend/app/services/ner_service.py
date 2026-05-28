import logging
import re
from typing import Set
from app.services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)

class NERService:
    """
    Named Entity Recognition Service for Medical Chatbot.
    Identifies Drugs and Diseases from user queries using fuzzy matching.
    """
    
    def __init__(self):
        self.drug_names: Set[str] = set()
        self.disease_names: Set[str] = set()
        self._last_refresh = 0
        self._refresh_interval = 3600  # 1 hour

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if not s2:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def _normalize_text(self, text: str) -> str:
        # Lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()

    def refresh_entities(self):
        """Fetch drug and disease names from Neo4j."""
        try:
            logger.info("Refreshing NER entity cache from Neo4j...")
            # This is a bit heavy, but good for fuzzy matching. 
            # In a real large-scale app, we'd use a search engine like ElasticSearch.
            drugs = neo4j_service.search_drugs("", limit=1000)
            diseases = neo4j_service.search_diseases("", limit=1000)
            
            self.drug_names = {d["name"] for d in drugs}
            self.disease_names = {d["name"] for d in diseases}
            logger.info(f"NER cache refreshed: {len(self.drug_names)} drugs, {len(self.disease_names)} diseases.")
        except Exception as e:
            logger.error(f"Failed to refresh NER cache: {e}")

    def extract_entities(self, text: str) -> dict:
        """
        Extract drugs and diseases from text.
        Supports Vietnamese and English via fuzzy matching.
        """
        if not self.drug_names:
            self.refresh_entities()

        normalized_query = self._normalize_text(text)
        words = normalized_query.split()
        
        extracted_drugs = set()
        extracted_diseases = set()

        # Simple window-based matching
        # Check for 1, 2, or 3-word entities
        for n in range(1, 4):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                
                # Check Drugs
                for drug in self.drug_names:
                    norm_drug = self._normalize_text(drug)
                    dist = self._levenshtein_distance(phrase, norm_drug)
                    # Allow 1 typo for short words, 2 for longer ones
                    threshold = 1 if len(norm_drug) < 6 else 2
                    if dist <= threshold:
                        extracted_drugs.add(drug)

                # Check Diseases
                for disease in self.disease_names:
                    norm_disease = self._normalize_text(disease)
                    dist = self._levenshtein_distance(phrase, norm_disease)
                    threshold = 1 if len(norm_disease) < 6 else 2
                    if dist <= threshold:
                        extracted_diseases.add(disease)

        return {
            "drugs": list(extracted_drugs),
            "diseases": list(extracted_diseases)
        }

ner_service = NERService()
