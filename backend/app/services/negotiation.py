from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Load, NegotiationSession
from app.services.formatting import format_currency_whole


def evaluate_offer(
    db: Session,
    session_id: str,
    mc_number: str,
    load_id: str,
    carrier_offer: Decimal,
    round_number: int,
) -> dict:
    settings = get_settings()
    max_rounds = settings.negotiation_max_rounds

    load = db.execute(select(Load).where(Load.load_id == load_id)).scalar_one_or_none()
    if not load:
        return {
            "decision": "decline",
            "status": "declined",
            "load_id": load_id,
            "carrier_offer": carrier_offer,
            "round_count": round_number,
            "max_rounds": max_rounds,
            "message_to_carrier": "I could not find that load right now. I can check another load for you.",
            "next_action": "end_or_search_again",
        }

    if load.status != "available":
        return {
            "decision": "decline",
            "status": "declined",
            "load_id": load_id,
            "carrier_offer": carrier_offer,
            "round_count": round_number,
            "max_rounds": max_rounds,
            "message_to_carrier": "That load is no longer available. I can check for another load on that lane.",
            "next_action": "search_again",
        }

    negotiation = db.execute(
        select(NegotiationSession).where(
            NegotiationSession.session_id == session_id,
            NegotiationSession.load_id == load_id,
        )
    ).scalar_one_or_none()

    loadboard_rate = Decimal(load.loadboard_rate)
    max_acceptable_rate = _currency(
        loadboard_rate * (Decimal("1") + Decimal(str(settings.default_max_rate_premium_percent)) / Decimal("100"))
    )

    if not negotiation:
        negotiation = NegotiationSession(
            session_id=session_id,
            mc_number=mc_number,
            load_id=load_id,
            loadboard_rate=loadboard_rate,
            max_acceptable_rate=max_acceptable_rate,
            round_count=0,
            status="active",
        )
        db.add(negotiation)

    if negotiation.status in {"accepted", "declined"}:
        decision = "accept" if negotiation.status == "accepted" else "decline"
        key = "accepted_rate" if decision == "accept" else "counter_offer"
        value = negotiation.final_rate if decision == "accept" else None
        response = {
            "decision": decision,
            "status": negotiation.status,
            "load_id": load_id,
            "carrier_offer": carrier_offer,
            "round_count": negotiation.round_count,
            "max_rounds": max_rounds,
            "message_to_carrier": "This negotiation is already closed.",
            "next_action": "mock_transfer" if decision == "accept" else "end_or_search_again",
            key: value,
        }
        return response

    negotiation.round_count = max(negotiation.round_count, round_number)
    negotiation.last_carrier_offer = carrier_offer

    if carrier_offer <= max_acceptable_rate:
        negotiation.status = "accepted"
        negotiation.final_rate = carrier_offer
        db.commit()
        return {
            "decision": "accept",
            "status": "accepted",
            "load_id": load_id,
            "carrier_offer": carrier_offer,
            "accepted_rate": carrier_offer,
            "round_count": negotiation.round_count,
            "max_rounds": max_rounds,
            "message_to_carrier": (
                f"We can accept {format_currency_whole(carrier_offer)} on this load. "
                "I'll connect you with a sales rep to finalize the booking."
            ),
            "next_action": "mock_transfer",
        }

    if negotiation.round_count > max_rounds:
        negotiation.status = "declined"
        db.commit()
        return {
            "decision": "decline",
            "status": "declined",
            "load_id": load_id,
            "carrier_offer": carrier_offer,
            "round_count": negotiation.round_count,
            "max_rounds": max_rounds,
            "message_to_carrier": (
                "I'm sorry, we can't make that rate work on this load. "
                "I can check for another load or have someone follow up."
            ),
            "next_action": "no_agreement",
        }

    if negotiation.round_count == 1:
        counter_offer = loadboard_rate
    elif negotiation.round_count == 2:
        counter_offer = _currency((loadboard_rate + max_acceptable_rate) / Decimal("2"))
    elif negotiation.round_count == 3:
        counter_offer = max_acceptable_rate
    else:
        negotiation.status = "declined"
        db.commit()
        return {
            "decision": "decline",
            "status": "declined",
            "load_id": load_id,
            "carrier_offer": carrier_offer,
            "round_count": negotiation.round_count,
            "max_rounds": max_rounds,
            "message_to_carrier": (
                "I'm sorry, we can't make that rate work on this load. "
                "I can check for another load or have someone follow up."
            ),
            "next_action": "end_or_search_again",
        }

    negotiation.last_system_counter = counter_offer
    db.commit()

    return {
        "decision": "counter",
        "status": "active",
        "load_id": load_id,
        "carrier_offer": carrier_offer,
        "counter_offer": counter_offer,
        "round_count": negotiation.round_count,
        "max_rounds": max_rounds,
        "message_to_carrier": _counter_message(carrier_offer, counter_offer, negotiation.round_count, max_rounds),
        "next_action": "accept_or_decline" if negotiation.round_count >= max_rounds else "continue_negotiation",
    }


def _currency(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _counter_message(carrier_offer: Decimal, counter_offer: Decimal, round_count: int, max_rounds: int) -> str:
    if round_count >= max_rounds:
        return (
            f"I can't get to {format_currency_whole(carrier_offer)}. "
            f"My best and final offer is {format_currency_whole(counter_offer)}. "
            "Can you accept that rate?"
        )
    return (
        f"I can't get to {format_currency_whole(carrier_offer)}, "
        f"but I can offer {format_currency_whole(counter_offer)}. "
        "Would that work for you?"
    )
