from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.document_classification_service import DocumentClassifier
from app.services.pii_detection_service import PiiDetectionService
from app.infrastructure.text_extractor import TextExtractor
from app.domain.entities.document import Document
from app.constants import messages
from typing import List
from app.exceptions.custom_exceptions import(
    FileUploadError,
    TextractJobError,
    InvalidFileTypeError,
    DocumentClassificationError,
    ModelLoadingError,
    PiiDetectionError)
import pandas as pd

router = APIRouter(prefix="/documents")

text_extractor = TextExtractor()
document_classifier = DocumentClassifier()
pii_detection_service= PiiDetectionService()

@router.post("/extract-text")
async def classify(files: List[UploadFile] = File(...)):
    try:
        results = await text_extractor.process_files(files)
        df = pd.DataFrame(results) ############ esto es para eliminar
        df.to_csv("results.csv", index=False)
        return {
            "message": messages.SUCCESS_GENERIC,
            "data": results
        }
    except FileUploadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except TextractJobError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except InvalidFileTypeError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{messages.FAILED_GENERIC} :{str(e)}")

@router.post("/classify-text")
async def classify():
    try:
        results = pd.read_csv("results.csv")
        final_results = []
        for index, item in results.iterrows():
            document = Document(text=item["text"])
            classification = document_classifier.classify_text(document)
            final_results.append({
                "filename": item["filename"],
                "category": classification.category,
                "scores": classification.scores
            })

        return {
            "message": messages.SUCCESS_GENERIC,
            "data": final_results}
    except InvalidFileTypeError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except DocumentClassificationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ModelLoadingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{messages.FAILED_GENERIC} :{str(e)}")

@router.post("/detect-pii/")
async def detect_pii():
    try:
        texts=pd.read_csv("results.csv")["text"]
        pii_data = [pii_detection_service.extract_pii(text) for text in texts]
        return {"pii": pii_data}
    except PiiDetectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
