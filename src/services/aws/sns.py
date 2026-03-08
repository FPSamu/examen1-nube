import boto3

from src.core.config import settings

_client = boto3.client(
    "sns",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
)


def publish(subject: str, message: str) -> str:
    response = _client.publish(
        TopicArn=settings.sns_topic_arn,
        Subject=subject,
        Message=message,
    )
    return response["MessageId"]


def send_sell_note_notification(
    razon_social: str,
    folio: str,
    download_url: str,
) -> str:
    subject = f"Nota de venta generada – Folio {folio}"
    message = (
        f"Estimado(a) {razon_social},\n\n"
        f"Se ha generado su nota de venta con folio {folio}.\n\n"
        f"Descargue su nota en el siguiente enlace:\n{download_url}"
    )
    return publish(subject, message)
