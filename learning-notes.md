# Servicd — Learning Notes

Personal study reference for the concepts used while building Servicd. Organized by topic, each
concept has a short **What/Why**, a small **Example** (illustrating the concept generically — not
always lifted verbatim from this codebase), and a **Check yourself** question with the answer
tucked under a collapsible spoiler so you can quiz yourself without seeing the answer immediately.

This file grows over time — new concepts get added here as they come up, and this is the doc we
use for periodic live quizzing too.

---

## Database / SQL

### Constraints: NOT NULL, UNIQUE, CHECK
- **NOT NULL** — a column must always have a value; used anywhere the app can't function without
  the data (e.g. `users.username`).
- **UNIQUE** — no two rows can share the same value in that column (or combination of columns,
  for a composite UNIQUE like `car_config`'s `(year, make, model, engine)`).
- **CHECK** — a condition every row must satisfy (e.g. `service_scheduled` requiring at least one
  of `mileage_interval`/`months_interval` to be non-null; `car.vin` requiring a valid 17-char
  format).
- Why enforce these in the database instead of just the app? The database is the last line of
  defense — app code can have bugs or get bypassed, but a constraint violation is impossible to
  slip past.

**Example:**
```sql
CREATE TABLE product (
    product_id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0)
);
```

<details><summary>Check yourself</summary>

Why does `car_config.engine` default to `'Unknown'` instead of allowing `NULL` when the client
doesn't provide one?

**Answer:** The table has `UNIQUE (year, make, model, engine)`. In SQL, `NULL` is never considered
equal to another `NULL` (not even itself) — so two rows with the same year/make/model and both
`NULL` engines would NOT violate the UNIQUE constraint, silently creating duplicate catalog
entries. Using `'Unknown'` as a real string value makes the UNIQUE constraint actually work.
</details>

### Primary keys, including composite keys
- A **primary key** uniquely identifies a row. Usually a single auto-incrementing column
  (`SERIAL PRIMARY KEY`), but can be a **composite key** — multiple columns together, like
  `service_part`'s `PRIMARY KEY (part_id, service_id)`.

**Example:**
```sql
CREATE TABLE enrollment (
    student_id INTEGER REFERENCES student(student_id),
    course_id INTEGER REFERENCES course(course_id),
    PRIMARY KEY (student_id, course_id)
);
```

<details><summary>Check yourself</summary>

Why does `service_part` use a composite primary key instead of its own `SERIAL id` column?

**Answer:** The natural identity of a row in `service_part` already is the pair `(part_id,
service_id)` — that pair is exactly what should be unique (a part can't be logged twice on the
same service). Using it as the primary key gets that uniqueness enforcement for free, instead of
adding a separate `UNIQUE` constraint on top of an arbitrary generated ID.
</details>

### Foreign keys and ON DELETE behavior
- A **foreign key (FK)** ties a column to another table's primary key, guaranteeing referential
  integrity (you can't reference a car that doesn't exist).
- **ON DELETE CASCADE** — deleting the referenced row automatically deletes rows that reference
  it too.
- Default (no CASCADE) — deleting a referenced row is **blocked** if anything still references it.

**Example:**
```sql
CREATE TABLE comment (
    comment_id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(user_id)  -- no cascade: block delete instead
);
```

<details><summary>Check yourself</summary>

Why does `car.user_id` have `ON DELETE CASCADE`, but `car.config_id` doesn't?

**Answer:** `car.user_id` is an "ownership" relationship — a car has no meaning without its owner,
so deleting a user should clean up their cars automatically. `car.config_id` points to a shared
catalog row (`car_config`) that other users' cars might also reference — cascading would silently
destroy a catalog entry (and by extension, other users' data) just because one car referencing it
got deleted. Catalog tables should block deletion instead, forcing a deliberate decision.
</details>

### Junction tables (many-to-many)
- Two tables have a many-to-many relationship when each side can relate to multiple rows on the
  other side. SQL has no native way to express that directly — you need a third table
  ("junction table") with a foreign key to each side. `service_part` is the junction between
  `service` and `part`.

**Example:**
```sql
-- many-to-many: a student takes many courses, a course has many students
CREATE TABLE enrollment (
    student_id INTEGER REFERENCES student(student_id),
    course_id INTEGER REFERENCES course(course_id),
    PRIMARY KEY (student_id, course_id)
);
```

<details><summary>Check yourself</summary>

Why can't `service` just have a `part_id` column directly, instead of needing `service_part`?

**Answer:** A single column can only point to one row. One service can involve multiple parts
(e.g. an oil change uses both an oil filter and oil itself), and one part type gets reused across
many different services — a plain `part_id` column on `service` could only capture one part per
service.
</details>

### `ON CONFLICT DO NOTHING ... RETURNING` (find-or-create / upsert pattern)
- Pattern: try to `INSERT`; if a UNIQUE constraint would be violated, do nothing instead of
  erroring, and `RETURNING` gives back the new row's ID (or nothing, if it was skipped). Combined
  with a fallback `SELECT` for when the insert was skipped, this becomes an atomic "find this row,
  or create it if it doesn't exist yet" operation — used for every catalog table (`car_config`,
  `maintenance_type`, `part`, `service_scheduled`).

**Example:**
```sql
INSERT INTO tag (name) VALUES ('urgent')
ON CONFLICT (name) DO NOTHING
RETURNING tag_id;
-- if that returns no row, the tag already existed — fall back to:
SELECT tag_id FROM tag WHERE name = 'urgent';
```

<details><summary>Check yourself</summary>

Why is this pattern described as "atomic," and what problem would you hit without it (e.g. doing
a `SELECT` first, and only running `INSERT` if nothing came back)?

**Answer:** Two concurrent requests could both run the `SELECT`, both see "nothing exists yet,"
and both proceed to `INSERT` — resulting in two duplicate rows (a race condition), or one request
crashing with a UNIQUE violation depending on timing. `ON CONFLICT DO NOTHING` folds the
check-and-insert into a single database operation, so there's no window where two requests can
both "see" the row as missing at the same time.
</details>

### JOIN vs. LEFT JOIN
- A regular `JOIN` only returns rows that have a match on both sides. A `LEFT JOIN` keeps every
  row from the left table even if there's no match on the right (filling those columns with
  `NULL`).

**Example:**
```sql
-- regular JOIN: authors with zero books vanish from the results
SELECT author.name, book.title FROM author JOIN book ON book.author_id = author.author_id;

-- LEFT JOIN: every author appears, book.title is NULL if they have none
SELECT author.name, book.title FROM author LEFT JOIN book ON book.author_id = author.author_id;
```

<details><summary>Check yourself</summary>

Why does `GET /cars/{car_id}/services` use a `LEFT JOIN` to `service_part`/`part` instead of a
regular `JOIN`?

**Answer:** A service with zero parts attached would have no matching rows in `service_part` at
all. A regular `JOIN` would silently drop that service from the results entirely (since there's
no match), which would incorrectly make it look like the service was never logged. `LEFT JOIN`
keeps the service row and just gives it a `NULL` part.
</details>

### Storing money as integer cents
- Prices are stored as whole-number cents (`price_cents`), not floats/decimals, and only
  converted to dollars for display.

**Example:**
```python
price_cents = 1999          # $19.99, stored as an exact integer
display = f"${price_cents / 100:.2f}"   # "$19.99" — converted only for display

>>> 0.10 + 0.20 == 0.30      # classic float trap
False
```

<details><summary>Check yourself</summary>

What actually goes wrong if you store `19.99` as a float instead of `1999` as an integer?

**Answer:** Floating-point numbers can't represent most decimal fractions exactly in binary (the
same way 1/3 can't be written exactly in decimal). Doing arithmetic on floats (adding up many
prices) accumulates tiny rounding errors that compound over time — a total that should be exactly
$100.00 might come out as $99.9999999997. Integers have no such rounding error.
</details>

### Transactions (commit / rollback)
- A transaction groups a set of database operations so they either **all** succeed together
  (commit) or **all** get undone together (rollback) if anything goes wrong. `with
  conn.transaction():` commits automatically if the block finishes cleanly, and automatically
  rolls back if an exception is raised inside it.

**Example:**
```sql
BEGIN;
UPDATE account SET balance = balance - 100 WHERE account_id = 1;
UPDATE account SET balance = balance + 100 WHERE account_id = 2;
COMMIT;  -- if anything failed above, ROLLBACK instead — never half a transfer
```

<details><summary>Check yourself</summary>

Why does `POST /car`'s `try`/`except` wrap the *outer* `with conn.transaction():` block, rather
than putting the `try`/`except` only around the `cur.execute(...)` line itself?

**Answer:** The transaction context manager needs to actually see the exception in order to know
it should roll back — if the exception were caught and swallowed *inside* the `with
conn.transaction():` block, the transaction manager would think the block finished cleanly and
would try to commit a transaction that's actually in a broken/aborted state. Letting the exception
propagate out of the `with` block lets it roll back correctly, and only then does the outer
`except` catch it to build the HTTP response.
</details>

### Savepoints (nested transactions)
- Calling `conn.transaction()` while already inside an active transaction doesn't start a new,
  separate transaction — it creates a **savepoint**, a checkpoint inside the existing one. Rolling
  back the outer transaction erases everything, including anything "committed" at a savepoint
  along the way.

**Example:**
```sql
BEGIN;
INSERT INTO orders (customer_id) VALUES (1);
SAVEPOINT before_items;
INSERT INTO order_items (order_id, sku) VALUES (1, 'BAD-SKU');  -- fails
ROLLBACK TO SAVEPOINT before_items;  -- undoes just the item insert, order insert survives
COMMIT;
```

<details><summary>Check yourself</summary>

This is the mechanism the whole test-rollback system depends on. In your own words, why does an
endpoint's internal `with conn.transaction():` call NOT actually persist data during a test?

**Answer:** Because the test fixture already opened an outer transaction on that same connection
before the endpoint ever runs. When the endpoint's own code calls `with conn.transaction():`, it's
no longer the first/outermost transaction — it becomes a savepoint nested inside the test's
outer one. The endpoint "commits" the savepoint (which just means "checkpoint reached, don't worry
about undoing this part yet"), but nothing is truly persisted to disk until the *outermost*
transaction commits — and the test never lets that happen; it always rolls the outer one back.
</details>

### Connection pooling
- Opening a new database connection per request is slow. A **connection pool** keeps a set of
  already-open connections ready to hand out, and returns them to the pool (rather than closing
  them) when a request finishes.

**Example:**
```python
pool = ConnectionPool(conninfo="dbname=servicd ...")  # created ONCE, at startup

def handle_request():
    with pool.connection() as conn:   # borrow an existing connection
        ...                            # use it
    # returned to the pool automatically here, not closed
```

<details><summary>Check yourself</summary>

Why is the pool created once, at module load time, instead of once per request?

**Answer:** The whole point of a pool is to reuse a small set of already-established connections
across many requests. Creating a new pool per request would mean creating a fresh set of
connections every single time — defeating the purpose entirely and being just as slow as not
pooling at all.
</details>

---

## Backend / API Design

### Dependency injection (`Depends`)
- Instead of an endpoint function reaching out and grabbing things it needs itself (a DB
  connection, the current user), it declares them as parameters and lets the framework supply
  them (`conn = Depends(get_db)`, `user_id = Depends(get_current_user)`). FastAPI calls the
  dependency function and passes its result in.

**Example:**
```python
def get_db():
    with pool.connection() as conn:
        yield conn

@app.get("/items")
def list_items(conn = Depends(get_db)):   # framework supplies `conn`
    ...
```

<details><summary>Check yourself</summary>

What concrete capability does dependency injection unlock that direct calls (`pool.connection()`
inside the function body) don't?

**Answer:** Swappability. Because the endpoint asks *the framework* for a connection rather than
grabbing one directly, `app.dependency_overrides` can intercept that ask and hand back a different
connection during tests — which is exactly how the whole rollback-based test system works. If
endpoints called `pool.connection()` directly, there'd be no hook point to substitute anything.
</details>

### Path params, body params, query params
- **Path params** — part of the URL itself (`/cars/{car_id}` → `car_id`), for identifying a
  specific resource.
- **Body params** — the JSON payload of a `POST`/`PUT` request, for data being submitted.
- (Not used much yet in this project, but exists for completeness) **query params** — `?key=value`
  in the URL, typically for optional filters on a `GET`.

**Example:**
```
GET  /users/42/orders?status=shipped&limit=10
        └──┬──┘                └───────┬───────┘
     path param                  query params

POST /orders          body: {"item_id": 7, "quantity": 2}
```

<details><summary>Check yourself</summary>

Why does `DELETE /users/me` deliberately have no `user_id` path parameter, unlike `DELETE
/car/{car_id}`?

**Answer:** If `DELETE /users/{user_id}` existed and trusted a client-supplied ID, any logged-in
user could pass someone else's `user_id` and delete their account. By never accepting an ID from
the client for "which account is this," and always deriving it from the verified JWT instead, that
entire class of vulnerability is structurally impossible.
</details>

### Authentication vs. Authorization (401 vs. 403)
- **Authentication** — proving *who you are* (a valid token). Failure → `401 Unauthorized`.
- **Authorization** — proving you're *allowed to do this specific thing* (e.g. this car belongs to
  you). Failure → `403 Forbidden`.

**Example:**
```python
if token is None or not verify(token):
    raise HTTPException(401, "Invalid or missing token")   # who ARE you?

if resource.owner_id != current_user_id:
    raise HTTPException(403, "Not your resource")          # I know you, but no.
```

<details><summary>Check yourself</summary>

`POST /service` returns `403`, not `401`, when a user tries to log a service on someone else's
car. Why is `403` the correct choice here?

**Answer:** The request *does* include a valid, correctly-signed token — the server knows exactly
who's asking, so authentication succeeded. The problem is that the authenticated user isn't
permitted to act on that particular car. `401` would incorrectly imply "we don't know who you
are"; `403` correctly says "we know who you are, and the answer is no."
</details>

### Parameterized queries (SQL injection prevention)
- Never build SQL by string-concatenating user input. Use `%s` placeholders with a separate values
  tuple (`cur.execute("... WHERE username = %s", (username,))`) — the database driver handles
  safely inserting the value, rather than the value ever becoming part of the SQL text itself.

**Example:**
```python
# DANGEROUS — string concatenation
cur.execute(f"SELECT * FROM users WHERE username = '{username}'")

# SAFE — parameterized
cur.execute("SELECT * FROM users WHERE username = %s", (username,))
```

<details><summary>Check yourself</summary>

What could a malicious `username` value do if it were directly string-formatted into a query
instead of passed as a parameter?

**Answer:** A value like `' OR '1'='1` could turn a query's `WHERE` clause into something always
true, or a value containing `; DROP TABLE users; --` could append and execute an entirely separate
destructive statement. Parameterized queries prevent this because the driver treats the value
purely as *data*, never as part of the SQL structure, no matter what characters it contains.
</details>

### Mapping specific DB errors to HTTP responses
- Catching specific exception types (`psycopg.errors.ForeignKeyViolation`,
  `psycopg.errors.UniqueViolation`, `psycopg.errors.CheckViolation`) and converting each into a
  precise, meaningful HTTP status/message, instead of letting every DB failure surface as a
  generic `500`.

**Example:**
```python
try:
    with conn.transaction():
        cur.execute("INSERT INTO car (...) VALUES (...)")
except psycopg.errors.ForeignKeyViolation:
    raise HTTPException(404, "Invalid config_id")
except psycopg.errors.UniqueViolation:
    raise HTTPException(400, "VIN already registered")
```

<details><summary>Check yourself</summary>

Why does `POST /car` catch `ForeignKeyViolation` as a `404` but `UniqueViolation` as a `400`?

**Answer:** A `ForeignKeyViolation` here means the client referenced a `config_id` that doesn't
exist — that's "the thing you're pointing at wasn't found," a `404`. A `UniqueViolation` means the
VIN they supplied already belongs to another car — the request itself is well-formed and every
reference is valid, but the data conflicts with an existing row, which is a `400` (a bad/invalid
request as submitted), not a "not found."
</details>

---

## Authentication & Security

### Password hashing with bcrypt
- Passwords are never stored in plain text. `bcrypt.hashpw` produces a hash that embeds a random
  salt directly inside the output string — `checkpw` needs no separate salt argument.

**Example:**
```python
import bcrypt

hashed = bcrypt.hashpw(b"correct horse", bcrypt.gensalt())
# b'$2b$12$KIXQ6b...'   <- salt + hash, all in one string

bcrypt.checkpw(b"correct horse", hashed)   # True
bcrypt.checkpw(b"wrong guess", hashed)     # False
```

<details><summary>Check yourself</summary>

If two different users pick the exact same password, will their stored `password_hash` values be
identical?

**Answer:** No. bcrypt generates a new random salt every time `hashpw` is called, and that salt is
baked into the resulting hash string. Identical passwords produce different hashes, which is
exactly why a separate `salt` column turned out to be redundant — the salt is already inside the
hash.
</details>

### Timing-safe comparison / preventing username enumeration
- `POST /login` always returns the identical error for "wrong password" and "username doesn't
  exist," AND always performs a real (slow) `bcrypt.checkpw` call in both cases — even for a
  nonexistent username, checked against a dummy hash — so the response time can't leak which case
  occurred either.

**Example:**
```python
dummy_hash = bcrypt.hashpw(b"placeholder", bcrypt.gensalt())  # created once, at startup

user = find_user(username)
if user is None:
    bcrypt.checkpw(password.encode(), dummy_hash)   # burn equal time, discard result
    raise HTTPException(401, "Invalid username or password")
elif not bcrypt.checkpw(password.encode(), user.password_hash):
    raise HTTPException(401, "Invalid username or password")   # same message either way
```

<details><summary>Check yourself</summary>

Why isn't an identical error *message* enough on its own — what's the second thing an attacker
could measure instead?

**Answer:** Response time. `bcrypt.checkpw` is deliberately slow by design. If the "username not
found" path returned immediately (skipping the hash check entirely) while the "wrong password"
path took the full bcrypt time, an attacker could tell the two cases apart just by timing many
requests — even with identical error text — and use that to enumerate which usernames are real.
</details>

### JWTs — signed, not encrypted
- A JWT's payload is base64-encoded, not encrypted — anyone holding the token can read it (e.g. on
  jwt.io without the secret). Only the *signature* is protected by the secret key, which proves
  the token wasn't tampered with and was genuinely issued by the server.

**Example:**
```python
import base64, json

token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI0MiIsImV4cCI6MTc5OX0.abc123signature"
header, payload, signature = token.split(".")

decoded = json.loads(base64.urlsafe_b64decode(payload + "=="))
print(decoded)   # {'sub': '42', 'exp': 1799...} — readable with NO secret key needed
```

<details><summary>Check yourself</summary>

Why is it critical that the JWT payload never contains `password_hash` or other sensitive fields?

**Answer:** Because "signed" only means "can't be forged or altered without detection" — it does
NOT mean "hidden." Anyone who intercepts or is handed the token (which is normal — the client
holds it) can trivially decode the payload and read it in plain text. Only put things in a JWT
payload that are safe for the token holder (and anyone who might see it) to read.
</details>

### JWT vs. server-side sessions
- A session cookie only works cleanly in browsers. A JWT bearer token in an `Authorization`
  header works identically across a web frontend and native mobile apps, at the cost of not being
  individually revocable before it expires (nothing is tracked server-side).

**Example:**
```
Session:  Cookie: session_id=abc123        (server looks up abc123 in a sessions table)
JWT:      Authorization: Bearer eyJhbG...  (server just verifies the signature, no lookup)
```

<details><summary>Check yourself</summary>

What's the actual security tradeoff being accepted by choosing JWT over sessions here?

**Answer:** If a JWT leaks (e.g. stolen from `localStorage` via XSS), there is no way to
invalidate just that one token before its `exp` time — the server has no record of issued tokens
to revoke. A session-based system could delete the session server-side immediately. This is why
`exp` is kept short (1 day) — it bounds how long a leaked token stays dangerous.
</details>

---

## Testing

### Integration testing with `TestClient`
- FastAPI's `TestClient` (built on `httpx`) lets you call your actual endpoints in-process —
  `client.post("/users", json={...})` — without starting a real server or making real network
  calls, while still exercising the real routing, validation, and endpoint logic.

**Example:**
```python
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.post("/users", json={"username": "alice", "password": "hunter2"})
assert response.status_code == 200
```

### Test isolation
- Each test should leave the world exactly as it found it, so tests can run in any order, run
  repeatedly, and run in parallel without interfering with each other.

**Example:**
```python
# BAD: relies on order, pollutes shared state
def test_a():
    create_user("shared_name")   # if test_b runs first and left this behind, this fails

# GOOD: isolated, self-contained, cleans up after itself (or runs in a rolled-back transaction)
def test_b(client, db_conn):
    create_user("unique_per_test_name")
    ...  # rolled back automatically when the test ends
```

<details><summary>Check yourself</summary>

What specifically would go wrong if `test_create_user` didn't roll back, and you ran the full test
suite twice in a row?

**Answer:** The first run would successfully insert `some_test_username`. The second run would hit
the `username` column's `UNIQUE` constraint trying to insert the same username again, causing a
`UniqueViolation` — the test would fail not because the app is broken, but purely because of
leftover state from a previous run.
</details>

### Pytest test discovery (why naming matters)
- By default, pytest only collects and runs functions whose name starts with `test_` (inside
  files named `test_*.py`, and classes named `Test*`). A function that doesn't match this
  convention is silently skipped — not an error, not a warning, just quietly never executed.

**Example:**
```python
def get_maintenance_types_public(client, auth_headers):   # NOT collected — missing "test_" prefix
    ...
    assert response.status_code == 200   # this assertion never actually runs

def test_get_maintenance_types_public(client, auth_headers):   # collected and run normally
    ...
```

<details><summary>Check yourself</summary>

Why is a misnamed test function specifically more dangerous than a test that fails?

**Answer:** A failing test is loud — it shows up in red in the test output, demanding attention.
A misnamed test is silent: the suite reports "N passed" and looks completely healthy, while that
function's assertions never ran at all. It creates false confidence — you believe an endpoint is
covered when it genuinely isn't, and nothing in the normal test run output tells you otherwise.
</details>

### Dependency overrides for testing
- `app.dependency_overrides[get_db] = override_get_db` swaps out what `Depends(get_db)` resolves
  to, for the lifetime of the override — every endpoint called through that `TestClient` gets the
  test's specific connection instead of a fresh one from the real pool.

**Example:**
```python
def override_get_db():
    yield db_conn                        # always hand back this one test connection

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
...
app.dependency_overrides.clear()         # restore normal behavior afterward
```

<details><summary>Check yourself</summary>

Why does the `client` fixture clear `app.dependency_overrides` after the test, instead of leaving
it set?

**Answer:** `app` is a single shared module-level object — if the override were left in place,
every *subsequent* test (or even real server behavior, if tests and the app ever shared a process)
would keep using that one stale test connection instead of getting a correct new one. Clearing it
resets the app back to its normal behavior for whatever runs next.
</details>

### Fixture composition (fixtures depending on fixtures)
- A `@pytest.fixture` is a reusable piece of setup that pytest builds for you and hands to your
  test — you request it by name as a parameter, you never call it like a normal function. Fixtures
  can themselves depend on other fixtures the exact same way: by listing them as parameters, not
  by calling them. Pytest resolves the whole chain bottom-up automatically. `auth_headers`
  (creates a user, logs in, returns `{"Authorization": "Bearer <token>"}`) depends on `client`,
  which depends on `db_conn` — a three-layer pyramid built without a single manual function call
  between the layers.

**Example:**
```python
@pytest.fixture
def db_conn():
    ...

@pytest.fixture
def client(db_conn):        # requests db_conn as a parameter — never calls db_conn()
    ...

@pytest.fixture
def auth_headers(client):   # requests client as a parameter — never calls client()
    client.post("/users", json={...})
    response = client.post("/login", json={...})
    return {"Authorization": f"Bearer {response.json()['token']}"}

def test_something(client, auth_headers):   # pytest builds the whole chain automatically
    client.post("/car_config", json={...}, headers=auth_headers)
```

<details><summary>Check yourself</summary>

What actually goes wrong if a test calls `auth_headers(client)` directly instead of listing
`auth_headers` as one of its own parameters?

**Answer:** Calling a fixture function directly bypasses pytest's fixture machinery entirely —
the caching (computing the value once per test, even if referenced multiple times), and any
cleanup code that would run after a generator-based fixture yields. Recent pytest versions detect
this and raise an error outright ("fixtures are not meant to be called directly"), specifically to
stop this mistake from silently producing subtly wrong behavior.
</details>

### Fixture factories (a fixture that returns a function)
- A plain fixture like `auth_headers` computes one fixed value, once per test — perfect for "I
  need one logged-in user." But some tests need *more than one* independent instance of something
  (e.g. two separate logged-in users, to test that user B gets a `403` acting on user A's car),
  and you don't know in advance how many. The fix: instead of the fixture returning a value
  directly, it returns a **function** — the test calls that function as many times as it needs,
  and each call produces something fresh.

**Example:**
```python
@pytest.fixture
def make_auth_headers(client):
    counter = 0
    def create_headers():
        nonlocal counter          # reach into the enclosing function's variable, not a new local one
        counter += 1
        username = f"user_{counter}"
        client.post("/users", json={"username": username, "password": "pw"})
        response = client.post("/login", json={"username": username, "password": "pw"})
        return {"Authorization": f"Bearer {response.json()['token']}"}
    return create_headers        # hand back the FUNCTION itself, not a call to it

def test_ownership_denied(client, make_auth_headers):
    owner = make_auth_headers()      # a real, distinct logged-in user
    intruder = make_auth_headers()   # a second, different real logged-in user
```
This is the same idea as a "factory function" in general programming — a function whose job is to
produce other things on demand — just applied to test setup.

<details><summary>Check yourself</summary>

If the fixture had ended with `return create_headers()` (calling it, with parentheses) instead of
`return create_headers` (just naming it), what would break?

**Answer:** `create_headers()` calls the inner function immediately, during the fixture's own
setup, and returns *its result* — one fixed headers dict — instead of returning the function
itself. Every test using `make_auth_headers` would then only ever get that one single dict (created
once, whether the test needs one user or five), and there'd be no way to call it again for a
second user — defeating the entire reason for making it a factory in the first place.
</details>

### `nonlocal` — reading/writing a variable from an enclosing function
- A nested function can normally *read* a variable from the function that contains it (this is
  called a **closure**), but *reassigning* it (`counter += 1`) would normally create a brand new
  local variable inside the nested function instead of updating the outer one. `nonlocal` tells
  Python "no — when I modify this name, modify the actual variable from the enclosing function,"
  which is what lets the counter in `make_auth_headers` actually persist and increment across
  multiple calls to `create_headers()`.

**Example:**
```python
def make_counter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

next_value = make_counter()
print(next_value())  # 1
print(next_value())  # 2
print(next_value())  # 3 — the same `count` persists across calls, thanks to nonlocal
```

<details><summary>Check yourself</summary>

What would happen to the counter in `make_auth_headers` if `nonlocal counter` were removed?

**Answer:** `counter += 1` inside `create_headers` would be treated as creating a brand-new local
variable named `counter` scoped only to that inner function call — and since it's read (`+= 1`
reads before writing) before ever being assigned in that scope, Python would actually raise an
`UnboundLocalError` the first time `create_headers()` runs, rather than silently using the wrong
value.
</details>

---

## Frontend (React + TypeScript)

### Function components & hooks
- Hooks (`useState`, `useEffect`, etc.) only work inside function components, not class
  components — this is a React rule, not a style preference.

**Example:**
```tsx
function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

### `useEffect` and dependency arrays
- `useEffect(fn, [])` runs `fn` once, after the first render (good for "fetch data on page load").
  `useEffect(fn, [carId])` re-runs whenever `carId` changes (needed when navigating between two
  instances of the same route without the component unmounting/remounting).

**Example:**
```tsx
useEffect(() => {
  fetchData();
}, []);          // runs once, on mount

useEffect(() => {
  fetchCar(carId);
}, [carId]);      // re-runs every time carId changes
```

<details><summary>Check yourself</summary>

Why does `CarDetailPage` need `[carId]` as its dependency array instead of `[]`, unlike
`CarsDashboard`?

**Answer:** `CarsDashboard` is only ever visited at one URL (`/cars`), so `[]` (run once on mount)
is sufficient. `CarDetailPage` sits at `/cars/:carId` — navigating from one car's detail page
directly to a different car's detail page reuses the *same component instance* (React doesn't
tear it down and remount just because a route param changed), so a `[]` effect would never
re-fire, and the page would keep showing the previous car's data. Including `carId` in the
dependency array makes the effect re-run whenever that value changes.
</details>

### Controlled inputs
- An `<input>`'s displayed value is driven by React state (`value={x}`, `onChange={...}`), rather
  than the DOM owning the value itself — this is what makes the current form data readable in
  JavaScript at any time (e.g. on submit).

**Example:**
```tsx
const [username, setUsername] = useState("");
<input value={username} onChange={(e) => setUsername(e.target.value)} />
```

### React Router: `Link` vs. `<a>`, `useParams`, `useNavigate`, declarative redirects
- `<Link>` performs client-side navigation, preserving React state and avoiding a full page
  reload; a plain `<a>` forces a full browser reload, wiping all in-memory state.
- `useParams()` reads dynamic segments out of the current URL (`:carId`).
- `useNavigate()` — *imperative* navigation, triggered by code (e.g. after a successful form
  submit).
- `<Navigate to="..." />` — *declarative* navigation, used when the redirect condition is already
  known synchronously at render time (e.g. "if already logged in, redirect off the home page").

**Example:**
```tsx
<Link to={`/cars/${carId}`}>View car</Link>          // client-side nav

const { carId } = useParams<{ carId: string }>();     // read from URL

const navigate = useNavigate();
navigate("/cars");                                     // imperative, after an event

if (loggedIn) return <Navigate to="/cars" replace />;  // declarative, at render time
```

<details><summary>Check yourself</summary>

Why does `HomePage` use `<Navigate>` instead of `useNavigate()` for its logged-in redirect?

**Answer:** `useNavigate()` is meant for redirecting *in response to something happening* (a click,
a completed async call) — it's called imperatively, inside an event handler or effect.
`HomePage`'s redirect condition (a token already existing in `localStorage`) is known immediately,
during the render itself, with no async step or user action involved — `<Navigate>` fits that
"just render the outcome" case declaratively, matching how the rest of JSX works.
</details>

### Rendering lists and nested lists
- Every item in a `.map()` needs a stable `key` prop. Nested lists (a list inside a list, like each
  service's `parts` inside the outer `services` list) need `key`s at *both* levels, and the inner
  list needs its own wrapping element (e.g. `<ul>`) — items can't be direct siblings of the outer
  list's items.

**Example:**
```tsx
<ul>
  {services.map((service) => (
    <li key={service.service_id}>
      {service.maintenance_name}
      <ul>
        {service.parts.map((part) => (
          <li key={part.part_id}>{part.name}</li>
        ))}
      </ul>
    </li>
  ))}
</ul>
```

### `<datalist>` for "pick existing or type new"
- `<input list="id">` paired with `<datalist id="id">` gives free-text input with autocomplete
  suggestions, unlike `<select>` which restricts input to exactly the listed options. Unlike
  `<select>`, the input's value is always the typed *text*, never a separate hidden ID — so
  resolving that text to a real database ID needs an explicit backend step (the find-or-create
  pattern).

**Example:**
```tsx
<input list="maintenance-types" value={name} onChange={(e) => setName(e.target.value)} />
<datalist id="maintenance-types">
  {types.map((t) => <option key={t.id} value={t.name} />)}
</datalist>
```

---

## Data Structures & Algorithms (interview-relevant)

Servicd doesn't hand-implement classic DSA from scratch, but the same patterns show up constantly
under the hood — in Postgres internals, in the schema itself, and in the Python grouping logic.
Recognizing "oh, this is just X" is most of what coding interviews actually test, so it's worth
naming the pattern explicitly wherever it appears.

### Hash maps — grouping flat rows into nested structures
- `GET /cars/{car_id}/services` gets back one flat SQL row per (service, part) pair (because of
  the `LEFT JOIN`) and needs to group them into a nested `{service: {..., parts: [...]}}`
  structure. The way to do that in O(n) instead of O(n²) is a hash map keyed by `service_id`.

**Example:**
```python
grouped = {}
for row in rows:
    service_id = row["service_id"]
    if service_id not in grouped:
        grouped[service_id] = {"service_id": service_id, "parts": []}
    if row["part_id"] is not None:
        grouped[service_id]["parts"].append({"part_id": row["part_id"]})
```
This is the exact same technique as LeetCode's "Group Anagrams" — bucket items by a computed key,
using a hash map for O(1) average lookup/insert per item.

<details><summary>Check yourself</summary>

What's the time complexity of the grouping loop above over `n` rows, and what would make it
O(n²) instead?

**Answer:** O(n) — each row is visited once, and dict lookup/insert (`in`, `[key] = ...`) is O(1)
average. It would degrade to O(n²) if, instead of a dict, you searched a plain list for the
matching service on every row (`for s in result_list: if s["service_id"] == service_id: ...`) —
an O(n) search repeated for each of the n rows.
</details>

### Sets — fast membership/duplicate checks
- A SQL `UNIQUE` constraint is conceptually a set: "this column can never contain the same value
  twice." The in-memory equivalent for O(1) duplicate detection is Python's `set`.

**Example:**
```python
seen_vins = set()
for car in cars:
    if car["vin"] in seen_vins:      # O(1) average membership check
        raise ValueError("duplicate VIN")
    seen_vins.add(car["vin"])
```
Interview parallel: LeetCode's "Contains Duplicate" — a hash set turns an O(n²) nested-loop
comparison (or an O(n log n) sort-then-scan) into a single O(n) pass.

### Tuples as composite keys
- `service_part`'s composite primary key `(part_id, service_id)` mirrors a very common Python
  pattern: using a **tuple** as a dict/set key when uniqueness depends on more than one value.
  Tuples work as keys because they're immutable (hashable); lists don't, because they're mutable.

**Example:**
```python
seen_pairs = set()
for row in service_part_rows:
    key = (row["service_id"], row["part_id"])
    if key in seen_pairs:
        raise ValueError("duplicate service_part")
    seen_pairs.add(key)
```

<details><summary>Check yourself</summary>

Why can a tuple be used as a dict key or set element in Python, but a list cannot?

**Answer:** Dict keys and set elements must be hashable, and hashability requires immutability —
the hash value has to stay constant for as long as the object lives inside the hash table. A list
can be mutated after insertion (`my_list.append(...)`), which would silently change its hash and
break the hash table's internal bucketing. A tuple can't be mutated, so its hash is stable forever,
making it safe to use as a key.
</details>

### Stacks (LIFO) — nested transactions/savepoints
- The savepoint mechanism the test suite relies on (see "Savepoints" above) behaves exactly like a
  stack: opening a nested transaction pushes a new frame, and committing/rolling back pops it.
  Rolling back the outermost frame unwinds everything pushed on top of it.

**Example:**
```python
# a stack modeling the SAVEPOINT nesting: push on BEGIN, pop on COMMIT/ROLLBACK
savepoint_stack = []
savepoint_stack.append("outer_test_transaction")
savepoint_stack.append("endpoint_internal_commit")   # push: nested transaction
savepoint_stack.pop()                                 # pop: endpoint's "commit" resolves
# rolling back the outer transaction discards everything, even already-popped frames,
# because nothing was EVER truly persisted until the outermost frame commits
```
Interview parallel: "Valid Parentheses," undo/redo history, and the call stack itself during
recursion/backtracking all use the identical push/pop discipline.

### Trees & binary search — why indexes make lookups fast
- Every `PRIMARY KEY`/`UNIQUE` constraint in Postgres automatically creates a **B-tree index** — a
  balanced tree structure that turns "does this value already exist?" from an O(n) full-table scan
  into an O(log n) lookup. This is why `ON CONFLICT DO NOTHING` stays fast even as `car_config` or
  `part` grow to millions of rows.

**Example:**
```python
# the coding-interview version of the same O(log n) idea: binary search on sorted data
def binary_search(sorted_list, target):
    lo, hi = 0, len(sorted_list) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

<details><summary>Check yourself</summary>

Why does a `UNIQUE` constraint make `ON CONFLICT DO NOTHING` fast even on a huge table?

**Answer:** Postgres doesn't check for a conflict by scanning every existing row — it uses the
B-tree index that's automatically created for the `UNIQUE` column(s) to look up the value in
O(log n) time, the same way binary search narrows down a sorted array by repeatedly halving the
search space instead of checking every element.
</details>

### Graphs — foreign keys as a dependency graph, and topological sort
- Servicd's 8 tables and their foreign keys form a **directed graph**: each table is a node, each
  FK is an edge pointing from the referencing table to the table it depends on (`car → users`,
  `car → car_config`, `service → car`, `service → maintenance_type`, etc.). Two real consequences
  of that:
  1. Cascading deletes are a graph traversal — deleting a `user` follows the `car.user_id` edge to
     find dependents, then follows *their* dependents' edges (`service.car_id`), and so on.
  2. `servicdDB.sql` had to `CREATE TABLE` statements in an order where every table's dependencies
     already exist — that's a **topological sort** of the dependency graph, done by hand.

**Example:**
```python
# topological sort via DFS — the general algorithm for "what order do I create/build these in?"
def topological_sort(graph):  # graph: {table: [tables it depends on]}
    visited, order = set(), []
    def visit(node):
        if node in visited:
            return
        visited.add(node)
        for dep in graph[node]:
            visit(dep)
        order.append(node)  # a node is only appended after all its dependencies are
    for node in graph:
        visit(node)
    return order

schema_deps = {
    "users": [], "car_config": [],
    "car": ["users", "car_config"],
    "maintenance_type": [],
    "service": ["car", "maintenance_type"],
}
print(topological_sort(schema_deps))
# ['users', 'car_config', 'car', 'maintenance_type', 'service'] — a valid CREATE TABLE order
```
Interview parallel: this exact algorithm solves "Course Schedule" (can you finish all courses
given prerequisites?) and "Build Order" — both are topological sort on a dependency DAG.

<details><summary>Check yourself</summary>

Is the FK dependency graph among Servicd's 8 tables a DAG (directed, **acyclic** graph)? Why does
that property matter here?

**Answer:** Yes — `car` depends on `users`/`car_config`, `service` depends on `car`/
`maintenance_type`, and so on, with nothing depending back on something that (directly or
indirectly) depends on it. It has to be acyclic: a cycle (e.g. table A requires table B to exist
first, but B also requires A) would make it *impossible* to pick a valid creation order at all —
topological sort is only defined for DAGs, and a cycle means there's genuinely no correct answer.
</details>

---

## How we'll use this file
- New concepts get added here as they come up, in the same What/Why + Example + Check-yourself
  format.
- Periodically (or whenever asked), we'll do a live quiz pass using the questions in this file —
  I'll ask them out loud in conversation rather than just leaving them for silent self-review.
