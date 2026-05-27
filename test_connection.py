# test_connection.py
from hdbcli import dbapi
from dotenv import load_dotenv
import os

load_dotenv()

conn = dbapi.connect(
    address=os.getenv("HANA_DB_ADDRESS"),
    port=int(os.getenv("HANA_DB_PORT")),
    user=os.getenv("HANA_DB_USER"),
    password=os.getenv("HANA_DB_PASSWORD"),
    encrypt=True
)

cursor = conn.cursor()
cursor.execute("SELECT VERSION FROM SYS.M_DATABASE")
print("Connection successful! HANA Version:", cursor.fetchone()[0])
conn.close()