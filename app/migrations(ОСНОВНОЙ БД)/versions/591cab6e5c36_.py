"""empty message

Revision ID: 591cab6e5c36
Revises: c73a21c0f7de
Create Date: 2019-09-13 17:35:29.842196

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '591cab6e5c36'
down_revision = 'c73a21c0f7de'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('component', sa.Column('note_count', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('component', 'note_count')
    # ### end Alembic commands ###
