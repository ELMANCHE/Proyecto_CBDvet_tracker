"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa

revision = '001_aux_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'staging_carga',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('batch_id', sa.String(36), nullable=False),
        sa.Column('fila_num', sa.Integer()),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('estado', sa.String(20), server_default='pendiente'),
        sa.Column('errores', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('ix_staging_batch', 'staging_carga', ['batch_id'])

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entidad', sa.String(50), nullable=False),
        sa.Column('entidad_id', sa.Integer()),
        sa.Column('accion', sa.String(20), nullable=False),
        sa.Column('usuario', sa.String(100)),
        sa.Column('datos', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('ix_audit_entidad', 'audit_log', ['entidad', 'entidad_id'])

    op.create_table(
        'usuario',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('api_key', sa.String(64), nullable=False, unique=True),
        sa.Column('rol', sa.String(20), server_default='viewer'),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime()),
    )


def downgrade():
    op.drop_table('usuario')
    op.drop_table('audit_log')
    op.drop_index('ix_staging_batch', 'staging_carga')
    op.drop_table('staging_carga')
