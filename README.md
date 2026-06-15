# Inbound Carrier Sales Automation POC

Production-grade monorepo for the non-HappyRobot portion of an inbound carrier load sales workflow. This project provides secured backend APIs, FMCSA verification integration, load matching, negotiation logic, post-call ingestion, and a polished operations dashboard.

## What This System Does

- Verifies incoming carrier MC numbers through an FMCSA client (`/api/carriers/verify`)
- Searches load opportunities from Postgres (`/api/loads/search`)
- Negotiates counteroffers up to a configured round limit (`/api/offers/evaluate`)
- Mocks transfer handoff after accepted pricing (`/api/transfer/mock`)
- Ingests extracted post-call outcomes/sentiment/transcripts (`/api/calls/complete`)
- Powers custom metrics + dashboard without HappyRobot analytics (`/api/metrics/*`)

## Monorepo Layout

```text
carrier-sales-poc/
  backend/                FastAPI + SQLAlchemy + Alembic
  frontend/               Next.js + Tailwind + Recharts dashboard
  docs/                   Prospect email + broker build docs + demo script
  docker-compose.yml
  .env.example
  README.md
```

## Architecture (Text Diagram)

```text
Carrier (Web Call)
   |
   v
HappyRobot Voice Agent
   |-- Tool: Verify Carrier ------> POST /api/carriers/verify
   |-- Tool: Load Search ---------> POST /api/loads/search
   |-- Tool: Offer Evaluate ------> POST /api/offers/evaluate
   |-- Tool: Mock Transfer -------> POST /api/transfer/mock
   |
   +--> AI Extract (post-call)
           |
           v
      POST /api/calls/complete

Dashboard (Next.js)
   |-- server-side fetch ----------> GET /api/metrics/summary
   |-- server-side fetch ----------> GET /api/metrics/calls

Backend (FastAPI)
   |-- X-API-Key auth for all /api/*
   |-- SQLAlchemy models/services
   +--> Postgres
```

## HappyRobot Integration Points

- **MC Verification Tool**: `POST /api/carriers/verify`
- **Load Search Tool**: `POST /api/loads/search`
- **Offer Evaluation Tool**: `POST /api/offers/evaluate`
- **Mock Transfer Tool**: `POST /api/transfer/mock`
- **Post-call Webhook**: `POST /api/calls/complete`
- **Metrics for dashboard**: `GET /api/metrics/summary`, `GET /api/metrics/calls`

## Environment Variables

Copy the provided `.env.example`:

```bash
cp .env.example .env
```

Required values:

- `APP_API_KEY`: shared backend API key for all `/api/*` requests
- `FMCSA_API_KEY`: FMCSA key used by the verification client
- `FMCSA_BASE_URL`: configurable FMCSA base URL
- `DATABASE_URL`: SQLAlchemy DB URL
- `NEGOTIATION_MAX_ROUNDS`: default `3`
- `DEFAULT_MAX_RATE_PREMIUM_PERCENT`: default `8`
- `SERVER_API_BASE_URL`: frontend server-side target for backend API (use backend internal URL in containers)
- `SERVER_APP_API_KEY`: frontend server-side API key used for backend requests

FMCSA configuration notes:

- `FMCSA_BASE_URL` and `FMCSA_API_KEY` are fully environment-driven.
- If the key is missing/default, `/api/carriers/verify` returns a graceful `verification_status: "error"` response.
- TODO: confirm your FMCSA account endpoint path/field mapping and update `backend/app/services/fmcsa.py` if required.

## Local Setup

1. Copy env file and set values:

```bash
cp .env.example .env
```

2. Start services (migrations auto-run at backend startup):

```bash
docker-compose up --build
```

3. (Optional manual migration command):

```bash
docker-compose exec backend alembic upgrade head
```

4. Seed realistic load + call data:

```bash
docker-compose exec backend python -m app.seed
```

5. Run smoke test flow:

```bash
python3 backend/scripts/smoke_test.py --api-base-url http://localhost:8000 --app-api-key change-me-local-api-key
```

6. Open apps:

- Frontend dashboard: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

## API Authentication

All `/api/*` routes require:

```http
X-API-Key: <APP_API_KEY>
```

`/health` is public.

## Endpoint Quick Reference + cURL

Set your key first:

```bash
export API_KEY="change-me-local-api-key"
```

Health:

```bash
curl http://localhost:8000/health
```

Carrier verification:

```bash
curl -X POST http://localhost:8000/api/carriers/verify \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mc_number":"123456"}'
```

Load search:

```bash
curl -X POST http://localhost:8000/api/loads/search \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"origin":"Dallas, TX","destination":"Atlanta, GA","equipment_type":"Dry Van"}'
```

Offer evaluate:

```bash
curl -X POST http://localhost:8000/api/offers/evaluate \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"session_123","mc_number":"123456","load_id":"LD-1001","carrier_offer":2550,"round_number":1}'
```

Mock transfer:

```bash
curl -X POST http://localhost:8000/api/transfer/mock \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"session_123","mc_number":"123456","load_id":"LD-1001","accepted_rate":2550}'
```

Post-call complete:

```bash
curl -X POST http://localhost:8000/api/calls/complete \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"happyrobot_run_id":"run_123","session_id":"session_123","mc_number":"123456","outcome":"booked","sentiment":"positive"}'
```

Metrics summary:

```bash
curl -X GET http://localhost:8000/api/metrics/summary \
  -H "X-API-Key: $API_KEY"
```

Recent calls:

```bash
curl -X GET "http://localhost:8000/api/metrics/calls?limit=20&offset=0" \
  -H "X-API-Key: $API_KEY"
```

## HappyRobot Configuration Guide

This section follows the platform assumptions provided in the challenge.

1. **Use Web Call trigger** for testing (no purchased phone number).
2. For every external call use **Tool node -> child Webhook node**.
3. Tool params are available in child nodes via `@` variables.
4. Configure Webhook node with method, URL, headers, auth, JSON body.
5. Store API keys as HappyRobot env vars and reference with `@`.
6. The final child-node output becomes the tool result visible to the agent.

Recommended flow:

```text
Web Call Trigger
  -> Voice Agent
      -> Tool: verify_carrier (POST /api/carriers/verify)
      -> Tool: search_loads (POST /api/loads/search)
      -> Tool: evaluate_offer (POST /api/offers/evaluate)
      -> Tool: mock_transfer (POST /api/transfer/mock)
  -> AI Extract
  -> Webhook POST /api/calls/complete
```

Debugging:

- Inspect runs in **HappyRobot Runs -> Details/Graph**
- Validate each node input/output payload
- Verify extracted schema before webhook submission

Notes:

- Transfer is intentionally mocked in Web Call mode (`/api/transfer/mock`)
- Public share links are not documented; provide reviewer org Viewer access

## Deployment (Render or Railway)

Both providers can run backend and frontend as separate services with managed Postgres.

### Railway (example)

1. Create Postgres plugin.
2. Deploy `backend/` service from `backend/Dockerfile`.
3. Backend env vars:
   - `APP_ENV=production`
   - `APP_API_KEY=<strong-random-key>`
   - `FMCSA_API_KEY=<real-key>`
   - `FMCSA_BASE_URL=<real-fmcsa-base-url>`
   - `DATABASE_URL=<railway-postgres-url>`
   - `CORS_ORIGINS=<https://your-frontend-domain>`
   - `NEGOTIATION_MAX_ROUNDS=3`
   - `DEFAULT_MAX_RATE_PREMIUM_PERCENT=8`
4. Backend start command:
   - `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Run one-time seed job (optional): `python -m app.seed`.
6. Deploy `frontend/` service from `frontend/Dockerfile`.
7. Frontend env vars:
   - `NEXT_PUBLIC_API_BASE_URL=<https://backend-public-url>`
   - `SERVER_API_BASE_URL=<https://backend-public-url>`
   - `SERVER_APP_API_KEY=<same APP_API_KEY>`

### Render (example)

1. Create managed Postgres.
2. Create backend Web Service from `backend/Dockerfile`.
3. Backend build/start:
   - Build command: default Docker build
   - Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set backend env vars (same list as Railway section), especially `CORS_ORIGINS=<https://frontend-url>`.
5. Run one-time seed in Render shell (optional): `python -m app.seed`.
6. Create frontend Web Service from `frontend/Dockerfile`.
7. Frontend env vars:
   - `NEXT_PUBLIC_API_BASE_URL=<https://backend-public-url>`
   - `SERVER_API_BASE_URL=<https://backend-public-url>`
   - `SERVER_APP_API_KEY=<same APP_API_KEY>`

## HTTPS and Security Notes

- Local dev is HTTP on localhost.
- In deployment, HTTPS is expected via provider-managed TLS (Render/Railway/Fly/etc.).
- All operational APIs are guarded by `X-API-Key`.
- Dashboard API key usage is server-side only (`SERVER_APP_API_KEY`); it is not required in browser requests.
- If you expose API key from browser for quick demos, treat that mode as demo-only and replace with session/BFF auth in production.

## Production Hardening Recommendations

- Replace static API key model with scoped service auth / OAuth / mTLS.
- Add request signing or nonce-based replay protection for webhooks.
- Add structured logging + trace IDs + audit log pipeline.
- Add Redis for idempotency and rate limits.
- Improve FMCSA adapter with explicit schema mapping per endpoint version.
- Add CI for lint/test/security scans and image vulnerability scanning.

## Testing

Backend tests live at `backend/tests/test_api.py` and cover:

- API key enforcement
- Health endpoint
- Load search
- Negotiation accept/counter logic
- Call completion persistence
- Metrics summary shape

Run with:

```bash
docker-compose exec backend pytest
```

Frontend build test:

```bash
cd frontend && npm run build
```

Docker smoke test:

```bash
python3 backend/scripts/smoke_test.py --api-base-url http://localhost:8000 --app-api-key change-me-local-api-key
```

## Demo Script (5 Minutes)

1. Show architecture quickly in `README.md` and point to HappyRobot integration endpoints.
2. Open dashboard at `http://localhost:3000` and explain KPI cards and trend charts.
3. Run smoke flow live:
   - `python3 backend/scripts/smoke_test.py --api-base-url http://localhost:8000 --app-api-key <key>`
4. Refresh dashboard and show new call rows + metric movement.
5. Show API auth behavior with missing key (`401`) and explain production security posture.

## Final Demo Placeholders

- `BACKEND_PUBLIC_URL=`
- `FRONTEND_PUBLIC_URL=`
- `HAPPYROBOT_WORKFLOW_NAME=`
- `DEMO_VIDEO_LINK=`

## Challenge Deliverables Checklist

- Prospect update email template: `docs/prospect_update_email.md`
- Broker-facing build document: `docs/acme_logistics_build_description.md`
- Deployed dashboard URL: add after deploy (Railway/Render/Fly)
- Code repository URL: add your repo URL
- HappyRobot workflow URL: add your org workflow link (viewer access)
- Demo video URL (<= 5 min): add Loom/Drive link
