from pydantic import BaseModel


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
