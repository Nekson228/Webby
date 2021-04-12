"""

Revision ID: b8edf353543c
Revises: a14f10c51cb6
Create Date: 2021-03-28 20:10:24.630867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8edf353543c'
down_revision = 'a14f10c51cb6'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('rank', sa.VARCHAR(), nullable=True))
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'rank_id')
    # ### end Alembic commands ###