def test_create_user(client, db_conn):
    response = client.post(
        "/users",
        json={"username": "some_test_username", "password": "some_password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "some_test_username"
    assert "user_id" in data
    assert "password_hash" not in data

    with db_conn.cursor() as cur:
        cur.execute("SELECT username FROM users WHERE username = %s", ("some_test_username",))
        row = cur.fetchone()
        assert row is not None
        