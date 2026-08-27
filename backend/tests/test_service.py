

def test_create_service(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 2000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)

    assert response.status_code == 200
    assert response.json()["car_id"] == car_id

def test_create_service_bad_car_id(client, auth_headers):
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    response = client.post("/service", json={"car_id": 99999, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers)
    assert response.status_code == 404


def test_create_service_wrong_owner(client, make_auth_headers):
    owner_headers = make_auth_headers()
    intruder_headers = make_auth_headers()

    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=owner_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 2000}, headers=owner_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=intruder_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]

    response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=intruder_headers)
    assert response.status_code == 403


def test_create_service_bad_maintenance_type_id(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 2000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]

    response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": 1234, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers)
    assert response.status_code == 404


def test_create_service_part(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 2000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=auth_headers,)
    part_id = part_response.json()["part_id"]

    response = client.post("/service_part", json={"service_id": service_id, "part_id": part_id, "price_at_service_cents": 1299}, headers=auth_headers,)

    assert response.status_code == 200
    assert response.json()["service_id"] == service_id
    assert response.json()["part_id"] == part_id


def test_create_service_part_bad_service_id(client, auth_headers):
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=auth_headers,)
    part_id = part_response.json()["part_id"]

    response = client.post("/service_part", json={"service_id": 99999, "part_id": part_id}, headers=auth_headers,)
    assert response.status_code == 404


def test_create_service_part_bad_part_id(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 2000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]

    response = client.post("/service_part", json={"service_id": service_id, "part_id": 99999}, headers=auth_headers,)
    assert response.status_code == 404


def test_create_service_part_duplicate(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 2000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=auth_headers)
    part_id = part_response.json()["part_id"]

    first_resp = client.post("/service_part", json={"service_id": service_id, "part_id": part_id}, headers=auth_headers)
    second_resp = client.post("/service_part", json={"service_id": service_id, "part_id": part_id}, headers=auth_headers)

    assert second_resp.status_code == 400


def test_create_service_part_wrong_owner(client, make_auth_headers):
    owner_headers = make_auth_headers()
    intruder_headers = make_auth_headers()

    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=owner_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 2000}, headers=owner_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=owner_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=owner_headers,)
    service_id = service_response.json()["service_id"]
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=intruder_headers,)
    part_id = part_response.json()["part_id"]

    response = client.post("/service_part", json={"service_id": service_id, "part_id": part_id}, headers=intruder_headers,)
    assert response.status_code == 403
