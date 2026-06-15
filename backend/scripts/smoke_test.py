#!/usr/bin/env python3

import argparse
import json
import sys
from datetime import datetime, timezone
from urllib import error, parse, request


def http_json(method: str, url: str, payload: dict | None = None, api_key: str | None = None) -> tuple[int, dict | str]:
    data = None
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = request.Request(url, method=method, headers=headers, data=data)
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, body
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def print_result(label: str, ok: bool, details: str = "") -> None:
    state = "PASS" if ok else "FAIL"
    suffix = f" - {details}" if details else ""
    print(f"[{state}] {label}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Carrier Sales POC smoke test")
    parser.add_argument("--api-base-url", default="http://localhost:8000")
    parser.add_argument("--app-api-key", required=True)
    args = parser.parse_args()

    base = args.api_base_url.rstrip("/")
    key = args.app_api_key
    failures = 0

    status, body = http_json("GET", f"{base}/health")
    ok = status == 200 and isinstance(body, dict) and body.get("status") == "ok"
    print_result("GET /health", ok, f"status={status}")
    failures += 0 if ok else 1

    status, body = http_json("POST", f"{base}/api/carriers/verify", {"mc_number": "123456"}, key)
    ok = status == 200 and isinstance(body, dict) and "eligible" in body and "verification_status" in body
    print_result("POST /api/carriers/verify", ok, f"status={status}")
    failures += 0 if ok else 1

    search_payload = {
        "origin": "Dallas, TX",
        "destination": "Atlanta, GA",
        "equipment_type": "Dry Van",
        "pickup_date": datetime.now(timezone.utc).date().isoformat(),
        "mc_number": "123456",
    }
    status, body = http_json("POST", f"{base}/api/loads/search", search_payload, key)
    best_match = body.get("best_match") if isinstance(body, dict) else None
    load_id = best_match.get("load_id") if isinstance(best_match, dict) else None
    ok = status == 200 and isinstance(body, dict) and body.get("found") is True and bool(load_id)
    print_result("POST /api/loads/search", ok, f"status={status}, load_id={load_id}")
    failures += 0 if ok else 1

    if not load_id:
        print("Stopping flow because no load_id was returned.")
        return 1

    offer_payload = {
        "session_id": "smoke-session-001",
        "mc_number": "123456",
        "load_id": load_id,
        "carrier_offer": 2500,
        "round_number": 1,
    }
    status, body = http_json("POST", f"{base}/api/offers/evaluate", offer_payload, key)
    decision = body.get("decision") if isinstance(body, dict) else None
    accepted_rate = body.get("accepted_rate") if isinstance(body, dict) else None
    ok = status == 200 and isinstance(body, dict) and decision in {"accept", "counter", "decline"}
    print_result("POST /api/offers/evaluate", ok, f"status={status}, decision={decision}")
    failures += 0 if ok else 1

    transfer_rate = accepted_rate if accepted_rate is not None else 2500
    transfer_payload = {
        "session_id": "smoke-session-001",
        "mc_number": "123456",
        "load_id": load_id,
        "accepted_rate": transfer_rate,
    }
    status, body = http_json("POST", f"{base}/api/transfer/mock", transfer_payload, key)
    ok = status == 200 and isinstance(body, dict) and body.get("transfer_status") == "successful"
    print_result("POST /api/transfer/mock", ok, f"status={status}")
    failures += 0 if ok else 1

    call_payload = {
        "happyrobot_run_id": "run_smoke_001",
        "session_id": "smoke-session-001",
        "mc_number": "123456",
        "carrier_name": "ABC Trucking",
        "load_id": load_id,
        "origin": "Dallas, TX",
        "destination": "Atlanta, GA",
        "equipment_type": "Dry Van",
        "loadboard_rate": 2400,
        "final_offer": transfer_rate,
        "outcome": "booked",
        "sentiment": "positive",
        "call_summary": "Smoke test booking flow completed.",
        "transcript": "Carrier accepted the load in smoke test.",
        "negotiation_rounds": 1,
    }
    status, body = http_json("POST", f"{base}/api/calls/complete", call_payload, key)
    ok = status == 200 and isinstance(body, dict) and body.get("stored") is True
    print_result("POST /api/calls/complete", ok, f"status={status}")
    failures += 0 if ok else 1

    status, body = http_json("GET", f"{base}/api/metrics/summary", None, key)
    ok = status == 200 and isinstance(body, dict) and "total_calls" in body and "booking_rate" in body
    print_result("GET /api/metrics/summary", ok, f"status={status}")
    failures += 0 if ok else 1

    status, body = http_json("GET", f"{base}/api/metrics/calls?limit=5&offset=0", None, key)
    ok = status == 200 and isinstance(body, dict) and "calls" in body
    print_result("GET /api/metrics/calls", ok, f"status={status}")
    failures += 0 if ok else 1

    if failures:
        print(f"\nSmoke test completed with {failures} failure(s).")
        return 1

    print("\nSmoke test completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
