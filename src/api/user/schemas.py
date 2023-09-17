from pydantic import BaseModel
from typing import Optional




# Base model inherent in all classes
class UserBase(BaseModel):
    phone_number: str
    # approved: bool = False


# For 'creating' (POST) a user
class UserCreate(UserBase):
    pass

class UserLogin(UserBase):
    otp: str


# For 'updating' (PUT) a user
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


# For 'reading' (GET) a user
class User(UserBase):
    id: int

    name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True

class MiniUser(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str