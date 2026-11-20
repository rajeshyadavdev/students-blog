"""Add role column to User

Revision ID: 36b9ec790d9c
Revises: a9894bed09fe
Create Date: 2026-11-19 07:40:22.928992

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '36b9ec790d9c'
down_revision = 'a9894bed09fe'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Pehle Enum type banao
    userrole = sa.Enum('USER', 'MODERATOR', 'ADMIN', name='userrole')
    userrole.create(op.get_bind(), checkfirst=True)

    # 2. Phir column add karo
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', userrole, server_default='USER', nullable=False))
        batch_op.alter_column('image_file',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=64),
               existing_nullable=False)

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('image_file',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
        batch_op.drop_column('role')

    # Enum type bhi delete karo
    userrole = sa.Enum('USER', 'MODERATOR', 'ADMIN', name='userrole')
    userrole.drop(op.get_bind(), checkfirst=True)
