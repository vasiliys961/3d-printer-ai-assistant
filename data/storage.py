"""File storage (LocalFS или S3)"""
import os
from pathlib import Path
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
from config import settings


class StorageManager:
    """Менеджер для работы с файловым хранилищем"""
    
    def __init__(self):
        self.storage_type = settings.storage_type
        if self.storage_type == "s3":
            self.s3_client = boto3.client(
                's3',
                region_name=settings.s3_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            self.bucket_name = settings.s3_bucket_name
        else:
            self.local_storage_path = Path("./data/storage")
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_content: bytes, file_path: str) -> str:
        """Сохранить файл"""
        if self.storage_type == "s3":
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_content
            )
            return f"s3://{self.bucket_name}/{file_path}"
        else:
            full_path = self.local_storage_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(file_content)
            return str(full_path)
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Получить файл"""
        if self.storage_type == "s3":
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                return response['Body'].read()
            except ClientError:
                return None
        else:
            full_path = self.local_storage_path / file_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    return f.read()
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Удалить файл"""
        if self.storage_type == "s3":
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                return True
            except ClientError:
                return False
        else:
            full_path = self.local_storage_path / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False


storage = StorageManager()

