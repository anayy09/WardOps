"""Add bottlenecks column to simulation_runs

Revision ID: 7199bdc36a1c
Revises: 001_initial
Create Date: 2026-01-18 21:17:52.238028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7199bdc36a1c'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Just add the bottlenecks column that's missing
    op.add_column('simulation_runs', sa.Column('bottlenecks', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove the bottlenecks column
    op.drop_column('simulation_runs', 'bottlenecks')
