"""add positive constraints for users and drugs

Revision ID: 2970bc148bbe
Revises: 2088957b3722
Create Date: 2025-10-09 22:35:40.964727

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2970bc148bbe'
down_revision: Union[str, Sequence[str], None] = '2088957b3722'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем CheckConstraint для пользователей
    op.create_check_constraint(
        "check_positive_height",
        "users",
        "height > 0"
    )
    op.create_check_constraint(
        "check_positive_weight",
        "users",
        "weight > 0"
    )

    # Добавляем CheckConstraint для лекарств
    op.create_check_constraint(
        "check_positive_dosage",
        "drugs",
        "dosage > 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Убираем CheckConstraint
    op.drop_constraint("check_positive_height", "users", type_="check")
    op.drop_constraint("check_positive_weight", "users", type_="check")
    op.drop_constraint("check_positive_dosage", "drugs", type_="check")
