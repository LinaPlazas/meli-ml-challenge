from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.document_classification_service import DocumentClassifier
from app.services.pii_detection_service import PiiDetectionService
from app.services.duplicate_document_detector import DuplicateFileDetector
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
    PiiDetectionError,
    S3DownloadError,
    DuplicateDetectionError)

router = APIRouter(prefix="/documents")

text_extractor = TextExtractor()
document_classifier = DocumentClassifier()
pii_detection_service= PiiDetectionService()
duplicate_file_detector=DuplicateFileDetector()

@router.post("/extract-text")
async def extract_text(files: List[UploadFile] = File(...)):
    try:
        results = await text_extractor.process_files(files)
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
async def classify_text():
    try:
        final_results = await document_classifier.classify_all_documents()
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
        pii_data = await pii_detection_service.detect_all_pii()
        return {
            "message": messages.SUCCESS_GENERIC,
            "data": pii_data}
    except PiiDetectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{messages.FAILED_GENERIC} :{str(e)}")

@router.post("/detect-documents-duplicates")
async def detect_duplicates():
    try:
        resultado = await duplicate_file_detector.find_duplicates()
        return resultado
    except S3DownloadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except DuplicateDetectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{messages.FAILED_GENERIC}: {str(e)}")
