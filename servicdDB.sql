CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name TEXT,
    username TEXT UNIQUE NOT NULL,
    password_hash VARCHAR(60) NOT NULL,
    salt VARCHAR(60) NOT NULL
);

CREATE TABLE car_config (
    config_id SERIAL PRIMARY KEY,
    year INT NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    engine TEXT
);

CREATE TABLE car (
    car_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE NOT NULL,
    config_id INT REFERENCES car_config(config_id) NOT NULL,
    vin VARCHAR(17) UNIQUE,
    total_miles INT,

    --Checking if vin it's entered its 17 char
    CONSTRAINT valid_vin_format CHECK (
        vin IS NULL OR vin ~ '^[A-HJ-NPR-Z0-9]{17}$'
    )

);

CREATE TABLE maintenance_type(
    maintenance_type_id SERIAL PRIMARY KEY,
    maintenance_name TEXT NOT NULL UNIQUE
);

CREATE TABLE service(
    service_id SERIAL PRIMARY KEY,
    car_id INT REFERENCES car(car_id) ON DELETE CASCADE NOT NULL,
    maintenance_type_id INT REFERENCES maintenance_type(maintenance_type_id) NOT NULL,
    miles_at_service INT NOT NULL,
    date DATE NOT NULL
);

CREATE TABLE part(
    part_id SERIAL PRIMARY KEY,
    part_name TEXT NOT NULL,
    brand TEXT NOT NULL,
    UNIQUE (part_name, brand),
    price_cents INT --part price
);

CREATE TABLE service_part(

    part_id INT REFERENCES part(part_id),
    service_id INT REFERENCES service(service_id) ON DELETE CASCADE,
    price_at_service_cents INT, --price snapshot at the time of service, part price may change overtime
    PRIMARY KEY (part_id, service_id)
);

CREATE TABLE service_scheduled(
    schedule_id SERIAL PRIMARY KEY,
    config_id INT REFERENCES car_config(config_id) NOT NULL,
    maintenance_type_id INT REFERENCES maintenance_type(maintenance_type_id) NOT NULL,
    mileage_interval INT,
    months_interval INT,
    CONSTRAINT valid_miles CHECK (
        mileage_interval IS NOT NULL OR months_interval IS NOT NULL
    )

);
