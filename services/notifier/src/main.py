from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from src.services import s3, sns

app = FastAPI(title="Notifier Service", version="1.0.0")


class NotifyRequest(BaseModel):
    razon_social: str
    folio: str
    download_url: str
    s3_key: str


class NotifyResponse(BaseModel):
    message_id: str


@app.post("/notify", response_model=NotifyResponse)
def notify(request: NotifyRequest):
    try:
        s3.update_notification_metadata(request.s3_key)
        message_id = sns.send_sell_note_notification(
            razon_social=request.razon_social,
            folio=request.folio,
            download_url=request.download_url,
        )
        return NotifyResponse(message_id=message_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.get("/health")
def health_check():
    return {"status": "ok"}
