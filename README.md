# Inbound Carrier Sales Automation

This monorepo powers the external application for a HappyRobot inbound carrier sales workflow. HappyRobot handles the Web Call voice agent, Tool nodes, Webhook nodes, and AI Extract/classification flow; this repo provides the production-style backend APIs, FMCSA integration, Postgres load/metrics storage, negotiation engine, post-call ingestion, and custom dashboard.

The proof of concept automates a freight broker's inbound carrier calls: collect MC number, verify carrier authority, find and pitch viable loads, negotiate pricing, mock transfer to sales, ingest post-call outcomes/sentiment, and report operational metrics.

## Live Deployment

- Frontend/dashboard: `https://carrier-sales-frontend.onrender.com/`
- Backend base URL: `https://carrier-sales-backend.onrender.com`
- Database: Render Postgres
- HTTPS: Render-managed TLS
- Security note: all `/api/*` endpoints require `X-API-Key`; do not publish API keys or database credentials.

## What This System Does

- Receives MC numbers from the HappyRobot voice workflow.
- Verifies carrier eligibility with FMCSA using a server-side `webKey`.
- Searches Postgres-backed loads with required challenge load fields.
- Returns voice-ready load pitches for the agent.
- Evaluates carrier counteroffers with bounded 3-round negotiation logic.
- Mocks transfer to sales for accepted rates because Web Call cannot perform PSTN transfer.
- Stores post-call extracted call details, offer data, outcome, sentiment, transcript, and negotiation metadata.
- Powers a custom dashboard with persisted metrics, not HappyRobot platform analytics.

## Challenge Requirement Coverage

| Requirement | Implementation | Evidence / Endpoint |
|---|---|---|
| Web Call trigger | HappyRobot platform configuration | External to repo; backend supports required webhooks |
| Agent asks MC number | HappyRobot Voice Agent prompt | `POST /api/carriers/verify` consumes `mc_number` |
| Verifies FMCSA | Backend FMCSA client uses server-side key | `POST /api/carriers/verify` |
| Searches loads | DB-backed FastAPI endpoint | `POST /api/loads/search` |
| Required load fields | `Load` model + deterministic demo data | `backend/app/models.py`, `backend/app/demo_data.py` |
| Pitches load | Backend returns `best_match.pitch` | `POST /api/loads/search` response |
| Asks carrier interest | HappyRobot Voice Agent prompt | Uses load search response |
| Handles counteroffers | Negotiation service evaluates offers | `POST /api/offers/evaluate` |
| Up to 3 rounds | Configurable max rounds, default 3 | `NEGOTIATION_MAX_ROUNDS=3` |
| Mock transfer | Marks load held and returns transfer message | `POST /api/transfer/mock` |
| Extracts data | HappyRobot AI Extract posts structured payload | `POST /api/calls/complete` |
| Outcome classification | Stored from post-call webhook | `call_records.outcome` |
| Sentiment classification | Stored from post-call webhook | `call_records.sentiment` |
| Custom dashboard | Next.js dashboard using backend metrics | `https://carrier-sales-frontend.onrender.com/` |
| Deployed backend/frontend/db | Render Web Services + Render Postgres | Live URLs above |
| Docker | Backend/frontend Dockerfiles + compose | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| HTTPS | Render-managed TLS | `https://...onrender.com` URLs |
| API key auth | `X-API-Key` dependency on `/api/*` | `backend/app/security.py` |

## Tech Stack

- HappyRobot: Web Call trigger, Voice Agent, Tool nodes, child Webhook nodes, AI Extract/classification.
- Backend: FastAPI, Python 3.11, SQLAlchemy 2.x, Alembic, Pydantic, httpx.
- Database: PostgreSQL / Render Postgres.
- Frontend: Next.js, React, TypeScript, Tailwind CSS, Recharts.
- Deployment: Render Web Services + Render Postgres.
- Containerization: Docker and docker-compose.
- Testing: pytest, smoke test script, Next.js production build.

## Architecture

```text
Carrier
  -> HappyRobot Web Call Voice Agent
      -> Tool: verify_carrier
          -> Webhook POST /api/carriers/verify
      -> Tool: find_available_loads
          -> Webhook POST /api/loads/search
      -> Tool: evaluate_offer
          -> Webhook POST /api/offers/evaluate
      -> Tool: mock_transfer
          -> Webhook POST /api/transfer/mock
      -> AI Extract / classification
          -> Webhook POST /api/calls/complete

FastAPI Backend
  -> FMCSA API
  -> Render Postgres

Next.js Dashboard
  -> server-side fetch with SERVER_APP_API_KEY
  -> GET /api/metrics/summary
  -> GET /api/metrics/calls
```

## Monorepo Layout

```text
carrier-sales-poc/
  backend/
    app/
    alembic/
    tests/
    Dockerfile
    start.sh
    requirements.txt
  frontend/
    app/
    components/
    lib/
    Dockerfile
    package.json
  docs/
  docker-compose.yml
  .env.example
  README.md
```

## Data Model / Required Load Fields

Loads are stored in Postgres in the `loads` table and include every challenge-required field.

| Challenge Field | Stored Field | Notes |
|---|---|---|
| `load_id` | `loads.load_id` | Unique load identifier |
| `origin` | `loads.origin` | Lane origin |
| `destination` | `loads.destination` | Lane destination |
| `pickup_datetime` | `loads.pickup_datetime` | Timezone-aware timestamp |
| `delivery_datetime` | `loads.delivery_datetime` | Timezone-aware timestamp |
| `equipment_type` | `loads.equipment_type` | Dry Van, Reefer, Flatbed, etc. |
| `loadboard_rate` | `loads.loadboard_rate` | Listed rate |
| `notes` | `loads.notes` | Handling details |
| `weight` | `loads.weight` | Load weight |
| `commodity_type` | `loads.commodity_type` | Goods type |
| `num_of_pieces` | `loads.num_of_pieces` | Piece count |
| `miles` | `loads.miles` | Lane mileage |
| `dimensions` | `loads.dimensions` | Trailer/dimension details |

Additional core tables:

- `carrier_verifications`: FMCSA verification results and raw response payloads.
- `negotiation_sessions`: active/closed negotiation state, last carrier offer, last system counter, final rate, and round count.
- `call_records`: post-call extracted details, outcome, sentiment, final offer, transcript, summary, negotiation rounds, and richer call/load details.

## API Authentication and Security

- All `/api/*` endpoints require the `X-API-Key` header.
- `GET /health` is public for health checks.
- Render provides HTTPS/TLS for deployed backend and frontend.
- `CORS_ORIGINS` controls allowed frontend origins.
- The dashboard uses `SERVER_APP_API_KEY` on the Next.js server side only.
- Do not put backend API secrets in `NEXT_PUBLIC_*` variables.
- Secrets are managed through Render environment variables or local `.env` files.
- Current limitations: static API key auth, no webhook signing, no rate limiting, and public FastAPI docs unless disabled by deployment policy.

## Environment Variables

Backend variables:

| Variable | Secret? | Purpose |
|---|---:|---|
| `APP_ENV` | No | Runtime environment label |
| `APP_API_KEY` | Yes | API key required for `/api/*` |
| `FMCSA_API_KEY` | Yes | FMCSA `webKey` |
| `FMCSA_BASE_URL` | No | FMCSA service base URL, usually `https://mobile.fmcsa.dot.gov/qc/services` |
| `DATABASE_URL` | Yes | SQLAlchemy/Postgres URL |
| `CORS_ORIGINS` | No | Comma-separated allowed frontend origins |
| `NEGOTIATION_MAX_ROUNDS` | No | Defaults to `3` |
| `DEFAULT_MAX_RATE_PREMIUM_PERCENT` | No | Defaults to `8` |

Frontend variables:

| Variable | Secret? | Purpose |
|---|---:|---|
| `SERVER_API_BASE_URL` | No | Backend URL for server-side dashboard fetches |
| `SERVER_APP_API_KEY` | Yes | Backend API key used only on the Next.js server |
| `NEXT_PUBLIC_API_BASE_URL` | No | URL-only public backend base URL if needed |

## Local Development

1. Create local env file:

```bash
cp .env.example .env
```

2. Start the local stack:

```bash
docker-compose up --build
```

3. Migrations run automatically through the backend startup script. Optional manual migration:

```bash
docker-compose exec backend alembic upgrade head
```

4. Seed deterministic demo loads and sample calls:

```bash
docker-compose exec backend python -m app.seed
```

5. Reset demo inventory before repeated demos:

```bash
docker-compose exec backend python -m app.reset_demo_data
```

6. Open local services:

- Dashboard: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

7. Run local smoke test:

```bash
python3 backend/scripts/smoke_test.py \
  --api-base-url http://localhost:8000 \
  --app-api-key change-me-local-api-key
```

## Render Deployment

Render is the primary deployment target for this submission.

1. Create a Render Postgres database.
2. Create backend Web Service from `backend/Dockerfile`.
3. Leave Render Docker Command blank so Docker uses `CMD ["./start.sh"]`.
4. Backend startup uses `backend/start.sh`:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
```

5. Configure backend environment variables:
   - `APP_ENV=production`
   - `APP_API_KEY=<secret>`
   - `FMCSA_API_KEY=<secret>`
   - `FMCSA_BASE_URL=https://mobile.fmcsa.dot.gov/qc/services`
   - `DATABASE_URL=<Render Postgres URL>`
   - `CORS_ORIGINS=https://carrier-sales-frontend.onrender.com`
   - `NEGOTIATION_MAX_ROUNDS=3`
   - `DEFAULT_MAX_RATE_PREMIUM_PERCENT=8`
6. Optional backend shell commands after deploy:

```bash
python -m app.seed
python -m app.reset_demo_data
```

7. Create frontend Web Service from `frontend/Dockerfile`.
8. Configure frontend environment variables:
   - `SERVER_API_BASE_URL=https://carrier-sales-backend.onrender.com`
   - `SERVER_APP_API_KEY=<same backend API key>`
   - `NEXT_PUBLIC_API_BASE_URL=https://carrier-sales-backend.onrender.com`
9. Verify deployment:
   - `GET https://carrier-sales-backend.onrender.com/health`
   - Remote smoke test passes.
   - Dashboard loads at `https://carrier-sales-frontend.onrender.com/`.
   - Recent call modal opens and shows full summary/transcript after a completed call.
   - If browser CORS errors appear, check `CORS_ORIGINS`.

## Alternative Deployment

Railway, Fly.io, or another Docker-friendly provider can run the same services. Use managed Postgres, configure the same environment variables, run Alembic migrations, and deploy backend/frontend Docker services separately.

## Endpoint Reference

Set variables:

```bash
export API_BASE_URL=https://carrier-sales-backend.onrender.com
export API_KEY=<your-api-key>
```

Health check:

```bash
curl "$API_BASE_URL/health"
```

Carrier verification:

```bash
curl -X POST "$API_BASE_URL/api/carriers/verify" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mc_number":"MC-135797","session_id":"hr-run-123"}'
```

Load search:

```bash
curl -X POST "$API_BASE_URL/api/loads/search" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"origin":"Kansas City, MO","destination":"Minneapolis, MN","equipment_type":"Dry Van","pickup_date":"","mc_number":"135797","session_id":"hr-run-123"}'
```

Offer evaluation:

```bash
curl -X POST "$API_BASE_URL/api/offers/evaluate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"hr-run-123","mc_number":"135797","load_id":"LD-1007","carrier_offer":"$2,500","round_number":"1"}'
```

Round 3 too-high offers return a final counter with `next_action="accept_or_decline"`. Round 4+ too-high offers return no-agreement semantics.

Mock transfer:

```bash
curl -X POST "$API_BASE_URL/api/transfer/mock" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"hr-run-123","mc_number":"135797","load_id":"LD-1007","accepted_rate":"1900"}'
```

Post-call completion:

```bash
curl -X POST "$API_BASE_URL/api/calls/complete" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "happyrobot_run_id":"hr-run-123",
    "session_id":"hr-run-123",
    "mc_number":"135797",
    "carrier_name":"Test Carrier",
    "load_id":"LD-1007",
    "origin":"Kansas City, MO",
    "destination":"Minneapolis, MN",
    "equipment_type":"Dry Van",
    "pickup_datetime":"2026-06-18T09:00:00Z",
    "delivery_datetime":"2026-06-19T12:00:00Z",
    "loadboard_rate":"1900",
    "final_offer":"1900",
    "commodity_type":"Paper products",
    "weight":"33000",
    "miles":"438",
    "num_of_pieces":"20",
    "dimensions":"53ft trailer",
    "transfer_successful":true,
    "outcome":"booked",
    "sentiment":"positive",
    "call_summary":"Carrier booked LD-1007 at $1,900.",
    "transcript":"Full transcript text here.",
    "negotiation_rounds":"1",
    "call_duration_seconds":"240"
  }'
```

Metrics:

```bash
curl -H "X-API-Key: $API_KEY" "$API_BASE_URL/api/metrics/summary"
curl -H "X-API-Key: $API_KEY" "$API_BASE_URL/api/metrics/calls?limit=20&offset=0"
```

## HappyRobot Integration

All Tool node child Webhook nodes should include:

```http
X-API-Key: @APP_API_KEY
Content-Type: application/json
```

Store `APP_API_KEY` as a HappyRobot environment variable.

| Tool / Workflow Step | Purpose | Endpoint |
|---|---|---|
| `verify_carrier` | Verify MC with FMCSA | `POST /api/carriers/verify` |
| `find_available_loads` | Search and pitch loads | `POST /api/loads/search` |
| `evaluate_offer` | Accept/counter/decline carrier rate | `POST /api/offers/evaluate` |
| `mock_transfer` | Mock transfer after accepted rate | `POST /api/transfer/mock` |
| Post-call AI Extract webhook | Persist outcome/sentiment/details | `POST /api/calls/complete` |

Expected outcome labels:

```text
booked, declined, ineligible, transferred, no_load_found, unresolved, unknown
```

Expected sentiment labels:

```text
positive, neutral, negative, unknown
```

Mock transfer language returned by the backend explains that transfer was successful and a sales rep can finalize the booking. This is intentional for Web Call mode.

## Negotiation Policy

- Max rounds default to `3` via `NEGOTIATION_MAX_ROUNDS`.
- Max acceptable rate defaults to loadboard rate plus `DEFAULT_MAX_RATE_PREMIUM_PERCENT`.
- If carrier offer is within the threshold, backend returns `decision="accept"` and `next_action="mock_transfer"`.
- If offer is too high before the final round, backend returns `decision="counter"` and `next_action="continue_negotiation"`.
- Round 3 too-high offers return a best/final counter and `next_action="accept_or_decline"`.
- Round 4+ too-high offers return no-agreement semantics and `next_action="no_agreement"`.
- Accepted rates should trigger `POST /api/transfer/mock`.

## Dashboard

The dashboard is custom-built and does not use HappyRobot analytics.

It shows:

- KPI cards for total calls, booking rate, booked loads, avg accepted rate, avg accepted premium, and follow-up exceptions.
- Outcome distribution chart.
- Sentiment distribution chart.
- Recent call volume chart.
- Accepted rate vs loadboard chart.
- Recent calls table.
- Clickable call detail modal with full summary, transcript, lane, rates, premium, negotiation rounds, transfer status, and captured load details.

The dashboard fetches protected backend data server-side using `SERVER_APP_API_KEY`; the backend API key is not exposed to the browser bundle.

## Dashboard Metric Definitions

- Total Calls: count of persisted `call_records`.
- Booking Rate: booked calls divided by total calls.
- Booked Loads: calls with outcome `booked`.
- Avg Accepted Rate: average `final_offer` for calls with outcome `booked` or `transferred` only.
- Avg Accepted Premium vs Loadboard: average per-call percentage premium for accepted calls: `(final_offer - loadboard_rate) / loadboard_rate * 100`.
- Follow-up / Exceptions: declined, no-load-found, unresolved, and ineligible outcomes.
- Outcome Distribution: grouped persisted call outcomes.
- Sentiment Distribution: grouped persisted call sentiments.
- Recent Call Volume: call records grouped over the recent time window.

Declined, unresolved, no-load-found, and ineligible calls may show last/final offers in call details, but they do not affect accepted-rate KPIs.

## Testing and Validation

Backend tests cover:

- API key enforcement.
- Load search and empty HappyRobot optional fields.
- FMCSA MC normalization and response parsing helpers.
- Negotiation accept/counter/final/no-agreement behavior.
- Unavailable load protection.
- Mock transfer behavior.
- Call completion persistence.
- Idempotency by `happyrobot_run_id`.
- Optional rich call fields.
- Outcome/sentiment safety fallback.
- Metrics correctness for accepted-rate calculations.

Run backend tests:

```bash
cd backend
APP_ENV=test pytest
```

Run frontend build/typecheck:

```bash
cd frontend
npm run build
```

Build Docker images:

```bash
docker build -t carrier-sales-backend:predeploy ./backend
docker build -t carrier-sales-frontend:predeploy ./frontend
```

Run remote smoke test:

```bash
python3 backend/scripts/smoke_test.py \
  --api-base-url https://carrier-sales-backend.onrender.com \
  --app-api-key <APP_API_KEY>
```

Validate migrations on Postgres:

```bash
cd backend
alembic upgrade head
```

## Demo Runbook

1. Open deployed dashboard: `https://carrier-sales-frontend.onrender.com/`.
2. Start a HappyRobot Web Call.
3. Use a valid MC number.
4. Ask for a known lane, such as Kansas City, MO -> Minneapolis, MN with Dry Van.
5. Accept the posted rate or negotiate once.
6. Confirm the mocked sales transfer message.
7. Let HappyRobot post the AI Extract output to `/api/calls/complete`.
8. Refresh dashboard.
9. Open the newest recent call detail modal.
10. Show outcome, sentiment, full summary, transcript, lane, rate, premium, and negotiation rounds.
11. Optionally show missing-key 401 behavior for API security.

Smoke tests are validation tools; the customer-facing demo should be the HappyRobot Web Call plus dashboard update.

## Troubleshooting

- Render cold starts: first request may be slow; retry `/health` if a free service is sleeping.
- Migration failures: check backend deploy logs for `alembic upgrade head` output.
- CORS errors: verify `CORS_ORIGINS` includes the deployed frontend origin.
- Missing API key: protected endpoints return HTTP 401.
- FMCSA upstream errors: `/api/carriers/verify` returns a graceful `verification_status="error"` response.
- No loads found: run `python -m app.reset_demo_data` from backend shell to restore deterministic demo inventory.
- Dashboard empty state: verify `/api/metrics/summary` and `/api/metrics/calls` with `X-API-Key`.
- HappyRobot webhook debugging: inspect HappyRobot Runs -> Details/Graph and compare node inputs/outputs with the endpoint reference above.

## Production Hardening / Future Work

- Add webhook signing and replay protection.
- Add rate limiting.
- Replace static API key with scoped auth, OAuth, or mTLS.
- Add structured logs, request IDs, and tracing.
- Add a normalized offer event history table for every carrier offer and system counter.
- Add dashboard filters and deeper call drilldowns.
- Protect or disable FastAPI docs in production.
- Add CI for tests, builds, and image scanning.

## Deliverables Checklist

- Dashboard URL: `https://carrier-sales-frontend.onrender.com/`
- Backend URL: `https://carrier-sales-backend.onrender.com`
- Code repository: add GitHub repository URL before final submission.
- HappyRobot workflow link/name: fill before submission.
- Demo video link: fill before submission.
- Prospect update email draft: `docs/prospect_update_email.md`
- Broker-facing build description: `docs/acme_logistics_build_description.md`
