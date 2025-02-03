"""add_speaker_properties

Revision ID: d29780e56e25
Revises: 06961b9faac8
Create Date: 2025-02-02 15:02:18.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d29780e56e25"
down_revision: Union[str, None] = "06961b9faac8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to speakers table
    with op.batch_alter_table("speakers") as batch_op:
        batch_op.add_column(sa.Column("sensitivity", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("impedance", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("weight", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("height", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("width", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("depth", sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove columns from speakers table
    with op.batch_alter_table("speakers") as batch_op:
        batch_op.drop_column("depth")
        batch_op.drop_column("width")
        batch_op.drop_column("height")
        batch_op.drop_column("weight")
        batch_op.drop_column("impedance")
        batch_op.drop_column("sensitivity")
