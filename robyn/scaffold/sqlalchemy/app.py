from robyn import Robyn
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./example.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = Robyn(__file__)


@app.get("/")
def index():
    return "Hello World!"


if __name__ == "__main__":
    # create a configured "Session" class
    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, index=True)
        username = Column(String, unique=True, index=True)
        hashed_password = Column(String)
        is_active = Column(Boolean, default=True)
        is_superuser = Column(Boolean, default=False)

    Base.metadata.create_all(bind=engine)

    app.start(url="0.0.0.0", port=8080)
