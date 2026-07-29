"""Add behavioral_scores table for per-computation score tracking

Revision ID: 010
Revises: 009
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'behavioral_scores',
        sa.Column('id',          sa.Integer(),     nullable=False),
        sa.Column('user_id',     sa.Integer(),     nullable=False),
        sa.Column('score',       sa.Float(),       nullable=False),
        sa.Column('computed_at', sa.DateTime(),    nullable=False),
        sa.Column('role',        sa.String(32),    nullable=False),
        sa.Column('created_at',  sa.DateTime(),    nullable=False),
        sa.Column('updated_at',  sa.DateTime(),    nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_behavioral_scores_id',          'behavioral_scores', ['id'])
    op.create_index('ix_behavioral_scores_user_id',     'behavioral_scores', ['user_id'])
    op.create_index('ix_behavioral_scores_computed_at', 'behavioral_scores', ['computed_at'])


def downgrade() -> None:
    op.drop_index('ix_behavioral_scores_computed_at', table_name='behavioral_scores')
    op.drop_index('ix_behavioral_scores_user_id',     table_name='behavioral_scores')
    op.drop_index('ix_behavioral_scores_id',          table_name='behavioral_scores')
    op.drop_table('behavioral_scores')
