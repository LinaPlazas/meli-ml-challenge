import spacy
import re
from app.exceptions.custom_exceptions import PiiDetectionError

nlp = spacy.load("es_core_news_lg")
regex_patterns = {
    "EMAIL": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
    "ID_DOC": r"\b\d{6,10}\b",
    "PHONE": r"\b3\d{9}\b",
    "ADDRESS": r'\b(?:Calle|Cra|Carrera|Av|Avenida|Diagonal|Transversal|Cl|Kr|Tv|Trv)\.?\s*\d+[A-Z]?\s*(?:#|No\.?|N°)?\s*\d+[A-Z]?(?:\s*[-–]\s*\d+[A-Z]?)?'
}

class PiiDetectionService:
    def __init__(self):
        pass

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
                for type, pattern in regex_patterns.items()
                for match in re.findall(pattern, text, flags=re.IGNORECASE)
            ]
            all_ents = ents_spacy + ents_regex
            unique_list = list({(d["type"], d["value"]): d for d in all_ents}.values())
            return unique_list
        except Exception as e:
            raise PiiDetectionError(detail=f"Error extracting PII: {str(e)}")
