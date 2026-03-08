import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class TipoDireccion(str, enum.Enum):
    FACTURACION = "FACTURACIÓN"
    ENVIO = "ENVÍO"


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    domicilio: Mapped[str] = mapped_column(String(255), nullable=False)
    colonia: Mapped[str] = mapped_column(String(255), nullable=False)
    municipio: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_direccion: Mapped[TipoDireccion] = mapped_column(
        Enum(
            TipoDireccion,
            name="tipo_direccion_enum",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    client: Mapped["Client"] = relationship("Client", back_populates="addresses")  # noqa: F821
