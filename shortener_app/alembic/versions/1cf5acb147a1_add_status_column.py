"""add status column

Revision ID: 1cf5acb147a1
Revises: 8c78862500f2
Create Date: 2024-07-28 14:47:38.743373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cf5acb147a1'
down_revision: Union[str, None] = '8c78862500f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    '''op.drop_table('scan_records')
    op.drop_table('urls_to_check')'''
    op.add_column('urls', sa.Column('status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('urls', 'status')
    
    '''op.create_table('urls_to_check',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('url', sa.VARCHAR(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('scan_records',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.Column('url', sa.VARCHAR(), nullable=False),
    sa.Column('status', sa.VARCHAR(length=25), nullable=True),
    sa.Column('scan_type', sa.VARCHAR(), nullable=False),
    sa.Column('result', sa.VARCHAR(), nullable=True),
    sa.Column('submission_type', sa.VARCHAR(), nullable=True),
    sa.Column('scan_id', sa.VARCHAR(), nullable=True),
    sa.Column('sha256', sa.VARCHAR(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )'''
    # ### end Alembic commands ###
