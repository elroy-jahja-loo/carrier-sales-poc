from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MetricsSummaryResponse
from app.services.metrics import get_metrics_summary


router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummaryResponse)
def summary(db: Session = Depends(get_db)) -> MetricsSummaryResponse:
    return MetricsSummaryResponse(**get_metrics_summary(db))
