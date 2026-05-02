"""SQLAlchemy models for receipt-worker (read-only access to the shared RDS schema)."""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class TipoDireccion(str, enum.Enum):
    FACTURACION = "FACTURACIÓN"
    ENVIO = "ENVÍO"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    razon_social: Mapped[str] = mapped_column(String(255))
    nombre_comercial: Mapped[str] = mapped_column(String(255))
    rfc: Mapped[str] = mapped_column(String(13))
    correo_electronico: Mapped[str] = mapped_column(String(255))
    telefono: Mapped[str] = mapped_column(String(20))


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255))
    unidad_medida: Mapped[str] = mapped_column(String(50))
    precio_base: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class SellNoteItem(Base):
    __tablename__ = "sell_note_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    sell_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sell_notes.id")
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    importe: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    product: Mapped["Product"] = relationship("Product")


class SellNote(Base):
    __tablename__ = "sell_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    folio: Mapped[str] = mapped_column(String(50))
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id")
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    pdf_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    client: Mapped["Client"] = relationship("Client", foreign_keys=[client_id])
    items: Mapped[list["SellNoteItem"]] = relationship("SellNoteItem")
