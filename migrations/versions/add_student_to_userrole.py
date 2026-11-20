"""Add STUDENT to userrole enum

Revision ID: add_student_enum
Revises: d548d1d24094
Create Date: 2026-11-20

"""
from alembic import op

revision = 'add_student_enum'
down_revision = 'd548d1d24094'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'STUDENT'")

def downgrade():
    pass
