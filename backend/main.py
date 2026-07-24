from fastapi import FastAPI
from pydantic import BaseModel
import bcrypt
from db import get_connection


class UserCreate(BaseModel):
    username: str
    password: str
    name: str | None = None


app = FastAPI()

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