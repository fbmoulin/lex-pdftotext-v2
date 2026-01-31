"""S3-compatible storage backend."""

import os
from typing import BinaryIO

from .base import Storage


class S3Storage(Storage):
    """S3-compatible storage implementation (AWS S3, MinIO, etc.)."""

    def __init__(
        self,
        bucket: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint: str | None = None,
        region: str = "us-east-1",
    ):
        """
        Initialize S3 storage.

        Args:
            bucket: S3 bucket name
            access_key: AWS access key ID
            secret_key: AWS secret access key
            endpoint: Custom endpoint URL (for MinIO, etc.)
            region: AWS region
        """
        self.bucket = bucket or os.getenv("S3_BUCKET")
        self.access_key = access_key or os.getenv("S3_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("S3_SECRET_KEY")
        self.endpoint = endpoint or os.getenv("S3_ENDPOINT")
        self.region = region or os.getenv("S3_REGION", "us-east-1")

        if not self.bucket:
            raise ValueError("S3 bucket name is required")

        self._client = None

    @property
    def client(self):
        """Get or create boto3 S3 client."""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for S3 storage. Install with: pip install boto3"
                ) from None

            client_kwargs = {
                "region_name": self.region,
            }

            if self.access_key and self.secret_key:
                client_kwargs["aws_access_key_id"] = self.access_key
                client_kwargs["aws_secret_access_key"] = self.secret_key

            if self.endpoint:
                client_kwargs["endpoint_url"] = self.endpoint

            self._client = boto3.client("s3", **client_kwargs)

        return self._client

    def save(self, content: bytes | BinaryIO, path: str) -> str:
        """Save content to S3."""
        if isinstance(content, bytes):
            self.client.put_object(Bucket=self.bucket, Key=path, Body=content)
        else:
            self.client.upload_fileobj(content, self.bucket, path)

        return f"s3://{self.bucket}/{path}"

    def load(self, path: str) -> bytes:
        """Load content from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=path)
            return response["Body"].read()
        except self.client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"File not found: {path}") from None

    def delete(self, path: str) -> bool:
        """Delete file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False

    def exists(self, path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False

    def get_url(self, path: str, expires: int = 3600) -> str:
        """Get presigned URL for S3 object."""
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": path},
            ExpiresIn=expires,
        )
        return url

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in S3 bucket."""
        files = []
        paginator = self.client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                files.append(obj["Key"])

        return files
