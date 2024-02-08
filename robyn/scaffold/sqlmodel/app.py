from robyn import Robyn

from sqlmodel import SQLModel, Session, create_engine, select
from models import Hero


app = Robyn(__file__)

engine = create_engine("sqlite:///database.db", echo=True)


@app.get("/")
def index():
    return "Hello World"


@app.get("/create")
def create():
    SQLModel.metadata.create_all(bind=engine)
    return "created tables"


@app.get("/insert")
def insert():
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
    hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)

    with Session(engine) as session:
        session.add(hero_1)
        session.add(hero_2)
        session.add(hero_3)
        session.commit()
        return "inserted"


@app.get("/select")
def get_data():
    with Session(engine) as session:
        statement = select(Hero).where(Hero.name == "Spider-Boy")
        hero = session.exec(statement).first()
        return hero


if __name__ == "__main__":
    # create a configured "Session" class
    app.start(host="0.0.0.0", port=8080)
