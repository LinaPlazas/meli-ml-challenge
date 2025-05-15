import re
import joblib
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from app.domain.entities.document import Document, ClassificationResult

nltk.download('stopwords')

stemmer = SnowballStemmer("spanish")
tokenizer = RegexpTokenizer(r'\b\w+\b')
stop_words = set(stopwords.words("spanish"))


def limpiar_texto(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto).strip()
    tokens = tokenizer.tokenize(texto)
    tokens = [stemmer.stem(palabra) for palabra in tokens if palabra not in stop_words]
    return " ".join(tokens)


class DocumentClassifier:
    def __init__(self, model_path: str =  "app/models/modelo_random forest_documentos.pkl"):
        self.model = joblib.load(model_path)

    def classify(self, document: Document) -> ClassificationResult:
        cleaned_text = limpiar_texto(document.text)
        prediction = self.model.predict([cleaned_text])[0]
        probabilities = self.model.predict_proba([cleaned_text])[0]

        category = prediction
        scores = dict(zip(self.model.classes_, probabilities))

        return ClassificationResult(category=category, scores=scores)
