import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class SellNote(Base):
    __tablename__ = "sell_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    folio: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False
    )
    direccion_facturacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False
    )
    direccion_envio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pdf_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True, default=None)

    client: Mapped["Client"] = relationship("Client", foreign_keys=[client_id])  # noqa: F821
    direccion_facturacion: Mapped["Address"] = relationship(  # noqa: F821
        "Address", foreign_keys=[direccion_facturacion_id]
    )
    direccion_envio: Mapped["Address"] = relationship(  # noqa: F821
        "Address", foreign_keys=[direccion_envio_id]
    )
    items: Mapped[list["SellNoteItem"]] = relationship(  # noqa: F821
        "SellNoteItem", back_populates="sell_note", cascade="all, delete-orphan"
    )
