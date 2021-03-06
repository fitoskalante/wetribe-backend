"""empty message

Revision ID: 1d7903bb7029
Revises: 
Create Date: 2019-12-16 11:35:50.692153

"""
from alembic import op
import sqlalchemy as sa, sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '1d7903bb7029'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('interests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('image_url', sa.String(), nullable=True),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lng', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('flask_dance_oauth',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('token', sqlalchemy_utils.types.json.JSONType(), nullable=False),
    sa.Column('provider_user_id', sa.String(length=256), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider_user_id')
    )
    op.create_table('token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('userinterests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('interest_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['interest_id'], ['interests.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('attendances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('eventcategories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('eventcategories')
    op.drop_table('comments')
    op.drop_table('attendances')
    op.drop_table('userinterests')
    op.drop_table('token')
    op.drop_table('flask_dance_oauth')
    op.drop_table('events')
    op.drop_table('users')
    op.drop_table('interests')
    op.drop_table('categories')
    # ### end Alembic commands ###
