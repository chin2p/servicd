from fastapi import Depends, FastAPI
import psycopg
from pydantic import BaseModel
import bcrypt
from db import pool, secret_key
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer
import jwt
from datetime import datetime, timedelta, timezone
from psycopg import errors





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