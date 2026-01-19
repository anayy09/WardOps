"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create units table
    op.create_table(
        'units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('floor', sa.Integer(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('unit_type', sa.String(length=50), nullable=True, server_default='medical'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_units_name', 'units', ['name'], unique=True)
    op.create_index('ix_units_code', 'units', ['code'], unique=True)

    # Create beds table (note: current_patient_id FK will be added after patients table is created)
    op.create_table(
        'beds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('bed_number', sa.String(length=20), nullable=False),
        sa.Column('bed_type', sa.String(length=50), nullable=True, server_default='standard'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='empty'),
        sa.Column('x_position', sa.Float(), nullable=True, server_default='0'),
        sa.Column('y_position', sa.Float(), nullable=True, server_default='0'),
        sa.Column('current_patient_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_beds_unit_id', 'beds', ['unit_id'])

    # Create nurses table
    op.create_table(
        'nurses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('employee_id', sa.String(length=20), nullable=False),
        sa.Column('specialty', sa.String(length=50), nullable=True),
        sa.Column('max_patients', sa.Integer(), nullable=True, server_default='4'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_nurses_employee_id', 'nurses', ['employee_id'], unique=True)
    op.create_index('ix_nurses_unit_id', 'nurses', ['unit_id'])

    # Create shifts table
    op.create_table(
        'shifts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nurse_id', sa.Integer(), nullable=False),
        sa.Column('shift_date', sa.DateTime(), nullable=False),
        sa.Column('shift_type', sa.String(length=20), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assigned_patients', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['nurse_id'], ['nurses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_shifts_nurse_id', 'shifts', ['nurse_id'])

    # Create patients table
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mrn', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=False),
        sa.Column('acuity', sa.String(length=50), nullable=False, server_default='medium'),
        sa.Column('chief_complaint', sa.String(length=255), nullable=True),
        sa.Column('arrival_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('discharge_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_unit_id', sa.Integer(), nullable=True),
        sa.Column('current_bed_id', sa.Integer(), nullable=True),
        sa.Column('is_isolation', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('requires_imaging', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('requires_consult', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['current_unit_id'], ['units.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['current_bed_id'], ['beds.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_patients_mrn', 'patients', ['mrn'], unique=True)
    op.create_index('ix_patients_current_bed_id', 'patients', ['current_bed_id'])
    
    # Now add FK constraint for beds.current_patient_id (after patients table exists)
    op.create_foreign_key(
        'beds_current_patient_id_fkey',
        'beds', 'patients',
        ['current_patient_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create scenarios table BEFORE events (events references scenarios)
    op.create_table(
        'scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_baseline', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('bed_id', sa.Integer(), nullable=True),
        sa.Column('nurse_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['bed_id'], ['beds.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['nurse_id'], ['nurses.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_events_patient_id', 'events', ['patient_id'])
    op.create_index('ix_events_timestamp', 'events', ['timestamp'])
    op.create_index('ix_events_event_type', 'events', ['event_type'])

    # Create state_snapshots table
    op.create_table(
        'state_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('state_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_state_snapshots_unit_id', 'state_snapshots', ['unit_id'])
    op.create_index('ix_state_snapshots_timestamp', 'state_snapshots', ['timestamp'])

    # Create simulation_runs table
    op.create_table(
        'simulation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timeseries', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_simulation_runs_scenario_id', 'simulation_runs', ['scenario_id'])

    # Create policy_documents table
    op.create_table(
        'policy_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('doc_type', sa.String(length=50), nullable=True),
        sa.Column('doc_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create policy_embeddings table
    op.create_table(
        'policy_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['policy_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_policy_embeddings_document_id', 'policy_embeddings', ['document_id'])


def downgrade() -> None:
    # Drop FK constraint that references patients before dropping patients table
    op.drop_constraint('beds_current_patient_id_fkey', 'beds', type_='foreignkey')
    
    op.drop_table('policy_embeddings')
    op.drop_table('policy_documents')
    op.drop_table('simulation_runs')
    op.drop_table('events')
    op.drop_table('state_snapshots')
    op.drop_table('scenarios')
    op.drop_table('patients')
    op.drop_table('shifts')
    op.drop_table('nurses')
    op.drop_table('beds')
    op.drop_table('units')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS vector')
