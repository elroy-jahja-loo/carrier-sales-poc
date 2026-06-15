import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

os.environ["APP_ENV"] = "test"
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.demo_data import build_demo_loads
from app.models import Load
from app.reset_demo_data import reset_demo_data
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
    db.add_all([Load(**row) for row in build_demo_loads(datetime.now(timezone.utc))])
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


@pytest.mark.parametrize(
    "payload",
    [
        {
            "origin": "Kansas City, MO",
            "mc_number": "135797",
            "destination": "Minneapolis, MN",
            "pickup_date": "",
            "equipment_type": "Dry Van",
        },
        {
            "origin": "Kansas City, MO",
            "mc_number": "135797",
            "destination": "Minneapolis, MN",
            "pickup_date": "   ",
            "equipment_type": "Dry Van",
        },
        {
            "origin": "Kansas City, MO",
            "mc_number": "135797",
            "destination": "Minneapolis, MN",
            "equipment_type": "Dry Van",
        },
        {
            "origin": "Kansas City, MO",
            "mc_number": "135797",
            "destination": "Minneapolis, MN",
            "pickup_date": None,
            "equipment_type": "Dry Van",
        },
    ],
)
def test_load_search_accepts_empty_optional_pickup_date(payload):
    response = client.post("/api/loads/search", headers=api_headers(), json=payload)
    assert response.status_code == 200


def test_reset_demo_data_restores_kansas_city_dry_van_loads():
    db = TestingSessionLocal()
    try:
        for load in db.execute(select(Load).where(Load.origin == "Kansas City, MO")).scalars():
            load.status = "held"
        db.commit()
    finally:
        db.close()

    db = TestingSessionLocal()
    try:
        reset_demo_data(db)
    finally:
        db.close()

    response = client.post(
        "/api/loads/search",
        headers=api_headers(),
        json={
            "origin": "Kansas City, MO",
            "destination": "Minneapolis, MN",
            "equipment_type": "Dry Van",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["found"] is True
    assert payload["best_match"]["origin"] == "Kansas City, MO"
    assert payload["best_match"]["destination"] == "Minneapolis, MN"
    assert payload["best_match"]["equipment_type"] == "Dry Van"


def test_mock_transfer_leaves_another_kansas_city_variant_available():
    search_payload = {
        "origin": "Kansas City, MO",
        "destination": "Minneapolis, MN",
        "equipment_type": "Dry Van",
    }
    first = client.post("/api/loads/search", headers=api_headers(), json=search_payload)
    assert first.status_code == 200
    first_load_id = first.json()["best_match"]["load_id"]

    transfer = client.post(
        "/api/transfer/mock",
        headers=api_headers(),
        json={
            "session_id": "test-run-held-variant",
            "mc_number": "135797",
            "load_id": first_load_id,
            "accepted_rate": "1900",
        },
    )
    assert transfer.status_code == 200

    second = client.post("/api/loads/search", headers=api_headers(), json=search_payload)
    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["found"] is True
    assert second_payload["best_match"]["load_id"] != first_load_id
    assert second_payload["best_match"]["origin"] == "Kansas City, MO"
    assert second_payload["best_match"]["equipment_type"] == "Dry Van"


def test_equipment_fallback_preserves_dry_van_before_other_equipment():
    db = TestingSessionLocal()
    try:
        for load in db.execute(select(Load).where(Load.origin == "Kansas City, MO")).scalars():
            load.status = "held"
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/loads/search",
        headers=api_headers(),
        json={"origin": "Kansas City, MO", "equipment_type": "Dry Van"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["found"] is True
    assert all(item["equipment_type"] == "Dry Van" for item in payload["loads"])


def test_origin_only_search_returns_kansas_city_loads():
    response = client.post(
        "/api/loads/search",
        headers=api_headers(),
        json={"origin": "Kansas City, MO"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["found"] is True
    assert all(item["origin"] == "Kansas City, MO" for item in payload["loads"])


def test_offer_evaluate_accepts_within_max():
    response = client.post(
        "/api/offers/evaluate",
        headers=api_headers(),
        json={
            "session_id": "session_test_1",
            "mc_number": "123456",
            "load_id": "LD-1001",
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
            "load_id": "LD-1001",
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


def test_offer_evaluate_accepts_happyrobot_string_payload():
    response = client.post(
        "/api/offers/evaluate",
        headers=api_headers(),
        json={
            "session_id": "test-run-1",
            "mc_number": "135797",
            "load_id": "LD-1001",
            "carrier_offer": " $2,500 ",
            "round_number": "1",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "accept"
    assert payload["round_count"] == 1


def test_mock_transfer_accepts_happyrobot_string_rate():
    response = client.post(
        "/api/transfer/mock",
        headers=api_headers(),
        json={
            "session_id": "test-run-2",
            "mc_number": "135797",
            "load_id": "LD-1001",
            "accepted_rate": " 1,900 ",
        },
    )
    assert response.status_code == 200
    assert response.json()["load_status"] == "held"


def test_call_complete_accepts_happyrobot_string_numbers():
    response = client.post(
        "/api/calls/complete",
        headers=api_headers(),
        json={
            "happyrobot_run_id": "test-run-3",
            "session_id": "test-run-3",
            "mc_number": "135797",
            "carrier_name": "Test Carrier",
            "load_id": "LD-1001",
            "origin": "Kansas City, MO",
            "destination": "Minneapolis, MN",
            "equipment_type": "Dry Van",
            "loadboard_rate": "1900",
            "final_offer": "$1,900",
            "outcome": "booked",
            "sentiment": "positive",
            "call_summary": "Carrier booked load LD-1001 at 1900.",
            "transcript": "Test transcript",
            "negotiation_rounds": "1",
        },
    )
    assert response.status_code == 200
    assert response.json()["stored"] is True


def test_call_complete_empty_rate_strings_and_rounds():
    response = client.post(
        "/api/calls/complete",
        headers=api_headers(),
        json={"loadboard_rate": "", "final_offer": " ", "negotiation_rounds": ""},
    )
    assert response.status_code == 200
    assert response.json()["stored"] is True


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
