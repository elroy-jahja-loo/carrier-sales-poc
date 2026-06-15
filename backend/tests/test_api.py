import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

os.environ["APP_ENV"] = "test"
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models import Load
from app.services.fmcsa import _extract_carrier_data, normalize_mc_number


TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(
        Load(
            load_id="LD-T1",
            origin="Dallas, TX",
            destination="Atlanta, GA",
            pickup_datetime=datetime.now(timezone.utc) + timedelta(days=1),
            delivery_datetime=datetime.now(timezone.utc) + timedelta(days=2),
            equipment_type="Dry Van",
            loadboard_rate=Decimal("2400"),
            notes="No-touch",
            weight=35000,
            commodity_type="Food",
            num_of_pieces=10,
            miles=781,
            dimensions="53ft trailer",
            status="available",
        )
    )
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def api_headers():
    return {"X-API-Key": get_settings().app_api_key}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_key_required():
    response = client.post("/api/loads/search", json={})
    assert response.status_code == 401


def test_load_search_returns_load():
    response = client.post(
        "/api/loads/search",
        headers=api_headers(),
        json={"origin": "Dallas", "destination": "Atlanta", "equipment_type": "Dry Van"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["found"] is True
    assert payload["count"] >= 1


def test_offer_evaluate_accepts_within_max():
    response = client.post(
        "/api/offers/evaluate",
        headers=api_headers(),
        json={
            "session_id": "session_test_1",
            "mc_number": "123456",
            "load_id": "LD-T1",
            "carrier_offer": 2450,
            "round_number": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "accept"


def test_offer_evaluate_counters_above_max():
    response = client.post(
        "/api/offers/evaluate",
        headers=api_headers(),
        json={
            "session_id": "session_test_2",
            "mc_number": "123456",
            "load_id": "LD-T1",
            "carrier_offer": 3000,
            "round_number": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "counter"


def test_call_completion_stores_record():
    response = client.post(
        "/api/calls/complete",
        headers=api_headers(),
        json={
            "session_id": "session_complete",
            "mc_number": "123456",
            "outcome": "booked",
            "sentiment": "positive",
        },
    )
    assert response.status_code == 200
    assert response.json()["stored"] is True


def test_metrics_summary_fields_present():
    response = client.get("/api/metrics/summary", headers=api_headers())
    assert response.status_code == 200
    payload = response.json()
    for key in ["total_calls", "booking_rate", "sentiment", "outcomes"]:
        assert key in payload


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("135797", "135797"),
        ("MC135797", "135797"),
        ("MC-135797", "135797"),
        ("MC 135797", "135797"),
        ("#135797", "135797"),
    ],
)
def test_normalize_mc_number(raw, expected):
    assert normalize_mc_number(raw) == expected


@pytest.mark.parametrize(
    "payload",
    [
        {"content": {"carrier": {"legalName": "ABC TRUCKING", "dotNumber": "123"}}},
        {"content": [{"carrier": {"legalName": "ABC TRUCKING", "dotNumber": "123"}}]},
        {"content": [{"legalName": "ABC TRUCKING", "dotNumber": "123"}]},
        {"carrier": {"legalName": "ABC TRUCKING", "dotNumber": "123"}},
        {"legalName": "ABC TRUCKING", "dotNumber": "123"},
        {"content": [{"allowedToOperate": "Y", "phyCity": "Dallas", "phyState": "TX"}]},
    ],
)
def test_extract_carrier_data_supported_shapes(payload):
    data = _extract_carrier_data(payload)
    assert data is not None
    assert any(key in data for key in ["legalName", "dotNumber", "allowedToOperate", "phyCity"])


def test_extract_carrier_data_returns_none_for_unrecognized_payload():
    assert _extract_carrier_data({"content": {"message": "No carrier found"}}) is None
