from . import schemas
from db.models.receipt import Receipt, Item, UserReceiptAssociation
from db.models.room import Room
from db.models.user import User
from typing import Tuple
from argon2 import PasswordHasher
from typing import List

from fastapi import UploadFile
import boto3
from botocore.exceptions import NoCredentialsError

from sqlalchemy.orm import Session, joinedload, selectinload, load_only
from sqlalchemy import select, insert
from psycopg2.errors import UniqueViolation
import logging, random, string
import os
from io import BytesIO

class ReceiptService:
    def __init__(self, db_engine, s3_access_key, s3_secret_key, bucket_name):
        self.db_engine = db_engine.get_engine()
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.bucket_name = bucket_name


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
    def create_receipt(self, room_code: str, receipt_name: str, receipt_dict: dict) -> Receipt:
        with Session(self.db_engine) as session:
            try:
                # Get receipt room
                stmt = select(Room).where(Room.room_code == room_code)
                room = session.scalars(stmt).first()

                # Get user to assign as receipt owner
                stmt = select(User).where(User.id == room.room_owner_id)
                user = session.scalars(stmt).first()

                # Create items for receipt
                items_list = []
                for item in receipt_dict["items"]:
                    item = Item(item_name=item["name"], item_cost=item["price"], item_quantity=item["quantity"])
                    items_list.append(item)

                # id: Mapped[int] = mapped_column(primary_key=True)
                # receipt_name: Mapped[str] = mapped_column(String(50))
                # room_code: Mapped[str] = mapped_column(String, ForeignKey("rooms.room_code"))
                # room: Mapped["Room"] = relationship("Room", back_populates="receipts")
                # owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
                # owner_name: Mapped[str] = mapped_column(String(50))
                # merchant_name: Mapped[str] = mapped_column(String(50))
                # total_amount: Mapped[float] = mapped_column(Float)
                # tax_amount: Mapped[float] = mapped_column(Float)
                # tip_amount: Mapped[float] = mapped_column(Float)
                # date: Mapped[str] = mapped_column(String(50))
                # Create a new receipt
                new_receipt = Receipt(receipt_name=receipt_name, 
                                      room_code=room_code, 
                                      owner_id=user.id, 
                                      owner_name=user.name, 
                                      merchant_name=receipt_dict["merchant_name"], 
                                      total_amount=receipt_dict["total_amount"], 
                                      tip_amount=receipt_dict["tip_amount"],
                                      tax_amount=receipt_dict["tax_amount"], 
                                      date=receipt_dict["date"], 
                                      items=items_list)
                # Add the receipt to the room's receipts list (back-populates)
                room.receipts.append(new_receipt)
                session.add(room)
                session.add(new_receipt)
                session.commit()
                session.refresh(new_receipt)  # Refresh the object after committing
                # Commit the session to save both the new receipt and the updated room
                logging.info("receipt.services.create_receipt(): Receipt created sucessfully")
                print("in service function: ", new_receipt)
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
            
    # get list of all receipts for the current user from the UserReceiptAssociation
    def get_user_receipts(self, user_id: int) -> List[Receipt]:
        with Session(self.db_engine) as session:
            try:
                stmt = select(UserReceiptAssociation).where(UserReceiptAssociation.user_id == user_id)
                associations = session.scalars(stmt).all()
                receipts = []
                for assoc in associations:
                    stmt = select(Receipt).where(Receipt.id == assoc.receipt_id)
                    receipt = session.scalars(stmt).first()
                    receipts.append(receipt)
                return receipts
            except Exception as e:
                logging.error(f"receipt.services.get_user_receipts(): Error getting user receipts - {e}")
                return []

            
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
    ## also populate the user_receipt "receipt_total_cost" field with the total cost of the receipt
    ##      The total cost is calculated on the frontend and sent in the request body
    ## This function/API is only called when the user clicks on the "Confirm total" button
    ## THIS FUNCTION ALLOWS FOR UPDATING THE TOTAL COST OF THE RECEIPT AND ITEM SELECTION (ADD MORE ITEMS)
    def user_select_items(self, items_data: list, user_id: int, receipt_id: int, user_total_cost: float, room_code: str) -> bool:
        with Session(self.db_engine) as session:
            try:
                user_stmt = select(User).where(User.id == user_id)
                user = session.execute(user_stmt).scalars().first()

                receipt_stmt = select(Receipt).where(Receipt.id == receipt_id)
                receipt = session.execute(receipt_stmt).scalars().first()

                if receipt.room_code != room_code:
                    return False

                if user not in receipt.room.users:
                    return False

                # Check if the UserReceiptAssociation already exists
                assoc_stmt = select(UserReceiptAssociation).where(UserReceiptAssociation.user_id == user_id, UserReceiptAssociation.receipt_id == receipt_id)
                association = session.execute(assoc_stmt).scalars().first()

                if association:
                    # Update the receipt_total_cost if the association already exists
                    association.receipt_total_cost = user_total_cost
                else:
                    # Create a new association if it doesn't exist
                    receipt.user_associations.append(UserReceiptAssociation(user=user, receipt_total_cost=user_total_cost))

                session.commit()

                for item_id in items_data:
                    item_stmt = select(Item).where(Item.id == item_id)
                    item = session.execute(item_stmt).scalars().first()

                    if item.receipt_id != receipt.id:
                        continue

                    if user in item.users:
                        continue

                    item.users.append(user)

                session.commit()
                return True
            except Exception as e:
                logging.error(f"receipt.services.user_select_items(): Error adding user to items - {e}")
                return False


    def get_user_and_receipt(self, receipt_id: int, user_id: int, room_code: str) -> tuple:
        with Session(self.db_engine) as session:
            try:
                user_stmt = select(User).where(User.id == user_id)
                user = session.execute(user_stmt).scalars().first()

                room_stmt = select(Room).where(Room.room_code == room_code)
                room = session.execute(room_stmt).scalars().first()

                # check if user is a part of this room
                if user not in room.users:
                    return None
                
                # Hold a reference to the Receipt object
                receipt_stmt = select(Receipt).where(Receipt.id == receipt_id)
                receipt = session.execute(receipt_stmt).scalars().first()

                # get receipt_total_cost for this user in the association table
                user_rcpt_stmt = select(UserReceiptAssociation).where(UserReceiptAssociation.user_id == user_id).where(UserReceiptAssociation.receipt_id == receipt_id)
                user_rcpt = session.execute(user_rcpt_stmt).scalars().first()
                cost = user_rcpt.receipt_total_cost

                 # Get items that belong to the user for the given receipt
                items_stmt = select(Item).join(Item.users).where(User.id == user_id).where(Item.receipt_id == receipt_id)
                user_items = session.execute(items_stmt).scalars().all()

                return (user, receipt, user_items, cost)
            except Exception as e:
                logging.error(f"receipt.services.get_user_items(): Error getting items for user - {e}")
                return None
            
    
    ## adds a receipt to the appropriate s3 bucket for the room with the given room code
    ## NOTE: adding an image to a bucket folder causes an lambda function event to trigger for processing
    ## the receipt. The lambda function processes the receipt and sends the JSON data back to this server to
    ## to return to the client. USE Boto3 package for S3 file handling
    # 
    # For right now, implement dummy function in AWS Lambda that returns random JSON data. 
    def add_receipt_to_s3_room(self, room_code: str, receipt_img: UploadFile) -> bool:
        # Initialize the S3 client
        s3 = boto3.client('s3', aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_secret_key)

        # Define the bucket name and the file name (you can customize this)
        bucket_name = self.bucket_name
        file_name = f"{room_code}/{receipt_img.filename}"  # This will save the image in a folder named after the room_code

        try:
            # Upload the file to S3
            s3.upload_fileobj(receipt_img.file, bucket_name, file_name)

            # Here, you can trigger the AWS Lambda function if need be
            # For now, as you mentioned, we'll assume the Lambda function is triggered automatically upon file upload

            logging.info(f"room.services.add_receipt_to_s3_room(): Receipt uploaded to {room_code} folder in S3")
            return True

        except NoCredentialsError:
            logging.error("room.services.add_receipt_to_s3_room(): Missing AWS credentials")
            return False
        except Exception as e:
            logging.error(f"room.services.add_receipt_to_s3_room(): An error occurred: {e}")
            return False
        

    def download_receipts_from_s3_room(self, room_code: str) -> List[Tuple[str, BytesIO]]:
        """
        Download all receipt images from the specified room_code folder in the S3 bucket.
        :param room_code: The code of the room.
        :return: A list of tuples containing filename and the corresponding file content.
        """
        # Initialize the S3 client
        s3 = boto3.client('s3', aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_secret_key)

        try:
            # List objects in the specified folder
            response = s3.list_objects_v2(Bucket=self.bucket_name, Prefix=f"{room_code}/")

            # Check if the response contains 'Contents' key
            if 'Contents' not in response:
                logging.warning(f"room.services.download_receipts_from_s3_room(): No receipts found for room {room_code}")
                return []

            file_contents = []
            for content in response['Contents']:
                file_name = content['Key'].split('/')[-1]  # Extract just the file name from the Key
                file_obj = BytesIO()
                s3.download_fileobj(self.bucket_name, content['Key'], file_obj)
                file_contents.append((file_name, file_obj))

            logging.info(f"room.services.download_receipts_from_s3_room(): Downloaded {len(file_contents)} receipts for room {room_code}")
            return file_contents

        except Exception as e:
            logging.error(f"room.services.download_receipts_from_s3_room(): An error occurred: {e}")
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
            
    def parse_receipt(self, room_code: str, receipt_img: UploadFile) -> dict:
        # Parse the receipt and return a Receipt object
        # For now, we'll just return a dummy Receipt dictionary
        sample_receipt_dict = {
            "merchant_name": "DIN TAI FUNG",
            "total_amount": 181.06,
            "tax_amount": 14.26,
            "tip_amount": 0.00,
            "date": "2023-07-18",
            "items": [
                {
                    "name": "Seaweed & Beancurd Salad",
                    "price": 7.5,
                    "quantity": 1
                },
                {
                    "name": "Sweet & Sour Pork Baby Back Ribs",
                    "price": 14.5,
                    "quantity": 1
                },
                {
                    "name": "Hot & Sour Soup",
                    "price": 12.5,
                    "quantity": 1
                },
                {
                    "name": "Pork Xiao Long Bao",
                    "price": 15.5,
                    "quantity": 1
                },
                {
                    "name": "Sticky Rice & Pork Shao Mai",
                    "price": 10.5,
                    "quantity": 1
                },
                {
                    "name": "Taiwanese Cabbage w / Garlic",
                    "price": 14.0,
                    "quantity": 1
                },
                {
                    "name": "Vegan Dumplings",
                    "price": 15.5,
                    "quantity": 1
                },
                {
                    "name": "Shrimp & Pork Spicy Wontons",
                    "price": 15.0,
                    "quantity": 1
                },
                {
                    "name": "Pork Chop Fried Rice",
                    "price": 18.0,
                    "quantity": 1
                },
                {
                    "name": "Chicken Shanghai Rice Cakes",
                    "price": 16.0,
                    "quantity": 1
                }
            ]
        }

        return sample_receipt_dict

            
    