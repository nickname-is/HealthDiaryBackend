"""replace uuid_generate_v4 with gen_random_uuid

Revision ID: e7c85208ef1c
Revises: a7945a3ee3b2
Create Date: 2026-10-03 18:52:15.913086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7c85208ef1c'
down_revision: Union[str, Sequence[str], None] = 'a7945a3ee3b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GUID_TABLES = (
    'tasks',
    'activities',
    'water_intakes',
    'sleeps',
    'body_temperatures',
)


def upgrade() -> None:
    """Upgrade schema."""
    # gen_random_uuid() — встроенная функция PostgreSQL 13+, uuid-ossp не нужен
    for table in GUID_TABLES:
        op.alter_column(
            table,
            'guid',
            existing_type=sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
        )

    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    for table in GUID_TABLES:
        op.alter_column(
            table,
            'guid',
            existing_type=sa.UUID(),
            server_default=sa.text('uuid_generate_v4()'),
        )
