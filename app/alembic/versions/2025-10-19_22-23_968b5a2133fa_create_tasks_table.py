"""create tasks table

Revision ID: 968b5a2133fa
Revises: 461d679a29f4
Create Date: 2025-10-19 22:23:02.345766

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '968b5a2133fa'
down_revision: Union[str, Sequence[str], None] = '461d679a29f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('tasks',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('all_day', sa.Boolean(), nullable=False),
    sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=False),
    sa.Column('reminder_minutes', sa.Integer(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), nullable=False),
    sa.Column('drug_id', sa.BigInteger(), nullable=True),
    sa.Column('task_repeat_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('edited_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_datetime >= start_datetime', name=op.f('ck_tasks_check_end_after_start')),
    sa.CheckConstraint('reminder_minutes >= 0', name=op.f('ck_tasks_check_non_negative_reminder')),
    sa.ForeignKeyConstraint(['drug_id'], ['drugs.id'], name=op.f('fk_tasks_drug_id_drugs'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['task_repeat_id'], ['task_repeats.id'], name=op.f('fk_tasks_task_repeat_id_task_repeats'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_tasks_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tasks')),
    sa.UniqueConstraint('guid', name=op.f('uq_tasks_guid')),
    sa.UniqueConstraint('task_repeat_id', name=op.f('uq_tasks_task_repeat_id'))
    )
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tasks_user_id'), table_name='tasks')
    op.drop_table('tasks')
