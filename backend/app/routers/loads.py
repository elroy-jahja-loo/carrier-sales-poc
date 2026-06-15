from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoadItem, LoadSearchRequest, LoadSearchResponse
from app.services.loads import build_load_pitch, search_loads


router = APIRouter(prefix="/api/loads", tags=["loads"])


@router.post("/search", response_model=LoadSearchResponse)
def load_search(payload: LoadSearchRequest, db: Session = Depends(get_db)) -> LoadSearchResponse:
    loads = search_loads(
        db=db,
        origin=payload.origin,
        destination=payload.destination,
        equipment_type=payload.equipment_type,
        pickup_date=payload.pickup_date,
        limit=3,
    )

    if not loads:
        return LoadSearchResponse(
            found=False,
            count=0,
            best_match=None,
            loads=[],
            recommended_agent_message=(
                "I'm not seeing a matching load for that lane right now. "
                "I can check another lane or have a rep follow up."
            ),
        )

    serialized = [
        LoadItem(
            load_id=load.load_id,
            origin=load.origin,
            destination=load.destination,
            pickup_datetime=load.pickup_datetime,
            delivery_datetime=load.delivery_datetime,
            equipment_type=load.equipment_type,
            loadboard_rate=load.loadboard_rate,
            notes=load.notes,
            weight=load.weight,
            commodity_type=load.commodity_type,
            num_of_pieces=load.num_of_pieces,
            miles=load.miles,
            dimensions=load.dimensions,
            pitch=build_load_pitch(load),
        )
        for load in loads
    ]

    return LoadSearchResponse(found=True, count=len(serialized), best_match=serialized[0], loads=serialized)
