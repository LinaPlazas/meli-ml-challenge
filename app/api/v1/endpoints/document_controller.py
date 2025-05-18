from fastapi import APIRouter, UploadFile, File, HTTPException,Body, Depends
from app.services.document_classification_service import DocumentClassifier
from app.services.pii_detection_service import PiiDetectionService
from app.services.duplicate_document_detector import DuplicateFileDetector
from app.infrastructure.text_extractor import TextExtractor
from app.services.normative_extractor_service import NormativeSectionService
from app.domain.entities.document import Document
from app.utils import messages
from typing import List,Optional
from app.exceptions.custom_exceptions import(
    FileUploadError,
    TextractJobError,
    InvalidFileTypeError,
    DocumentClassificationError,
    ModelLoadingError,
    PiiDetectionError,
    S3DownloadError,
    DuplicateDetectionError,
    NormativeSectionError)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import AuthService

router = APIRouter(prefix="/documents")

text_extractor = TextExtractor()
document_classifier = DocumentClassifier()
pii_detection_service= PiiDetectionService()
duplicate_file_detector=DuplicateFileDetector()
normative_section_service=NormativeSectionService()
auth_service = AuthService()
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_service.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload.get("sub")

@router.post("/extract-text", dependencies=[Depends(get_current_user)])
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

@router.post("/classify-text", dependencies=[Depends(get_current_user)])
async def classify_text(
    filenames: Optional[List[str]] = Body(
        default=None,
        example=["filename1.pdf", "filename2.pdf"],)):
    try:
        if filenames:
            final_results = await document_classifier.classify_documents_by_filenames(filenames)
        else:
            final_results = await document_classifier.classify_all_documents()
        return {
            "message": messages.SUCCESS_GENERIC,
            "data": final_results
        }
    except InvalidFileTypeError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except DocumentClassificationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ModelLoadingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{messages.FAILED_GENERIC} :{str(e)}")

@router.post("/detect-pii/", dependencies=[Depends(get_current_user)])
async def detect_pii(
    filenames: Optional[List[str]] = Body(
        default=None,
        example=["filename1.pdf", "filename2.pdf"],)):
    try:
        if filenames:
            pii_data = await pii_detection_service.detect_pii_by_filenames(filenames)
        else:
            pii_data = await pii_detection_service.detect_all_pii()
        return {
            "message": messages.SUCCESS_GENERIC,
            "data": pii_data}
    except PiiDetectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{messages.FAILED_GENERIC} :{str(e)}")

@router.post("/detect-documents-duplicates", dependencies=[Depends(get_current_user)])
async def detect_duplicates(similarity_threshold: int=90):
    try:
        resultado = await duplicate_file_detector.find_duplicates(similarity_threshold)
        return resultado
    except S3DownloadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except DuplicateDetectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{messages.FAILED_GENERIC}: {str(e)}")

@router.post("/extract-normative-sections", dependencies=[Depends(get_current_user)])
async def extract_normative_sections(
    filenames: Optional[List[str]] = Body(
        default=None,
        example=["filename1.pdf", "filename2.pdf"])):
    try:
        if filenames:
            final_results = await normative_section_service.extract_normative_sections_by_filenames(filenames)
        else:
            final_results = await normative_section_service.extract_all_normative_sections()

        return {
            "message": messages.SUCCESS_GENERIC,
            "data": final_results
        }
    except NormativeSectionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500,
            detail=f"{messages.FAILED_GENERIC}: {str(e)}"
        )
