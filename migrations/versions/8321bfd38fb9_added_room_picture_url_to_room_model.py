"""added room_picture_url to ROom model

Revision ID: 8321bfd38fb9
Revises: 41f86ad0d851
Create Date: 2024-04-24 00:17:05.490030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8321bfd38fb9'
down_revision: Union[str, None] = '41f86ad0d851'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'room_picture_url' column to 'rooms' table
    op.add_column('rooms', sa.Column('room_picture_url', sa.String(), nullable=True))

def downgrade() -> None:
    # Remove 'room_picture_url' column from 'rooms' table
    op.drop_column('rooms', 'room_picture_url')