import os
from dotenv import load_dotenv

# Load test-specific settings (servicd_test) BEFORE db.py's own load_dotenv() runs,
# since load_dotenv() never overrides values that are already set.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.test"), override=True)

import pytest
from fastapi.testclient import TestClient

from db import pool, get_db
from main import app


class Rollback(Exception):
    pass


@pytest.fixture
def db_conn():
    with pool.connection() as conn:
        try:
            with conn.transaction():
                yield conn
                raise Rollback()
        except Rollback:
            pass


@pytest.fixture
def client(db_conn):
    def override_get_db():
        yield db_conn

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/users", json={"username": "auth_fixture_user", "password": "correct_password"})
    response = client.post("/login", json={"username": "auth_fixture_user", "password": "correct_password"})
    tokenBearer = response.json()["token"]
    return {"Authorization": f"Bearer {tokenBearer}"}


@pytest.fixture
def make_auth_headers(client):
    counter = 0
    def create_headers():
        nonlocal counter
        counter+=1
        client.post("/users", json={"username": f"create_header_user {counter}", "password": "correct_pass"})
        response = client.post("/login", json={"username": f"create_header_user {counter}", "password": "correct_pass"})
        auth_token = response.json()["token"]
        return {"Authorization": f"Bearer {auth_token}"}

    return create_headers