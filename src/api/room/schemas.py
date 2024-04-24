# room.schemas.py

from pydantic import BaseModel
from typing import List, Optional

class RoomBase(BaseModel):
    room_name: str

class RoomCreate(RoomBase):
    room_password: str

class RoomJoin(BaseModel):
    room_code: str
    room_password: str

class Room(RoomBase):
    id: int
    room_code: str
    room_owner_id: int
    num_members: int
    room_picture_url: Optional[str]

    class Config:
        from_attributes = True

class RoomUser(BaseModel):
    id: int
    phone_number: str
    name: str
    username: str
    profile_picture_url: Optional[str]

    class Config:
        from_attributes = True
