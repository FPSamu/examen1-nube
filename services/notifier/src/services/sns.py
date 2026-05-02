import boto3

from src.config import settings

_client = boto3.client("sns", region_name=settings.aws_region)


def send_sell_note_notification(razon_social: str, folio: str, download_url: str) -> str:
    subject = f"Nota de venta generada – Folio {folio}"
    message = (
        f"Estimado(a) {razon_social},\n\n"
        f"Se ha generado su nota de venta con folio {folio}.\n\n"
        f"Descargue su nota en el siguiente enlace:\n{download_url}"
    )
    response = _client.publish(
        TopicArn=settings.sns_topic_arn,
        Subject=subject,
        Message=message,
    )
    return response["MessageId"]
