"""add_secretkey_to_scan_records

Revision ID: b0edf936bd95
Revises: 749406a1c23e
Create Date: 2024-08-12 10:26:57.895745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0edf936bd95'
down_revision: Union[str, None] = '749406a1c23e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scan_records', sa.Column('secret_key', sa.String(), unique=True, index=True))


def downgrade() -> None:
    op.drop_index('ix_scan_records_secret_key', table_name='scan_records')
    op.drop_column('scan_records', 'secret_key')
