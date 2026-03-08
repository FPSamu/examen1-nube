import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from src.schemas.product import ProductResponse


class SellNoteItemCreate(BaseModel):
    product_id: uuid.UUID
    cantidad: Decimal = Field(..., gt=0, decimal_places=3)
    precio_unitario: Decimal = Field(..., gt=0, decimal_places=2)


class SellNoteItemUpdate(BaseModel):
    cantidad: Decimal | None = Field(None, gt=0, decimal_places=3)
    precio_unitario: Decimal | None = Field(None, gt=0, decimal_places=2)


class SellNoteItemResponse(BaseModel):
    id: uuid.UUID
    sell_note_id: uuid.UUID
    product: ProductResponse
    cantidad: Decimal
    precio_unitario: Decimal
    importe: Decimal

    model_config = {"from_attributes": True}
