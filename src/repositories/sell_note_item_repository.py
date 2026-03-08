import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from src.models.sell_note_item import SellNoteItem
from src.schemas.sell_note_item import SellNoteItemCreate, SellNoteItemUpdate


def get_all_by_sell_note(db: Session, sell_note_id: uuid.UUID) -> list[SellNoteItem]:
    return db.query(SellNoteItem).filter(SellNoteItem.sell_note_id == sell_note_id).all()


def get_by_id(db: Session, item_id: uuid.UUID) -> SellNoteItem | None:
    return db.query(SellNoteItem).filter(SellNoteItem.id == item_id).first()


def create(db: Session, sell_note_id: uuid.UUID, data: SellNoteItemCreate) -> SellNoteItem:
    importe = data.cantidad * data.precio_unitario
    item = SellNoteItem(
        sell_note_id=sell_note_id,
        importe=importe,
        **data.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update(db: Session, item: SellNoteItem, data: SellNoteItemUpdate) -> SellNoteItem:
    changes = data.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(item, field, value)
    item.importe = item.cantidad * item.precio_unitario
    db.commit()
    db.refresh(item)
    return item


def delete(db: Session, item: SellNoteItem) -> None:
    db.delete(item)
    db.commit()
