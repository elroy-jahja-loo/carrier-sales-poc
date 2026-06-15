from sqlalchemy import delete, or_, select

from app.database import SessionLocal
from app.demo_data import build_demo_loads
from app.models import CallRecord, Load, NegotiationSession


DEMO_RUN_PREFIXES = ("run_100", "test-run", "run_smoke")
DEMO_SESSION_PREFIXES = ("session_100", "test-run", "smoke-session")


def reset_demo_data(db=None) -> None:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        demo_loads = build_demo_loads()
        demo_load_ids = [row["load_id"] for row in demo_loads]
        existing_loads = {
            row.load_id: row for row in db.execute(select(Load).where(Load.load_id.in_(demo_load_ids))).scalars()
        }

        for row in demo_loads:
            existing = existing_loads.get(row["load_id"])
            if existing:
                for key, value in row.items():
                    setattr(existing, key, value)
            else:
                db.add(Load(**row))

        # Clear only deterministic demo/smoke records; real call history remains untouched.
        db.execute(
            delete(CallRecord).where(
                CallRecord.load_id.in_(demo_load_ids),
                or_(*[CallRecord.happyrobot_run_id.like(f"{prefix}%") for prefix in DEMO_RUN_PREFIXES]),
            )
        )
        db.execute(
            delete(NegotiationSession).where(
                NegotiationSession.load_id.in_(demo_load_ids),
                or_(*[NegotiationSession.session_id.like(f"{prefix}%") for prefix in DEMO_SESSION_PREFIXES]),
            )
        )

        db.commit()
        print(f"Reset {len(demo_loads)} demo loads to available status.")
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    reset_demo_data()
