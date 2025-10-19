"""create task repeats table

Revision ID: 461d679a29f4
Revises: 5fc5406bed13
Create Date: 2025-10-19 22:20:33.081223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '461d679a29f4'
down_revision: Union[str, Sequence[str], None] = '5fc5406bed13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('task_repeats',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('repeat_type', sa.Enum('DAY', 'WEEK', 'MONTH', 'YEAR', name='repeattypeenum'), nullable=False),
    sa.Column('repeat_interval', sa.Integer(), nullable=False),
    sa.CheckConstraint('repeat_interval >= 1', name=op.f('ck_task_repeats_check_positive_repeat_interval')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_task_repeats'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('task_repeats')
