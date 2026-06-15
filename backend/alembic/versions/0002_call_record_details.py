"""add call record detail fields

Revision ID: 0002_call_record_details
Revises: 0001_initial_schema
Create Date: 2026-06-15 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa


revision: str = "0002_call_record_details"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("call_records", sa.Column("pickup_datetime", sa.DateTime(timezone=True), nullable=True))
    op.add_column("call_records", sa.Column("delivery_datetime", sa.DateTime(timezone=True), nullable=True))
    op.add_column("call_records", sa.Column("commodity_type", sa.String(length=255), nullable=True))
    op.add_column("call_records", sa.Column("weight", sa.Integer(), nullable=True))
    op.add_column("call_records", sa.Column("miles", sa.Integer(), nullable=True))
    op.add_column("call_records", sa.Column("num_of_pieces", sa.Integer(), nullable=True))
    op.add_column("call_records", sa.Column("dimensions", sa.String(length=255), nullable=True))
    op.add_column("call_records", sa.Column("transfer_successful", sa.Boolean(), nullable=True))
    op.add_column("call_records", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column("call_records", sa.Column("call_duration_seconds", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("call_records", "call_duration_seconds")
    op.drop_column("call_records", "failure_reason")
    op.drop_column("call_records", "transfer_successful")
    op.drop_column("call_records", "dimensions")
    op.drop_column("call_records", "num_of_pieces")
    op.drop_column("call_records", "miles")
    op.drop_column("call_records", "weight")
    op.drop_column("call_records", "commodity_type")
    op.drop_column("call_records", "delivery_datetime")
    op.drop_column("call_records", "pickup_datetime")
