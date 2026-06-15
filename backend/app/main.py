import logging
import os
import time

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import SessionLocal
from app.routers.calls import router as calls_router
from app.routers.carriers import router as carriers_router
from app.routers.health import router as health_router
from app.routers.loads import router as loads_router
from app.routers.metrics import router as metrics_router
from app.routers.offers import router as offers_router
from app.routers.transfers import router as transfer_router
from app.security import require_api_key


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="Carrier Sales Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(carriers_router, dependencies=[Depends(require_api_key)])
app.include_router(loads_router, dependencies=[Depends(require_api_key)])
app.include_router(offers_router, dependencies=[Depends(require_api_key)])
app.include_router(transfer_router, dependencies=[Depends(require_api_key)])
app.include_router(calls_router, dependencies=[Depends(require_api_key)])
app.include_router(metrics_router, dependencies=[Depends(require_api_key)])


@app.on_event("startup")
def wait_for_database() -> None:
    if settings.app_env.lower() in {"test", "testing"}:
        return

    max_attempts = 20
    for attempt in range(1, max_attempts + 1):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            logger.info("Database connection established")
            return
        except SQLAlchemyError as exc:
            logger.warning("Database unavailable on attempt %s/%s: %s", attempt, max_attempts, exc)
            time.sleep(1)
    logger.error("Database connection could not be established at startup")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Carrier sales backend online"}
