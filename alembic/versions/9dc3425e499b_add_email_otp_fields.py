"""add email otp fields

Revision ID: 9dc3425e499b
Revises: 92bf1cc17195
Create Date: 2026-09-14 13:55:03.892250
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9dc3425e499b"
down_revision: Union[str, Sequence[str], None] = "92bf1cc17195"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "email_otp_hash",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_otp_expires_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_otp_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_otp_last_sent_at",
            sa.DateTime(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("users", "email_otp_last_sent_at")
    op.drop_column("users", "email_otp_attempts")
    op.drop_column("users", "email_otp_expires_at")
    op.drop_column("users", "email_otp_hash")