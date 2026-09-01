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
  authentication tokens (see login/auth design below). `psycopg_pool` for connection pooling
  (see below) — all endpoints borrow connections from a shared pool rather than opening a new
  one per request. `requests` for calling NHTSA's public VIN-decode API (see `GET /vin/{vin}/decode`
  below) — the first outbound call this backend makes to a third-party service, as opposed to
  its own database. **`pytest` + FastAPI's `TestClient`** (built on `httpx`) for backend
  integration tests (see "Backend Testing Infrastructure" below).
- **Database:** PostgreSQL (database name: `servicd`; a second database, `servicd_test`, exists
  purely for running the automated test suite against, same schema, kept structurally empty
  between test runs)
- **Frontend:** React + TypeScript (via Vite), ESLint for linting, Tailwind CSS v4 for styling
- **Mobile (future, not started):** Native — Swift/SwiftUI (iOS), Kotlin/Jetpack Compose (Android).
  Chosen over cross-platform frameworks because native feel was prioritized over code sharing.

## Environment Status (as of last session)
- PostgreSQL installed via Homebrew (`postgresql@18`), started/stopped manually via
  `brew services start/stop postgresql@18` (user prefers not to leave it running all the time)
- Database renamed from `car_maintenance` to `servicd`; connect via `psql servicd`
- Python virtual environment created at `~/servicd/venv`, activate via `source venv/bin/activate`
- `fastapi`, `uvicorn`, `psycopg[binary]`, `python-dotenv`, `bcrypt`, `pyjwt`, and `psycopg_pool`
  all installed in the venv
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
    candidate for a separate config module later), and builds a `psycopg_pool.ConnectionPool`
    (`pool`, module-level, created once at import time) from a `libpq`-style connection string
    (`f"dbname={db_name} user={db_user} ..."`). Superseded the original `get_connection()`
    (opened a fresh connection per call) — that function has been removed, no longer needed.
    Verified working end-to-end, including that the pool correctly recovers a connection after
    an aborted transaction (tested: a failed `POST /car` request immediately followed by a
    successful `POST /car_config` on the same pool, no issues). Later gained `get_db()`, a
    generator dependency (`with pool.connection() as conn: yield conn`) that every endpoint now
    uses via `Depends(get_db)` instead of calling `pool.connection()` directly — see "Backend
    Testing Infrastructure" below for why.
  - `main.py` — nineteen working FastAPI endpoints, plus a reusable auth dependency:
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
    - `POST /car_config`: requires a valid token (`Depends(get_current_user)`) purely as an
      anti-abuse gate — the row itself isn't tied to any user, so `user_id` is deliberately
      unused in the function body; "must be authenticated to write" and "this data belongs to
      you" are treated as separate concerns. Uses `INSERT ... ON CONFLICT (year, make, model,
      engine) DO NOTHING RETURNING config_id`, falling back to a `SELECT` for the existing row
      when the insert is skipped — a "find or create" pattern that's atomic (avoids a
      check-then-insert race condition two concurrent identical requests could otherwise hit).
      `engine` defaults to `"Unknown"` in the endpoint (not the Pydantic model) when omitted,
      so both "field left out" and "explicitly sent as `null`" are handled the same way.
    - `POST /car`: the first endpoint where `Depends(get_current_user)`'s `user_id` is actually
      *used* (not just gatekept) — `car.user_id` is always taken from the verified token, never
      from client input, closing the vulnerability that motivated building auth in the first
      place. Client supplies `config_id`/`vin`/`total_miles`. Catches
      `psycopg.errors.ForeignKeyViolation` (bad `config_id`) and `UniqueViolation` (duplicate
      VIN) and turns each into a specific `404`/`400` instead of a raw `500`. Chose this over
      reusing the `car_config`-style `ON CONFLICT` pattern deliberately: a duplicate VIN is a
      genuine error to report, not a legitimate case to silently resolve like a repeated
      car_config combo was.
    - `POST /maintenance_type` and `POST /part`: same `ON CONFLICT DO NOTHING RETURNING` +
      fallback-`SELECT` "find or create" pattern as `car_config`, applied to their own `UNIQUE`
      constraints (`maintenance_name` alone; `(part_name, brand)` composite). `part.brand`
      defaults to `"Unknown"` when omitted (same convention as `car_config.engine`), and
      `part.price_cents` stays `NULL` when omitted — deliberately *not* defaulted to `0`, since
      "unknown price" and "price is $0" are different facts and conflating them would corrupt
      future cost-per-mile/cost-breakdown calculations.
    - `POST /service`: the first endpoint needing an **authorization** check, not just
      authentication — `service` has no `user_id` of its own, only `car_id`, so
      `Depends(get_current_user)` alone only proves *who's asking*, not *whether they own the
      car they're referencing*. Fix: `SELECT user_id FROM car WHERE car_id = %s` before the
      insert — `404` if the car doesn't exist, `403` (not `401` — the client *is* authenticated,
      just not permitted) if it exists but belongs to someone else. Verified with a real
      cross-user test (a second user correctly blocked from logging a service on the first
      user's car). Also catches `ForeignKeyViolation` for a bad `maintenance_type_id`.
    - `POST /service_part`: same ownership-check idea, one relationship further removed —
      `service_part` only references `service_id`, so verifying ownership means tracing
      `service_part → service → car → user` via a SQL `JOIN` (`SELECT car.user_id FROM service
      JOIN car ON service.car_id = car.car_id WHERE service.service_id = %s`), first real use of
      a JOIN in this codebase. No `RETURNING` on the `INSERT`, since `service_part`'s primary key
      is the composite `(part_id, service_id)`, not a `SERIAL` column — there's no generated ID
      to fetch back. Catches `ForeignKeyViolation` (bad `part_id`) and `UniqueViolation`
      (duplicate part already logged on this service).
    - `POST /service_scheduled`: same `ON CONFLICT DO NOTHING RETURNING` + fallback-`SELECT`
      pattern as `car_config`/`maintenance_type`/`part`, on the `UNIQUE (config_id,
      maintenance_type_id)` constraint. Also catches `psycopg.errors.CheckViolation` (client
      submitted neither `mileage_interval` nor `months_interval`) — note `ON CONFLICT` only
      suppresses `UNIQUE` violations, not `CHECK` violations, so both a `try`/`except` *and* the
      `ON CONFLICT` clause were needed together. `user_id` unused (anti-abuse gate only, same
      reasoning as the other catalog-table endpoints).
    - `GET /cars`: first endpoint using `cur.fetchall()` instead of `fetchone()` (a user can own
      multiple cars) and the first read-side use of `Depends(get_current_user)` — here the token
      isn't just an ownership *check*, it's the actual filter (`WHERE car.user_id = %s`) scoping
      the whole query. Joins in `car_config` columns (year/make/model/engine) so the frontend
      doesn't need a second request per car just to know what it is.
    - `GET /cars/{car_id}`: first use of a path parameter (`{car_id}` in the route, `car_id: int`
      as a function param — FastAPI extracts and type-validates it automatically, `422` if it's
      not a valid int). Same `404`/`403` ownership-check pattern as the `POST` write endpoints,
      applied to a read this time.
    - `GET /cars/{car_id}/services`: combines the `/cars/{car_id}` ownership check with a joined
      `fetchall()` (`service` joined to `maintenance_type`, so the response has a readable
      `maintenance_name`, not just an ID) — the car's service history. Later extended to also
      `LEFT JOIN service_part`/`part` (specifically `LEFT`, not a regular `JOIN` — a service with
      zero parts attached must still appear in results, not be silently dropped) and return each
      service's `parts` as a nested list. Since SQL rows are flat, one row comes back per
      (service, part) pair — a service with 2 parts repeats twice, with its own columns
      duplicated each time — so the endpoint groups the flat rows into nested dicts in Python
      afterward (a dict keyed by `service_id`, appending a part entry only when that row's
      `part_id` isn't `NULL`, which is what a `LEFT JOIN` non-match looks like). Built to close a
      real gap the user noticed: after building `POST /service_part`, nothing surfaced attached
      parts anywhere in a response — this was the first backend change made specifically because
      a frontend page needed to display something the API didn't yet expose.
    - `GET /maintenance_types` and `GET /parts`: plain catalog listings, deliberately made
      **public** (no `Depends(get_current_user)`) — unlike the `POST` versions, a `GET` here
      doesn't need an anti-abuse gate since reading isn't an abuse vector the way writing is;
      being public also lets a frontend populate dropdowns before a user is logged in, and makes
      the response cacheable (identical for every caller, unlike a per-user authenticated
      response).
    - `GET /vin/{vin}/decode`: calls NHTSA's free public `decodevinvalues` API via `requests`,
      returning `year`/`make`/`model`/`engine` to pre-fill the frontend's "add a car" flow.
      Requires `Depends(get_current_user)` — an anti-abuse gate for a different reason than the
      `POST` endpoints: every call here triggers an *outbound* call to a third party, so an
      unauthenticated flood would let anyone hammer NHTSA's service through this backend.
      `response.raise_for_status()` inside a `try`/`except requests.exceptions.RequestException`
      catches network failures/timeouts (`timeout=5` set explicitly — an external service could
      otherwise hang the request indefinitely) and turns them into a clean `503`. Real bug caught
      in review, confirmed by testing the live NHTSA API directly: initial code checked
      `result["Make"] is None` to detect an unrecognized VIN, but NHTSA actually returns empty
      strings (`""`) for missing data, never `null` — so that check silently never fired, and
      invalid VINs returned a `200` with blank fields instead of a `404`. Fixed by checking
      `== ""` instead, verified against both a real VIN and a deliberately invalid one.
    - **First four `DELETE` endpoints**, added in escalating order of blast radius (smallest
      first, most consequential last), each reusing the same ownership-check pattern already
      established for reads/writes:
      - `DELETE /service_part/{service_id}/{part_id}`: composite-key deletion (both IDs as path
        params, matching `service_part`'s composite primary key). First use of `cur.rowcount`
        (not `RETURNING`/`fetchone()`, since a `DELETE` has nothing meaningful to hand back) —
        `0` after the `DELETE` means nothing matched, i.e. that part was never attached to that
        service, translated into a `404`.
      - `DELETE /service/{service_id}` and `DELETE /car/{car_id}`: same ownership-check-then-
        delete shape; no `rowcount` check needed here since the ownership `SELECT` already
        confirms the row exists before the `DELETE` runs. Both rely entirely on the schema's
        existing `ON DELETE CASCADE` chain for cleanup (deleting a car with a service that has
        an attached part removes all three rows in one call) — verified for real, not just
        assumed from the schema, by creating disposable test data with a part attached and
        confirming all three rows vanished after a single `DELETE /car` call.
      - `DELETE /users/me`: deliberately has **no `user_id` path parameter at all** — always
        deletes whichever account the verified token belongs to, never an ID the client
        supplies, closing the same category of vulnerability `POST /car` was built to avoid
        (never trust a client-supplied identifier for "which account/resource does this affect").
        Verified end-to-end with a disposable throwaway user: row confirmed gone via `psql`, and
        a follow-up login attempt correctly failed.
    - All nineteen endpoints use `with pool.connection() as conn: with conn.cursor() as cur:`
      instead of manual `.close()` calls — guarantees the connection is returned to the pool
      (not leaked) even when an exception/`HTTPException` is raised inside the block.
    - `CORSMiddleware` added, `allow_origins` scoped specifically to `http://localhost:5173`
      (the Vite dev server) — needed once frontend work started, since the browser blocks
      cross-origin requests by default (different port = different origin). Will need updating
      once deployed somewhere real.
    - All verified working end-to-end via `uvicorn main:app --reload` + real requests, including
      multi-user cross-ownership tests; rows/tokens confirmed correct in `psql` and via local
      `jwt.decode()`.
- `frontend/` (React + TypeScript via Vite) — moved past the bare scaffold, now containing:
  - `react-router-dom` installed for client-side routing; `main.tsx` wraps the app in
    `BrowserRouter`, `App.tsx` defines `<Routes>`/`<Route>` mappings.
  - `src/api.ts` — a shared `apiFetch()` wrapper every page calls instead of raw `fetch`:
    prepends the backend base URL, auto-attaches `Authorization: Bearer <token>` from
    `localStorage` when a token exists, and throws a real `Error` (reading the backend's
    `detail` field) on any non-`2xx` response, so callers get one consistent `try`/`catch`
    pattern instead of repeating error handling everywhere.
  - `src/pages/SignupPage.tsx` (`/signup`) and `src/pages/LoginPage.tsx` (`/login`) — both
    working end-to-end: controlled form inputs via `useState`, submit via `apiFetch`, errors
    displayed inline. `LoginPage` saves the returned JWT to `localStorage` on success and
    navigates to `/cars`. Verified for real: a signup created an actual row in `users` (confirmed
    via `psql`), and a login stored a real token (confirmed via browser DevTools → Application →
    Local Storage).
  - Both pages required real debugging of fundamental React/TypeScript syntax the user was new
    to — class vs. function components (hooks only work in function components), `useState`
    destructuring syntax, `async`/`await` placement, `FormEvent<HTMLFormElement>` typing
    (`React.FormEvent` namespace access is deprecated in current `@types/react`, use a named
    `import type { FormEvent }` instead), `unknown` typing on `catch` blocks needing a type
    assertion (`err as Error`) before accessing `.message`, and remembering `export default` —
    all now understood and correctly applied.
  - `src/pages/CarsDashboard.tsx` (`/cars`) — first page that fetches data on load rather than
    on form submit, using `useEffect` with an empty dependency array (`[]`, runs once on mount);
    the async fetch logic lives in a separate function defined *inside* the effect and called
    immediately after (an effect callback can't be `async` itself). Three pieces of state
    (`cars`, `loading`, `error`) drive an "early return" pattern — render a loading message,
    then an error message, then only fall through to the actual list if neither applies. Defines
    a `type Car = {...}` matching the `GET /cars` response shape for type safety in the
    `.map()` render, with each list item keyed by `car_id`. Verified working end-to-end,
    including the error path (deleted the token from `localStorage`, confirmed a `401` correctly
    renders the error message instead of a car list). Each list item is wrapped in a
    react-router-dom `<Link to={"/cars/" + car_id}>` (not a plain `<a>`, which would force a full
    page reload/reset all React state) linking to that car's detail page; `Car` type exported so
    `CarDetailPage` can reuse it.
  - `src/pages/CarDetailPage.tsx` (`/cars/:carId`) — first use of a dynamic route param
    (`useParams<{ carId: string }>()`); the `useEffect` dependency array is `[carId]` rather than
    `[]`, since the component wouldn't remount (and thus wouldn't refetch) if navigating directly
    from one car's detail page to another. Makes two sequential `apiFetch` calls in one effect
    (car details, then service history). Required an explicit `if (!car) return ...;` guard
    before rendering — TypeScript can't infer `car` is non-null just from the `loading`/`error`
    early returns above it, since those are separate, unrelated state variables; only a direct
    null-check on `car` itself narrows its type. Verified end-to-end against both a car with
    logged services and one with none (confirmed the empty-service-history case renders
    correctly, not as a bug). Each service's `parts` array is rendered as a nested `<ul>` inside
    that service's `<li>` — first nested-list rendering in the app (a `.map()` inside a `.map()`,
    each level still needing its own `key`). Price display converts stored cents to dollars only
    at render time (`(cents / 100).toFixed(2)`, never touching the stored integer) using an
    explicit `!== null` check rather than a truthy check — a plain truthy check would have
    incorrectly hidden a genuinely free ($0.00) part, same "unknown price ≠ $0 price" principle
    enforced everywhere else in this project. One structural bug caught in review: the inner
    `.map()`'s `<li>` elements were initially direct children of the outer service `<li>` with no
    wrapping `<ul>` — same category of invalid-list-nesting mistake as `CarsDashboard` earlier.
    **Later extended with delete buttons** for car/service/part, each `window.confirm(...)`-gated
    before calling its `DELETE` endpoint. Deleting a car/service updates local state by filtering
    it out of the `services`/removal via `navigate("/cars")`; deleting a part is the trickiest —
    since `parts` is nested *inside* one specific service inside the outer `services` array,
    removing one requires `.map()`-ing the outer array, and only for the matching service,
    returning a **new** object (`{...service, parts: service.parts.filter(...)}`) rather than
    mutating it directly. Two real bugs caught in review on the user's first attempt: comparing
    `services.service_id` (the whole array, which has no such property — always `undefined`,
    making the check permanently `true` and the function a silent no-op) instead of `service`
    (the loop variable), and the handler doing only the local state update with no actual
    `DELETE` call, `confirm()`, or error handling at all — fixed to match the same
    confirm/try-`apiFetch`/catch shape as the other two delete handlers.
  - `src/pages/AddCarPage.tsx` (`/cars/new`) — two-step form in a single component, using a
    `step` state variable (`1`/`2`) with plain `if (step === 1) return (...)` early-return logic
    to switch between forms, rather than two separate routes — matches the two-call backend flow
    (`POST /car_config` then `POST /car`, `config_id` from the first carried in state into the
    second). Linked from `CarsDashboard` via `<Link to="/cars/new">`. Two real bugs caught in
    review: wrong endpoint paths (initially called `/cars/config` and `/car_config` for the two
    steps, instead of `/car_config` then `/car`), and `HTMLFormEvent` (not a real type) instead
    of `HTMLFormElement` in both handlers' `FormEvent<...>` typing. Deliberately sends `vin:
    undefined` (not `""`) when the field is left blank — the `car` table's VIN `CHECK` constraint
    accepts `NULL` or a valid 17-char VIN, not an empty string, and `/car` doesn't catch
    `CheckViolation`, so a raw empty string would have surfaced as an unhandled `500`. Error
    display deliberately kept *inline within each form* (`{error && <p>{error}</p>}`, same as
    `SignupPage`/`LoginPage`) rather than a full early-return replacing the page — unlike
    `CarsDashboard`/`CarDetailPage` (read-only, an error is a dead end), a failed submission here
    needs the form to stay visible so the user can fix their input and retry. Verified end-to-end:
    full two-step submission lands a new car on `/cars`.
    **Later expanded to three steps** to add VIN decoding: a new step 1 asks for a VIN, with
    three actions — "Decode" (`GET /vin/{vin}/decode`, pre-fills year/make/model/engine and
    advances), "Skip, I'll enter manually" (advances with fields blank), or Cancel (`<Link
    to="/cars">`, present on every step — no partial progress is persisted, so navigating away
    just abandons it). Step 1 uses plain buttons with individual `onClick` handlers rather than
    a `<form onSubmit>`, since it has three distinct actions, not one submission; introduces a
    per-action `decoding` loading state (disables/relabels just the Decode button while in
    flight) as distinct from the whole-page `loading` pattern used on read-only pages. The old
    steps shifted to 2 (car details, now with `required` on `year`/`make`/`model` — native HTML
    validation, blocks submission client-side before the backend's own validation even runs) and
    3 (VIN/mileage confirmation, `vin` carried over in state from step 1). Two real bugs caught
    in review: the decode fetch call was missing its leading `/` (`apiFetch` just concatenates
    `BASE_URL + path`, so this produced a malformed URL), and `handleCarSubmit`'s request body
    was missing `vin` entirely after the restructure. Also caught: a trailing slash on the
    decode URL didn't match the backend route exactly, silently working only via an automatic
    `307` redirect — confirmed via a direct `curl -i` test showing the redirect `Location`
    header — removed to hit the endpoint directly.
  - `src/pages/LogServicePage.tsx` (`/cars/:carId/services/new`) — first form populated from a
    fetched catalog (`GET /maintenance_types` on mount, same `useEffect` pattern as
    `CarsDashboard`). `<input type="date">` needed no conversion — its `"YYYY-MM-DD"` value
    already matches what the backend's `date` field expects, unlike `miles_at_service` (still
    needs `Number(...)`, same reasoning as `year` elsewhere). Two real bugs caught in initial
    review: `error` state was being set but never rendered anywhere in the JSX (user caught this
    one themselves before asking), and `navigate("/cars/$(carID)")` — not inside backticks so
    `$(carID)` was a literal string, not interpolation, plus `carID` didn't match the actual
    variable `carId` (case-sensitive). Linked from `CarDetailPage` via `<Link to={\`/cars/${carId}/services/new\`}>`.
    **Upgraded from a `<select>` to an `<input list>`/`<datalist>` combo** once the user asked a
    genuinely good product question — "how does a user log a maintenance type that isn't in the
    catalog yet?" — since a plain dropdown only lets you pick from what already exists. A
    `<datalist>` behaves differently from `<select>`: it doesn't carry a hidden `value`/`id`
    separate from the displayed text, so the input holds the type's *name* (string), not its ID.
    This changed `handleSubmit` into a two-step call: `POST /maintenance_type` first (idempotent
    find-or-create — works identically whether the name is new or already exists) to resolve the
    name to an ID, *then* `POST /service` with that ID. Considered `react-select`'s `Creatable`
    variant (the fuller "real" production pattern — search-as-you-type plus an explicit "Create
    X" affordance) but chose the dependency-free native `datalist` approach instead, since the
    core name-to-ID resolution logic is identical either way and the UI layer can be swapped
    later with low risk if ever needed. Verified end-to-end against both an existing type and a
    brand-new one (confirmed the new one landed in `maintenance_type` via a direct query).
  - `src/pages/AttachPartPage.tsx` (`/cars/:carId/services/:serviceId/parts/new`) — same
    `datalist`-based find-or-create pattern as the upgraded `LogServicePage`, applied to `part`.
    One added wrinkle `maintenance_type` didn't have: a part's identity is `part_name` **+**
    `brand` together (the composite `UNIQUE`), so this needed *two* separate datalist-backed
    inputs (name, brand) rather than one, both drawing their suggestions from the same single
    fetched `parts` array (mapping it twice — once for `.name`, once for `.brand` — rather than
    fetching two separate catalogs). `handleSubmit` is a three-value two-step call: `POST /part`
    with `{name, brand}` to resolve/create a `part_id`, then `POST /service_part` with that
    `part_id` plus `service_id` (from the URL) and `price_at_service_cents`. The latter
    deliberately reuses the empty-string-to-`undefined` pattern from `AddCarPage`'s `vin` field —
    `Number("")` evaluates to `0` in JavaScript (not `NaN`), which would have silently submitted
    a "free" price instead of "unknown," violating the exact same principle already established
    for `part.price_cents` on the backend (unknown price ≠ $0 price). Required real back-and-forth
    debugging on the user's part around conflating two different pieces of state into one
    variable (the fetched catalog array vs. the user's typed text) before landing on the correct
    `parts`/`partName`/`brand` three-way split — a good worked example of the general "what state
    does this component need" reasoning process (used moving forward: list every field the
    target API call's body needs → check if anything needs fetching just to populate choices →
    pull out anything URL-derived via `useParams` → add `error`/`loading` by default). Linked
    from each service in `CarDetailPage`'s history list. Verified end-to-end via a direct `psql`
    check of the `service_part` table (confirmed the row, including a `NULL` price when left
    blank, not `0`).
  - **Visual polish pass** — added `tailwindcss` + `@tailwindcss/vite` (v4, the modern setup: a
    Vite plugin plus a single `@import "tailwindcss";` in `index.css`, no separate config file
    needed). User chose this over plain CSS or a component library, explicitly for the real-world
    skill (utility classes are the dominant styling approach in production React apps). Since
    this was framed as design polish rather than logic to derive, the collaboration mode shifted
    from the teach/pseudocode/write-it-yourself loop to Claude applying styling directly across
    all pages, user reviewing — a deliberate one-off departure from the usual workflow, agreed
    with the user first rather than assumed. Added `src/components/Layout.tsx` — a shared nav
    header (branding + a **Log out** button) wrapping every authenticated page; logout didn't
    exist anywhere in the app before this. **Later added a "Delete Account" button** next to
    Log out — `window.confirm(...)`-gated, calls `DELETE /users/me`, then does the same
    cleanup as logout on success. Uses `alert()` for the error case rather than an inline error
    message, since `Layout` wraps every page and has no page-specific error state of its own to
    render into, unlike individual pages. Added `src/pages/HomePage.tsx` for the previously
    unhandled `/` route: `<Navigate to="/cars" replace />` if a token already exists in
    `localStorage` (first use of React Router's *declarative* redirect, vs. the `useNavigate()`
    *imperative* pattern used everywhere else — appropriate here since the redirect condition is
    known synchronously at render time, not triggered by a user action), otherwise a simple
    pitch + Sign Up/Log In buttons for logged-out visitors. Cleaned up dead files left over from
    the original Vite scaffold (`App.css`, unused SVGs/`hero.png`, none referenced anywhere
    anymore) and updated the browser tab title from the Vite default to "Servicd".
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
- `engine` — TEXT NOT NULL (use `'Unknown'` when the client doesn't provide one, rather than
  NULL — same NULL-uniqueness reasoning as `part.brand`, needed for the UNIQUE below to work)
- UNIQUE (`year`, `make`, `model`, `engine`) — prevents duplicate catalog rows for the same
  real-world car (e.g. two users both adding a "2020 Honda Civic" independently); added after
  the table was already live but still empty, so no data migration was needed

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
- `brand` — TEXT NOT NULL (use `'Unknown'` when the client doesn't provide one, rather than
  NULL — avoids NULL-uniqueness edge case on the composite UNIQUE below; same convention as
  `car_config.engine`)
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
- UNIQUE (`config_id`, `maintenance_type_id`) — one rule per maintenance type per car config; the
  mileage-vs-time "whichever comes first" logic already lives inside a single row via the two
  interval columns, so a repeat of this pair is a duplicate, not a second legitimate rule; added
  after the table was already live but still empty, same as `car_config`'s UNIQUE
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
- **`db.py` uses `psycopg_pool.ConnectionPool`** instead of opening a fresh connection per call.
  Started with "one connection per call" deliberately as the simplest correct starting point
  (a single shared connection would be unsafe across concurrent FastAPI requests), then upgraded
  to a real pool once multiple endpoints worked end-to-end — same "simple first, refine later"
  reasoning used elsewhere (JWT expiration, `car_config`'s dedup logic). The pool is created
  once at module load (critical — creating it per-request would defeat the purpose); endpoints
  borrow a connection via `with pool.connection() as conn:`, which returns it to the pool on
  block exit rather than closing it.

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
- **Frontend stores the JWT in `localStorage`**, chosen deliberately over the more XSS-resistant
  hybrid pattern (short-lived access token in memory only + longer-lived refresh token in an
  `httpOnly` cookie), since that hybrid needs the refresh-token backend infrastructure already
  deferred above. `localStorage` is the common real-world SPA choice, not the most secure one —
  user has explicitly signed off on this tradeoff and wants the hybrid kept as a known upgrade
  path once refresh tokens are built, not dismissed.

## Backend Testing Infrastructure
First piece of the "Automated tests + CI/CD" priority (see Strategic Direction below). User
explicitly rejected a pragmatic shortcut (point tests at a separate DB, reset via table
truncation, don't touch existing endpoint code) in favor of the "correct textbook version,"
reasoning it's what's actually used in the real world and worth the extra setup cost — this
governs the design below.
- **Dependency-injected DB connections.** `db.py` gained `get_db()`, a generator dependency
  (`with pool.connection() as conn: yield conn`) alongside the existing module-level `pool`.
  Every one of the 19 database-touching endpoints in `main.py` (all except
  `GET /vin/{vin}/decode`, which never touches the DB) was refactored from calling
  `pool.connection()` directly to accepting `conn = Depends(get_db)` as a parameter — this is
  what makes swapping the connection during tests possible at all, since `Depends()` is the only
  thing FastAPI lets a test override.
- **Explicit transaction blocks instead of manual commits.** Every write endpoint's insert/
  update/delete now runs inside `with conn.transaction():` (auto-commits on clean exit,
  auto-rolls-back on exception) instead of a manual `conn.commit()` call. Pure `GET` reads
  stayed as plain `with conn.cursor() as cur:` blocks — nothing to commit. Endpoints with
  `try`/`except` around specific `psycopg.errors.*` (FK/Unique/Check violations) have the
  `try` wrap the *outer* `with conn.transaction():` block, so the transaction context manager
  sees the exception, rolls back, and re-raises it for the `except` to convert into the right
  `HTTPException`.
- **`servicd_test` database** — same schema as `servicd` (run from `servicdDB.sql`), used only
  by the test suite, never by manual dev work. Selected via `backend/.env.test` (git-ignored,
  same shape as `.env` but with `DB_NAME=servicd_test`); `.gitignore` changed from `.env` to
  `.env*` so this new file stays ignored too.
- **`backend/tests/conftest.py`** — the core test infrastructure, built around one problem:
  endpoint code itself calls "commit" (via `with conn.transaction():`), so a naive "wrap the
  whole test in a transaction and roll back at the end" won't work, since the endpoint's own
  commits would already have persisted. Fix: `conn.transaction()`, when called while already
  inside an active transaction, automatically becomes a **SAVEPOINT** (a nested transaction)
  instead of a new top-level one — so an outer `with conn.transaction():` opened once per test,
  wrapping a request through the real `TestClient`, causes every endpoint-internal "commit" to
  just release a savepoint rather than actually persisting anything, and rolling back the outer
  transaction undoes all of it. Since `conn.transaction()` has no explicit "please roll back,
  nothing's wrong" method, a placeholder `Rollback(Exception)` is raised deliberately right
  after the test body runs and caught immediately outside — the `db_conn` fixture yields the
  connection, then always raises `Rollback` once the test is done, forcing the rollback whether
  or not the test itself passed. A second fixture, `client`, depends on `db_conn` and overrides
  `get_db` (`app.dependency_overrides[get_db] = lambda: (yield db_conn)`) so every request made
  through the returned `TestClient` uses that same connection/transaction, then clears the
  override on teardown.
- **`backend/tests/test_users.py`** and **`backend/tests/test_login.py`** — the first 4 tests
  (`test_create_user`; `test_login_success`, `test_login_wrong_password`,
  `test_login_nonexistent_username`), covering `POST /users` and `POST /login`. Verified for
  real, not just "tests pass": after running them, directly queried `servicd_test` via `psql`
  and confirmed zero rows persisted (including a repeat run, to rule out the first pass being a
  fluke and to confirm `SERIAL` sequences advancing across rolled-back inserts — expected,
  harmless — doesn't break anything).
- **Coverage later expanded to all 19 endpoints — 46 tests total across 7 files**, once two more
  `conftest.py` fixtures existed to support it: `auth_headers` (creates one user via `POST
  /users` + `POST /login`, returns `{"Authorization": "Bearer <token>"}`) for endpoints requiring
  auth, and `make_auth_headers` (a **fixture factory** — returns a function the test calls
  however many times it needs, each call producing an independent logged-in user via a `nonlocal`
  counter for unique usernames) for the ownership-check (`403`) tests, which need two different
  users in the same test. Organized one file per resource: `test_car.py` (`car_config`/`car`,
  including the `ON CONFLICT` idempotency check), `test_service.py` (`service`/`service_part`,
  including cross-user `403` ownership checks), `test_catalog.py` (`maintenance_type`/`part`/
  `service_scheduled`, including the `CheckViolation` `400` case), `test_cars_read.py` (all 5
  `GET`s, including asserting on the `LEFT JOIN`-grouped nested `parts` structure, a service with
  zero parts still appearing, list results correctly scoped to the requesting user, and the two
  public catalog `GET`s explicitly called with no `headers=` at all to prove no auth is required),
  and `test_delete.py` (all 4 `DELETE`s, in the same escalating-blast-radius order as the
  endpoints themselves — verifying `ON DELETE CASCADE` by checking directly via `db_conn` that a
  deleted car's service row is also gone, rather than indirectly through another endpoint's
  behavior, and verifying account deletion the same way against the `users` table).
- **Full-codebase refactor verified two ways after completion:** (1) the existing 4-test pytest
  suite still passes unchanged; (2) a full manual smoke test via `curl` against the real running
  `servicd` (dev) database, specifically re-exercising the structurally trickiest endpoints —
  `car_config`/`maintenance_type`/`part`/`service_scheduled`'s `ON CONFLICT` find-or-create
  flows (repeat calls return the same ID), `car`'s `ForeignKeyViolation`/`UniqueViolation`
  handling now that the `try`/`except` wraps `with conn.transaction():`, `service`/
  `service_part`'s ownership-check-then-transactional-write split, `service_scheduled`'s
  `CheckViolation`, `GET /cars/{car_id}/services`'s `LEFT JOIN` + Python-side grouping (now
  split across two separate `with conn.cursor()` blocks instead of one), `DELETE
  /service_part/...`'s `cur.rowcount` check now living inside a transaction block, and
  `DELETE /car`'s `ON DELETE CASCADE` chain — all confirmed correct, no regressions found.

## Next Steps (not yet done)
Backend: all 8 tables have a working, tested `POST` endpoint, plus 5 `GET` endpoints, plus
`GET /vin/{vin}/decode` (NHTSA integration), plus 4 `DELETE` endpoints (part-from-service,
service, car, account — in escalating order of blast radius) — full read+write+delete coverage
with authorization checks everywhere ownership matters. All DB-touching endpoints now use
dependency-injected connections (`Depends(get_db)`) so tests can override them; pytest coverage
is now complete across all 19 endpoints (46 tests across 7 files — see "Backend Testing
Infrastructure" above). **GitHub Actions CI is live** (`.github/workflows/backend-tests.yml`) —
runs the full pytest suite against a fresh disposable Postgres service container on every push/PR
to `main`, verified via a real passing run (all 46 tests green in ~1 minute). Added
`backend/requirements.txt` (the project had no machine-readable dependency list before this,
verified by installing it into a completely fresh venv and rerunning the suite from it). This
completes the "Automated tests + CI/CD" priority.

Frontend: signup, login, the `/cars` dashboard, the car detail page (now including each
service's attached parts, nested under it, with prices, and delete buttons for the car/each
service/each part), adding a car (now a three-step `/cars/new` flow with VIN decoding,
skip-to-manual, and cancel on every step), logging a service (`/cars/:carId/services/new`, now a
two-step flow — scan a receipt via `POST /receipt/decode` or skip to manual entry, with an
editable pre-filled parts list), and attaching a part to a service
(`/cars/:carId/services/:serviceId/parts/new`) are all done and verified end-to-end. Visual
polish pass complete (Tailwind CSS, shared nav/logout, home page). Delete-account button in the
shared nav.

## Strategic Direction (decided — supersedes the plain feature-completion path above)
Explicitly pivoted away from "just keep building the originally-planned features" toward: make
this project maximally impressive to recruiters *and* genuinely viable as a real startup pitch.
Prompted by the user directly asking "ignore the current plan — what would make this impressive
to recruiters and marketable as a startup," discussed at length, then adopted as the actual path
forward rather than just a brainstorm. Maintenance recommendations and cost insights (below) are
**deprioritized, not abandoned** — still the app's stated core differentiators per Project
Overview, just no longer next in line.

Priority order:
1. **Automated tests + CI/CD — done.** Backend `pytest` suite (46 tests, all 19 endpoints) plus
   GitHub Actions running it on every push/PR to `main` are both live (see "Backend Testing
   Infrastructure" and "Next Steps" above). React Testing Library for key frontend flows was
   considered but not pursued — not blocking, could still be added later. This was identified as
   the first thing a technical reviewer checks for, and the thing that makes every later change
   safer to make.
2. **Receipt/photo OCR for logging services — done.** User uploads a photo or PDF of a service
   receipt, Claude extracts maintenance type/mileage/date/parts/prices, and it pre-fills
   `LogServicePage` for review before submitting. Chosen over "AI second-guesses the
   manufacturer's maintenance interval" (also discussed) — OCR's failure mode is low-risk (user
   corrects a misread field), whereas AI-generated maintenance-interval advice risks giving wrong
   mechanical guidance with real consequences. If AI-generated interval advice is ever pursued,
   "commentary alongside the manufacturer schedule" is the safer framing — supplementary
   context, never a replacement number.
   - **Backend:** `backend/ai.py` — a module-level `anthropic.Anthropic` client (mirrors `db.py`'s
     pool-created-once-at-import pattern), reading `ANTHROPIC_API_KEY` from `.env`.
     `backend/schemas.py` — new file (first Pydantic models split out of `main.py`, a precedent
     for eventually migrating the other nine); `ReceiptExtraction`/`ExtractedPart` describe the
     exact JSON shape requested from Claude via `output_format=`, deliberately asking for
     `price_dollars` (not cents) — reading a printed dollar amount is a safe, verifiable task for
     the model, while the cents conversion (`round(dollars * 100)`) is done deterministically in
     Python, same "AI's job should be low-risk" reasoning as the OCR feature choice itself.
     `POST /receipt/decode` in `main.py` — requires auth (anti-abuse *and* cost-control gate,
     stronger reasoning than `GET /vin/decode`'s since this triggers a real paid API call, not a
     free government one), reads the upload via `file.file.read()` (deliberately synchronous,
     not `await file.read()`, to keep this the only endpoint in the file staying consistent with
     every other endpoint's plain `def` style rather than becoming the one `async def` outlier),
     branches on `file.content_type` to build an `"image"` or `"document"` content block, and
     catches `anthropic.AnthropicError` (confirmed via direct introspection to be the real base
     class every SDK exception inherits from) → `503`.
   - **Frontend:** `api.ts`'s `apiFetch` was fixed to conditionally omit the `Content-Type`
     header when the request body is `FormData` — a hardcoded `application/json` header would
     have silently broken every file upload, since the browser only auto-fills the required
     multipart boundary parameter when it's left to set `Content-Type` itself.
     `LogServicePage.tsx` gained a new step 1 (upload/skip, mirroring `AddCarPage`'s VIN-decode
     pattern) and an editable parts list in step 2, backed by `updatePart` — a small function
     demonstrating the "replace one item in an array of state objects immutably" pattern via
     `.map()` plus a computed property key (`{...part, [field]: value}`), and a **fixture-factory
     style** reusable across any field. `handleSubmit` was extended with a `for...of` loop
     (deliberately not `.map()`, since each `POST /service_part` needs to `await` the matching
     `POST /part` finishing first — sequential, not fire-and-forget) that creates each part after
     the service exists, skipping any row a user cleared the name on (the only way to "remove" an
     unwanted OCR-extracted part, since there's no dedicated remove button yet).
   - **Verified end-to-end for real**, not just via `tsc`/build: a synthetic receipt image driven
     through an actual headless-Chromium session (Playwright, installed temporarily for this one
     test and removed afterward — not a project dependency) — uploaded → scanned → form
     pre-filled with exactly the right values, including the date correctly normalized to
     `YYYY-MM-DD` after a prompt-wording fix (Claude initially echoed the receipt's printed
     `MM/DD/YYYY` format verbatim) → submitted → confirmed via direct `psql` query that the
     `service` and both `service_part` rows landed with correct data, including accurate
     dollars-to-cents conversion.

Deprioritized (still real, just later):
- **Maintenance recommendations** — `POST /service_scheduled` exists on the backend, but
  nothing surfaces schedules anywhere, and no logic yet actually calculates "due soon" by
  combining a car's schedule rules with its service history and current mileage/date.
- **Cost insights** — cost-per-mile, cost breakdown by category. Needs new aggregate queries
  (`SUM`/`GROUP BY`, not used anywhere yet) plus a display page.
- **Deployment** — this has all been local dev only so far.

## Future Feature Ideas (not scheduled, just captured)
Split by which audience they serve — the strongest ideas serve both.

**Recruiter-facing (demonstrates engineering depth beyond this app's core CRUD):**
- A live deployed URL (Railway/Render/Fly.io) instead of local-only — a working link beats a
  README every time.
- Docker/docker-compose for the whole stack (Postgres + backend + frontend).
- Rate limiting on auth endpoints (e.g. `slowapi`) — nothing currently stops repeated hammering
  of `POST /login`.
- Recall alerts via NHTSA's separate recall API — reuses the exact external-API-integration
  pattern already built for VIN decoding, cheap to add since it extends a known pattern rather
  than starting from scratch.

**Startup/business viability (real user value, real differentiation from existing competitors):**
- Shareable/exportable maintenance history (PDF or a public read-only link) — ties to genuine
  resale value (a documented service history raises what a car sells for), not just a
  nice-to-have.
- Household/multi-user car sharing — families frequently share one vehicle; the schema
  currently enforces strictly one owner per car.
- Shop/mechanic-side accounts — let a mechanic log a service directly into a customer's account
  at checkout instead of the customer typing it in later, solving the data-entry friction
  problem structurally rather than just making manual entry easier.
- Aggregated/anonymized insights ("cars like yours typically need X around this mileage") — a
  feature that gets *more* valuable as the user base grows, the kind of data-network-effect a
  real investor pitch would care about.
