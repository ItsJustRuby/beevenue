"""empty message

Revision ID: 139d8410796c
Revises: 9612abc1d885
Create Date: 2022-02-06 08:29:49.655116

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "139d8410796c"
down_revision = "9612abc1d885"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("medium", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("medium", sa.Column("height", sa.Integer(), nullable=True))
    op.add_column(
        "medium", sa.Column("filesize", sa.BigInteger(), nullable=True)
    )
    op.add_column("medium", sa.Column("insert_date", sa.Date(), nullable=True))
    op.drop_column("medium", "aspect_ratio")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "medium",
        sa.Column(
            "aspect_ratio",
            sa.NUMERIC(precision=4, scale=2),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("medium", "insert_date")
    op.drop_column("medium", "filesize")
    op.drop_column("medium", "height")
    op.drop_column("medium", "width")
    # ### end Alembic commands ###
