"""create sleeps table

Revision ID: ed978e6a3503
Revises: dbae209d5edd
Create Date: 2025-11-02 21:20:30.501996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed978e6a3503'
down_revision: Union[str, Sequence[str], None] = 'dbae209d5edd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('sleeps',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('record_date', sa.Date(), nullable=False),
    sa.Column('sleep_duration_minutes', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('sleep_quality', sa.SmallInteger(), server_default=sa.text('5'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('sleep_duration_minutes >= 0', name=op.f('ck_sleeps_check_positive_sleep_duration')),
    sa.CheckConstraint('sleep_quality >= 1 AND sleep_quality <= 5', name=op.f('ck_sleeps_check_sleep_quality_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_sleeps_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sleeps')),
    sa.UniqueConstraint('guid', name=op.f('uq_sleeps_guid')),
    sa.UniqueConstraint('user_id', 'record_date', name='uq_sleeps_user_id_record_date')
    )
    op.create_index(op.f('ix_sleeps_record_date'), 'sleeps', ['record_date'], unique=False)
    op.create_index(op.f('ix_sleeps_user_id'), 'sleeps', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sleeps_user_id'), table_name='sleeps')
    op.drop_index(op.f('ix_sleeps_record_date'), table_name='sleeps')
    op.drop_table('sleeps')
