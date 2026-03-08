import uuid

from sqlalchemy.orm import Session

from src.models.address import Address
from src.schemas.address import AddressCreate, AddressUpdate


def get_all_by_client(db: Session, client_id: uuid.UUID) -> list[Address]:
    return db.query(Address).filter(Address.client_id == client_id).all()


def get_by_id(db: Session, address_id: uuid.UUID) -> Address | None:
    return db.query(Address).filter(Address.id == address_id).first()


def create(db: Session, client_id: uuid.UUID, data: AddressCreate) -> Address:
    address = Address(client_id=client_id, **data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update(db: Session, address: Address, data: AddressUpdate) -> Address:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    return address


def delete(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()
