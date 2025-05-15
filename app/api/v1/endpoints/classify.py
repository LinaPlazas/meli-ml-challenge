from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.document_classifier import DocumentClassifier
from app.infrastructure.textract_reader import TextractReader
from app.domain.entities.document import Document
from typing import List

router = APIRouter()

# Inicializar las instancias de las clases
textract_reader = TextractReader()
document_classifier = DocumentClassifier()

@router.post("/classify")
async def classify(files: List[UploadFile] = File(...)):
    results = await textract_reader.process_files(files)
    final_results = []
    for item in results:
        document = Document(text=item["text"])
        classification = document_classifier.classify(document)

        final_results.append({
            "filename": item["filename"],
            "category": classification.category,
            "scores": classification.scores
        })

    return final_results
