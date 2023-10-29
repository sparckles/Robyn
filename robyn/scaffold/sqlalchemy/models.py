from sqlalchemy.orm import declarative_base
from sqlalchem.orm import Column, Integer, String, Boolean

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
