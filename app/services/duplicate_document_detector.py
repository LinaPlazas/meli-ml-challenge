import os
import hashlib
import ssdeep
import boto3
import tempfile
from typing import Dict, Tuple, List
from itertools import combinations
from botocore.exceptions import BotoCoreError, ClientError
from app.exceptions.custom_exceptions import S3DownloadError, DuplicateDetectionError
from app.config.db import MongoDB

class DuplicateFileDetector:
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "")
        aws_region = os.getenv("AWS_REGION", "us-east-2")
        self.prefix = os.getenv("S3_PREFIX", "uploadss/")
        self.s3 = boto3.client("s3", region_name=aws_region)
        self.db = MongoDB()

    def calculate_md5(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def download_files_from_s3(self) -> Dict[str, str]:
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=self.prefix)
            if "Contents" not in response:
                return {}
            files = {}
            for obj in response["Contents"]:
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                temp_path = tempfile.mktemp()
                self.s3.download_file(self.bucket_name, key, temp_path)
                files[key] = temp_path
            return files
        except (BotoCoreError, ClientError) as e:
            raise S3DownloadError(detail=f"Error downloading files from S3: {str(e)}")

    def get_file_hashes(self, s3_files: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
        hashes = {}
        for key, path in s3_files.items():
            md5 = self.calculate_md5(path)
            fuzzy = ssdeep.hash_from_file(path)
            hashes[key] = (md5, fuzzy)
        return hashes

    def get_exact_duplicates(self, hashes: Dict[str, Tuple[str, str]]) -> List[Tuple[str, str]]:
        md5_map = {}
        duplicates = []
        for key, (md5, _) in hashes.items():
            if md5 in md5_map:
                duplicates.append((key, md5_map[md5]))
            else:
                md5_map[md5] = key
        return duplicates

    def get_similar_files(self, hashes: Dict[str, Tuple[str, str]], threshold: int) -> List[Tuple[str, str, int]]:
        similars = []
        for a, b in combinations(hashes.keys(), 2):
            sim = ssdeep.compare(hashes[a][1], hashes[b][1])
            if threshold <= sim < 100:
                similars.append((a, b, sim))
        return similars

    async def update_db_with_duplicates(
        self,
        s3_files: Dict[str, str],
        exact_duplicates: List[Tuple[str, str]],
        similar_files: List[Tuple[str, str, int]]
    ):
        collection = self.db.document_analysis

        for key in s3_files:
            await collection.update_one(
                {"filename": key},
                {"$set": {"exact_duplicates": [], "similar_files": []}},
                upsert=True
            )

        for a, b in exact_duplicates:
            if a in s3_files:
                await collection.update_one({"filename": a}, {"$addToSet": {"exact_duplicates": b}}, upsert=True)
            if b in s3_files:
                await collection.update_one({"filename": b}, {"$addToSet": {"exact_duplicates": a}}, upsert=True)

        for a, b, sim in similar_files:
            if a in s3_files:
                await collection.update_one(
                    {"filename": a},
                    {"$addToSet": {"similar_files": {"filename": b, "similarity": sim}}},
                    upsert=True
                )
            if b in s3_files:
                await collection.update_one(
                    {"filename": b},
                    {"$addToSet": {"similar_files": {"filename": a, "similarity": sim}}},
                    upsert=True
                )


    async def find_duplicates(self, similarity_threshold: int = 90) -> dict:
        try:
            s3_files = self.download_files_from_s3()
            hashes = self.get_file_hashes(s3_files)
            exact_duplicates = self.get_exact_duplicates(hashes)
            similar_files = self.get_similar_files(hashes, similarity_threshold)
            await self.update_db_with_duplicates(s3_files, exact_duplicates, similar_files)

            return {
                "exact_duplicates": exact_duplicates,
                "similar_files": similar_files
            }
        except Exception as e:
            detail = getattr(e, "detail", str(e))
            raise DuplicateDetectionError(detail=f"Error detecting duplicates: {detail}")
