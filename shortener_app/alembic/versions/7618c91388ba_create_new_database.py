"""Create new database

Revision ID: 7618c91388ba
Revises: 1cf5acb147a1
Create Date: 2024-08-08 09:20:29.840868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7618c91388ba'
down_revision: Union[str, None] = '1cf5acb147a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
