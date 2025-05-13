import spacy
from app.resources.keywords import document_keywords
from app.domain.entities.document import Document, ClassificationResult

class DocumentClassifier:
    def __init__(self, nlp_model: str = "en_core_web_sm"):
        self.nlp = spacy.load(nlp_model)
        self.document_keywords = document_keywords

    def classify(self, document: Document) -> ClassificationResult:
        doc = self.nlp(document.text.lower())
        scores = {category: 0 for category in self.document_keywords}

        for token in doc:
            for category, keywords in self.document_keywords.items():
                if token.text in keywords:
                    scores[category] += 1

        best_category = max(scores, key=scores.get)
        return ClassificationResult(category=best_category, scores=scores)
