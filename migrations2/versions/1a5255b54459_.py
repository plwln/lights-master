"""empty message

Revision ID: 1a5255b54459
Revises: 223d0a9ed75a
Create Date: 2019-08-15 09:54:17.714396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a5255b54459'
down_revision = '223d0a9ed75a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('product_order',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('doc_id', sa.Integer(), nullable=True),
    sa.Column('prod_id', sa.Integer(), nullable=True),
    sa.Column('count', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['doc_id'], ['document.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['prod_id'], ['product.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('product_order')
    # ### end Alembic commands ###
