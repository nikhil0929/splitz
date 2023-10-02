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

from sqlalchemy.orm import Session, joinedload, selectinload, load_only
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

                # Get user to assign as receipt owner
                stmt = select(User).where(User.id == room.room_owner_id)
                user = session.scalars(stmt).one()

                # Create items for receipt
                items_list = []
                for item_name, (item_cost, item_quantity) in items_dict.items():
                    item = Item(item_name=item_name, item_cost=item_cost, item_quantity=item_quantity)
                    items_list.append(item)
                    
                # Create a new receipt
                new_receipt = Receipt(receipt_name=receipt_name, room_code=room_code, items=items_list, owner_id=user.id)
                session.add(new_receipt)
                session.commit()
                session.refresh(new_receipt)  # Refresh the object after committing
                # print(new_receipt)
                return new_receipt
            except Exception as e:
                ## logging.error("room.services.join_room(): User is already part of the room")
                logging.error(f"receipt.services.create_receipt(): Error creating receipt - {e}")
                return None
    
    # get all receipts that are in this room_code. Only send back receipt data (NO ITEM DATA)
    def get_receipts(self, room_code: str) -> List[Receipt]:
        with Session(self.db_engine) as session:
            try:
                stmt = select(Receipt).where(Receipt.room_code == room_code)
                receipts = session.scalars(stmt).all()
                print(receipts)
                return receipts
            except Exception as e:
                logging.error(f"receipt.services.get_receipts(): Error getting receipts - {e}")
                return []
            
    # get receipt by id with all item data
    def get_receipt(self, receipt_id: int) -> Receipt:
        with Session(self.db_engine) as session:
            try:
                # Use joinedload to load the items and users eagerly
                stmt = (
                select(Receipt)
                .options(
                    joinedload(Receipt.items)  # Load items
                    .joinedload(Item.users)  # Load users for each item
                )
                .where(Receipt.id == receipt_id)
            )

                receipt = session.scalars(stmt).first()
                return receipt
            except Exception as e:
                logging.error(e)
                return None

            
    def get_items(self, receipt_id: int) -> List[Item]:
        with Session(self.db_engine) as session:
            try:
                stmt = (select(Item)
                    .where(Item.receipt_id == receipt_id)
                    .options(selectinload(Item.users).load_only(User.id, User.name)))
                itms = session.scalars(stmt).all()
                return itms
            except Exception as e:
                logging.error(f"receipt.services.get_items(): Error getting items - {e}")
                return []
            
    ## add user to item 'users' field for each of the selected items
    ## send a list of item ids in the request body in the "item_id_list" field
    def user_select_items(self, items_data: schemas.GetItems, user_id: int, receipt_id: int) -> bool:
        with Session(self.db_engine) as session:
            try:
                user = session.query(User).get(user_id)
            
                # Hold a reference to the Receipt object
                receipt = session.query(Receipt).get(receipt_id)

                # Use the reference throughout your code
                if user not in receipt.users:
                    receipt.users.append(user)
                    session.commit()

                # Add the user to the user_item_association table for each item in the item_id_list
                for item_id in items_data.item_id_list:
                    stmt = select(Item).where(Item.id == item_id)
                    item = session.scalars(stmt).one()

                    # Check if the item belongs to the receipt
                    if item.receipt_id != receipt_id:
                        continue
                    

                    # Check if the user is already in the item's users list
                    if user in item.users:
                        continue

                    # Add the user to the item's users list (back-populates)
                    item.users.append(user)
                session.commit()
                return True
            except Exception as e:
                logging.error(f"receipt.services.user_select_items(): Error adding user to items - {e}")
                return False

    def get_user_items(self, receipt_id: int, user_id: int) -> List[Item]:
        with Session(self.db_engine) as session:
            try:
                stmt = (select(Item)
                    .where(Item.receipt_id == receipt_id)
                    .options(selectinload(Item.users).load_only(User.id, User.name)))
                itms = session.scalars(stmt).all()
                return itms
            except Exception as e:
                logging.error(f"receipt.services.get_user_items(): Error getting items for user - {e}")
                return []    

    ## HELPER FUNCTIONS ##
            
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