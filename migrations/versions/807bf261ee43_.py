"""empty message

Revision ID: 807bf261ee43
Revises: ae45db382230
Create Date: 2019-12-12 00:32:31.306282

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '807bf261ee43'
down_revision = 'ae45db382230'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('datesssss', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'datesssss')
    # ### end Alembic commands ###
