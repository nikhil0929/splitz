from typing import List, TYPE_CHECKING, Optional
# from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Table, ForeignKey, UUID, Column, Float
from sqlalchemy.orm import Mapped, relationship, mapped_column
from ..base_model import Base

# Association table for many-to-many relationship between User and Room
user_room_association = Table(
    "user_room",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("room_id", Integer, ForeignKey("rooms.id"), primary_key=True),
    Column("user_room_price", Float, default=0.0)
)


class Room(Base):
    __tablename__ = "rooms"

    id = mapped_column(Integer, primary_key=True)  # Auto-incrementing primary key
    room_code = mapped_column(String(6), unique=True)
    room_name = mapped_column(String(50))
    room_password = mapped_column(String(100))
    room_owner_id = mapped_column(Integer, ForeignKey("users.id"))
    num_members = mapped_column(Integer, default=1)

    # Establish a one to many relationship with receipts. This room can have many receipts
    receipts = relationship(List["Receipt"], back_populates="room")

    # Establish the many-to-many relationship with User
    users = relationship(
        List["User"],
        secondary=user_room_association,
        back_populates="rooms"
    )

    def __repr__(self) -> str:
        return f"Room(id={self.id!r}, name={self.room_name!r}, code={self.room_code!r} )"