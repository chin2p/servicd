from dotenv import load_dotenv
import os
import psycopg
from psycopg_pool import ConnectionPool

load_dotenv()

db_name = os.getenv("DB_NAME")
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_port = os.getenv("DB_PORT")
secret_key = os.getenv("SECRET_KEY")

pool = ConnectionPool(conninfo=f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}")






