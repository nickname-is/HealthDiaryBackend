"""drop verification tables

Revision ID: b3f1a4c7d920
Revises: e7c85208ef1c
Create Date: 2026-10-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f1a4c7d920'
down_revision: Union[str, Sequence[str], None] = 'e7c85208ef1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # OTP-коды перенесены в Redis, таблицы больше не используются
    op.drop_index(op.f('ix_verifications_user_id'), table_name='verifications')
    op.drop_index(op.f('ix_verifications_verification_type_id'), table_name='verifications')
    op.drop_table('verifications')
    op.drop_table('verification_types')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('verification_types',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_verification_types')),
    sa.UniqueConstraint('name', name=op.f('uq_verification_types_name'))
    )

    op.create_table('verifications',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.String(length=6), nullable=False),
    sa.Column('verification_type_id', sa.BigInteger(), nullable=False),
    sa.Column('attempts', sa.SmallInteger(), nullable=False),
    sa.Column('max_attempts', sa.SmallInteger(), nullable=False),
    sa.Column('expire_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_verifications_check_attempts_positive')),
    sa.CheckConstraint('max_attempts > 0', name=op.f('ck_verifications_check_max_attempts_positive')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_verifications_user_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['verification_type_id'], ['verification_types.id'], name=op.f('fk_verifications_verification_type_id_verification_types'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_verifications'))
    )
    op.create_index(op.f('ix_verifications_user_id'), 'verifications', ['user_id'], unique=True)
    op.create_index(op.f('ix_verifications_verification_type_id'), 'verifications', ['verification_type_id'], unique=False)
