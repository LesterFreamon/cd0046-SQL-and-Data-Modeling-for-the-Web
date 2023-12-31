"""empty message

Revision ID: b04d66e8138a
Revises: 9da39c61db5f
Create Date: 2023-11-28 11:12:56.597632

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b04d66e8138a'
down_revision = '9da39c61db5f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('artists', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_date', sa.DateTime(), nullable=True))

    with op.batch_alter_table('venues', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_date', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('venues', schema=None) as batch_op:
        batch_op.drop_column('created_date')

    with op.batch_alter_table('artists', schema=None) as batch_op:
        batch_op.drop_column('created_date')

    # ### end Alembic commands ###
