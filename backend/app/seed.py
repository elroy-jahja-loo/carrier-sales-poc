from decimal import Decimal

from sqlalchemy import select

from app.database import SessionLocal
from app.demo_data import build_demo_loads
from app.models import CallRecord, Load


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(Load.id).limit(1))
        if not existing:
            db.add_all([Load(**row) for row in build_demo_loads()])

        existing_calls = db.scalar(select(CallRecord.id).limit(1))
        if not existing_calls:
            sample_calls = [
                CallRecord(
                    happyrobot_run_id="run_1001",
                    session_id="session_1001",
                    mc_number="123456",
                    carrier_name="ABC Trucking",
                    load_id="LD-1001",
                    origin="Dallas, TX",
                    destination="Atlanta, GA",
                    equipment_type="Dry Van",
                    loadboard_rate=Decimal("2400"),
                    final_offer=Decimal("2525"),
                    outcome="booked",
                    sentiment="positive",
                    call_summary="Carrier verified and booked at $2,525.",
                    transcript="Carrier asked for Dallas to Atlanta load and accepted after one counter.",
                    negotiation_rounds=2,
                ),
                CallRecord(
                    happyrobot_run_id="run_1002",
                    session_id="session_1002",
                    mc_number="222333",
                    carrier_name="Prime Freight",
                    load_id="LD-1002",
                    origin="Chicago, IL",
                    destination="Denver, CO",
                    equipment_type="Reefer",
                    loadboard_rate=Decimal("2850"),
                    final_offer=Decimal("3020"),
                    outcome="booked",
                    sentiment="neutral",
                    call_summary="Carrier accepted final counter after 3 rounds.",
                    transcript="Carrier pushed above max, accepted cap in final round.",
                    negotiation_rounds=3,
                ),
                CallRecord(
                    happyrobot_run_id="run_1003",
                    session_id="session_1003",
                    mc_number="999888",
                    carrier_name="Legacy Lines",
                    load_id="LD-1008",
                    origin="Houston, TX",
                    destination="New Orleans, LA",
                    equipment_type="Flatbed",
                    loadboard_rate=Decimal("1500"),
                    final_offer=Decimal("1850"),
                    outcome="declined",
                    sentiment="negative",
                    call_summary="No rate agreement reached by round 3.",
                    transcript="Carrier insisted on $1,850. System declined.",
                    negotiation_rounds=3,
                ),
                CallRecord(
                    happyrobot_run_id="run_1004",
                    session_id="session_1004",
                    mc_number="666777",
                    carrier_name="Blue Ridge Logistics",
                    load_id="LD-1005",
                    origin="Columbus, OH",
                    destination="Newark, NJ",
                    equipment_type="Dry Van",
                    loadboard_rate=Decimal("2050"),
                    final_offer=None,
                    outcome="ineligible",
                    sentiment="neutral",
                    call_summary="Carrier failed authority check.",
                    transcript="Verification returned inactive authority.",
                    negotiation_rounds=0,
                ),
                CallRecord(
                    happyrobot_run_id="run_1005",
                    session_id="session_1005",
                    mc_number="444555",
                    carrier_name="Evergreen Carriers",
                    load_id=None,
                    origin="Miami, FL",
                    destination="Atlanta, GA",
                    equipment_type="Dry Van",
                    loadboard_rate=None,
                    final_offer=None,
                    outcome="no_load_found",
                    sentiment="neutral",
                    call_summary="No matching load found on requested lane.",
                    transcript="Carrier requested Miami outbound load not available.",
                    negotiation_rounds=0,
                ),
            ]
            db.add_all(sample_calls)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
