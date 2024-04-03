from io import BytesIO
from . import schemas
from db.models.user import User
from typing import Tuple
import boto3
from botocore.exceptions import NoCredentialsError

from sqlalchemy.orm import Session
from sqlalchemy import select
from psycopg2.errors import UniqueViolation
import logging

class UserService:
    """
    Initialize UserService with db_engine, twilio_authenticator, and jwt_authenticator.
    """
    def __init__(self, db_engine, twilio_authenticator, jwt_authenticator, bucket_name):
        self.db_engine = db_engine.get_engine()
        self.twilio_authenticator = twilio_authenticator
        self.jwt_authenticator = jwt_authenticator
        self.bucket_name = bucket_name

    def get_user(self, user_id: int) -> User:
        """
        Fetch a single user by their ID.

        Args:
            user_id (int): The ID of the user to fetch.

        Returns:
            User: The fetched user object.
        """
        with Session(self.db_engine) as db:
            try:
                stmt = select(User).where(User.id == user_id)
                usr = db.scalars(stmt).one()
                logging.info("user.services.get_user(): Sucessfully queried record")
                return usr
            except:
                logging.error("user.services.get_user(): Unable to locate record with given parameters")
                return None
            

    def get_user_by_phone_number(self, phone_number: str) -> User:
        """
        Fetch a single user by their phone number.

        Args:
            phone_number (str): The phone number of the user to fetch.

        Returns:
            User: The fetched user object.
        """
        with Session(self.db_engine) as db:
            try:
                stmt = select(User).where(User.phone_number == phone_number)
                usr = db.scalars(stmt).one()
                logging.info("user.services.get_user_by_phone_number(): Sucessfully queried record")
                return usr
            except:
                logging.error("user.services.get_user_by_phone_number(): Unable to locate record with given parameters")


    def get_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Fetch all users.

        Returns:
            List[User]: A list of all user objects.
        """
        with Session(self.db_engine) as db:
            try:
                stmt = select(User).offset(skip).limit(limit)
                usrs = db.scalars(stmt).all()
                logging.info("user.services.get_users(): Sucessfully queried records")
                return usrs
            except:
                logging.error("user.services.get_users(): Unable to query records")



    def intialize_verification(self, phone_number: str):
        """
        Initialize the SMS verification for the given user (phone number).

        Args:
            phone_number (str): The phone number of the user to initialize verification for.
        """
        self.twilio_authenticator.create_verification(phone_number)
        logging.info("user.services.intialize_verification(): Successfully created twilio verification")


    def verify(self, phone_number, otp: str) -> str:
        """
        Verify the user's phone number and OTP, and create a JWT to send back to the client.

        Args:
            phone_number (str): The phone number of the user to verify.
            otp (str): The OTP to verify.

        Returns:
            str: The created JWT.
        """
        is_verified = self.check_verification(phone_number, otp)
        if not is_verified:
            return None
        db_user = self.get_user_by_phone_number(phone_number)
        if not db_user:
            db_user = self.create_user(schemas.UserCreate(phone_number=phone_number))

        jwt_user = {
            "id": db_user.id,
            "phone_number": db_user.phone_number,
        }

        jwt = self.jwt_authenticator.create_access_token({"usr": jwt_user})
        logging.info("user.services.get_jwt(): Successfully created JWT")
        return jwt


    def check_verification(self, phone_number: str, otp: str) -> bool:
        """
        Check the verification of the user's phone number and OTP.

        Args:
            phone_number (str): The phone number of the user to check verification for.
            otp (str): The OTP to check.

        Returns:
            bool: True if the verification is successful, False otherwise.
        """
        # print("USER LOGIN: ", phone_number, otp)
        status = self.twilio_authenticator.check_verification(phone_number, otp)
        if status != "approved":
            logging.error("user.services.check_verification(): User could not be approved (incorrect OTP)")
            return False
        else:
            logging.info("user.services.check_verification(): User OTP successful")
            return True
        

    def create_user(self, user: schemas.UserCreate) -> User:
        """
        Create a new user in the database using the 'UserCreate' schema.

        Args:
            user (schemas.UserCreate): The user data to create a new user.

        Returns:
            User: The created user object.
        """
        # db_user = user_model(**user.dict())

        with Session(self.db_engine) as db:
            db_user = User(**user.model_dump())
            print(db_user)
            # db_user = User(phone_number=user.phone_number)
            try:
                db.add(db_user)
                db.commit()
                logging.info("user.services.get_user(): User created sucessfully")
                return self.get_user_by_phone_number(user.phone_number)
            except UniqueViolation:
                logging.error("user.services.get_user(): Phone number already exists; Cannot create user")
                return None

    def update_user(self, id: int, email: str = None, name: str = None, username: str = None) -> User:
        """
        Update a user in the database using the 'UserUpdate' schema.

        Args:
            id (int): The ID of the user to update.
            email (str, optional): The new email of the user. Defaults to None.
            name (str, optional): The new name of the user. Defaults to None.
            username (str, optional): The new username of the user. Defaults to None.

        Returns:
            User: The updated user object.
        """
        with Session(self.db_engine) as db:
            db_user = self.get_user(id)
            if not db_user:
                return None
            if email:
                db_user.email = email
            if name:
                db_user.name = name
            if username:
                db_user.username = username
            try:
                db.add(db_user)
                db.commit()
                logging.info("user.services.update_user(): User updated sucessfully")
                # print("DB USER: ", db_user)
                db.refresh(db_user)
                return db_user
            except:
                logging.error("user.services.update_user(): User update failed")
                return None
            
    def add_friend(self, user_id: int, friend_id: int) -> User:
        """
        Add a friend to a user.

        Args:
            user_id (int): The ID of the user to add a friend to.
            friend_id (int): The ID of the friend to add.

        Returns:
            User: The updated user object.
        """
        with Session(self.db_engine) as db:
            user = self.get_user(user_id)
            friend = self.get_user(friend_id)

            if not user or not friend:
                logging.error("user.services.add_friend(): User or friend not found")
                return None

            user.friends.append(friend)
            try:
                db.add(user)
                db.commit()
                logging.info("user.services.add_friend(): Friend added successfully")
                db.refresh(user)
                return user
            except:
                logging.error("user.services.add_friend(): Failed to add friend")
                return None
            
    def upload_profile_picture(self, user_id: int, file_content: bytes) -> bool:
        """
        Upload a user's profile picture to an AWS S3 bucket.

        Args:
            user_id (int): The ID of the user.
            file_content (bytes): The binary content of the image file.

        Returns:
            bool: True if the upload is successful, False otherwise.
        """
        # Initialize the S3 client
        s3 = boto3.client('s3', aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_secret_key)

        try:
            # Upload the file to S3
            s3.upload_fileobj(BytesIO(file_content), self.bucket_name, str(user_id))
            logging.info("user.services.upload_profile_picture(): Successfully uploaded image")
            return True
        except NoCredentialsError:
            logging.error("user.services.upload_profile_picture(): No AWS credentials found")
            return False
        except Exception as e:
            logging.error(f"user.services.upload_profile_picture(): An error occurred: {e}")
            return False
        

    def get_profile_picture(self, user_id: int) -> bytes:
        """
        Retrieve a user's profile picture from an AWS S3 bucket.

        Args:
            user_id (int): The ID of the user.

        Returns:
            bytes: The binary content of the image file.
        """
        s3 = boto3.client('s3', aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_secret_key)

        try:
            obj = s3.get_object(Bucket=self.bucket_name, Key=str(user_id))
            return obj['Body'].read()
        except NoCredentialsError:
            logging.error("user.services.get_profile_picture(): No AWS credentials found")
            return b''
        except Exception as e:
            logging.error(f"user.services.get_profile_picture(): An error occurred: {e}")
            return b''