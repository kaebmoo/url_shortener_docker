"""remove_secretkey_to_scan_records

Revision ID: 788ee2472ec6
Revises: b0edf936bd95
Create Date: 2024-08-12 10:56:14.409653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '788ee2472ec6'
down_revision: Union[str, None] = 'b0edf936bd95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_scan_records_secret_key', table_name='scan_records')
    op.drop_column('scan_records', 'secret_key')


def downgrade() -> None:
    op.add_column('scan_records', sa.Column('secret_key', sa.String(), unique=True))
    op.create_index('ix_scan_records_secret_key', 'scan_records', ['secret_key'])
