"""Add a columns again

Revision ID: da9f2d670731
Revises: bd2cbaa07a14
Create Date: 2024-06-22 20:42:23.808601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da9f2d670731'
down_revision: Union[str, None] = 'bd2cbaa07a14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
