"""empty message

Revision ID: d4f5f1fabda9
Revises: c15296d8779e
Create Date: 2019-08-10 15:18:52.926585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f5f1fabda9'
down_revision = 'c15296d8779e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('component', sa.Column('stock_count', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('component', 'stock_count')
    # ### end Alembic commands ###
