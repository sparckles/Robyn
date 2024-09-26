from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)


class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool
    is_superuser: bool

    class Config:
        orm_mode = True


# Pydantic model for creating/updating a user
class UserCreate(BaseModel):
    username: str
    password: str

    class Config:
        orm_mode = True
