import uuid

from sqlalchemy.orm import Session

from src.models.product import Product
from src.schemas.product import ProductCreate, ProductUpdate


def get_all(db: Session) -> list[Product]:
    return db.query(Product).all()


def get_by_id(db: Session, product_id: uuid.UUID) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def create(db: Session, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update(db: Session, product: Product, data: ProductUpdate) -> Product:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()
