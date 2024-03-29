from typing import Optional, List, TYPE_CHECKING
# from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from ..base_model import Base
from sqlalchemy.orm import relationship
from .room import user_room_association
from .receipt import user_item_association, UserReceiptAssociation

# if TYPE_CHECKING:
#     from .room import Room  # Import Room only for type checking
#     from .receipt import Item, Receipt, UserReceiptAssociation  # Import Item only for type checking

class User(Base):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(255))
    phone_number = mapped_column(String(15), unique=True, nullable=False)
    email = mapped_column(String(255), unique=True)
    username = mapped_column(String(50))
    # addresses: Mapped[List["Address"]] = relationship(
    #     back_populates="users", cascade="all, delete-orphan"
    # )

    # Establish the many-to-many relationship with Room
    rooms = relationship(
        "Room",
        secondary=user_room_association,
        back_populates="users"
    )

     # Establish the many-to-many relationship with Item
    items = relationship(
        "Item",
        secondary=user_item_association,
        back_populates="users"
    )

    receipts = relationship(
        "Receipt",
        secondary="user_receipt", 
        back_populates="users", 
        viewonly=True
    )    

    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, phone-number={self.phone_number!r}, email={self.email!r} )"