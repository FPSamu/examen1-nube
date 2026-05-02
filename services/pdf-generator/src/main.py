from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from src.services import pdf, s3

app = FastAPI(title="PDF Generator Service", version="1.0.0")


class ClientData(BaseModel):
    razon_social: str
    nombre_comercial: str
    rfc: str
    correo_electronico: str
    telefono: str


class ItemData(BaseModel):
    product_name: str
    cantidad: str
    precio_unitario: str
    importe: str


class GenerateRequest(BaseModel):
    sell_note_id: str
    folio: str
    rfc: str
    client: ClientData
    items: list[ItemData]
    total: str


class GenerateResponse(BaseModel):
    s3_key: str


@app.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
def generate(request: GenerateRequest):
    try:
        pdf_bytes = pdf.generate_pdf(request.model_dump())
        s3_key = s3.upload_pdf(pdf_bytes, request.rfc, request.folio)
        return GenerateResponse(s3_key=s3_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.get("/health")
def health_check():
    return {"status": "ok"}
