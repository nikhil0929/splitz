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

if TYPE_CHECKING:
    from .user import User  # Import Room only for type checking
    from .receipt import Receipt

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)  # Auto-incrementing primary key
    room_code: Mapped[str] = mapped_column(String(6), unique=True)
    room_name: Mapped[str] = mapped_column(String(50))
    room_password: Mapped[str] = mapped_column(String(100))
    room_owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # Establish a one to many relationship with receipts. This room can have many receipts
    receipts: Mapped[List["Receipt"]] = relationship("Receipt", back_populates="room")

    # Establish the many-to-many relationship with User
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_room_association,
        back_populates="rooms"
    )

    def __repr__(self) -> str:
        return f"Room(id={self.id!r}, name={self.room_name!r}, code={self.room_code!r} )"