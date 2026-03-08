import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from src.services import address_service

router = APIRouter(prefix="/clients/{client_id}/addresses", tags=["Addresses"])


@router.get("/", response_model=list[AddressResponse])
def list_addresses(client_id: uuid.UUID, db: Session = Depends(get_db)):
    return address_service.get_all(db, client_id)


@router.get("/{address_id}", response_model=AddressResponse)
def get_address(client_id: uuid.UUID, address_id: uuid.UUID, db: Session = Depends(get_db)):
    return address_service.get_by_id(db, client_id, address_id)


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(client_id: uuid.UUID, data: AddressCreate, db: Session = Depends(get_db)):
    return address_service.create(db, client_id, data)


@router.put("/{address_id}", response_model=AddressResponse)
def update_address(client_id: uuid.UUID, address_id: uuid.UUID, data: AddressUpdate, db: Session = Depends(get_db)):
    return address_service.update(db, client_id, address_id, data)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(client_id: uuid.UUID, address_id: uuid.UUID, db: Session = Depends(get_db)):
    address_service.delete(db, client_id, address_id)
