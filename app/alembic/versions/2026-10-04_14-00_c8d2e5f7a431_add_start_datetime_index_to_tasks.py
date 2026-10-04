"""add start_datetime index to tasks

Revision ID: c8d2e5f7a431
Revises: b3f1a4c7d920
Create Date: 2026-10-04 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c8d2e5f7a431'
down_revision: Union[str, Sequence[str], None] = 'b3f1a4c7d920'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        op.f('ix_tasks_start_datetime'), 'tasks', ['start_datetime'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tasks_start_datetime'), table_name='tasks')
