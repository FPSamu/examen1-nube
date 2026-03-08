import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class SellNoteItem(Base):
    __tablename__ = "sell_note_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sell_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sell_notes.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    importe: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sell_note: Mapped["SellNote"] = relationship("SellNote", back_populates="items")  # noqa: F821
    product: Mapped["Product"] = relationship("Product")  # noqa: F821
