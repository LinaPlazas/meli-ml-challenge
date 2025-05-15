import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from typing import List
from fastapi import UploadFile
from app.exceptions.custom_exceptions import FileUploadError, TextractJobError,InvalidFileTypeError
from botocore.exceptions import BotoCoreError, ClientError

class TextExtractor:
    def __init__(self, region_name: str = "us-east-2", bucket_name: str = "melichallegebucket"):
        self.textract = boto3.client("textract", region_name=region_name)
        self.s3 = boto3.client("s3", region_name=region_name)
        self.bucket_name = bucket_name

    def validate_file_type(self, file: UploadFile) -> bool:
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
        file_extension = file.filename.split('.')[-1].lower()

        if file_extension not in allowed_extensions:
            raise InvalidFileTypeError(detail=f"Invalid file type: {file.filename}")
        return True

    async def upload_file_to_bucket(self, file: UploadFile, folder: str = "uploads") -> str:
        self.validate_file_type(file)
        key = f"{folder}/{file.filename}"
        try:
            contents = await file.read()
            self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=contents)
            return key
        except (BotoCoreError, ClientError) as e:
            raise FileUploadError(detail=f"Error uploading file {file.filename}: {str(e)}")

    async def start_textract_job(self, file_key: str) -> str:
        loop = asyncio.get_event_loop()
        try:
            job_id = await loop.run_in_executor(
                None,
                lambda: self.textract.start_document_text_detection(
                    DocumentLocation={'S3Object': {'Bucket': self.bucket_name, 'Name': file_key}}
                )['JobId']
            )
            return job_id
        except botocore.exceptions.BotoCoreError as e:
            raise TextractJobError(detail=f"Failed to start Textract job for file {file_key}: {str(e)}")

    def wait_for_job_result(self, job_id: str) -> str:
        try:
            while True:
                response = self.textract.get_document_text_detection(JobId=job_id)
                status = response['JobStatus']
                if status == 'SUCCEEDED':
                    blocks = response['Blocks']
                    lines = [b["Text"] for b in blocks if b["BlockType"] == "LINE"]
                    return " ".join(lines)
                elif status == 'FAILED':
                    raise TextractJobError(detail=f"Textract job {job_id} failed.")
                time.sleep(5)
        except botocore.exceptions.BotoCoreError as e:
            raise TextractJobError(detail=f"Error during Textract job {job_id}: {str(e)}")

    async def process_files(self, files: List[UploadFile], folder: str = "uploads") -> List[dict]:
        file_keys = []
        for file in files:
            key = await self.upload_file_to_bucket(file, folder)
            file_keys.append(key)

        loop = asyncio.get_event_loop()
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            jobs = await asyncio.gather(
                *(self.start_textract_job(file_key) for file_key in file_keys)
            )

            futures = []
            for job_id in jobs:
                futures.append(loop.run_in_executor(executor, self.wait_for_job_result, job_id))

            texts = await asyncio.gather(*futures)

            for file_key, text in zip(file_keys, texts):
                results.append({
                    "filename": file_key,
                    "text": text
                })

        return results
