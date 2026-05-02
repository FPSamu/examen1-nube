import uuid

from pydantic import BaseModel, EmailStr, Field


class ClientBase(BaseModel):
    razon_social: str = Field(..., max_length=255)
    nombre_comercial: str = Field(..., max_length=255)
    rfc: str = Field(..., min_length=12, max_length=13)
    correo_electronico: EmailStr
    telefono: str = Field(..., max_length=20)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    razon_social: str | None = Field(None, max_length=255)
    nombre_comercial: str | None = Field(None, max_length=255)
    rfc: str | None = Field(None, min_length=12, max_length=13)
    correo_electronico: EmailStr | None = None
    telefono: str | None = Field(None, max_length=20)


class ClientResponse(ClientBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
