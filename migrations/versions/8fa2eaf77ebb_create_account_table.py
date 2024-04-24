"""create account table

Revision ID: 8fa2eaf77ebb
Revises: 9862bcf17910
Create Date: 2024-04-22 20:42:25.184083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fa2eaf77ebb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter 'phone_number' column to be nullable
    op.alter_column('users', 'phone_number', 
                    existing_type=sa.String(length=30),
                    nullable=True)

def downgrade() -> None:
    # Revert 'phone_number' column to not be nullable
    op.alter_column('users', 'phone_number', 
                    existing_type=sa.String(length=30),
                    nullable=False)