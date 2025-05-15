import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from typing import List
from fastapi import UploadFile

class TextractReader:
    def __init__(self, region_name: str = "us-east-2", bucket_name: str = "melichallegebucket"):
        self.textract = boto3.client("textract", region_name=region_name)
        self.s3 = boto3.client("s3", region_name=region_name)
        self.bucket_name = bucket_name

    async def upload_file_to_s3(self, file: UploadFile, folder: str = "uploads") -> str:
        key = f"{folder}/{file.filename}"
        contents = await file.read()
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=contents)
        return key

    async def start_textract_job(self, file_key: str) -> str:
        loop = asyncio.get_event_loop()
        job_id = await loop.run_in_executor(
            None,
            lambda: self.textract.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': self.bucket_name, 'Name': file_key}}
            )['JobId']
        )
        return job_id

    def wait_for_job_result(self, job_id: str) -> str:
        while True:
            response = self.textract.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            if status == 'SUCCEEDED':
                blocks = response['Blocks']
                lines = [b["Text"] for b in blocks if b["BlockType"] == "LINE"]
                return " ".join(lines)
            elif status == 'FAILED':
                return ""
            time.sleep(5)

    async def process_files(self, files: List[UploadFile], folder: str = "uploads") -> List[dict]:
        # Subir archivos y preparar lista de keys
        file_keys = []
        for file in files:
            key = await self.upload_file_to_s3(file, folder)
            file_keys.append(key)

        loop = asyncio.get_event_loop()
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Iniciar jobs de textract asincrónicamente
            jobs = await asyncio.gather(
                *(self.start_textract_job(file_key) for file_key in file_keys)
            )

            futures = []
            for job_id in jobs:
                futures.append(loop.run_in_executor(executor, self.wait_for_job_result, job_id))

            texts = await asyncio.gather(*futures)

            # Construir resultados
            for file_key, text in zip(file_keys, texts):
                results.append({
                    "filename": file_key,
                    "text": text
                })

        return results
