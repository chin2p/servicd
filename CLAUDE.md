# Servicd — Car Maintenance Tracker

## Project Overview
A car maintenance tracking web app (mobile app planned later, as separate native iOS/Android apps).
Users add cars, log services/parts replaced, and the app recommends future maintenance based on
manufacturer schedules (mileage and/or time interval, whichever comes first). Cost tracking and
insights (e.g., cost per mile, cost breakdown by category) are core differentiating features.

## Learning Preference (IMPORTANT)
The user is using this project to learn backend/database/frontend concepts deeply, not just to
get working code fast. When helping:
- Prefer hints, questions, and guided reasoning over handing over direct answers or full code.
- Let the user derive schema decisions, logic, and structure themselves where feasible.
- It's fine to be more direct/give code for pure tooling/setup steps (installs, config) — the
  Socratic approach is specifically for concepts (schema design, data types, security, architecture).

## Tech Stack
- **Backend:** Python + FastAPI, served via Uvicorn
- **Database:** PostgreSQL (database name: `car_maintenance`)
- **Frontend:** React + TypeScript (via Vite), ESLint for linting
- **Mobile (future, not started):** Native — Swift/SwiftUI (iOS), Kotlin/Jetpack Compose (Android).
  Chosen over cross-platform frameworks because native feel was prioritized over code sharing.

## Environment Status (as of last session)
- PostgreSQL installed via Homebrew (`postgresql@18`), started/stopped manually via
  `brew services start/stop postgresql@18` (user prefers not to leave it running all the time)
- Database renamed from `car_maintenance` to `servicd`; connect via `psql servicd`
- Python virtual environment created at `~/servicd/venv`, activate via `source venv/bin/activate`
- `fastapi` and `uvicorn` installed in the venv
- React + TypeScript scaffolded via Vite in `~/servicd/frontend`, ESLint configured, dev server
  confirmed working at `localhost:5173`
- All 8 tables created in the live `servicd` database by running `servicdDB.sql` (with finalized
  NOT NULL / UNIQUE / CHECK / foreign key constraints — see below). Verified via `psql servicd -c
  "\dt"`. Git/GitHub not yet set up.

## Finalized Database Schema

Full `CREATE TABLE` statements live in `servicdDB.sql` (source of truth for exact syntax); table
below summarizes the finalized constraints, written but not yet executed against the live DB.
Note: table is named `users`, not `user` — `user` is a reserved keyword in Postgres.

**users**
- `user_id` — SERIAL PRIMARY KEY
- `name` — TEXT, nullable
- `username` — TEXT, NOT NULL, UNIQUE
- `password_hash` — VARCHAR(60) NOT NULL (bcrypt-length; never store raw passwords)
- `salt` — VARCHAR(60) NOT NULL

**car_config** (reusable make/model/year/engine combo, decoupled from any individual physical car)
- `config_id` — SERIAL PRIMARY KEY
- `year` — INTEGER NOT NULL
- `make` — TEXT NOT NULL
- `model` — TEXT NOT NULL
- `engine` — TEXT, nullable

**car**
- `car_id` — SERIAL PRIMARY KEY
- `user_id` — INTEGER NOT NULL (FK → users, ON DELETE CASCADE)
- `config_id` — INTEGER NOT NULL (FK → car_config, no cascade — catalog table)
- `vin` — VARCHAR(17), nullable, UNIQUE; CHECK constraint enforces 17-char VIN charset
  (`[A-HJ-NPR-Z0-9]`, excludes I/O/Q per the real VIN standard) when not null
- `total_miles` — INTEGER, nullable

**maintenance_type** (catalog of maintenance categories, e.g. "Oil Change")
- `maintenance_type_id` — SERIAL PRIMARY KEY
- `maintenance_name` — TEXT NOT NULL, UNIQUE

**service** (an actual logged service event for a specific car)
- `service_id` — SERIAL PRIMARY KEY
- `car_id` — INTEGER NOT NULL (FK → car, ON DELETE CASCADE)
- `maintenance_type_id` — INTEGER NOT NULL (FK → maintenance_type, no cascade — catalog table)
- `miles_at_service` — INTEGER NOT NULL (required for mileage-based scheduling and cost-per-mile)
- `date` — DATE NOT NULL (required for time-based scheduling)

**part** (catalog of part types, reusable across services/cars)
- `part_id` — SERIAL PRIMARY KEY
- `part_name` — TEXT NOT NULL
- `brand` — TEXT NOT NULL (use `'Generic'`/`'Unbranded'` when unknown, rather than NULL — avoids
  NULL-uniqueness edge case on the composite UNIQUE below)
- UNIQUE (`part_name`, `brand`) — same part name can exist across different brands
- `price_cents` — INTEGER, nullable (money stored as integer cents to avoid float rounding errors;
  nullable since price may be unknown until an average-price lookup feature exists)

**service_part** (junction table — many-to-many between service and part)
- PRIMARY KEY (`part_id`, `service_id`) — composite key, prevents the same part being logged twice
  on the same service
- `part_id` — INTEGER (FK → part, no cascade — catalog table)
- `service_id` — INTEGER (FK → service, ON DELETE CASCADE)
- `price_at_service_cents` — INTEGER, nullable (historical price snapshot at time of service, since
  `part.price_cents` may change over time; nullable for the same reason as `part.price_cents`)

**service_scheduled** (manufacturer's recommended maintenance rules, tied to car_config not car)
- `schedule_id` — SERIAL PRIMARY KEY
- `config_id` — INTEGER NOT NULL (FK → car_config, no cascade — catalog table)
- `maintenance_type_id` — INTEGER NOT NULL (FK → maintenance_type, no cascade — catalog table)
- `mileage_interval` — INTEGER, nullable
- `months_interval` — INTEGER, nullable
- CHECK constraint requires at least one of `mileage_interval` / `months_interval` to be non-null
  (a rule needs at least one trigger — mileage-only, time-only, or both are all valid; both null
  is not)

### Relationships (all verified)
- user → car (one-to-many)
- car_config → car (one-to-many)
- car_config → service_scheduled (one-to-many)
- car → service (one-to-many)
- maintenance_type → service (one-to-many)
- maintenance_type → service_scheduled (one-to-many)
- service ↔ part via service_part (many-to-many)

## Key Design Decisions & Reasoning
- **Money stored as integer cents**, not float/decimal directly, to avoid floating-point rounding
  errors compounding across many transactions. Convert to dollars only for display in app code.
- **Passwords are hashed + salted**, never stored in plain text. Salt is per-user and random,
  stored alongside the hash (not secret — its job is uniqueness, not secrecy), so identical
  passwords across users don't produce identical hashes.
- **VIN uses VARCHAR(17)** (fixed length) as a built-in guardrail against malformed data, since
  VINs are always exactly 17 characters.
- **car_config exists separately from car** so make/model/year/engine data (and manufacturer
  schedules) aren't duplicated per physical car — a schedule/config is a reusable "type," while
  `car` represents one specific physical vehicle (with its own VIN and mileage).
- **service_part junction table** exists because service↔part is genuinely many-to-many (one
  service can involve multiple parts; one part type can be used across many services).
- Originally planned to scrape manufacturer service schedules — deprioritized in favor of manually
  curated schedule data for 1-2 brands initially (scraping is legally/technically messy and low
  payoff for an MVP); framed as a future "expand the database" step instead.
- **`ON DELETE CASCADE` only on the "ownership" chain** (`car.user_id`, `service.car_id`,
  `service_part.service_id`) — deleting a user wipes their cars/services/parts-used, deleting a
  car wipes its service history. Catalog/reference tables (`car_config`, `maintenance_type`,
  `part`) deliberately have no cascade — the default (blocked delete while referenced) is correct
  there, since deleting e.g. a `part` catalog row shouldn't silently destroy other users' cost
  history that references it. App-layer delete-confirmation UI (warn the user what will be
  removed) is just a read-only preview query before the delete — the actual cleanup is left to
  the DB via CASCADE rather than manually orchestrated in app code.

## Next Steps (not yet done)
1. Set up Git/GitHub for version control.
2. Connect FastAPI to PostgreSQL and build first API endpoints.
3. Trace a full user scenario through the schema before/alongside writing insert logic.
