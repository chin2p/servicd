# Servicd

[![Backend Tests](https://github.com/chin2p/servicd/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/chin2p/servicd/actions/workflows/backend-tests.yml)

A car maintenance tracking web app. Log services and parts for your cars, and get maintenance
recommendations based on manufacturer schedules (mileage and/or time interval, whichever comes
first) — plus cost tracking and insights like cost-per-mile and cost breakdown by category.

A native mobile app (iOS/Android) is planned as a future addition, built separately rather than
cross-platform.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, `psycopg` (raw SQL, no ORM) with `psycopg_pool` for
  connection pooling, `bcrypt` + `pyjwt` for auth, Anthropic's Claude API for receipt-photo OCR
- **Database:** PostgreSQL
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Testing:** `pytest` + FastAPI's `TestClient` for backend integration tests, run against an
  isolated `servicd_test` database with automatic per-test rollback

## Project Status

Early development. Database schema is finalized and live. All 8 tables have a working, tested
`POST` endpoint, plus core `GET` endpoints for reading data back — full read+write coverage,
with ownership checks anywhere they matter:
- `POST /users` — create a user, with bcrypt password hashing
- `POST /login` — authenticate and receive a signed JWT (1-day expiration)
- JWT-based auth dependency in place for protecting endpoints (extracts the current user from an
  `Authorization: Bearer <token>` header)
- `POST /car_config` — add a car configuration (year/make/model/engine), reusing an existing one
  if the same combination already exists
- `POST /car` — register a car (config, VIN, mileage) to the logged-in user
- `POST /maintenance_type` — add a maintenance category (e.g. "Oil Change"), reusing an existing
  one if it already exists
- `POST /part` — add a part (name/brand/price), reusing an existing one if the same name+brand
  already exists
- `POST /service` — log a service on one of your own cars (rejects other users' cars with `403`)
- `POST /service_part` — attach a part to one of your own services
- `POST /service_scheduled` — add a manufacturer maintenance rule (mileage/time interval) for a
  car config
- `GET /cars` — list the logged-in user's cars
- `GET /cars/{car_id}` — view one car (must belong to the logged-in user)
- `GET /cars/{car_id}/services` — service history for one car (must belong to the logged-in user)
- `GET /maintenance_types` — browse the maintenance-type catalog (public, no auth needed)
- `GET /parts` — browse the parts catalog (public, no auth needed)
- `GET /vin/{vin}/decode` — decode a VIN via NHTSA's public API to auto-fill year/make/model/engine
- `POST /receipt/decode` — extract maintenance type/mileage/date/parts/prices from a photo or PDF
  of a service receipt via Claude, to pre-fill the log-a-service form
- `DELETE /service_part/{service_id}/{part_id}` — remove a part from one of your own services
- `DELETE /service/{service_id}` — delete one of your own logged services
- `DELETE /car/{car_id}` — delete one of your own cars (cascades to its service history)
- `DELETE /users/me` — delete your own account (cascades to all your cars/services/parts)

Frontend has a home page, signup, login, a cars dashboard, a car detail page, an "add a car"
form (VIN decode with manual-entry fallback), a "log a service" form (scan a receipt photo/PDF to
pre-fill maintenance type/mileage/date/parts, or skip to manual entry), and an "attach a part"
form working end-to-end (`/`, `/signup`, `/login`, `/cars`, `/cars/:carId`, `/cars/new`,
`/cars/:carId/services/new`, `/cars/:carId/services/:serviceId/parts/new`), with the JWT stored
in `localStorage` after login, a shared nav bar with logout, and a Tailwind-styled UI throughout.
The car detail page shows each service's attached parts and prices, with delete buttons for the
car, each service, and each attached part; account deletion is available from the nav bar.

Backend endpoints use dependency-injected database connections, so tests can swap in a
transaction that always rolls back afterward — a `pytest` suite of 46 tests covers all 19
endpoints, including ownership checks, validation errors, and cascading deletes. GitHub Actions
runs the full suite against a fresh Postgres instance on every push and pull request.

## Getting Started

### Prerequisites

- Python 3
- PostgreSQL
- Node.js

### Database

```bash
createdb servicd
psql servicd -f servicdDB.sql
```

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

Create a `backend/.env` file with your local database credentials, a JWT signing secret, and an
Anthropic API key (for receipt OCR — get one at [console.anthropic.com](https://console.anthropic.com)):

```
DB_NAME=servicd
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_postgres_user
DB_PASSWORD=
SECRET_KEY=
ANTHROPIC_API_KEY=
```

Generate a random value for `SECRET_KEY` with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`.

### Testing

```bash
createdb servicd_test
psql servicd_test -f servicdDB.sql
```

Create a `backend/.env.test` file identical to `.env` but with `DB_NAME=servicd_test`, then:

```bash
cd backend
pip install pytest
pytest tests/ -v
```

Each test runs inside a database transaction that's rolled back afterward, so the test database
stays empty between runs regardless of what the endpoints under test insert.

## Database Schema

Eight tables: `users`, `car_config`, `car`, `maintenance_type`, `service`, `part`, `service_part`,
`service_scheduled`. Full schema with constraints is in [`servicdDB.sql`](servicdDB.sql).

- A **car** belongs to a **user** and references a reusable **car_config** (year/make/model/engine),
  decoupling vehicle specs from any one physical car.
- A **service** is a logged maintenance event tied to a car, and can involve multiple **parts**
  (many-to-many, via `service_part`), with a price snapshot captured at time of service.
- **service_scheduled** holds manufacturer-recommended maintenance rules per car config, used to
  generate upcoming maintenance recommendations.
