from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# SQLAlchemy Base class for declarative mapping
class Base(DeclarativeBase):
    pass

# SQLAlchemy 2.0 model definition
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
