from datetime import datetime, timezone

import boto3

from src.config import settings

_client = boto3.client("s3", region_name=settings.aws_region)


def upload_pdf(pdf_bytes: bytes, rfc: str, folio: str) -> str:
    key = f"{rfc}/{folio}.pdf"
    _client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        Metadata={
            "hora-envio": datetime.now(timezone.utc).isoformat(),
            "nota-descargada": "false",
            "veces-enviado": "1",
        },
    )
    return key
