"""Increase column lengths

Revision ID: c58992262dc7
Revises: 92b8ac6c37fd
Create Date: 2025-03-10 21:19:45.929942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c58992262dc7'
down_revision = '92b8ac6c37fd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.alter_column('isbn',
               existing_type=sa.VARCHAR(length=13),
               type_=sa.String(length=255),
               existing_nullable=False)
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               existing_nullable=False)
        batch_op.alter_column('author',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=255),
               existing_nullable=False)
        batch_op.alter_column('publisher',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=255),
               existing_nullable=True)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=120),
               type_=sa.String(length=255),
               existing_nullable=False)
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=255),
               existing_nullable=False)
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=255),
               existing_nullable=True)
        batch_op.alter_column('first_name',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=255),
               existing_nullable=True)
        batch_op.alter_column('last_name',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=255),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('last_name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=64),
               existing_nullable=True)
        batch_op.alter_column('first_name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=64),
               existing_nullable=True)
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=128),
               existing_nullable=True)
        batch_op.alter_column('username',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=64),
               existing_nullable=False)
        batch_op.alter_column('email',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=120),
               existing_nullable=False)

    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.alter_column('publisher',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
        batch_op.alter_column('author',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)
        batch_op.alter_column('title',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               existing_nullable=False)
        batch_op.alter_column('isbn',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=13),
               existing_nullable=False)

    # ### end Alembic commands ###
