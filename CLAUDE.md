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
- Let the user derive schema decisions, logic, and structure themselves where feasible. For
  standalone design/config decisions (e.g. NOT NULL/UNIQUE choices, ON DELETE behavior, which
  library to use), open-ended questions work well on their own.
- **For writing actual implementation code** (endpoint logic, functions, etc.), follow this
  structured workflow: (1) teach the underlying concept first — the "why," not just the "what";
  (2) give pseudocode (language-agnostic steps, not real syntax) for the user to translate into
  actual code themselves; (3) review the code they write and point out mistakes as hints/questions
  rather than rewriting it for them; (4) once it's correct, briefly explain what the final code
  does.
- It's fine to be more direct/give real code for pure tooling/setup steps (installs, config,
  terminal commands) — the guided approach above is specifically for concepts and implementation
  logic (schema design, data types, security, architecture, endpoint code).

## Tech Stack
- **Backend:** Python + FastAPI, served via Uvicorn; `psycopg` (v3) as the raw DB driver — chosen
  deliberately over an ORM (e.g. SQLAlchemy) for now, to build real SQL fluency first; may
  introduce an ORM later once comfortable. `python-dotenv` loads DB credentials from `.env`
  (git-ignored) rather than hardcoding them. `bcrypt` for password hashing, `pyjwt` for
  authentication tokens (see login/auth design below).
- **Database:** PostgreSQL (database name: `servicd`)
- **Frontend:** React + TypeScript (via Vite), ESLint for linting
- **Mobile (future, not started):** Native — Swift/SwiftUI (iOS), Kotlin/Jetpack Compose (Android).
  Chosen over cross-platform frameworks because native feel was prioritized over code sharing.

## Environment Status (as of last session)
- PostgreSQL installed via Homebrew (`postgresql@18`), started/stopped manually via
  `brew services start/stop postgresql@18` (user prefers not to leave it running all the time)
- Database renamed from `car_maintenance` to `servicd`; connect via `psql servicd`
- Python virtual environment created at `~/servicd/venv`, activate via `source venv/bin/activate`
- `fastapi`, `uvicorn`, `psycopg[binary]`, `python-dotenv`, `bcrypt`, and `pyjwt` all installed
  in the venv
- React + TypeScript scaffolded via Vite in `~/servicd/frontend`, ESLint configured, dev server
  confirmed working at `localhost:5173`
- All 8 tables created in the live `servicd` database by running `servicdDB.sql` (with finalized
  NOT NULL / UNIQUE / CHECK / foreign key constraints — see below). Verified via `psql servicd -c
  "\dt"`.
- Git initialized, initial commit made, pushed to private GitHub repo:
  https://github.com/chin2p/servicd (remote `origin`, branch `main`)
- `backend/` directory created, containing:
  - `.env` (git-ignored) — holds `DB_NAME`, `DB_HOST`, `DB_USER`, `DB_PASSWORD` (blank — local
    Homebrew Postgres uses trust auth for the OS user, no real password), `DB_PORT`, and
    `SECRET_KEY` (random 64-char hex string via `secrets.token_hex(32)`, used to sign JWTs)
  - `db.py` — loads `.env` via `load_dotenv()`, reads the values via `os.getenv` (including
    `secret_key`, imported into `main.py` — noted as thematically mismatched with a DB module,
    candidate for a separate config module later), and exposes `get_connection()` which returns
    a **fresh** `psycopg.connect(...)` connection per call (deliberately not a single shared
    connection, and not yet a pool — see below). Verified working end-to-end.
  - `main.py` — two working FastAPI endpoints, plus a reusable auth dependency:
    - `POST /users`: validates the request body via a Pydantic `UserCreate` model (`username`,
      `password`, optional `name`), hashes the password with `bcrypt.hashpw` (salt embedded
      automatically — see schema notes below), inserts via a parameterized query (`%s`
      placeholders, values passed as a separate params tuple — not string-formatted, to avoid
      SQL injection) using `RETURNING user_id`, and returns `user_id`/`username`/`name` only
      (never `password_hash`).
    - `POST /login`: looks up the user by `username` (parameterized `SELECT`), then verifies the
      password against the stored hash with `bcrypt.checkpw`. On success, returns a signed JWT
      (`pyjwt`, `HS256`, payload `{"sub": str(user_id), "exp": <now + 1 day>}`). See "Login/Auth
      Design" below for the full security reasoning (timing-safe dummy-hash check, generic error
      messages, why JWT over session cookies).
    - `get_current_user(credentials = Security(HTTPBearer()))`: a reusable FastAPI dependency —
      any endpoint adding `user_id: int = Depends(get_current_user)` as a parameter gets the
      token verified (`jwt.decode`, signature + expiration checked) and `user_id` extracted
      before the endpoint body runs; raises `401` on missing/expired/invalid tokens. Note:
      `sub` must be cast to `str` when encoding and back to `int` when decoding — the JWT spec
      (RFC 7519) requires `sub` to be a string, which `pyjwt`'s `decode()` enforces (raises
      `InvalidSubjectError`) even though `encode()` doesn't warn you at write time. Proven working
      end-to-end via a throwaway `GET /me` test endpoint (since removed — it was scaffolding, not
      a real feature) that returned the caller's own profile using only the token.
    - All verified working end-to-end via `uvicorn main:app --reload` + real requests; rows/
      tokens confirmed correct in `psql` and via local `jwt.decode()`.
- `readme.md` (separate file, human-facing) now exists alongside this `CLAUDE.md`; keep both in
  sync when project state changes — this file is for my working context, `readme.md` is for
  humans/GitHub visitors.

## Finalized Database Schema

Full `CREATE TABLE` statements live in `servicdDB.sql` (source of truth for exact syntax); table
below summarizes the finalized constraints, written but not yet executed against the live DB.
Note: table is named `users`, not `user` — `user` is a reserved keyword in Postgres.

**users**
- `user_id` — SERIAL PRIMARY KEY
- `name` — TEXT, nullable
- `username` — TEXT, NOT NULL, UNIQUE
- `password_hash` — VARCHAR(60) NOT NULL (bcrypt-length; never store raw passwords)

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
- **Passwords are hashed with bcrypt**, never stored in plain text. Originally the schema had a
  separate `salt` column, but investigation (via `bcrypt.hashpw`/`checkpw`) confirmed bcrypt
  generates a random salt per call and embeds it directly inside the 60-char hash string itself
  (`$2b$<cost>$<22-char salt><31-char hash>`) — `checkpw` needs no separate salt argument. A
  standalone `salt` column was therefore redundant and has been dropped from both `servicdDB.sql`
  and the live table (table was still empty, so no migration/backfill was needed). Identical
  passwords across users still produce different hashes, since bcrypt's embedded salt is random
  per call regardless.
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
- **`db.py`'s `get_connection()` opens a brand-new connection per call**, not a single shared
  connection — deliberate simple starting point since a shared connection is unsafe across
  concurrent FastAPI requests. Real production pattern would be a connection pool (`psycopg_pool`),
  planned as a learning step once a basic endpoint is working end-to-end (see Next Steps).

## Login/Auth Design
- **`POST /login` never reveals whether a username exists.** Wrong password and nonexistent
  username both return the identical `401` + `"Invalid username or password"` — prevents a
  username-enumeration vulnerability where an attacker could distinguish real accounts from fake
  ones via differing error text.
- **Timing-safe lookup, not just a matching error message.** Even a generic error message can
  leak the same info via response time, since a real `bcrypt.checkpw` call is deliberately slow
  and a "user not found, return immediately" path would be conspicuously fast by comparison. Fix:
  a `dummy_hash` (bcrypt hash of a throwaway placeholder string) is generated once at module load,
  and the nonexistent-username branch still runs a real `bcrypt.checkpw` against it (result
  discarded) before responding, so both branches always do equal work. Considered a random sleep
  instead — rejected, since it only adds noise on top of genuinely different work, is statistically
  distinguishable over many samples, and requires manually tuning the delay to match real bcrypt
  timing (which drifts if the cost factor ever changes).
- **JWT chosen over server-side session cookies** for the auth token itself, specifically because
  of the planned native iOS/Android apps (see Project Overview) — cookies are a browser-specific
  mechanism, while a bearer token in an `Authorization` header works identically across a web
  frontend and future native clients. Trade-off accepted: unlike server-side sessions, a JWT can't
  be individually revoked before it expires, since nothing is stored server-side.
- **Payload only contains `sub` (user_id) and `exp`.** Important underlying concept: a JWT is
  *signed, not encrypted* — the payload is just base64-encoded and trivially readable by anyone
  holding the token (verified firsthand by decoding a real token on jwt.io without supplying the
  secret — payload was readable, only the signature check failed). This means nothing sensitive
  (e.g. `password_hash`) can ever go in the payload.
- **`exp` set to 1 day** as a starting point — short enough to limit damage if a token leaks, long
  enough to not be annoying during development. Noted future refinement: the more robust
  production pattern is a short-lived access token plus a separate longer-lived refresh token,
  deferred for now (same "simple first, refine later" reasoning as connection pooling).
- **Signing secret lives in `.env`** (`SECRET_KEY`), generated via `secrets.token_hex(32)` —
  same reasoning as DB credentials: anyone who obtains it could forge valid tokens for any user.

## Next Steps (not yet done)
1. Build `car`/`car_config` endpoints (first tables with FK dependencies on `users`), using the
   `Depends(get_current_user)` auth pattern to get `user_id` from the token rather than trusting
   a client-supplied value.
2. Revisit `get_connection()` and learn/introduce `psycopg_pool` connection pooling as the
   production-grade pattern, now that endpoints work end-to-end.
3. Trace a full user scenario through the schema alongside writing further insert logic.
