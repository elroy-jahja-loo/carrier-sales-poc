# Acme Logistics: Inbound Carrier Sales Automation Build Description

## Executive Overview

This solution automates the inbound load-booking call workflow for carriers calling in to request loads. It integrates carrier authority verification, load discovery, rate negotiation support, and post-call analytics into one operational system.

The voice experience is managed in HappyRobot; this implementation provides the external APIs and dashboard infrastructure required to operationalize the workflow.

## Scope Delivered

### 1) Carrier Verification

- Endpoint: `POST /api/carriers/verify`
- Accepts MC number, normalizes format, queries FMCSA, stores verification payload, and returns a clear eligibility decision for the voice agent.

### 2) Load Matching

- Endpoint: `POST /api/loads/search`
- Searches available loads from Postgres using lane/equipment/date preferences and returns top 3 options with a best match and a voice-ready pitch.

### 3) Negotiation Engine

- Endpoint: `POST /api/offers/evaluate`
- Creates/updates negotiation sessions and applies bounded negotiation logic:
  - Accept if offer is within configured premium cap
  - Counter according to round strategy
  - Decline after max rounds

### 4) Booking Handoff (Web Call-Compatible)

- Endpoint: `POST /api/transfer/mock`
- Marks load held and returns a successful transfer message since PSTN transfer is unavailable in HappyRobot Web Call mode.

### 5) Post-call Ingestion

- Endpoint: `POST /api/calls/complete`
- Receives AI Extract output and stores outcome, sentiment, summary, transcript, and negotiation metadata.

### 6) Analytics Dashboard

- UI endpoint: `/` and `/dashboard`
- Displays:
  - KPI cards (total calls, booking rate, booked loads, avg rates, ineligible count)
  - Outcome distribution
  - Sentiment distribution
  - Recent call trend
  - Avg final offer vs loadboard comparison
  - Recent calls table
  - Integration status panel

## System Architecture

- Backend: FastAPI (Python 3.11+)
- Database: Postgres
- ORM: SQLAlchemy 2.x
- Migrations: Alembic
- Frontend: Next.js + TypeScript + Tailwind + Recharts
- Containerization: Docker + docker-compose

## Security

- All `/api/*` endpoints require `X-API-Key`
- Secrets are environment-driven, not hardcoded
- HTTPS assumed in production via cloud provider TLS termination

## Infrastructure and Deployment

- Local orchestration through `docker-compose`
- Cloud deployment path documented for Render/Railway
- Includes reproducible migration and seed steps

## Operational Readiness

- Includes realistic seeded load and call data for immediate stakeholder demos
- Includes backend tests for key decision logic and endpoint security
- Includes FMCSA integration adapter with configurable base URL and mapping notes
