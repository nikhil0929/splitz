from pydantic import BaseModel
from typing import Optional




# Base model inherent in all classes
class UserBase(BaseModel):
    name: Optional[str] = None
    phone_number: str
    email: Optional[str] = None
    # approved: bool = False


# For 'creating' (POST) a user
class UserCreate(UserBase):
    pass


class UserLogin(UserBase):
    otp: str


# For 'updating' (PUT) a user
class UserUpdate(UserBase):
    pass


# For 'reading' (GET) a user
class User(UserBase):
    id: int

    class Config:
        from_attributes = True