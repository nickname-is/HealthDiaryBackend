"""create user subscriptions table

Revision ID: a7945a3ee3b2
Revises: b79ad1cb544e
Create Date: 2025-11-08 16:38:19.705512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7945a3ee3b2'
down_revision: Union[str, Sequence[str], None] = 'b79ad1cb544e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_subscriptions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('plan_id', sa.BigInteger(), nullable=False),
    sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name=op.f('ck_user_subscriptions_check_end_date_after_start_date')),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], name=op.f('fk_user_subscriptions_plan_id_subscription_plans'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_subscriptions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_subscriptions')),
    sa.UniqueConstraint('user_id', name=op.f('uq_user_subscriptions_user_id'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_subscriptions')
