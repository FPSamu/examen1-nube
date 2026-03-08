import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from src.schemas.address import AddressResponse
from src.schemas.client import ClientResponse


class SellNoteBase(BaseModel):
    folio: str = Field(..., max_length=50)
    client_id: uuid.UUID
    direccion_facturacion_id: uuid.UUID
    direccion_envio_id: uuid.UUID
    total: Decimal = Field(..., gt=0, decimal_places=2)


class SellNoteCreate(SellNoteBase):
    pass


class SellNoteUpdate(BaseModel):
    folio: str | None = Field(None, max_length=50)
    direccion_facturacion_id: uuid.UUID | None = None
    direccion_envio_id: uuid.UUID | None = None
    total: Decimal | None = Field(None, gt=0, decimal_places=2)


class SellNoteResponse(BaseModel):
    id: uuid.UUID
    folio: str
    total: Decimal
    pdf_s3_key: str | None
    client: ClientResponse
    direccion_facturacion: AddressResponse
    direccion_envio: AddressResponse
    items: list["SellNoteItemResponse"] = []

    model_config = {"from_attributes": True}


# Imported after SellNoteResponse to avoid circular imports
from src.schemas.sell_note_item import SellNoteItemResponse  # noqa: E402

SellNoteResponse.model_rebuild()
