import re
import joblib
import nltk
import os
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from app.domain.entities.document import Document, ClassificationResult
from app.exceptions.custom_exceptions import InvalidFileTypeError, DocumentClassificationError, ModelLoadingError
from fastapi import HTTPException
from typing import List
from app.config.db import MongoDB

nltk.download('stopwords')

class DocumentClassifier:
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.getenv("MODEL_PATH", "app/models/random_forest_model.pkl")
        try:
            self.model = joblib.load(model_path)
        except FileNotFoundError:
            raise ModelLoadingError(detail=f"The model could not be found at path: {model_path}")
        except Exception as e:
            raise ModelLoadingError(detail=f"Error loading the model: {str(e)}")
        self.stemmer = SnowballStemmer("spanish")
        self.tokenizer = RegexpTokenizer(r'\b\w+\b')
        self.stop_words = set(stopwords.words("spanish"))
        self.db= MongoDB()
        self.prefix = os.getenv("S3_PREFIX", "uploads/")

    def preprocessing_text(self, text: str) -> str:
        if not text:
            raise InvalidFileTypeError(detail="The text cannot be empty for classification.")
        text = text.lower()
        text = re.sub(r"\s+", " ", text).strip()
        tokens = self.tokenizer.tokenize(text)
        tokens = [self.stemmer.stem(word) for word in tokens if word not in self.stop_words]
        return " ".join(tokens)

    def classify_text(self, document: Document) -> ClassificationResult:
        cleaned_text = self.preprocessing_text(document.text)
        prediction = self.model.predict([cleaned_text])[0]
        probabilities = self.model.predict_proba([cleaned_text])[0]
        scores = dict(zip(self.model.classes_, probabilities))
        return ClassificationResult(category=prediction, scores=scores)

    async def classify_all_documents(self) -> list[dict]:
        try:
            collection = self.db.document_analysis
            documents = await collection.find({}).to_list(None)
            final_results = []
            for doc in documents:
                try:
                    filename = doc.get("filename")
                    text = doc.get("text", "")

                    document = Document(text=text)
                    classification = self.classify_text(document)
                    await collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {
                            "category": classification.category,
                            "scores": classification.scores
                        }}
                    )
                    final_results.append({
                        "filename": filename,
                        "category": classification.category,
                        "scores": classification.scores
                    })
                except (InvalidFileTypeError, ValueError) as e:
                    continue
            return final_results
        except Exception as e:
            raise DocumentClassificationError(detail=f"Unexpected error during document classification: {str(e)}")

    async def classify_documents_by_filenames(self, filenames: List[str]) -> list[dict]:
        try:
            filenames_with_prefix = [f"{self.prefix}{filename}" if not filename.startswith(self.prefix) else filename for filename in filenames]
            collection = self.db.document_analysis
            documents = await collection.find({"filename": {"$in": filenames_with_prefix}}).to_list(None)
            found_filenames = {doc.get("filename") for doc in documents}
            final_results = []
            for doc in documents:
                try:
                    filename = doc.get("filename")
                    text = doc.get("text", "")
                    document = Document(text=text)
                    classification = self.classify_text(document)
                    await collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {
                            "category": classification.category,
                            "scores": classification.scores
                        }}
                    )
                    final_results.append({
                        "filename": filename,
                        "category": classification.category,
                        "scores": classification.scores,
                        "message": "Successfully classified"
                    })
                except (InvalidFileTypeError, ValueError) as e:
                    final_results.append({
                        "filename": doc.get("filename"),
                        "category": None,
                        "scores": {},
                        "message": f"Skipped due to error: {str(e)}"
                    })
            missing_files = set(filenames_with_prefix) - found_filenames
            for missing_filename in missing_files:
                final_results.append({
                    "filename": missing_filename,
                    "category": None,
                    "scores": {},
                    "message": "File not found in the database"
                })

            return final_results

        except Exception as e:
            raise DocumentClassificationError(detail=f"Unexpected error during classification by filenames: {str(e)}")
