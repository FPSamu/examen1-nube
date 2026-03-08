import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.sell_note_item import SellNoteItem
from src.repositories import product_repository, sell_note_item_repository
from src.schemas.sell_note_item import SellNoteItemCreate, SellNoteItemUpdate
from src.services import sell_note_service


def get_all(db: Session, sell_note_id: uuid.UUID) -> list[SellNoteItem]:
    sell_note_service.get_by_id(db, sell_note_id)  # ensures sell note exists
    return sell_note_item_repository.get_all_by_sell_note(db, sell_note_id)


def get_by_id(db: Session, sell_note_id: uuid.UUID, item_id: uuid.UUID) -> SellNoteItem:
    sell_note_service.get_by_id(db, sell_note_id)  # ensures sell note exists
    item = sell_note_item_repository.get_by_id(db, item_id)
    if not item or item.sell_note_id != sell_note_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


def create(db: Session, sell_note_id: uuid.UUID, data: SellNoteItemCreate) -> SellNoteItem:
    sell_note_service.get_by_id(db, sell_note_id)  # ensures sell note exists
    if not product_repository.get_by_id(db, data.product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return sell_note_item_repository.create(db, sell_note_id, data)


def update(db: Session, sell_note_id: uuid.UUID, item_id: uuid.UUID, data: SellNoteItemUpdate) -> SellNoteItem:
    item = get_by_id(db, sell_note_id, item_id)
    return sell_note_item_repository.update(db, item, data)


def delete(db: Session, sell_note_id: uuid.UUID, item_id: uuid.UUID) -> None:
    item = get_by_id(db, sell_note_id, item_id)
    sell_note_item_repository.delete(db, item)
