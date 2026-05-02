import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.address import TipoDireccion
from src.models.sell_note import SellNote
from src.repositories import address_repository, sell_note_repository
from src.schemas.sell_note import SellNoteCreate, SellNoteUpdate
from src.services import client_service


def _download_url(sell_note_id: uuid.UUID) -> str:
    from src.core.config import settings
    return f"{settings.api_base_url}/api/v1/sell-notes/{sell_note_id}/pdf/download"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_address(
    db: Session,
    client_id: uuid.UUID,
    address_id: uuid.UUID,
    expected_type: TipoDireccion,
) -> None:
    address = address_repository.get_by_id(db, address_id)
    if not address or address.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address {address_id} not found for this client",
        )
    if address.tipo_direccion != expected_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Address {address_id} must be of type '{expected_type.value}'",
        )


def get_all(db: Session) -> list[SellNote]:
    return sell_note_repository.get_all(db)


def get_by_id(db: Session, sell_note_id: uuid.UUID) -> SellNote:
    sell_note = sell_note_repository.get_by_id(db, sell_note_id)
    if not sell_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sell note not found")
    return sell_note


def create(db: Session, data: SellNoteCreate) -> SellNote:
    from src.services.aws import sqs

    client_service.get_by_id(db, data.client_id)

    if sell_note_repository.get_by_folio(db, data.folio):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A sell note with folio '{data.folio}' already exists",
        )

    _validate_address(db, data.client_id, data.direccion_facturacion_id, TipoDireccion.FACTURACION)
    _validate_address(db, data.client_id, data.direccion_envio_id, TipoDireccion.ENVIO)

    sell_note = sell_note_repository.create(db, data)

    # Publish message to SQS and return immediately (async PDF generation)
    sqs.publish_sell_note_created(str(sell_note.id))

    return sell_note_repository.get_by_id(db, sell_note.id)


def update(db: Session, sell_note_id: uuid.UUID, data: SellNoteUpdate) -> SellNote:
    sell_note = get_by_id(db, sell_note_id)

    if data.folio and data.folio != sell_note.folio:
        if sell_note_repository.get_by_folio(db, data.folio):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A sell note with folio '{data.folio}' already exists",
            )

    if data.direccion_facturacion_id:
        _validate_address(
            db, sell_note.client_id, data.direccion_facturacion_id, TipoDireccion.FACTURACION
        )
    if data.direccion_envio_id:
        _validate_address(
            db, sell_note.client_id, data.direccion_envio_id, TipoDireccion.ENVIO
        )

    return sell_note_repository.update(db, sell_note, data)


def delete(db: Session, sell_note_id: uuid.UUID) -> None:
    sell_note = get_by_id(db, sell_note_id)
    sell_note_repository.delete(db, sell_note)


def download_pdf(db: Session, sell_note_id: uuid.UUID) -> tuple[bytes, str]:
    from src.services.aws import s3

    sell_note = get_by_id(db, sell_note_id)
    if not sell_note.pdf_s3_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF has not been generated yet for this sell note",
        )

    pdf_bytes = s3.get_object_bytes(sell_note.pdf_s3_key)
    s3.update_object_metadata(sell_note.pdf_s3_key, {"nota-descargada": "true"})

    return pdf_bytes, f"nota-{sell_note.folio}.pdf"


def notify_client(db: Session, sell_note_id: uuid.UUID) -> None:
    """Manual re-notification: delegates to the notifier service."""
    import httpx

    from src.core.config import settings

    sell_note = get_by_id(db, sell_note_id)
    if not sell_note.pdf_s3_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF has not been generated yet for this sell note",
        )

    notifier_url = settings.notifier_url
    response = httpx.post(
        f"{notifier_url}/notify",
        json={
            "razon_social": sell_note.client.razon_social,
            "folio": sell_note.folio,
            "download_url": _download_url(sell_note.id),
            "s3_key": sell_note.pdf_s3_key,
        },
        timeout=30,
    )
    response.raise_for_status()
