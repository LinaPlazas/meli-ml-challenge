import os
import hashlib
import ssdeep
import boto3
import tempfile
from typing import Dict, Tuple, List
from itertools import combinations
from botocore.exceptions import BotoCoreError, ClientError
from app.exceptions.custom_exceptions import S3DownloadError, DuplicateDetectionError


class DuplicateFileDetector:
    def __init__(self, bucket_name: str, aws_region: str = "us-east-2"):
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", region_name=aws_region)

    def _calcular_md5(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _descargar_archivos_s3(self, prefix: str = "upload/") -> Dict[str, str]:
        try:
            objetos = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            if "Contents" not in objetos:
                return {}

            archivos = {}
            for obj in objetos["Contents"]:
                nombre_archivo = obj["Key"]
                if nombre_archivo.endswith("/"):
                    continue
                ruta_temporal = tempfile.mktemp()
                self.s3.download_file(self.bucket_name, nombre_archivo, ruta_temporal)
                archivos[nombre_archivo] = ruta_temporal

            return archivos
        except (BotoCoreError, ClientError) as e:
            raise S3DownloadError(detail=f"Error downloading files from S3: {str(e)}")

    def encontrar_duplicados(self, prefix_s3: str = "uploads/", umbral_similitud: int = 90) -> dict:
        try:
            archivos_s3 = self._descargar_archivos_s3(prefix=prefix_s3)
            archivos_info: Dict[str, Tuple[str, str]] = {}
            md5_map: Dict[str, str] = {}
            duplicados: List[Tuple[str, str]] = []
            similares: List[Tuple[str, str, int]] = []

            for nombre_s3, ruta_local in archivos_s3.items():
                md5_hash = self._calcular_md5(ruta_local)
                ssdeep_hash = ssdeep.hash_from_file(ruta_local)
                archivos_info[nombre_s3] = (md5_hash, ssdeep_hash)

                if md5_hash in md5_map:
                    duplicados.append((nombre_s3, md5_map[md5_hash]))
                else:
                    md5_map[md5_hash] = nombre_s3

            for archivo1, archivo2 in combinations(archivos_info.keys(), 2):
                hash1 = archivos_info[archivo1][1]
                hash2 = archivos_info[archivo2][1]
                sim = ssdeep.compare(hash1, hash2)
                if sim >= umbral_similitud and sim != 100:
                    similares.append((archivo1, archivo2, sim))

            return {
                "duplicados_exactos": duplicados,
                "similares": similares
            }

        except Exception as e:
            raise DuplicateDetectionError(detail=f"Error detecting duplicates: {str(e)}")
