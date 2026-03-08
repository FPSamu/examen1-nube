import uuid

from sqlalchemy.orm import Session

from src.models.client import Client
from src.schemas.client import ClientCreate, ClientUpdate


def get_all(db: Session) -> list[Client]:
    return db.query(Client).all()


def get_by_id(db: Session, client_id: uuid.UUID) -> Client | None:
    return db.query(Client).filter(Client.id == client_id).first()


def get_by_rfc(db: Session, rfc: str) -> Client | None:
    return db.query(Client).filter(Client.rfc == rfc).first()


def create(db: Session, data: ClientCreate) -> Client:
    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update(db: Session, client: Client, data: ClientUpdate) -> Client:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


def delete(db: Session, client: Client) -> None:
    db.delete(client)
    db.commit()
