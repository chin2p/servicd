def test_create_maintenance_type(client, auth_headers):
    response = client.post("/maintenance_type", json={"name": "Brake Pad Replacement"}, headers=auth_headers,)

    assert response.status_code == 200
    assert "maintenance_type_id" in response.json()


def test_maintenance_type_is_idempotent(client, auth_headers):
    response_one = client.post("/maintenance_type", json={"name": "Brake Pad Replacement"}, headers=auth_headers,)
    response_two = client.post("/maintenance_type", json={"name": "Brake Pad Replacement"}, headers=auth_headers,)

    assert response_one.json()["maintenance_type_id"] == response_two.json()["maintenance_type_id"]


def test_create_part(client, auth_headers):
    response = client.post("/part", json={"name": "Brake Pad", "brand": "Akebono"}, headers=auth_headers,)

    assert response.status_code == 200
    assert "part_id" in response.json()


def test_part_is_idempotent(client, auth_headers):
    response_one = client.post("/part", json={"name": "Brake Pad", "brand": "Akebono"}, headers=auth_headers,)
    response_two = client.post("/part", json={"name": "Brake Pad", "brand": "Akebono"}, headers=auth_headers,)

    assert response_one.json()["part_id"] == response_two.json()["part_id"]


def test_create_service_scheduled(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]

    response = client.post("/service_scheduled", json={"config_id": config_id, "maintenance_type_id": maint_id, "mileage_interval": 5000}, headers=auth_headers,)

    assert response.status_code == 200
    assert "schedule_id" in response.json()


def test_service_scheduled_is_idempotent(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]

    response_one = client.post("/service_scheduled", json={"config_id": config_id, "maintenance_type_id": maint_id, "mileage_interval": 5000}, headers=auth_headers,)
    response_two = client.post("/service_scheduled", json={"config_id": config_id, "maintenance_type_id": maint_id, "mileage_interval": 5000}, headers=auth_headers,)

    assert response_one.json()["schedule_id"] == response_two.json()["schedule_id"]


def test_service_scheduled_missing_intervals(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]

    response = client.post("/service_scheduled", json={"config_id": config_id, "maintenance_type_id": maint_id}, headers=auth_headers,)

    assert response.status_code == 400


def test_service_scheduled_bad_config_id(client, auth_headers):
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]

    response = client.post("/service_scheduled", json={"config_id": 99999, "maintenance_type_id": maint_id, "mileage_interval": 5000}, headers=auth_headers,)

    assert response.status_code == 404
