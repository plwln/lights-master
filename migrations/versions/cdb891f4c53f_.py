"""empty message

Revision ID: cdb891f4c53f
Revises: 6e1c1198ef06
Create Date: 2019-08-12 16:35:01.209938

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cdb891f4c53f'
down_revision = '6e1c1198ef06'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_stock',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('stock_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['stock_id'], ['stock.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('component', sa.Column('unfired', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('component', 'unfired')
    op.drop_table('user_stock')
    # ### end Alembic commands ###