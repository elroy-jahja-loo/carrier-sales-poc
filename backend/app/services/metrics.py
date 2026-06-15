from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CallRecord, CarrierVerification


def get_metrics_summary(db: Session) -> dict:
    total_calls = db.scalar(select(func.count(CallRecord.id))) or 0
    verified_carriers = db.scalar(
        select(func.count(CarrierVerification.id)).where(CarrierVerification.allowed_to_operate.is_(True))
    ) or 0
    ineligible_carriers = db.scalar(
        select(func.count(CarrierVerification.id)).where(CarrierVerification.allowed_to_operate.is_(False))
    ) or 0

    outcome_counts_rows = db.execute(
        select(CallRecord.outcome, func.count(CallRecord.id)).group_by(CallRecord.outcome)
    ).all()
    sentiment_counts_rows = db.execute(
        select(CallRecord.sentiment, func.count(CallRecord.id)).group_by(CallRecord.sentiment)
    ).all()

    outcomes = {
        "booked": 0,
        "declined": 0,
        "ineligible": 0,
        "no_load_found": 0,
        "unresolved": 0,
        "transferred": 0,
        "unknown": 0,
    }
    for outcome, count in outcome_counts_rows:
        outcomes[str(outcome)] = count

    sentiment = {"positive": 0, "neutral": 0, "negative": 0, "unknown": 0}
    for sentiment_key, count in sentiment_counts_rows:
        sentiment[str(sentiment_key)] = count

    successful_calls = outcomes.get("booked", 0) + outcomes.get("transferred", 0)
    booked_calls = successful_calls
    declined_calls = outcomes.get("declined", 0)
    no_load_found_calls = outcomes.get("no_load_found", 0)
    unresolved_calls = outcomes.get("unresolved", 0)

    accepted_filter = CallRecord.outcome.in_(["booked", "transferred"])
    avg_final_offer = db.scalar(
        select(func.avg(CallRecord.final_offer)).where(accepted_filter, CallRecord.final_offer.is_not(None))
    )
    avg_loadboard_rate = db.scalar(
        select(func.avg(CallRecord.loadboard_rate)).where(
            accepted_filter,
            CallRecord.final_offer.is_not(None),
            CallRecord.loadboard_rate.is_not(None),
        )
    )

    average_final_offer = float(avg_final_offer or 0)
    average_loadboard_rate = float(avg_loadboard_rate or 0)

    avg_premium = db.scalar(
        select(
            func.avg(
                ((CallRecord.final_offer - CallRecord.loadboard_rate) / CallRecord.loadboard_rate) * 100
            )
        ).where(
            accepted_filter,
            CallRecord.final_offer.is_not(None),
            CallRecord.loadboard_rate.is_not(None),
            CallRecord.loadboard_rate > 0,
        )
    )
    average_premium_percent = float(avg_premium or 0)
    average_negotiation_rounds = db.scalar(
        select(func.avg(CallRecord.negotiation_rounds)).where(CallRecord.negotiation_rounds.is_not(None))
    )
    negotiated_calls = db.scalar(select(func.count(CallRecord.id)).where(CallRecord.negotiation_rounds > 0)) or 0
    negotiation_acceptance_rate = float(successful_calls / negotiated_calls) if negotiated_calls else 0.0

    booking_rate = float(successful_calls / total_calls) if total_calls else 0.0

    bookings_over_time = _bookings_over_time(db)

    return {
        "total_calls": int(total_calls),
        "verified_carriers": int(verified_carriers),
        "ineligible_carriers": int(ineligible_carriers),
        "booked_calls": int(booked_calls),
        "declined_calls": int(declined_calls),
        "no_load_found_calls": int(no_load_found_calls),
        "unresolved_calls": int(unresolved_calls),
        "booking_rate": round(booking_rate, 4),
        "average_final_offer": round(average_final_offer, 2),
        "average_loadboard_rate": round(average_loadboard_rate, 2),
        "average_premium_percent": round(average_premium_percent, 2),
        "average_accepted_rate": round(average_final_offer, 2),
        "average_accepted_loadboard_rate": round(average_loadboard_rate, 2),
        "average_accepted_premium_percent": round(average_premium_percent, 2),
        "average_negotiation_rounds": round(float(average_negotiation_rounds or 0), 2),
        "negotiation_acceptance_rate": round(negotiation_acceptance_rate, 4),
        "follow_up_count": int(declined_calls + no_load_found_calls + unresolved_calls + outcomes.get("ineligible", 0)),
        "sentiment": sentiment,
        "outcomes": outcomes,
        "bookings_over_time": bookings_over_time,
    }


def _bookings_over_time(db: Session) -> list[dict[str, int | str]]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=6)
    rows = db.execute(
        select(CallRecord.created_at)
        .where(CallRecord.created_at >= start)
        .order_by(CallRecord.created_at.asc())
    ).scalars()

    buckets = defaultdict(int)
    for ts in rows:
        day_key = ts.date().isoformat()
        buckets[day_key] += 1

    result = []
    for day_offset in range(7):
        day = (start + timedelta(days=day_offset)).date().isoformat()
        result.append({"date": day, "calls": buckets.get(day, 0)})
    return result


def decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)
