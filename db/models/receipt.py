from typing import List, TYPE_CHECKING, Optional
# from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Table, ForeignKey, UUID, Column, Float
from sqlalchemy.orm import Mapped, relationship, mapped_column
from ..base_model import Base

'''
Item table:
- id (int) - auto-incrementing primary key
- Item_name (str) - just a name of the item
- item_quantity (int) - this is only used for the user to see. The price is divided amongst the people that select the same items (the ‘users’ column; see field below)
- item_cost (float) - total item cost
- Users (1 to n mapping) - each item can belong to one or many people [foreign key]

'''
'''
receipt Table:
- id (int) - auto-incrementing primary key
- receipt_name (str) - just a name of the receipt
- room_code (str) - the room code that the receipt belongs to
- items (1 to n mapping) - each receipt can have one or many items [foreign key]
'''

if TYPE_CHECKING:
    from .user import User
    from .room import Room

user_item_association = Table(
    'user_item', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('item_id', Integer, ForeignKey('items.id')),
    # Additional columns for relationship-specific data
    Column('split_cost', Float)
)



class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(String(100))
    item_quantity: Mapped[int] = mapped_column(Integer)
    item_cost: Mapped[float] = mapped_column(Float)
    
    # Establish a many-to-many relationship with User
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_item_association,
        back_populates="items"
    )

    # Establish a many-to-one relationship with Receipt
    receipt_id: Mapped[int] = mapped_column(Integer, ForeignKey("receipts.id"))
    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="items")

    def __repr__(self) -> str:
        return f"Item(id={self.id!r}, name={self.item_name!r}, quantity={self.item_quantity!r}, cost={self.item_cost!r})"

class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_name: Mapped[str] = mapped_column(String(50))
    room_code: Mapped[str] = mapped_column(String, ForeignKey("rooms.room_code"))
    room: Mapped["Room"] = relationship("Room", back_populates="receipts")
    
    # Establish a one-to-many relationship with Item
    items: Mapped[List["Item"]] = relationship("Item", back_populates="receipt")

    def __repr__(self) -> str:
        return f"Receipt(id={self.id!r}, name={self.receipt_name!r}, room_code={self.room_code!r})"