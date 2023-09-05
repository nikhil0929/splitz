from . import schemas
from db.models.receipt import Receipt
from db.models.room import Room
from db.models.receipt import Item
from db.models.user import User
from typing import Tuple
from argon2 import PasswordHasher
from typing import List

from fastapi import UploadFile
import boto3
from botocore.exceptions import NoCredentialsError

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select
from psycopg2.errors import UniqueViolation
import logging, random, string
import os
from io import BytesIO

class ReceiptService:
    def __init__(self, db_engine):
        self.db_engine = db_engine.get_engine()


    '''
    class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)  # Auto-incrementing primary key
    item_name: Mapped[str] = mapped_column(String(100))
    item_quantity: Mapped[int] = mapped_column(Integer)
    item_cost: Mapped[float] = mapped_column(Float)

    # Establish a one to many relationship with users. This item can be shared amongh many users
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    users: Mapped[Optional["User"]] = relationship()

    # Establish a one to one relationship with receipt. This item can only belong to one receipt
    receipt_id: Mapped[Optional[int]] = mapped_column(ForeignKey("receipts.id"))
    receipt: Mapped[Optional["Receipt"]] = relationship()



    def __repr__(self) -> str:
        return f"Item(id={self.id!r}, name={self.item_name!r}, quantity={self.item_quantity!r}, cost={self.item_cost!r} )"
    

class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)  # Auto-incrementing primary key
    receipt_name: Mapped[str] = mapped_column(String(50))
    room_code: Mapped[String] = mapped_column(String, ForeignKey("rooms.room_code"))
    room: Mapped["Room"] = relationship(back_populates="receipts")
    items: Mapped[List["Item"]] = relationship("Item", back_populates="receipt")

    def __repr__(self) -> str:
        return f"Receipt(id={self.id!r}, name={self.receipt_name!r}, room_id={self.room_id!r} )"
        
    '''
    def create_receipt(self, room_code: str, receipt_name: str, items_dict: dict) -> Receipt:
        with Session(self.db_engine) as session:
            try:
                # Get receipt room
                stmt = select(Room).where(Room.room_code == room_code)
                room = session.scalars(stmt).one()

                # Create items for receipt
                items_list = []
                for item_name, (item_cost, item_quantity) in items_dict.items():
                    item = Item(item_name=item_name, item_cost=item_cost, item_quantity=item_quantity)
                    items_list.append(item)
                    session.add(item)
                    
                # Create a new receipt
                new_receipt = Receipt(receipt_name=receipt_name, room_code=room_code, items=items_list)
                session.add(new_receipt)
                session.commit()
                get_rcpt_stmt = select(Receipt).where(Receipt.id == new_receipt.id)
                new_rcpt = session.scalars(get_rcpt_stmt).one()
                return new_rcpt
            except Exception as e:
                logging.error(e)
                return None

            
    def get_receipts(self, room_code: str) -> List[Receipt]:
        with Session(self.db_engine) as session:
            try:
                # stmt = select(Receipt).where(Receipt.room_code == room_code)
                # receipts = session.scalars(stmt).all()
                # receipts = session.query(Receipt).options(joinedload(Receipt.items)).all()
                # stmt = select(Receipt).where(Receipt.room_code == room_code).options(joinedload(Receipt.items))
                # receipts = session.scalars(stmt).all()
                stmt = (select(Receipt)
                    .where(Receipt.room_code == room_code)
                    .options(selectinload(Receipt.items)))
                receipts = session.scalars(stmt).all()
                # print("Receipts: " ,receipts)
                return receipts
            except Exception as e:
                logging.error(e)
                return []
            
    def get_items(self, receipt_id: int) -> List[Item]:
        with Session(self.db_engine) as session:
            try:
                stmt = select(Receipt).where(Receipt.id == receipt_id)
                receipt = session.scalars(stmt).one()
                return receipt.items
            except Exception as e:
                logging.error(e)
                return []
            
    ## add user to item 'users' field for each of the selected items
    def user_selected_items(self, items: List[Item], user_id: int, receipt_id: int) -> bool:
        with Session(self.db_engine) as session:
            try:
                for item in items:
                    stmt = select(Item).where(Item.id == item.id)
                    item = session.scalars(stmt).one()

                    # Check if the item belongs to the receipt
                    if item.receipt_id != receipt_id:
                        continue

                    # Add the user to the room's users list (back-populates)
                    user = session.query(User).get(user_id)

                    # Check if the user is already in the item's users list
                    if user in item.users:
                        continue

                    # Add the user to the item's users list (back-populates)
                    item.users.append(user)
                session.commit()
                return True
            except Exception as e:
                logging.error(e)
                return False
            
    def is_user_in_room(self, user_id: int, room_code: str) -> bool:
        with Session(self.db_engine) as session:
            try:
                stmt = select(Room).where(Room.room_code == room_code)
                room = session.scalars(stmt).one()
                user = session.query(User).get(user_id)
                # print(user)
                # print(room.users)
                # print(user in room.users)
                return user in room.users
            except Exception as e:
                logging.error(e)
                return False