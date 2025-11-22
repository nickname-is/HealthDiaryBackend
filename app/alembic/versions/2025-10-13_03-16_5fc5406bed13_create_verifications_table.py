"""create verifications table

Revision ID: 5fc5406bed13
Revises: 2970bc148bbe
Create Date: 2025-10-13 03:16:42.387154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import pathlib
import orjson


# revision identifiers, used by Alembic.
revision: str = '5fc5406bed13'
down_revision: Union[str, Sequence[str], None] = '2970bc148bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    verification_types_table = op.create_table('verification_types',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True),
             server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True),
             server_default=sa.text('now()'), nullable=False),
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

    with open(pathlib.Path(__file__).parent.parent / "data" / "verification_types.json", "rb") as rb_file:
        verification_types_data = orjson.loads(rb_file.read())

    op.bulk_insert(verification_types_table, verification_types_data)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_verifications_user_id'), table_name='verifications')
    op.drop_table('verifications')
    op.drop_index(op.f('ix_verifications_verification_type_id'), table_name='verifications')
    op.drop_table('verifications_types')
