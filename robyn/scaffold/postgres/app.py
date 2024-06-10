import psycopg2
from robyn import Robyn

DB_NAME = "postgresDB"
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "password"
DB_PORT = "5455"

conn = psycopg2.connect(database=DB_NAME, host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT)

app = Robyn(__file__)


# create a route to fetch all users
@app.get("/users")
def get_users():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()
    return {"users": all_users}


@app.get("/")
def index():
    return "Hello World!"


if __name__ == "__main__":
    app.start(url="0.0.0.0", port=8080)
