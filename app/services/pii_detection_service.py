import spacy
import re
import os
from app.exceptions.custom_exceptions import PiiDetectionError
from app.config.db import MongoDB

nlp = spacy.load("es_core_news_lg")

class PiiDetectionService:
    def __init__(self):
        self.db= MongoDB()
        self.regex_patterns = {
            "EMAIL": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
            "ID_DOC": r"\b\d{6,10}\b",
            "PHONE": r"\b3\d{9}\b",
            "ADDRESS": r'\b(?:Calle|Cra|Carrera|Av|Avenida|Diagonal|Transversal|Cl|Kr|Tv|Trv)\.?\s*\d+[A-Z]?\s*(?:#|No\.?|N°)?\s*\d+[A-Z]?(?:\s*[-–]\s*\d+[A-Z]?)?'
        }
        self.prefix = os.getenv("S3_PREFIX", "uploads/")

    async def detect_all_pii(self) -> list[dict]:
        try:
            collection = self.db.document_analysis
            documents = await collection.find({}).to_list(None)
            final_results = []
            for doc in documents:
                result = await self._detect_and_update(doc)
                if result:
                    final_results.append(result)
            return final_results
        except Exception as e:
            raise PiiDetectionError(detail=f"Unexpected error during PII detection: {str(e)}")

    async def detect_pii_by_filenames(self, filenames: list[str]) -> list[dict]:
        try:
            filenames_with_prefix = [
                f"{self.prefix}{filename}" if not filename.startswith(self.prefix) else filename
                for filename in filenames
            ]
            collection = self.db.document_analysis
            documents = await collection.find({"filename": {"$in": filenames_with_prefix}}).to_list(None)
            found_filenames = {doc.get("filename") for doc in documents}

            final_results = []
            for doc in documents:
                try:
                    filename = doc.get("filename")
                    text = doc.get("text", "")

                    pii_entities = self.extract_pii(text)

                    await collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"pii_entities": pii_entities}}
                    )
                    final_results.append({
                        "filename": filename,
                        "pii_entities": pii_entities,
                        "message": "Successfully detected"
                    })
                except Exception as e:
                    final_results.append({
                        "filename": doc.get("filename"),
                        "pii_entities": [],
                        "message": f"Skipped due to error: {str(e)}"
                    })
            missing_files = set(filenames_with_prefix) - found_filenames
            for missing_filename in missing_files:
                final_results.append({
                    "filename": missing_filename,
                    "pii_entities": [],
                    "message": "File not found in the database"
                })
            return final_results
        except Exception as e:
            raise PiiDetectionError(detail=f"Unexpected error during PII detection by filenames: {str(e)}")

    async def _detect_and_update(self, doc: dict) -> dict | None:
        try:
            filename = doc.get("filename")
            text = doc.get("text", "")
            pii_entities = self.extract_pii(text)
            await self.db.document_analysis.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "pii_entities": pii_entities
                }}
            )
            return {
                "filename": filename,
                "pii_entities": pii_entities
            }
        except Exception as e:
            raise PiiDetectionError(detail=f"Unexpected error during PII detection: {str(e)}")

    def extract_pii(self, text: str) -> list:
        try:
            text = text.lower()
            doc = nlp(text)

            ents_spacy = [
                {"type": e.label_, "value": e.text}
                for e in doc.ents
                if e.label_ in {"PER"}
            ]
            ents_regex = [
                {"type": type, "value": match}
                for type, pattern in self.regex_patterns.items()
                for match in re.findall(pattern, text, flags=re.IGNORECASE)
            ]
            all_ents = ents_spacy + ents_regex
            unique_list = list({(d["type"], d["value"]): d for d in all_ents}.values())
            return unique_list
        except Exception as e:
            raise PiiDetectionError(detail=f"Error extracting PII: {str(e)}")
