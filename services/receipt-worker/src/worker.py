import logging
import uuid

import httpx
from sqlalchemy.orm import Session

from src.config import settings
from src.db.models import SellNote

logger = logging.getLogger(__name__)


def _download_url(sell_note_id: uuid.UUID) -> str:
    return f"{settings.api_base_url}/api/v1/sell-notes/{sell_note_id}/pdf/download"


def process_message(db: Session, sell_note_id: str) -> None:
    """Orchestrate PDF generation and client notification for a sell note."""
    note_uuid = uuid.UUID(sell_note_id)

    sell_note = db.query(SellNote).filter(SellNote.id == note_uuid).first()
    if not sell_note:
        logger.error("Sell note %s not found in DB", sell_note_id)
        return

    # Build payload for pdf-generator
    pdf_payload = {
        "sell_note_id": sell_note_id,
        "folio": sell_note.folio,
        "rfc": sell_note.client.rfc,
        "client": {
            "razon_social": sell_note.client.razon_social,
            "nombre_comercial": sell_note.client.nombre_comercial,
            "rfc": sell_note.client.rfc,
            "correo_electronico": sell_note.client.correo_electronico,
            "telefono": sell_note.client.telefono,
        },
        "items": [
            {
                "product_name": item.product.nombre,
                "cantidad": str(item.cantidad),
                "precio_unitario": str(item.precio_unitario),
                "importe": str(item.importe),
            }
            for item in sell_note.items
        ],
        "total": str(sell_note.total),
    }

    # Request PDF generation
    logger.info("Requesting PDF generation for sell note %s", sell_note_id)
    pdf_response = httpx.post(
        f"{settings.pdf_generator_url}/generate",
        json=pdf_payload,
        timeout=60,
    )
    pdf_response.raise_for_status()
    pdf_result = pdf_response.json()

    s3_key = pdf_result["s3_key"]

    # Persist s3_key in DB
    sell_note.pdf_s3_key = s3_key
    db.commit()

    # Request client notification
    logger.info("Requesting notification for sell note %s", sell_note_id)
    notify_payload = {
        "razon_social": sell_note.client.razon_social,
        "folio": sell_note.folio,
        "download_url": _download_url(note_uuid),
        "s3_key": s3_key,
    }
    notify_response = httpx.post(
        f"{settings.notifier_url}/notify",
        json=notify_payload,
        timeout=30,
    )
    notify_response.raise_for_status()

    logger.info("Successfully processed sell note %s", sell_note_id)
