def test_get_cars(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    response = client.get("/cars", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["cars"][0]["car_id"] == car_response.json()["car_id"]


def test_get_cars_scoped_to_owner(client, make_auth_headers):
    user_one = make_auth_headers()
    user_two = make_auth_headers()

    one_config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=user_one,)
    one_config_id = one_config_response.json()["config_id"]
    one_car_response = client.post("/car", json={"config_id": one_config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=user_one,)

    two_config_response = client.post("/car_config", json={"year": 2020, "make": "Toyota", "model": "Camry"}, headers=user_two,)
    two_config_id = two_config_response.json()["config_id"]
    two_car_resp = client.post("/car", json={"config_id": two_config_id}, headers=user_two,)

    two_car_id = two_car_resp.json()["car_id"]
    response = client.get("/cars", headers=user_one)

    assert not any(car["car_id"] == two_car_id for car in response.json()["cars"])


def test_get_car(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]

    response = client.get(f"/cars/{car_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["car_id"] == car_id


def test_get_car_not_found(client, auth_headers):
    response = client.get("/cars/99999", headers=auth_headers)

    assert response.status_code == 404


def test_get_car_wrong_owner(client, make_auth_headers):
    owner_headers = make_auth_headers()
    intruder_headers = make_auth_headers()

    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=owner_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=owner_headers,)
    car_id = car_response.json()["car_id"]

    response = client.get(f"/cars/{car_id}", headers=intruder_headers)

    assert response.status_code == 403


def test_get_car_service_with_parts(client, auth_headers):
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

    service_with_part_response = client.post("/service_part", json={"service_id": service_id, "part_id": part_id, "price_at_service_cents": 1299}, headers=auth_headers,)

    response = client.get(f"/cars/{car_id}/services", headers=auth_headers)

    services = response.json()["services"]
    #exactly one service
    assert len(services) == 1

    #exactly one entry in parts list
    assert len(services[0]["parts"]) == 1
    #part id matches or not
    assert services[0]["parts"][0]["part_id"] == part_id

def test_get_car_services_no_parts(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    car_id = car_response.json()["car_id"]
    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]
    service_response = client.post("/service", json={"car_id": car_id, "maintenance_type_id": maint_id, "miles_at_service": 2500, "date": "2026-01-15"}, headers=auth_headers,)
    service_id = service_response.json()["service_id"]

    response = client.get(f"/cars/{car_id}/services", headers=auth_headers)
    
    services = response.json()["services"]

    assert len(services) == 1

    assert len(services[0]["parts"]) == 0

def test_get_maintenance_types_public(client, auth_headers):

    maint_response = client.post("/maintenance_type", json={"name": "Oil Change"}, headers=auth_headers,)
    maint_id = maint_response.json()["maintenance_type_id"]

    response = client.get("/maintenance_types")
    assert response.status_code == 200
    assert any(ids["maintenance_type_id"] == maint_id for ids in response.json()["maintenance_types"])


def test_get_parts_public(client, auth_headers):
    part_response = client.post("/part", json={"name": "Oil Filter", "brand": "ToyotaOEM"}, headers=auth_headers,)
    part_id = part_response.json()["part_id"]

    response = client.get("/parts")
    assert response.status_code == 200

    assert any(ids["part_id"] == part_id for ids in response.json()["parts"])