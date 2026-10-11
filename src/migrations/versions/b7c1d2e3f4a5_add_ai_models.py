"""Add ai_models and drop app_settings.ai_priority.

Revision ID: b7c1d2e3f4a5
Revises: a4a5daf13b6f
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'b7c1d2e3f4a5'
down_revision: Union[str, Sequence[str], None] = 'a4a5daf13b6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_models',
        sa.Column('provider', postgresql.ENUM('GEMINI', 'GROQ', name='ai_provider', create_type=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('last_used_model', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_models')),
        sa.UniqueConstraint('provider', 'name', name='provider_name'),
    )
    # Сидим из текущего ai_priority: основной провайдер получает order 0.
    op.execute(
        """
        INSERT INTO ai_models (provider, name, "order", is_active)
        SELECT 'GEMINI', 'gemini-3.1-flash-lite', CASE WHEN ai_priority = 'GEMINI' THEN 0 ELSE 1 END, true
        FROM app_settings
        UNION ALL
        SELECT 'GROQ', 'openai/gpt-oss-20b', CASE WHEN ai_priority = 'GROQ' THEN 0 ELSE 1 END, true
        FROM app_settings
        """
    )
    op.drop_column('app_settings', 'ai_priority')


def downgrade() -> None:
    op.add_column('app_settings', sa.Column(
        'ai_priority', postgresql.ENUM('GEMINI', 'GROQ', name='ai_provider', create_type=False), nullable=True,
    ))
    op.execute(
        """
        UPDATE app_settings
        SET ai_priority = COALESCE(
            (SELECT provider FROM ai_models WHERE is_active ORDER BY "order", id LIMIT 1),
            'GEMINI'
        )
        """
    )
    op.alter_column('app_settings', 'ai_priority', nullable=False)
    op.drop_table('ai_models')
