import boto3

from src.core.config import settings

_client = boto3.client(
    "ses",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
)


def send_email(to: list[str], subject: str, body_html: str, body_text: str = "") -> str:
    response = _client.send_email(
        Source=settings.ses_sender_email,
        Destination={"ToAddresses": to},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": body_text or subject, "Charset": "UTF-8"},
                "Html": {"Data": body_html, "Charset": "UTF-8"},
            },
        },
    )
    return response["MessageId"]


def send_sell_note_notification(
    razon_social: str,
    correo: str,
    folio: str,
    download_url: str,
) -> str:
    subject = f"Nota de venta generada – Folio {folio}"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
        <h2 style="color: #2c3e50;">Nota de venta generada</h2>
        <p>Estimado(a) <strong>{razon_social}</strong>,</p>
        <p>Se ha generado una nota de venta con el folio <strong>{folio}</strong>.</p>
        <p>Puede descargar su nota de venta haciendo clic en el siguiente botón:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{download_url}"
               style="background-color: #2c3e50; color: white; padding: 12px 28px;
                      text-decoration: none; border-radius: 4px; font-size: 15px;">
                Descargar nota de venta
            </a>
        </p>
        <p style="font-size: 12px; color: #888;">
            Si el botón no funciona, copie y pegue este enlace en su navegador:<br/>
            <a href="{download_url}">{download_url}</a>
        </p>
    </body>
    </html>
    """

    body_text = (
        f"Estimado(a) {razon_social},\n\n"
        f"Se ha generado su nota de venta con folio {folio}.\n"
        f"Descárguela en: {download_url}"
    )

    return send_email([correo], subject, body_html, body_text)
