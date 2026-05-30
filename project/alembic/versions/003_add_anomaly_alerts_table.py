"""Add anomaly_alerts table for ML-based behavioural anomaly detection

Revision ID: 003
Revises: 002
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'anomaly_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('anomaly_score', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('top_features', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('audit_entry_id', sa.Integer(), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['audit_entry_id'], ['audit_chain.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Stores ML-generated behavioural anomaly alerts for users'
    )
    op.create_index('idx_anomaly_alerts_user', 'anomaly_alerts', ['user_id'])
    op.create_index('idx_anomaly_alerts_severity', 'anomaly_alerts', ['severity'])
    op.create_index('idx_anomaly_alerts_created_at', 'anomaly_alerts', ['created_at'])
    op.create_index('idx_anomaly_alerts_acknowledged', 'anomaly_alerts', ['is_acknowledged'])


def downgrade() -> None:
    op.drop_index('idx_anomaly_alerts_acknowledged', table_name='anomaly_alerts')
    op.drop_index('idx_anomaly_alerts_created_at', table_name='anomaly_alerts')
    op.drop_index('idx_anomaly_alerts_severity', table_name='anomaly_alerts')
    op.drop_index('idx_anomaly_alerts_user', table_name='anomaly_alerts')
    op.drop_table('anomaly_alerts')
