import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.schemas.sell_note import SellNoteCreate, SellNoteResponse, SellNoteUpdate
from src.services import sell_note_service

router = APIRouter(prefix="/sell-notes", tags=["Sell Notes"])


@router.get("/", response_model=list[SellNoteResponse])
def list_sell_notes(db: Session = Depends(get_db)):
    return sell_note_service.get_all(db)


@router.get("/{sell_note_id}", response_model=SellNoteResponse)
def get_sell_note(sell_note_id: uuid.UUID, db: Session = Depends(get_db)):
    return sell_note_service.get_by_id(db, sell_note_id)


@router.post("/", response_model=SellNoteResponse, status_code=status.HTTP_201_CREATED)
def create_sell_note(data: SellNoteCreate, db: Session = Depends(get_db)):
    return sell_note_service.create(db, data)


@router.put("/{sell_note_id}", response_model=SellNoteResponse)
def update_sell_note(sell_note_id: uuid.UUID, data: SellNoteUpdate, db: Session = Depends(get_db)):
    return sell_note_service.update(db, sell_note_id, data)


@router.delete("/{sell_note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sell_note(sell_note_id: uuid.UUID, db: Session = Depends(get_db)):
    sell_note_service.delete(db, sell_note_id)


@router.get("/{sell_note_id}/pdf/download")
def download_sell_note_pdf(sell_note_id: uuid.UUID, db: Session = Depends(get_db)):
    pdf_bytes, filename = sell_note_service.download_pdf(db, sell_note_id)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{sell_note_id}/notify", status_code=status.HTTP_204_NO_CONTENT)
def notify_client(sell_note_id: uuid.UUID, db: Session = Depends(get_db)):
    sell_note_service.notify_client(db, sell_note_id)
