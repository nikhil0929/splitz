from . import schemas
from db.models.room import Room
from db.models.user import User
from typing import Tuple
from argon2 import PasswordHasher
from typing import List

from fastapi import UploadFile
import boto3
from botocore.exceptions import NoCredentialsError

from sqlalchemy.orm import Session
from sqlalchemy import select
from psycopg2.errors import UniqueViolation
import logging, random, string
import os

class RoomService:
    def __init__(self, db_engine, s3_access_key, s3_secret_key, bucket_name):
        self.db_engine = db_engine.get_engine()
        self.ph = PasswordHasher()
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.bucket_name = bucket_name

    # Create a new room from the given room_name, room_password, and user_id.
    def create_room(self, room_name: str, room_password: str, user_id: int) -> Room:
        
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
                return room
            except UniqueViolation:
                logging.error("room.services.create_room(): Room code already exists; Cannot create room")
                return None
    
    # get a room from the given room id
    def get_room_by_id(self, room_id: int) -> Room:
        with Session(self.db_engine) as db:
            stmt = select(Room).where(Room.id == room_id)
            room = db.scalars(stmt).one()
            return room
        
    # get a room from the given room code
    def get_room_by_code(self, room_code: str) -> Room:
        with Session(self.db_engine) as db:
            stmt = select(Room).where(Room.room_code == room_code)
            room = db.scalars(stmt).one()
            return room
        
    # Get all rooms that the user with the given user_id is a member of
    def get_rooms_by_user_id(self, user_id: int) -> List[Room]:
        with Session(self.db_engine) as db:
            stmt = select(User).where(User.id == user_id)
            user = db.scalars(stmt).first()
            if user:
                return user.rooms
            return []
        
    # get all users that are part of a room with the given room_id
    def get_users_by_room_id(self, room_id: int) -> List[User]:
        with Session(self.db_engine) as db:
            stmt = select(Room).where(Room.id == room_id)
            room = db.scalars(stmt).first()
            if room:
                return room.users
            return []
        
    # allows a user to join a room with a given room_code and room_password.
    # Checks the room_password against the room_password in the database.
    def join_room(self, room_code: str, room_password: str, user_id: int) -> bool:
        with Session(self.db_engine) as db:
            try:
                stmt = select(Room).where(Room.room_code == room_code)
                room = db.scalars(stmt).one()
                if room:
                    if self.ph.verify(room.room_password, room_password):
                        # Add the user to the room's users list (back-populates)
                        user = db.query(User).get(user_id)
                        room.users.append(user)
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


    def download_receipts_from_s3_room(self, room_code: str) -> List[str]:
        """
        Download all receipt images from the specified room_code folder in the S3 bucket and save them to ./assets.
        :param room_code: The code of the room.
        :return: A list of local paths to the downloaded receipt images.
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

            # Create assets directory if it doesn't exist
            if not os.path.exists('./assets'):
                os.makedirs('./assets')

            # Download each file and save to ./assets
            local_paths = []
            for content in response['Contents']:
                file_name = content['Key'].split('/')[-1]  # Extract just the file name from the Key
                local_path = os.path.join('./assets', file_name)
                s3.download_file(self.bucket_name, content['Key'], local_path)
                local_paths.append(local_path)

            logging.info(f"room.services.download_receipts_from_s3_room(): Downloaded {len(local_paths)} receipts for room {room_code}")
            return local_paths

        except Exception as e:
            logging.error(f"room.services.download_receipts_from_s3_room(): An error occurred: {e}")
            return []

    #### HELPER FUNCTIONS ####

    # Generate a random alphanumeric code of the given length.
    def generate_room_code(self, length=6):
        characters = string.ascii_uppercase + string.digits  # A-Z 0-9
        return ''.join(random.choice(characters) for _ in range(length))