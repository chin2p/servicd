from fastapi import FastAPI
from pydantic import BaseModel
import bcrypt
from db import get_connection, secret_key
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta, timezone


class UserCreate(BaseModel):
    username: str
    password: str
    name: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str



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
    conn_inst = get_connection()
    cur = conn_inst.cursor()
    cur.execute("INSERT INTO users(username, password_hash, name) VALUES (%s, %s, %s) RETURNING user_id", (user.username, database_password, user.name))
    row = cur.fetchone()
    conn_inst.commit()
    cur.close()
    conn_inst.close()
    return {"user_id": row[0], "username": user.username, "name": user.name}


@app.post("/login")
def login(request: LoginRequest):
    conn_inst = get_connection()
    cur = conn_inst.cursor()
    cur.execute("SELECT user_id, password_hash FROM users WHERE username = %s", (request.username,))
    row = cur.fetchone()
    cur.close()
    conn_inst.close()

    if row is None:
        bcrypt.checkpw(request.password.encode('utf-8'), dummy_hash)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    else:
        stored_hash = row[1].encode('utf-8')
        if bcrypt.checkpw(request.password.encode('utf-8'), stored_hash):
            token = jwt.encode({"sub": row[0], "exp": datetime.now(timezone.utc) + timedelta(days=1)}, secret_key, algorithm="HS256")
            return {"token": token}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")

