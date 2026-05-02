import uuid

from pydantic import BaseModel, Field

from src.models.address import TipoDireccion


class AddressBase(BaseModel):
    domicilio: str = Field(..., max_length=255)
    colonia: str = Field(..., max_length=255)
    municipio: str = Field(..., max_length=255)
    estado: str = Field(..., max_length=255)
    tipo_direccion: TipoDireccion


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    domicilio: str | None = Field(None, max_length=255)
    colonia: str | None = Field(None, max_length=255)
    municipio: str | None = Field(None, max_length=255)
    estado: str | None = Field(None, max_length=255)
    tipo_direccion: TipoDireccion | None = None


class AddressResponse(AddressBase):
    id: uuid.UUID
    client_id: uuid.UUID

    model_config = {"from_attributes": True}
