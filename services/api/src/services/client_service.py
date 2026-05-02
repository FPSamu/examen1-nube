import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.client import Client
from src.repositories import client_repository
from src.schemas.client import ClientCreate, ClientUpdate


def get_all(db: Session) -> list[Client]:
    return client_repository.get_all(db)


def get_by_id(db: Session, client_id: uuid.UUID) -> Client:
    client = client_repository.get_by_id(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


def create(db: Session, data: ClientCreate) -> Client:
    if client_repository.get_by_rfc(db, data.rfc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A client with RFC '{data.rfc}' already exists",
        )
    return client_repository.create(db, data)


def update(db: Session, client_id: uuid.UUID, data: ClientUpdate) -> Client:
    client = get_by_id(db, client_id)
    if data.rfc and data.rfc != client.rfc:
        if client_repository.get_by_rfc(db, data.rfc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A client with RFC '{data.rfc}' already exists",
            )
    return client_repository.update(db, client, data)


def delete(db: Session, client_id: uuid.UUID) -> None:
    client = get_by_id(db, client_id)
    client_repository.delete(db, client)
