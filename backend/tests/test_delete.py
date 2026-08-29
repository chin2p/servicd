def test_delete_service_part_not_attached(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=auth_headers,)
    part_id = part_response.json()["part_id"]

    response = client.delete(f"/service_part/{service_id}/{part_id}", headers=auth_headers)

    assert response.status_code == 404


def test_delete_service_part_wrong_owner(client, make_auth_headers):
    owner_headers = make_auth_headers()
    intruder_headers = make_auth_headers()

    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=owner_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=owner_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=owner_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=owner_headers,)
    service_id = service_response.json()["service_id"]
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=owner_headers,)
    part_id = part_response.json()["part_id"]
    client.post("/service_part", json={"service_id": service_id, "part_id": part_id}, headers=owner_headers,)

    response = client.delete(f"/service_part/{service_id}/{part_id}", headers=intruder_headers)

    assert response.status_code == 403


def test_delete_service_part_service_not_found(client, auth_headers):
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=auth_headers,)
    part_id = part_response.json()["part_id"]

    response = client.delete(f"/service_part/99999/{part_id}", headers=auth_headers)

    assert response.status_code == 404


def test_delete_service_not_found(client, auth_headers):
    response = client.delete("/service/99999", headers=auth_headers)

    assert response.status_code == 404


def test_delete_service_wrong_owner(client, make_auth_headers):
    owner_headers = make_auth_headers()
    intruder_headers = make_auth_headers()

    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=owner_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=owner_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=owner_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=owner_headers,)
    service_id = service_response.json()["service_id"]

    response = client.delete(f"/service/{service_id}", headers=intruder_headers)

    assert response.status_code == 403


def test_delete_car_not_found(client, auth_headers):
    response = client.delete("/car/99999", headers=auth_headers)

    assert response.status_code == 404


def test_delete_car_wrong_owner(client, make_auth_headers):
    owner_headers = make_auth_headers()
    intruder_headers = make_auth_headers()

    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=owner_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=owner_headers,)
    car_id = car_response.json()["car_id"]

    response = client.delete(f"/car/{car_id}", headers=intruder_headers)

    assert response.status_code == 403


def test_delete_service_part(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=auth_headers,)
    part_id = part_response.json()["part_id"]
    attached_response = client.post("/service_part", json={"service_id": service_id, "part_id": part_id}, headers=auth_headers)

    del_part_response = client.delete(f"/service_part/{service_id}/{part_id}", headers=auth_headers)
    del_again_response = client.delete(f"/service_part/{service_id}/{part_id}", headers=auth_headers)
    assert del_part_response.status_code == 200
    assert del_again_response.status_code == 404


def test_delete_service(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]

    # TODO: delete the service, then confirm (via GET /cars/{car_id}/services) that it no longer appears

    delete_service_response = client.delete(f"/service/{service_id}", headers=auth_headers)
    assert delete_service_response.status_code == 200
    get_service_response = client.get(f"/cars/{car_id}/services", headers=auth_headers)
    assert not any(ids["service_id"] == service_id for ids in get_service_response.json()["services"])


def test_delete_car(client, auth_headers, db_conn):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]

    # TODO: delete the car, then confirm (via GET /cars/{car_id}) that it's gone —
    # and think about whether that alone proves the CASCADE actually removed the service too,
    # or whether you'd want a db_conn check on the service row to really prove it
    del_car_response = client.delete(f"/car/{car_id}", headers=auth_headers)
    assert del_car_response.status_code == 200

    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM service WHERE service_id = %s", (service_id,))
        row = cur.fetchone()
        assert row is None



def test_delete_account(client, auth_headers, db_conn):
    # auth_headers already created "auth_fixture_user" via POST /users + POST /login internally —
    # no extra setup needed here.
    # TODO: call DELETE /users/me, then use db_conn to confirm no row in `users` has
    # username = "auth_fixture_user" anymore
    response = client.delete("/users/me", headers=auth_headers)
    assert response.status_code == 200
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE username = %s", ("auth_fixture_user",))
        row = cur.fetchone()
        assert row is None
