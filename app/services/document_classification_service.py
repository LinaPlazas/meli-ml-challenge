import re
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from app.domain.entities.document import Document, ClassificationResult
from app.exceptions.custom_exceptions import InvalidFileTypeError, DocumentClassificationError, ModelLoadingError
from fastapi import HTTPException

nltk.download('stopwords')

class DocumentClassifier:
    def __init__(self, model_path: str = "app/models/random_forest_model.pkl"):
        try:
            self.model = joblib.load(model_path)
        except FileNotFoundError:
            raise ModelLoadingError(detail=f"The model could not be found at path: {model_path}")
        except Exception as e:
            raise ModelLoadingError(detail=f"Error loading the model: {str(e)}")

        self.stemmer = SnowballStemmer("spanish")
        self.tokenizer = RegexpTokenizer(r'\b\w+\b')
        self.stop_words = set(stopwords.words("spanish"))

    def preprocessing_text(self, texto: str) -> str:
        if not texto:
            raise InvalidFileTypeError(detail="The text cannot be empty for classification.")

        texto = texto.lower()
        texto = re.sub(r"\s+", " ", texto).strip()
        tokens = self.tokenizer.tokenize(texto)
        tokens = [self.stemmer.stem(palabra) for palabra in tokens if palabra not in self.stop_words]
        return " ".join(tokens)

    def classify_text(self, document: Document) -> ClassificationResult:
        try:
            cleaned_text = self.preprocessing_text(document.text)
            prediction = self.model.predict([cleaned_text])[0]
            probabilities = self.model.predict_proba([cleaned_text])[0]

            category = prediction
            scores = dict(zip(self.model.classes_, probabilities))

            return ClassificationResult(category=category, scores=scores)

        except ValueError as e:
            raise DocumentClassificationError(detail=f"Error processing the text: {str(e)}")
        except Exception as e:
            raise DocumentClassificationError(detail=f"Error classifying the document: {str(e)}")
