"""correction of the time_mixin

Revision ID: 18f58b8cb4cf
Revises: 461d679a29f4
Create Date: 2025-10-21 21:29:22.543481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '18f58b8cb4cf'
down_revision: Union[str, Sequence[str], None] = '461d679a29f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('drugs', 'edited_at', new_column_name='updated_at')
    op.alter_column('email_verifications', 'edited_at', new_column_name='updated_at')
    op.alter_column('refresh_tokens', 'edited_at', new_column_name='updated_at')
    op.alter_column('users', 'edited_at', new_column_name='updated_at')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('drugs', 'updated_at', new_column_name='edited_at')
    op.alter_column('email_verifications', 'updated_at', new_column_name='edited_at')
    op.alter_column('refresh_tokens', 'updated_at', new_column_name='edited_at')
    op.alter_column('users', 'updated_at', new_column_name='edited_at')
