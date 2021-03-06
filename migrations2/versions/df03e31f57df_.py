"""empty message

Revision ID: df03e31f57df
Revises: 520909fdb700
Create Date: 2019-07-02 11:11:31.916292

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df03e31f57df'
down_revision = '520909fdb700'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('component',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('component_name', sa.String(length=255, collation='NOCASE'), nullable=False),
    sa.Column('component_unit', sa.String(length=255, collation='NOCASE'), nullable=True),
    sa.Column('component_item', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('component_item'),
    sa.UniqueConstraint('component_name')
    )
    op.create_table('product',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_name', sa.String(length=255, collation='NOCASE'), nullable=False),
    sa.Column('product_power', sa.Integer(), nullable=False),
    sa.Column('product_item', sa.Integer(), nullable=True),
    sa.Column('product_weight', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('product_item'),
    sa.UniqueConstraint('product_name')
    )
    op.create_table('specification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('component_type', sa.String(length=255, collation='NOCASE'), nullable=True),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('component_id', sa.Integer(), nullable=True),
    sa.Column('count', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['component_id'], ['component.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('specification')
    op.drop_table('product')
    op.drop_table('component')
    # ### end Alembic commands ###
