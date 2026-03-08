import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.schemas.sell_note_item import SellNoteItemCreate, SellNoteItemResponse, SellNoteItemUpdate
from src.services import sell_note_item_service

router = APIRouter(prefix="/sell-notes/{sell_note_id}/items", tags=["Sell Note Items"])


@router.get("/", response_model=list[SellNoteItemResponse])
def list_items(sell_note_id: uuid.UUID, db: Session = Depends(get_db)):
    return sell_note_item_service.get_all(db, sell_note_id)


@router.get("/{item_id}", response_model=SellNoteItemResponse)
def get_item(sell_note_id: uuid.UUID, item_id: uuid.UUID, db: Session = Depends(get_db)):
    return sell_note_item_service.get_by_id(db, sell_note_id, item_id)


@router.post("/", response_model=SellNoteItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(sell_note_id: uuid.UUID, data: SellNoteItemCreate, db: Session = Depends(get_db)):
    return sell_note_item_service.create(db, sell_note_id, data)


@router.put("/{item_id}", response_model=SellNoteItemResponse)
def update_item(sell_note_id: uuid.UUID, item_id: uuid.UUID, data: SellNoteItemUpdate, db: Session = Depends(get_db)):
    return sell_note_item_service.update(db, sell_note_id, item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(sell_note_id: uuid.UUID, item_id: uuid.UUID, db: Session = Depends(get_db)):
    sell_note_item_service.delete(db, sell_note_id, item_id)
