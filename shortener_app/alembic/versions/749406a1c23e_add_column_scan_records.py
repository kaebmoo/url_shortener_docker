"""add_column_scan_records

Revision ID: 749406a1c23e
Revises: ab7c1901a6be
Create Date: 2024-08-12 10:21:37.542308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '749406a1c23e'
down_revision: Union[str, None] = 'ab7c1901a6be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
