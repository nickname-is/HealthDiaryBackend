"""create users table

Revision ID: 17fc265b41ca
Revises: 
Create Date: 2025-09-25 20:54:46.518527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17fc265b41ca'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('first_name', sa.String(length=255), nullable=False),
    sa.Column('last_name', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('height', sa.Float(), nullable=True),
    sa.Column('weight', sa.Float(), nullable=True),
    sa.Column('chest_circumference', sa.Float(), nullable=True),
    sa.Column('waist_circumference', sa.Float(), nullable=True),
    sa.Column('hips_circumference', sa.Float(), nullable=True),
    sa.Column('gender', sa.Enum('M', 'F', name='genderenum'), nullable=True),
    sa.Column('birth_date', sa.Date(), nullable=True),
    sa.Column('avatar', sa.String(length=512), nullable=True),
    sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('edited_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
