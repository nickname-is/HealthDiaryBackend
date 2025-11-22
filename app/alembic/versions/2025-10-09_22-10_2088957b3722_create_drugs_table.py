"""create drugs table

Revision ID: 2088957b3722
Revises: efc1c9d23918
Create Date: 2025-10-09 22:10:40.851070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2088957b3722'
down_revision: Union[str, Sequence[str], None] = 'efc1c9d23918'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('drugs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('dosage', sa.Float(), nullable=False),
    sa.Column('dosage_unit', sa.Enum('MILLIGRAM', 'GRAM', 'MILLILITER', 'MICROGRAM', 'UNIT', 'PIECE', 'DROP', 'SPRAY', 'TABLESPOON', 'TEASPOON', name='dosageunitenum'), nullable=False),
    sa.Column('dosage_type', sa.Enum('CAPSULE', 'PILL', 'POWDER', 'AMPOULE', 'SOLUTION', 'SUSPENSION', 'CREAM', 'OINTMENT', 'GEL', 'SUPPOSITORY', 'SPRAY', 'DROP', 'FOAM', 'PATCH', 'INHALER', name='dosagetypeenum'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_drugs'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('drugs')
