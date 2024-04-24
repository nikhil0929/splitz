"""added profile_picture_url field to user class

Revision ID: 41f86ad0d851
Revises: 8fa2eaf77ebb
Create Date: 2024-04-23 22:54:19.031386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41f86ad0d851'
down_revision: Union[str, None] = '8fa2eaf77ebb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'profile_picture_url' column to 'users' table
    op.add_column('users', sa.Column('profile_picture_url', sa.String(), nullable=True))

def downgrade() -> None:
    # Remove 'profile_picture_url' column from 'users' table
    op.drop_column('users', 'profile_picture_url')
