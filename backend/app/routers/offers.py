from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OfferEvaluateRequest, OfferEvaluateResponse
from app.services.negotiation import evaluate_offer


router = APIRouter(prefix="/api/offers", tags=["offers"])


@router.post("/evaluate", response_model=OfferEvaluateResponse)
def evaluate(payload: OfferEvaluateRequest, db: Session = Depends(get_db)) -> OfferEvaluateResponse:
    result = evaluate_offer(
        db=db,
        session_id=payload.session_id,
        mc_number=payload.mc_number,
        load_id=payload.load_id,
        carrier_offer=payload.carrier_offer,
        round_number=payload.round_number,
    )
    return OfferEvaluateResponse(**result)
