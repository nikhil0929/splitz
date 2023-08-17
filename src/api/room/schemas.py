# room.schemas.py

from pydantic import BaseModel
from typing import List, Optional

class RoomBase(BaseModel):
    room_name: str

class RoomCreate(RoomBase):
    room_password: str

class Room(RoomBase):
    room_code: str
    room_owner_id: int

    class Config:
        from_attributes = True

class RoomUser(BaseModel):
    id: int
    phone_number: str

    class Config:
        from_attributes = True

class ReceiptUpload(BaseModel):
    room_code: str
    receipt_img_url: str

