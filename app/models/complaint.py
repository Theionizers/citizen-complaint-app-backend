from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text,Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import Department, Service, User


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="submitted"
    )

    expected_resolution: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    routing_confidence: Mapped[float | None] = mapped_column(
        nullable=True
    )

    citizen_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"),
        nullable=True
    )

    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"),
        nullable=True
    )

    assigned_officer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    citizen: Mapped["User"] = relationship(
        foreign_keys=[citizen_id]
    )

    assigned_officer: Mapped["User | None"] = relationship(
        foreign_keys=[assigned_officer_id]
    )

    department: Mapped["Department | None"] = relationship()

    service: Mapped["Service | None"] = relationship()

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )