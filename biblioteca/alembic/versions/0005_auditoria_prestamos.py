"""agrega prestamos.registrado_por_id (auditoría)

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prestamos",
        sa.Column("registrado_por_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_prestamos_registrado_por_id_usuarios",
        "prestamos",
        "usuarios",
        ["registrado_por_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_prestamos_registrado_por_id_usuarios",
        "prestamos",
        type_="foreignkey",
    )
    op.drop_column("prestamos", "registrado_por_id")
