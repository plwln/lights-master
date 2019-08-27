"""empty message

Revision ID: 030c65d45d2b
Revises: df03e31f57df
Create Date: 2019-07-02 12:40:53.304643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '030c65d45d2b'
down_revision = 'df03e31f57df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product', sa.Column('product_material', sa.String(length=255, collation='NOCASE'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product', 'product_material')
    # ### end Alembic commands ###
