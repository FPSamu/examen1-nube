import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    unidad_medida: str = Field(..., max_length=50)
    precio_base: Decimal = Field(..., gt=0, decimal_places=2)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=255)
    unidad_medida: str | None = Field(None, max_length=50)
    precio_base: Decimal | None = Field(None, gt=0, decimal_places=2)


class ProductResponse(ProductBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
