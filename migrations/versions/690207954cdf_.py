"""empty message

Revision ID: 690207954cdf
Revises: e3de4f09988e
Create Date: 2019-08-27 10:44:58.681675

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '690207954cdf'
down_revision = 'e3de4f09988e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product', sa.Column('p_unfired', sa.Float(), nullable=True))
    op.add_column('product_order', sa.Column('status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'stock', type_='foreignkey')
    op.drop_column('product_order', 'status')
    op.drop_column('product', 'p_unfired')
    # ### end Alembic commands ###
