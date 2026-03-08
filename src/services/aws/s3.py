import boto3

from src.core.config import settings

_client = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
)


def upload_file(
    file_bytes: bytes,
    key: str,
    content_type: str = "application/octet-stream",
    metadata: dict[str, str] | None = None,
) -> str:
    _client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
        Metadata=metadata or {},
    )
    return f"s3://{settings.s3_bucket_name}/{key}"


def get_object_bytes(key: str) -> bytes:
    response = _client.get_object(Bucket=settings.s3_bucket_name, Key=key)
    return response["Body"].read()


def get_object_metadata(key: str) -> dict[str, str]:
    response = _client.head_object(Bucket=settings.s3_bucket_name, Key=key)
    return response.get("Metadata", {})


def update_object_metadata(key: str, metadata_updates: dict[str, str]) -> None:
    current = get_object_metadata(key)
    merged = {**current, **metadata_updates}
    _client.copy_object(
        Bucket=settings.s3_bucket_name,
        CopySource={"Bucket": settings.s3_bucket_name, "Key": key},
        Key=key,
        Metadata=merged,
        MetadataDirective="REPLACE",
    )


def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
    return _client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": key},
        ExpiresIn=expires_in,
    )


def delete_file(key: str) -> None:
    _client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
