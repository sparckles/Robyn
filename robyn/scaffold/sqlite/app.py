from robyn import Robyn
import sqlite3

app = Robyn(__file__)


@app.get("/")
def index():
    # your db name
    conn = sqlite3.connect("example.db")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS test")
    cur.execute("CREATE TABLE test(column_1, column_2)")
    res = cur.execute("SELECT name FROM sqlite_master")
    th = res.fetchone()
    print(th)
    return "Hello World!"


if __name__ == "__main__":
    app.start()
