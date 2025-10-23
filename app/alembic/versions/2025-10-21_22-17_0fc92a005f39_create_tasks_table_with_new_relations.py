"""create tasks table with new relations

Revision ID: 0fc92a005f39
Revises: 18f58b8cb4cf
Create Date: 2025-10-21 22:17:19.247941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0fc92a005f39'
down_revision: Union[str, Sequence[str], None] = '18f58b8cb4cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.create_table('tasks',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('all_day', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=False),
    sa.Column('reminder_minutes', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('is_completed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('is_reminded', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_datetime >= start_datetime', name=op.f('ck_tasks_check_end_after_start')),
    sa.CheckConstraint('reminder_minutes >= 0', name=op.f('ck_tasks_check_non_negative_reminder')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_tasks_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tasks')),
    sa.UniqueConstraint('guid', name=op.f('uq_tasks_guid'))
    )
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)
    op.add_column('drugs', sa.Column('task_id', sa.BigInteger(), nullable=False))
    op.create_unique_constraint(op.f('uq_drugs_task_id'), 'drugs', ['task_id'])
    op.create_foreign_key(op.f('fk_drugs_task_id_tasks'), 'drugs', 'tasks', ['task_id'], ['id'], ondelete='CASCADE')
    op.drop_column('drugs', 'created_at')
    op.drop_column('drugs', 'updated_at')
    op.add_column('task_repeats', sa.Column('task_id', sa.BigInteger(), nullable=False))
    op.create_unique_constraint(op.f('uq_task_repeats_task_id'), 'task_repeats', ['task_id'])
    op.create_foreign_key(op.f('fk_task_repeats_task_id_tasks'), 'task_repeats', 'tasks', ['task_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('fk_task_repeats_task_id_tasks'), 'task_repeats', type_='foreignkey')
    op.drop_constraint(op.f('uq_task_repeats_task_id'), 'task_repeats', type_='unique')
    op.drop_column('task_repeats', 'task_id')
    op.add_column('drugs', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False))
    op.add_column('drugs', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False))
    op.drop_constraint(op.f('fk_drugs_task_id_tasks'), 'drugs', type_='foreignkey')
    op.drop_constraint(op.f('uq_drugs_task_id'), 'drugs', type_='unique')
    op.drop_column('drugs', 'task_id')
    op.drop_index(op.f('ix_tasks_user_id'), table_name='tasks')
    op.drop_table('tasks')
