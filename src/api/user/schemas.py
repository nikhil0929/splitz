from pydantic import BaseModel



# Base model inherent in all classes
class UserBase(BaseModel):
    name: str | None = None
    phone_number: str
    email: str | None = None
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
