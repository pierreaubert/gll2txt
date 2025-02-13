"""Initial migration

Revision ID: 06961b9faac8
Revises:
Create Date: 2025-02-02 07:53:57.383627

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "06961b9faac8"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "speakers",
        sa.Column("gll_file", sa.String(), nullable=False),
        sa.Column("speaker_name", sa.String(), nullable=False),
        sa.Column("skip", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("gll_file"),
        if_not_exists=True,
    )
    op.create_table(
        "config_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gll_file", sa.String(), nullable=False),
        sa.Column("config_file", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["gll_file"],
            ["speakers.gll_file"],
        ),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("config_files")
    op.drop_table("speakers")
    # ### end Alembic commands ###
