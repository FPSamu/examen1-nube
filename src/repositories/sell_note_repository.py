import uuid

from sqlalchemy.orm import Session

from src.models.sell_note import SellNote
from src.schemas.sell_note import SellNoteCreate, SellNoteUpdate


def get_all(db: Session) -> list[SellNote]:
    return db.query(SellNote).all()


def get_by_id(db: Session, sell_note_id: uuid.UUID) -> SellNote | None:
    return db.query(SellNote).filter(SellNote.id == sell_note_id).first()


def get_by_folio(db: Session, folio: str) -> SellNote | None:
    return db.query(SellNote).filter(SellNote.folio == folio).first()


def create(db: Session, data: SellNoteCreate) -> SellNote:
    sell_note = SellNote(**data.model_dump())
    db.add(sell_note)
    db.commit()
    db.refresh(sell_note)
    return sell_note


def update(db: Session, sell_note: SellNote, data: SellNoteUpdate) -> SellNote:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(sell_note, field, value)
    db.commit()
    db.refresh(sell_note)
    return sell_note


def delete(db: Session, sell_note: SellNote) -> None:
    db.delete(sell_note)
    db.commit()
