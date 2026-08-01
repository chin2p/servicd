# Servicd

A car maintenance tracking web app. Log services and parts for your cars, and get maintenance
recommendations based on manufacturer schedules (mileage and/or time interval, whichever comes
first) — plus cost tracking and insights like cost-per-mile and cost breakdown by category.

A native mobile app (iOS/Android) is planned as a future addition, built separately rather than
cross-platform.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, `psycopg` (raw SQL, no ORM), `bcrypt` + `pyjwt` for auth
- **Database:** PostgreSQL
- **Frontend:** React, TypeScript, Vite

## Project Status

Early development. Database schema is finalized and live. Backend API is in progress:
- `POST /users` — create a user, with bcrypt password hashing
- `POST /login` — authenticate and receive a signed JWT (1-day expiration)
- JWT-based auth dependency in place for protecting endpoints (extracts the current user from an
  `Authorization: Bearer <token>` header)
- `POST /car_config` — add a car configuration (year/make/model/engine), reusing an existing one
  if the same combination already exists

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
pip install fastapi uvicorn "psycopg[binary]" python-dotenv bcrypt pyjwt
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
