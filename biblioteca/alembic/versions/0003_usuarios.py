"""crea usuarios, el tipo enum rolusuario y su relación con socios

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "rol",
            sa.Enum(
                "admin",
                "bibliotecario",
                "socio",
                name="rolusuario",
            ),
            nullable=False,
            server_default="socio",
        ),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "intentos_fallidos",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "bloqueado_hasta",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("socio_id", sa.Integer(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["socio_id"],
            ["socios.id"],
            name="fk_usuarios_socio_id_socios",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_usuarios"),
        sa.UniqueConstraint("socio_id", name="uq_usuarios_socio_id"),
    )
    op.create_index(
        "ix_usuarios_email",
        "usuarios",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
    # El Enum de PostgreSQL crea un tipo en la base de datos.
    sa.Enum(name="rolusuario").drop(op.get_bind(), checkfirst=True)
