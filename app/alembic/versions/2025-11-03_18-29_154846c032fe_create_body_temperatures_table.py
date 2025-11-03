"""create body_temperatures table

Revision ID: 154846c032fe
Revises: ed978e6a3503
Create Date: 2025-11-03 18:29:39.372586

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '154846c032fe'
down_revision: Union[str, Sequence[str], None] = 'ed978e6a3503'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('body_temperatures',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('record_datetime', sa.DateTime(timezone=True), nullable=False),
    sa.Column('temperature_c', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('temperature_c >= 13.0 AND temperature_c <= 47.0', name=op.f('ck_body_temperatures_check_temperature_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_body_temperatures_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_body_temperatures')),
    sa.UniqueConstraint('guid', name=op.f('uq_body_temperatures_guid')),
    sa.UniqueConstraint('user_id', 'record_datetime', name='uq_body_temperatures_user_id_record_datetime')
    )
    op.create_index(op.f('ix_body_temperatures_record_datetime'), 'body_temperatures', ['record_datetime'], unique=False)
    op.create_index(op.f('ix_body_temperatures_user_id'), 'body_temperatures', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_body_temperatures_user_id'), table_name='body_temperatures')
    op.drop_index(op.f('ix_body_temperatures_record_datetime'), table_name='body_temperatures')
    op.drop_table('body_temperatures')
