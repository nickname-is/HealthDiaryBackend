"""create email verifications table

Revision ID: 5fc5406bed13
Revises: 2970bc148bbe
Create Date: 2025-10-13 03:16:42.387154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fc5406bed13'
down_revision: Union[str, Sequence[str], None] = '2970bc148bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('email_verifications',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('code', sa.String(length=6), nullable=False),
    sa.Column('attempts', sa.SmallInteger(), nullable=False),
    sa.Column('max_attempts', sa.SmallInteger(), nullable=False),
    sa.Column('expire_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('edited_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_email_verifications_check_attempts_positive')),
    sa.CheckConstraint('max_attempts > 0', name=op.f('ck_email_verifications_check_max_attempts_positive')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_email_verifications_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_email_verifications'))
    )
    op.create_index(op.f('ix_email_verifications_user_id'), 'email_verifications', ['user_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_email_verifications_user_id'), table_name='email_verifications')
    op.drop_table('email_verifications')
