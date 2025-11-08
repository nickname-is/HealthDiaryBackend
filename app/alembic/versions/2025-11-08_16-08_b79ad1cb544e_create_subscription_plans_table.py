"""create subscription plans table

Revision ID: b79ad1cb544e
Revises: 154846c032fe
Create Date: 2025-11-08 16:08:12.458157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import pathlib
import orjson


# revision identifiers, used by Alembic.
revision: str = 'b79ad1cb544e'
down_revision: Union[str, Sequence[str], None] = '154846c032fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    subscription_plans_table = op.create_table('subscription_plans',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.Column('price_rub', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('price_rub >= 0', name=op.f('ck_subscription_plans_ck_plan_price_non_negative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_subscription_plans')),
    sa.UniqueConstraint('name', name=op.f('uq_subscription_plans_name')),
    sa.UniqueConstraint('slug', name=op.f('uq_subscription_plans_slug'))
    )

    with open(pathlib.Path(__file__).parent.parent / "data" / "subscription_plans.json", "rb") as rb_file:
        subscription_plans_data = orjson.loads(rb_file.read())

    op.bulk_insert(subscription_plans_table, subscription_plans_data)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('subscription_plans')
