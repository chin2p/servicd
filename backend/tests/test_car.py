
def test_create_car_config(client, auth_headers):
    response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    data = response.json()
    assert response.status_code == 200
    assert "config_id" in data


def test_car_config_is_idempotent(client, auth_headers):
    response_one = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    response_two = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)

    assert response_one.json()["config_id"] == response_two.json()["config_id"]

def test_create_car(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    car_response = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)

    assert car_response.status_code == 200
    assert car_response.json()["config_id"] == config_id

def test_create_car_bad_config_id(client, auth_headers):
    response = client.post("/car", json={"config_id": 999999}, headers=auth_headers,)

    assert response.status_code == 404


def test_create_car_dup_vin(client, auth_headers):
    config_response = client.post("/car_config", json={"year": 2022, "make": "Toyota", "model": "Corolla"}, headers=auth_headers,)
    config_id = config_response.json()["config_id"]
    response_one = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)
    response_two = client.post("/car", json={"config_id": config_id, "vin": "5FNRL38409B123456", "total_miles": 20000}, headers=auth_headers,)

    assert response_two.status_code == 400