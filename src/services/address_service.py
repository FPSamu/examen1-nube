import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.address import Address
from src.repositories import address_repository
from src.schemas.address import AddressCreate, AddressUpdate
from src.services import client_service


def get_all(db: Session, client_id: uuid.UUID) -> list[Address]:
    client_service.get_by_id(db, client_id)  # ensures client exists
    return address_repository.get_all_by_client(db, client_id)


def get_by_id(db: Session, client_id: uuid.UUID, address_id: uuid.UUID) -> Address:
    client_service.get_by_id(db, client_id)  # ensures client exists
    address = address_repository.get_by_id(db, address_id)
    if not address or address.client_id != client_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address


def create(db: Session, client_id: uuid.UUID, data: AddressCreate) -> Address:
    client_service.get_by_id(db, client_id)  # ensures client exists
    return address_repository.create(db, client_id, data)


def update(db: Session, client_id: uuid.UUID, address_id: uuid.UUID, data: AddressUpdate) -> Address:
    address = get_by_id(db, client_id, address_id)
    return address_repository.update(db, address, data)


def delete(db: Session, client_id: uuid.UUID, address_id: uuid.UUID) -> None:
    address = get_by_id(db, client_id, address_id)
    address_repository.delete(db, address)
