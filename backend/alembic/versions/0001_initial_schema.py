"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-15 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "loads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("load_id", sa.String(length=50), nullable=False),
        sa.Column("origin", sa.String(length=255), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("pickup_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("equipment_type", sa.String(length=100), nullable=False),
        sa.Column("loadboard_rate", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=True),
        sa.Column("commodity_type", sa.String(length=255), nullable=True),
        sa.Column("num_of_pieces", sa.Integer(), nullable=True),
        sa.Column("miles", sa.Integer(), nullable=True),
        sa.Column("dimensions", sa.String(length=255), nullable=True),
        sa.Column("status", sa.Enum("available", "held", "booked", name="load_status"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("load_id"),
    )
    op.create_index(op.f("ix_loads_id"), "loads", ["id"], unique=False)
    op.create_index(op.f("ix_loads_load_id"), "loads", ["load_id"], unique=False)
    op.create_index(op.f("ix_loads_origin"), "loads", ["origin"], unique=False)
    op.create_index(op.f("ix_loads_destination"), "loads", ["destination"], unique=False)
    op.create_index(op.f("ix_loads_equipment_type"), "loads", ["equipment_type"], unique=False)
    op.create_index(op.f("ix_loads_status"), "loads", ["status"], unique=False)

    op.create_table(
        "carrier_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mc_number", sa.String(length=20), nullable=False),
        sa.Column("dot_number", sa.String(length=20), nullable=True),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("dba_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("allowed_to_operate", sa.Boolean(), nullable=False),
        sa.Column("out_of_service", sa.Boolean(), nullable=False),
        sa.Column("raw_response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_carrier_verifications_id"), "carrier_verifications", ["id"], unique=False)
    op.create_index(
        op.f("ix_carrier_verifications_mc_number"), "carrier_verifications", ["mc_number"], unique=False
    )

    op.create_table(
        "negotiation_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("mc_number", sa.String(length=20), nullable=False),
        sa.Column("load_id", sa.String(length=50), nullable=False),
        sa.Column("loadboard_rate", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("max_acceptable_rate", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("round_count", sa.Integer(), nullable=False),
        sa.Column("last_carrier_offer", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("last_system_counter", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "accepted", "declined", "expired", name="negotiation_status"),
            nullable=False,
        ),
        sa.Column("final_rate", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_negotiation_sessions_id"), "negotiation_sessions", ["id"], unique=False)
    op.create_index(
        op.f("ix_negotiation_sessions_session_id"), "negotiation_sessions", ["session_id"], unique=False
    )
    op.create_index(op.f("ix_negotiation_sessions_mc_number"), "negotiation_sessions", ["mc_number"], unique=False)
    op.create_index(op.f("ix_negotiation_sessions_load_id"), "negotiation_sessions", ["load_id"], unique=False)
    op.create_index(op.f("ix_negotiation_sessions_status"), "negotiation_sessions", ["status"], unique=False)

    op.create_table(
        "call_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("happyrobot_run_id", sa.String(length=100), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("mc_number", sa.String(length=20), nullable=True),
        sa.Column("carrier_name", sa.String(length=255), nullable=True),
        sa.Column("load_id", sa.String(length=50), nullable=True),
        sa.Column("origin", sa.String(length=255), nullable=True),
        sa.Column("destination", sa.String(length=255), nullable=True),
        sa.Column("equipment_type", sa.String(length=100), nullable=True),
        sa.Column("loadboard_rate", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("final_offer", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "outcome",
            sa.Enum(
                "booked",
                "declined",
                "ineligible",
                "transferred",
                "no_load_found",
                "unresolved",
                "unknown",
                name="call_outcome",
            ),
            nullable=False,
        ),
        sa.Column(
            "sentiment",
            sa.Enum("positive", "neutral", "negative", "unknown", name="call_sentiment"),
            nullable=False,
        ),
        sa.Column("call_summary", sa.Text(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("negotiation_rounds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_call_records_id"), "call_records", ["id"], unique=False)
    op.create_index(op.f("ix_call_records_happyrobot_run_id"), "call_records", ["happyrobot_run_id"], unique=False)
    op.create_index(op.f("ix_call_records_session_id"), "call_records", ["session_id"], unique=False)
    op.create_index(op.f("ix_call_records_mc_number"), "call_records", ["mc_number"], unique=False)
    op.create_index(op.f("ix_call_records_load_id"), "call_records", ["load_id"], unique=False)
    op.create_index(op.f("ix_call_records_outcome"), "call_records", ["outcome"], unique=False)
    op.create_index(op.f("ix_call_records_sentiment"), "call_records", ["sentiment"], unique=False)
    op.create_index(op.f("ix_call_records_created_at"), "call_records", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_call_records_created_at"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_sentiment"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_outcome"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_load_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_mc_number"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_session_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_happyrobot_run_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_id"), table_name="call_records")
    op.drop_table("call_records")

    op.drop_index(op.f("ix_negotiation_sessions_status"), table_name="negotiation_sessions")
    op.drop_index(op.f("ix_negotiation_sessions_load_id"), table_name="negotiation_sessions")
    op.drop_index(op.f("ix_negotiation_sessions_mc_number"), table_name="negotiation_sessions")
    op.drop_index(op.f("ix_negotiation_sessions_session_id"), table_name="negotiation_sessions")
    op.drop_index(op.f("ix_negotiation_sessions_id"), table_name="negotiation_sessions")
    op.drop_table("negotiation_sessions")

    op.drop_index(op.f("ix_carrier_verifications_mc_number"), table_name="carrier_verifications")
    op.drop_index(op.f("ix_carrier_verifications_id"), table_name="carrier_verifications")
    op.drop_table("carrier_verifications")

    op.drop_index(op.f("ix_loads_status"), table_name="loads")
    op.drop_index(op.f("ix_loads_equipment_type"), table_name="loads")
    op.drop_index(op.f("ix_loads_destination"), table_name="loads")
    op.drop_index(op.f("ix_loads_origin"), table_name="loads")
    op.drop_index(op.f("ix_loads_load_id"), table_name="loads")
    op.drop_index(op.f("ix_loads_id"), table_name="loads")
    op.drop_table("loads")
