from fastapi import status

class FileUploadError(Exception):
    def __init__(self, detail="Failed to upload file"):
        self.detail = detail
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

class TextractJobError(Exception):
    def __init__(self, detail="Textract job failed", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.detail = detail
        self.status_code = status_code

class InvalidFileTypeError(Exception):
    def __init__(self, detail="Invalid file type provided."):
        self.detail = detail
        self.status_code = status.HTTP_400_BAD_REQUEST

class DocumentClassificationError(Exception):
    def __init__(self, detail="Error during document classification.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.detail = detail
        self.status_code = status_code
        
class ModelLoadingError(Exception):
    def __init__(self, detail="Error loading the model.", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.detail = detail
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
