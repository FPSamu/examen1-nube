from datetime import datetime, timezone

import boto3

from src.config import settings

_client = boto3.client("s3", region_name=settings.aws_region)


def update_notification_metadata(s3_key: str) -> None:
    """Increment veces-enviado and update hora-envio on the PDF object."""
    head = _client.head_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    current = head.get("Metadata", {})
    veces = int(current.get("veces-enviado", "0")) + 1
    merged = {
        **current,
        "veces-enviado": str(veces),
        "hora-envio": datetime.now(timezone.utc).isoformat(),
    }
    _client.copy_object(
        Bucket=settings.s3_bucket_name,
        CopySource={"Bucket": settings.s3_bucket_name, "Key": s3_key},
        Key=s3_key,
        Metadata=merged,
        MetadataDirective="REPLACE",
    )
