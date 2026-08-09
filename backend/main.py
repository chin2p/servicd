from fastapi import Depends, FastAPI
import psycopg
from pydantic import BaseModel
import bcrypt
from db import pool, secret_key
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
import jwt
from datetime import datetime, date, timedelta, timezone
import requests




class UserCreate(BaseModel):
    username: str
    password: str
    name: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str

class CarConfigCreate(BaseModel):
    year: int
    make: str
    model: str
    engine: str | None = None  # Optional field for engine

class CarCreate(BaseModel):
    config_id: int
    vin: str | None = None  # Optional field for VIN
    total_miles: int | None = None  # Optional field for total miles

class MaintenanceTypeCreate(BaseModel):
    name: str

class PartCreate(BaseModel):
    name: str
    brand: str | None = None
    price_cents: int | None = None  # Optional field for price in cents

class ServiceCreate(BaseModel):
    car_id: int
    maintenance_type_id: int
    miles_at_service: int
    date: date

class ServicePartCreate(BaseModel):
    service_id: int
    part_id: int
    price_at_service_cents: int | None = None  # Optional field for price at service in cents


class ServiceScheduledCreate(BaseModel):
    config_id: int
    maintenance_type_id: int
    mileage_interval: int | None = None  # Optional field for mileage interval
    months_interval: int | None = None  # Optional field for months interval




security = HTTPBearer()

def get_current_user(credentials = Security(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dummy_hash = bcrypt.hashpw(b"dummy_password", bcrypt.gensalt())



@app.post("/users")
def create_user(user: UserCreate):


    password_bytes = user.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # store in database as string
    database_password = hashed_bytes.decode('utf-8')
    #if checking a login, encode user input password, encode database_password
    #then use bcrypt.checkpw(login_inp, database_password) return True or False
    
    
    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute("INSERT INTO users(username, password_hash, name) VALUES (%s, %s, %s) RETURNING user_id", (user.username, database_password, user.name))
            row = cur.fetchone()
            conn.commit()
            
    return {"user_id": row[0], "username": user.username, "name": user.name}


@app.post("/login")
def login(request: LoginRequest):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, password_hash FROM users WHERE username = %s", (request.username,))
            row = cur.fetchone()

    if row is None:
        bcrypt.checkpw(request.password.encode('utf-8'), dummy_hash)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    else:
        stored_hash = row[1].encode('utf-8')
        if bcrypt.checkpw(request.password.encode('utf-8'), stored_hash):
            token = jwt.encode({"sub": str(row[0]), "exp": datetime.now(timezone.utc) + timedelta(days=1)}, secret_key, algorithm="HS256")
            return {"token": token}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")



@app.post("/car_config")
def create_car_config(car_config: CarConfigCreate, user_id: int = Depends(get_current_user)):
    if car_config.engine:
        engine_value = car_config.engine
    else:
        engine_value = "Unknown"  # Default value if engine is not provided

    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute("INSERT INTO car_config(year, make, model, engine) VALUES (%s, %s, %s, %s) ON CONFLICT (year, make, model, engine) DO NOTHING RETURNING config_id", (car_config.year, car_config.make, car_config.model, engine_value))
            row = cur.fetchone()
            if row is not None:
                config_id = row[0]
            else:
                # If the row is None, it means the entry already exists, so we need to fetch the existing config_id
                cur.execute("SELECT config_id FROM car_config WHERE year = %s AND make = %s AND model = %s AND engine = %s", (car_config.year, car_config.make, car_config.model, engine_value))
                existing_row = cur.fetchone()
                if existing_row is not None:
                    config_id = existing_row[0]
                else:
                    raise HTTPException(status_code=500, detail="Failed to retrieve or create car configuration")
            conn.commit()

    
    return {"config_id": config_id, "year": car_config.year, "make": car_config.make, "model": car_config.model, "engine": engine_value}


@app.post("/car")
def create_car(car: CarCreate, user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO car(user_id, config_id, vin, total_miles) VALUES (%s, %s, %s, %s) RETURNING car_id", (user_id, car.config_id, car.vin, car.total_miles))
                row = cur.fetchone()
                conn.commit()
            except psycopg.errors.ForeignKeyViolation:
                raise HTTPException(status_code=404, detail="Invalid config_id: No such car configuration exists")
            except psycopg.errors.UniqueViolation:
                raise HTTPException(status_code=400, detail="Duplicate entry: A car with this VIN already exists")
        
    
    return {"car_id": row[0], "config_id": car.config_id, "vin": car.vin, "total_miles": car.total_miles}


@app.post("/maintenance_type")
def create_maintenance_type(maintenance_type: MaintenanceTypeCreate, user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
    
            cur.execute("INSERT INTO maintenance_type(maintenance_name) VALUES (%s) ON CONFLICT (maintenance_name) DO NOTHING RETURNING maintenance_type_id", (maintenance_type.name,))
            row = cur.fetchone()
            if row is not None:
                maintenance_type_id = row[0]
            else:
                # If the row is None, it means the entry already exists, so we need to fetch the existing maintenance_type_id
                cur.execute("SELECT maintenance_type_id FROM maintenance_type WHERE maintenance_name = %s", (maintenance_type.name,))
                existing_row = cur.fetchone()
                if existing_row is not None:
                    maintenance_type_id = existing_row[0]
                else:
                    raise HTTPException(status_code=500, detail="Failed to retrieve or create maintenance type")

            conn.commit()


    return {"maintenance_type_id": maintenance_type_id, "name": maintenance_type.name}


@app.post("/part")
def create_part(part: PartCreate, user_id: int = Depends(get_current_user)):

    if part.brand is None:
        part.brand = "Unknown"  # Default value if brand is not provided



    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO part(part_name, brand, price_cents) VALUES (%s, %s, %s) ON CONFLICT (part_name, brand) DO NOTHING RETURNING part_id", (part.name, part.brand, part.price_cents))
            row = cur.fetchone()
            if row is not None:
                part_id = row[0]
            else:
                # If the row is None, it means the entry already exists, so we need to fetch the existing part_id
                cur.execute("SELECT part_id FROM part WHERE part_name = %s AND brand = %s", (part.name, part.brand))
                existing_row = cur.fetchone()
                if existing_row is not None:
                    part_id = existing_row[0]
                else:
                    raise HTTPException(status_code=500, detail="Failed to retrieve or create part")
            conn.commit()

    return {"part_id": part_id, "name": part.name, "brand": part.brand, "price_cents": part.price_cents}


@app.post("/service")
def create_service(service: ServiceCreate, user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT user_id FROM car WHERE car_id = %s", (service.car_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Invalid car_id: No such car exists")
            elif row[0] != user_id:
                raise HTTPException(status_code=403, detail="Forbidden: You do not own this car")

            try:
                cur.execute("INSERT INTO service(car_id, maintenance_type_id, miles_at_service, date) VALUES (%s, %s, %s, %s) RETURNING service_id", (service.car_id, service.maintenance_type_id, service.miles_at_service, service.date))
                row = cur.fetchone()
                conn.commit()
            except psycopg.errors.ForeignKeyViolation:
                raise HTTPException(status_code=404, detail="Invalid maintenance_type_id: No such maintenance type exists")

    return {"service_id": row[0], "car_id": service.car_id, "maintenance_type_id": service.maintenance_type_id, "miles_at_service": service.miles_at_service, "date": service.date}



@app.post("/service_part")
def create_service_part(service_part: ServicePartCreate, user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:

            # Check if the service exists and belongs to the user
            cur.execute("SELECT car.user_id FROM service JOIN car ON service.car_id = car.car_id WHERE service.service_id = %s", (service_part.service_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Invalid service_id: No such service exists")
            if row[0] != user_id:
                raise HTTPException(status_code=403, detail="Forbidden: You do not own this service")
            
            
            try:
                cur.execute("INSERT INTO service_part(service_id, part_id, price_at_service_cents) VALUES (%s, %s, %s)", (service_part.service_id, service_part.part_id, service_part.price_at_service_cents))
                
                conn.commit()
            except psycopg.errors.ForeignKeyViolation:
                raise HTTPException(status_code=404, detail="Invalid part_id: No such part exists")
            except psycopg.errors.UniqueViolation:
                raise HTTPException(status_code=400, detail="Duplicate entry: This part is already associated with the service")

    return {"service_id": service_part.service_id, "part_id": service_part.part_id, "price_at_service_cents": service_part.price_at_service_cents}


@app.post("/service_scheduled")
def create_service_scheduled(service_scheduled: ServiceScheduledCreate, user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:

            try:
                cur.execute("INSERT INTO service_scheduled(config_id, maintenance_type_id, mileage_interval, months_interval) VALUES (%s, %s, %s, %s) ON CONFLICT (config_id, maintenance_type_id) DO NOTHING RETURNING schedule_id", (service_scheduled.config_id, service_scheduled.maintenance_type_id, service_scheduled.mileage_interval, service_scheduled.months_interval))
                row = cur.fetchone()
                if row is not None:
                    schedule_id = row[0]
                else:
                    # If the row is None, it means the entry already exists, so we need to fetch the existing schedule_id
                    cur.execute("SELECT schedule_id FROM service_scheduled WHERE config_id = %s AND maintenance_type_id = %s", (service_scheduled.config_id, service_scheduled.maintenance_type_id))
                    existing_row = cur.fetchone()
                    if existing_row is not None:
                        schedule_id = existing_row[0]
                    else:
                        raise HTTPException(status_code=500, detail="Failed to retrieve or create scheduled service")
                conn.commit()

            except psycopg.errors.CheckViolation:
                raise HTTPException(status_code=400, detail="At least one of mileage_interval or months_interval must be provided")
            except psycopg.errors.ForeignKeyViolation:
                raise HTTPException(status_code=404, detail="Invalid config_id or maintenance_type_id: No such car configuration or maintenance type exists")


    return {"schedule_id": schedule_id, "config_id": service_scheduled.config_id, "maintenance_type_id": service_scheduled.maintenance_type_id, "mileage_interval": service_scheduled.mileage_interval, "months_interval": service_scheduled.months_interval}



#Get end points
@app.get("/cars")
def get_cars(user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT car.car_id, car.vin, car.total_miles, car_config.year, car_config.make, car_config.model, car_config.engine FROM car JOIN car_config ON car.config_id = car_config.config_id WHERE car.user_id = %s", (user_id,))
            rows = cur.fetchall()
        cars = []
        for row in rows:
            cars.append({
                "car_id": row[0],
                "vin": row[1],
                "total_miles": row[2],
                "year": row[3],
                "make": row[4],
                "model": row[5],
                "engine": row[6]
            })

    return {"cars": cars}


@app.get("/cars/{car_id}")
def get_car(car_id: int, user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT car.car_id, car.user_id, car.vin, car.total_miles, car_config.year, car_config.make, car_config.model, car_config.engine FROM car JOIN car_config ON car.config_id = car_config.config_id WHERE car.car_id = %s", (car_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Car not found")
            if row[1] != user_id:
                raise HTTPException(status_code=403, detail="Forbidden: You do not own this car")

    return {
        "car_id": row[0],
        "vin": row[2],
        "total_miles": row[3],
        "year": row[4],
        "make": row[5],
        "model": row[6],
        "engine": row[7]
    }

@app.get("/cars/{car_id}/services")
def get_car_services(car_id: int, user_id: int = Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Check if the car exists and belongs to the user
            cur.execute("SELECT user_id FROM car WHERE car_id = %s", (car_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Invalid car_id: No such car exists")
            if row[0] != user_id:
                raise HTTPException(status_code=403, detail="Forbidden: You do not own this car")

            # Fetch services for the car
            cur.execute("""SELECT service.service_id, service.maintenance_type_id, maintenance_type.maintenance_name,
                                service.miles_at_service, service.date,
                                part.part_id, part.part_name, part.brand, service_part.price_at_service_cents
                            FROM service
                            JOIN maintenance_type ON service.maintenance_type_id = maintenance_type.maintenance_type_id
                            LEFT JOIN service_part ON service.service_id = service_part.service_id
                            LEFT JOIN part ON service_part.part_id = part.part_id
                            WHERE service.car_id = %s
                        """, (car_id,))
            rows = cur.fetchall()

            services_by_id = {}
            for row in rows:
                (service_id, maintenance_type_id, maintenance_name, miles_at_service, date, part_id, part_name, brand, price_at_service_cents) = row
                if service_id not in services_by_id:
                    services_by_id[service_id] = {
                        "service_id": service_id,
                        "maintenance_type_id": maintenance_type_id,
                        "maintenance_name": maintenance_name,
                        "miles_at_service": miles_at_service,
                        "date": date,
                        "parts": []
                    }
                if part_id:
                    services_by_id[service_id]["parts"].append({
                        "part_id": part_id,
                        "name": part_name,
                        "brand": brand,
                        "price_at_service_cents": price_at_service_cents
                    })
    services = list(services_by_id.values())
    return {"services": services}


@app.get("/maintenance_types")
def get_maintenance_types():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT maintenance_type_id, maintenance_name FROM maintenance_type")
            rows = cur.fetchall()
        maintenance_types = []
        for row in rows:
            maintenance_types.append({
                "maintenance_type_id": row[0],
                "name": row[1]
            })

    return {"maintenance_types": maintenance_types}


@app.get("/parts")
def get_parts():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT part_id, part_name, brand, price_cents FROM part")
            rows = cur.fetchall()
        parts = []
        for row in rows:
            parts.append({
                "part_id": row[0],
                "name": row[1],
                "brand": row[2],
                "price_cents": row[3]
            })

    return {"parts": parts}



@app.get("/vin/{vin}/decode")

def vin_decode(vin: str, user_id = Depends(get_current_user)):
    try:
        response = requests.get(
            f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json",
            timeout=5
        )
        response.raise_for_status()
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Unable to reach VIN decoding service")

    data = response.json()
    result = data["Results"][0]
    if result["Make"] == "" and result["Model"] == "":
        raise HTTPException(status_code=404, detail="VIN not recognized")

    return {
        "year": result["ModelYear"],
        "make": result["Make"],
        "model": result["Model"],
        "engine": f"{result["DisplacementL"][0:3]}L {result["EngineCylinders"]} Cyl {result["EngineModel"]}"
    }