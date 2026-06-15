from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Load
from app.schemas import MockTransferRequest, MockTransferResponse


router = APIRouter(prefix="/api/transfer", tags=["transfer"])


@router.post("/mock", response_model=MockTransferResponse)
def mock_transfer(payload: MockTransferRequest, db: Session = Depends(get_db)) -> MockTransferResponse:
    load = db.execute(select(Load).where(Load.load_id == payload.load_id)).scalar_one_or_none()
    if load:
        load.status = "held"
        db.commit()

    return MockTransferResponse(
        transfer_status="successful",
        mocked=True,
        message_to_carrier=(
            "Transfer was successful. A sales representative has the load details "
            "and can finalize the booking with you now."
        ),
        load_status="held" if load else "unknown",
    )
