from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.document_classifier import DocumentClassifier
from app.infrastructure.textract_reader import TextractReader
from app.domain.entities.document import Document

router = APIRouter()

# Inicializar las instancias de las clases
textract_reader = TextractReader()
document_classifier = DocumentClassifier()

@router.post("/classify")
async def classify(file: UploadFile = File(...)):
    content = await file.read()

    text = textract_reader.extract_text_from_pdf(content)

    document = Document(text=text)

    result = document_classifier.classify(document)

    return {
        "category": result.category,
        "scores": result.scores
    }
