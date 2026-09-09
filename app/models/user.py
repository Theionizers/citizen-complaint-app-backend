from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy import DateTime, String

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import Role,Department


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False
    )
    department_id: Mapped[int | None] = mapped_column(
    ForeignKey("departments.id"),
    nullable=True
)

    department: Mapped["Department | None"] = relationship()

    role: Mapped["Role"] = relationship()

    is_email_verified: Mapped[bool] = mapped_column(
    default=False,
    nullable=False
)

    email_verification_token_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    email_verification_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    password_reset_token_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )