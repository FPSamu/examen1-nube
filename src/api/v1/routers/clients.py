import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from src.services import client_service

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=list[ClientResponse])
def list_clients(db: Session = Depends(get_db)):
    return client_service.get_all(db)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: uuid.UUID, db: Session = Depends(get_db)):
    return client_service.get_by_id(db, client_id)


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    return client_service.create(db, data)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: uuid.UUID, data: ClientUpdate, db: Session = Depends(get_db)):
    return client_service.update(db, client_id, data)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: uuid.UUID, db: Session = Depends(get_db)):
    client_service.delete(db, client_id)
