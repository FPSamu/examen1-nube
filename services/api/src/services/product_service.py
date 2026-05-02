import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.product import Product
from src.repositories import product_repository
from src.schemas.product import ProductCreate, ProductUpdate


def get_all(db: Session) -> list[Product]:
    return product_repository.get_all(db)


def get_by_id(db: Session, product_id: uuid.UUID) -> Product:
    product = product_repository.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def create(db: Session, data: ProductCreate) -> Product:
    return product_repository.create(db, data)


def update(db: Session, product_id: uuid.UUID, data: ProductUpdate) -> Product:
    product = get_by_id(db, product_id)
    return product_repository.update(db, product, data)


def delete(db: Session, product_id: uuid.UUID) -> None:
    product = get_by_id(db, product_id)
    product_repository.delete(db, product)
