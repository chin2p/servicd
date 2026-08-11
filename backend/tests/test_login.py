def test_login_success(client):
    client.post("/users", json={"username": "login_success_user", "password": "correct_password"})

    response = client.post(
        "/login",
        json={"username": "login_success_user", "password": "correct_password"},
    )

    assert response.status_code == 200
    assert "token" in response.json()


def test_login_wrong_password(client):
    client.post("/users", json={"username": "login_wrong_pw_user", "password": "correct_password"})

    response = client.post(
        "/login",
        json={"username": "login_wrong_pw_user", "password": "wrong_password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_nonexistent_username(client):
    response = client.post(
        "/login",
        json={"username": "definitely_not_a_real_user", "password": "whatever"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
