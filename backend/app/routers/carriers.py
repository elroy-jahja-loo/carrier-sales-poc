from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import CarrierVerification
from app.schemas import CarrierVerifyRequest, CarrierVerifyResponse
from app.services.fmcsa import FmcsaClient


router = APIRouter(prefix="/api/carriers", tags=["carriers"])


@router.post("/verify", response_model=CarrierVerifyResponse)
async def verify_carrier(payload: CarrierVerifyRequest, db: Session = Depends(get_db)) -> CarrierVerifyResponse:
    settings = get_settings()
    client = FmcsaClient(base_url=settings.fmcsa_base_url, api_key=settings.fmcsa_api_key)
    verification = await client.verify_mc_number(payload.mc_number)

    db.add(
        CarrierVerification(
            mc_number=verification.mc_number,
            dot_number=verification.dot_number,
            legal_name=verification.legal_name,
            dba_name=verification.dba_name,
            status=verification.authority_status,
            allowed_to_operate=verification.allowed_to_operate,
            out_of_service=verification.out_of_service,
            raw_response=verification.raw_response,
        )
    )
    db.commit()

    return CarrierVerifyResponse(
        eligible=verification.eligible,
        verification_status=verification.verification_status,
        mc_number=verification.mc_number,
        dot_number=verification.dot_number,
        legal_name=verification.legal_name,
        dba_name=verification.dba_name,
        authority_status=verification.authority_status,
        allowed_to_operate=verification.allowed_to_operate,
        out_of_service=verification.out_of_service,
        reason=verification.reason,
        recommended_agent_message=verification.recommended_agent_message,
    )
