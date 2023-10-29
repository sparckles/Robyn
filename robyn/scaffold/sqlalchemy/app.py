from robyn import Robyn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = Robyn(__file__)


@app.get("/")
def index():
    return "Hello World!"


if __name__ == "__main__":
    # create a configured "Session" class
    app.start(host="0.0.0.0", port=8080)
