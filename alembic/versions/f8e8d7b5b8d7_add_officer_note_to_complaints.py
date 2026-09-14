"""add officer note to complaints

Revision ID: f8e8d7b5b8d7
Revises: f46ca8927dc8
Create Date: 2026-09-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8e8d7b5b8d7'
down_revision: Union[str, Sequence[str], None] = 'f46ca8927dc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('complaints', sa.Column('officer_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('complaints', 'officer_note')
