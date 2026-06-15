from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import Load
from app.services.formatting import format_currency_whole, safe_human_time


def search_loads(
    db: Session,
    origin: str | None,
    destination: str | None,
    equipment_type: str | None,
    pickup_date: date | None,
    limit: int = 3,
) -> list[Load]:
    stmt = select(Load).where(Load.status == "available")

    filters = []
    if origin:
        filters.append(func.lower(Load.origin).contains(origin.lower()))
    if destination:
        filters.append(func.lower(Load.destination).contains(destination.lower()))
    if equipment_type:
        filters.append(func.lower(Load.equipment_type).contains(equipment_type.lower()))
    if pickup_date:
        filters.append(func.date(Load.pickup_datetime) == pickup_date)
    if filters:
        stmt = stmt.where(and_(*filters))

    rows = db.execute(stmt).scalars().all()
    if not rows:
        rows = db.execute(select(Load).where(Load.status == "available")).scalars().all()

    def score(load: Load) -> int:
        value = 0
        if equipment_type and equipment_type.lower() in load.equipment_type.lower():
            value += 4
        if origin and origin.lower() in load.origin.lower():
            value += 3
        if destination and destination.lower() in load.destination.lower():
            value += 3
        if pickup_date and load.pickup_datetime.date() == pickup_date:
            value += 2
        return value

    ranked = sorted(rows, key=score, reverse=True)
    return ranked[:limit]


def build_load_pitch(load: Load) -> str:
    pickup_text = safe_human_time(load.pickup_datetime)
    delivery_text = safe_human_time(load.delivery_datetime)
    rate_text = format_currency_whole(Decimal(load.loadboard_rate))
    weight_text = f"{load.weight:,} pounds" if load.weight else "standard weight"
    commodity_text = load.commodity_type or "general freight"
    notes_text = load.notes or "standard handling"
    return (
        f"I have a {load.equipment_type.lower()} load from {load.origin} to {load.destination} "
        f"picking up {pickup_text} and delivering {delivery_text}. "
        f"It is {weight_text} of {commodity_text}, {notes_text}, posted at {rate_text}."
    )
