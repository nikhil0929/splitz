from db.models.receipt import Receipt
from src.api.receipt.services import ReceiptService
from . import schemas
from db.models.room import Room, user_room_association
from db.models.user import User
from typing import Tuple
from argon2 import PasswordHasher
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import select
from psycopg2.errors import UniqueViolation
from botocore.exceptions import NoCredentialsError
import logging, random, string
import os
from io import BytesIO
import boto3

class RoomService:
    """
    Initialize RoomService with db_engine.
    """
    def __init__(self, db_engine, bucket_name: str, s3_access_key: str, s3_secret_key: str):
        self.bucket_name = bucket_name
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.db_engine = db_engine.get_engine()
        self.ph = PasswordHasher()

    def create_room(self, room_name: str, room_password: str, user_id: int) -> Room:
        """
        Create a new room with the given room_name, room_password, and user_id.

        Args:
            room_name (str): The name of the room to create.
            room_password (str): The password of the room to create.
            user_id (int): The ID of the user creating the room.

        Returns:
            Room: The created room object.
        """

        room_code = self.generate_room_code()

        with Session(self.db_engine) as db:
            try:
                # Check for uniqueness
                while db.query(Room).filter_by(room_code=room_code).first() is not None:
                    room_code = self.generate_room_code()

                # Create a new room
                stmt = select(User).where(User.id == user_id)
                user = db.scalars(stmt).one()
                hashed_pass = self.ph.hash(room_password)
                room = Room(room_name=room_name, room_password=hashed_pass, room_code=room_code, room_owner_id=user_id)
                room.users.append(user) # Add the user to the room's users list (back-populates)
                db.add(room)
                db.commit()
                logging.info("room.services.create_room(): Room created sucessfully")
                return self.get_room_by_code(room_code)
            except UniqueViolation:
                logging.error("room.services.create_room(): Room code already exists; Cannot create room")
                return None

    def delete_room(self, room_code: str):
        with Session(self.db_engine) as session:
            room = session.query(Room).filter(Room.room_code == room_code).first()
            receipts = session.query(Receipt).filter(Receipt.room_code == room_code).all()
            for receipt in receipts:
                ReceiptService.delete_receipt(receipt.id)

            session.query(user_room_association).filter(user_room_association.c.room_id == room.id).delete()
            session.delete(room)
            session.commit()

    def get_room_by_id(self, room_id: int) -> Room:
        """
        Fetch a single room by its ID in the database.

        Args:
            room_id (int): The room ID of the room to fetch from database.

        Returns:
            Room: The fetched room object.
        """
        with Session(self.db_engine) as db:
            stmt = select(Room).where(Room.id == room_id)
            room = db.scalars(stmt).one()
            return room

    def get_room_by_code(self, room_code: str) -> Room:
        """
        Fetch a single room by its room code.

        Args:
            room_code (str): The room code of the room to fetch.

        Returns:
            Room: The fetched room object.
        """
        with Session(self.db_engine) as db:
            stmt = select(Room).where(Room.room_code == room_code)
            room = db.scalars(stmt).first()
            return room

    def get_rooms_by_user_id(self, user_id: int) -> List[Room]:
        """
        Fetch all rooms associated with a given user ID.

        Args:
            user_id (int): The ID of the user to fetch rooms for.

        Returns:
            List[Room]: A list of all room objects associated with the user.
        """
        with Session(self.db_engine) as db:
            stmt = select(User).where(User.id == user_id)
            user = db.scalars(stmt).first()
            if user:
                return user.rooms
            return []

    def get_users_by_room_id(self, room_id: int) -> List[User]:
        """
        Fetch all users associated with a given room ID.

        Args:
            room_id (int): The ID of the room to fetch users for.

        Returns:
            List[User]: A list of all user objects associated with the room.
        """
        with Session(self.db_engine) as db:
            stmt = select(Room).where(Room.id == room_id)
            room = db.scalars(stmt).first()
            if room:
                return room.users
            return []

    def join_room(self, room_code: str, room_password: str, user_id: int) -> bool:
        """
        Join a room with the given room_code, room_password, and user_id.

        Args:
            room_code (str): The room code of the room to join.
            room_password (str): The password of the room to join.
            user_id (int): The ID of the user joining the room.

        Returns:
            Room: The joined room object.
        """
        with Session(self.db_engine) as db:
            try:
                stmt = select(Room).where(Room.room_code == room_code)
                room = db.scalars(stmt).one()
                if room:
                    if self.ph.verify(room.room_password, room_password):
                        # Add the user to the room's users list (back-populates)
                        user = db.query(User).get(user_id)

                        # Check if the user is already part of the room
                        if user in room.users:
                            logging.warning("room.services.join_room(): User is already part of the room")
                            return False


                        room.users.append(user)
                        room.num_members += 1
                        db.commit()
                        logging.info("room.services.join_room(): User joined room sucessfully")
                        return True
                    else:
                        logging.error("room.services.join_room(): Incorrect room password")
                        return False
                else:
                    logging.error("room.services.join_room(): Room does not exist")
                    return False
            except:
                logging.error("room.services.join_room(): Unknown error")
                return False

    # Inside the RoomService class

    def get_user_costs_by_room_code(self, room_code: str) -> dict:
        """
        Fetch the total costs for each user in a room, given the room code.

        Args:
            room_code (str): The room code of the room to fetch user costs for.

        Returns:
            dict: A dictionary mapping user IDs to their total costs in the room.
        """
        with Session(self.db_engine) as db:
            # Get the room by code
            room = db.query(Room).filter(Room.room_code == room_code).first()
            if not room:
                logging.error("room.services.get_user_costs_by_room_code(): Room not found")
                return {}

            # Initialize a dictionary to store user details and total costs
            user_costs = {}

            # Iterate over each receipt in the room
            for receipt in room.receipts:
                # Iterate over each user-receipt association
                for association in receipt.user_associations:
                    user = association.user
                    user_id = user.id

                    # If user is not in the dictionary, add them
                    if user_id not in user_costs:
                        user_costs[user_id] = {
                            "name": user.name,
                            "username": user.username,
                            "total_cost": 0
                        }

                    # Add the cost to the user's total cost
                    user_costs[user_id]["total_cost"] += association.receipt_total_cost

            return user_costs

    def upload_room_picture(self, room_code: str, file_content: bytes) -> bool:
        """
        Upload a room's room picture to an AWS S3 bucket.
        Args:
            room_code (int): The code of the room.
            file_content (bytes): The binary content of the image file.
        Returns:
            bool: True if the upload is successful, False otherwise.
        """
        # Initialize the S3 client
        s3 = boto3.client('s3', aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_secret_key)
        object_key = f"room_{room_code}.jpg"
        with Session(self.db_engine) as db:
            room = db.query(Room).filter(Room.room_code == room_code).one_or_none()
            try:
                # Upload the file to S3
                s3.upload_fileobj(BytesIO(file_content), self.bucket_name, object_key, ExtraArgs={'ACL': 'public-read'})

                # add s3 url to room 'room_picture_url' field
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{object_key}"
                room.room_picture_url = s3_url
                db.add(room)
                db.commit()

                logging.info("room.services.upload_room_picture(): Successfully uploaded image")
                return True
            except NoCredentialsError:
                logging.error("room.services.upload_room_picture(): No AWS credentials found")
                return False
            except Exception as e:
                logging.error(f"room.services.upload_room_picture(): An error occurred: {e}")
                return False


    #### HELPER FUNCTIONS ####

    def generate_room_code(self, length=6):
        """
        Generate a unique alphanumeric room code of the given length.

        Args:
            length (int): The length of the room code to generate.

        Returns:
            str: The generated room code.
        """
        characters = string.ascii_uppercase + string.digits  # A-Z 0-9
        return ''.join(random.choice(characters) for _ in range(length))