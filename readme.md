# Servicd

A car maintenance tracking web app. Log services and parts for your cars, and get maintenance
recommendations based on manufacturer schedules (mileage and/or time interval, whichever comes
first) — plus cost tracking and insights like cost-per-mile and cost breakdown by category.

A native mobile app (iOS/Android) is planned as a future addition, built separately rather than
cross-platform.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, `psycopg` (raw SQL, no ORM) with `psycopg_pool` for
  connection pooling, `bcrypt` + `pyjwt` for auth
- **Database:** PostgreSQL
- **Frontend:** React, TypeScript, Vite

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
pip install fastapi uvicorn "psycopg[binary]" python-dotenv bcrypt pyjwt psycopg_pool
```

Create a `backend/.env` file with your local database credentials and a JWT signing secret:

```
DB_NAME=servicd
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_postgres_user
DB_PASSWORD=
SECRET_KEY=
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

## Database Schema

Eight tables: `users`, `car_config`, `car`, `maintenance_type`, `service`, `part`, `service_part`,
`service_scheduled`. Full schema with constraints is in [`servicdDB.sql`](servicdDB.sql).

- A **car** belongs to a **user** and references a reusable **car_config** (year/make/model/engine),
  decoupling vehicle specs from any one physical car.
- A **service** is a logged maintenance event tied to a car, and can involve multiple **parts**
  (many-to-many, via `service_part`), with a price snapshot captured at time of service.
- **service_scheduled** holds manufacturer-recommended maintenance rules per car config, used to
  generate upcoming maintenance recommendations.
