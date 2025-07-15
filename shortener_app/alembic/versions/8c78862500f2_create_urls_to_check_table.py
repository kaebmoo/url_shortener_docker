"""create_urls_to_check_table

Revision ID: 8c78862500f2
Revises: 92dfdd7b9ff4
Create Date: 2024-07-01 15:31:25.232912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c78862500f2'
down_revision: Union[str, None] = '92dfdd7b9ff4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'urls_to_check',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('url', sa.String, nullable=False)
    )


def downgrade() -> None:
    op.drop_table('urls_to_check')
