from . import schemas
from db.models.user import User
from typing import Tuple


from sqlalchemy.orm import Session
from sqlalchemy import select
from psycopg2.errors import UniqueViolation
import logging

class UserService:
    def __init__(self, db_engine, twilio_authenticator, jwt_authenticator):
        self.db_engine = db_engine.get_engine()
        self.twilio_authenticator = twilio_authenticator
        self.jwt_authenticator = jwt_authenticator

    # Read a single user by ID
    def get_user(self, user_id: int) -> User:
        with Session(self.db_engine) as db:
            try:
                stmt = select(User).where(User.id == user_id)
                usr = db.scalars(stmt).one()
                logging.info("user.services.get_user(): Sucessfully queried record")
                return usr
            except:
                logging.error("user.services.get_user(): Unable to locate record with given parameters")
                return None
            

    # Read a single user by phone number
    def get_user_by_phone_number(self, phone_number: str) -> User:
        with Session(self.db_engine) as db:
            try:
                stmt = select(User).where(User.phone_number == phone_number)
                usr = db.scalars(stmt).one()
                logging.info("user.services.get_user_by_phone_number(): Sucessfully queried record")
                return usr
            except:
                logging.error("user.services.get_user_by_phone_number(): Unable to locate record with given parameters")


    # Read multiple users from the database with a given offset and limit
    def get_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        with Session(self.db_engine) as db:
            try:
                stmt = select(User).offset(skip).limit(limit)
                usrs = db.scalars(stmt).all()
                logging.info("user.services.get_users(): Sucessfully queried records")
                return usrs
            except:
                logging.error("user.services.get_users(): Unable to query records")



    # Initialize the sms verification for the given user (phone number)
    def intialize_verification(self, phone_number: str):
        self.twilio_authenticator.create_verification(phone_number)
        logging.info("user.services.intialize_verification(): Successfully created twilio verification")


    # parent function for check_verification and create_user. Creates a JWT to send back to client
    def verify(self, phone_number, otp: str) -> str:
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
        # print("USER LOGIN: ", phone_number, otp)
        status = self.twilio_authenticator.check_verification(phone_number, otp)
        if status != "approved":
            logging.error("user.services.check_verification(): User could not be approved (incorrect OTP)")
            return False
        else:
            logging.info("user.services.check_verification(): User OTP successful")
            return True
        


    # Create a new user in the database using the 'UserCreate' schema. #
    #  - The phone number is the only necessary field
    # Steps:
    # 1. Create a SQLAlchemy model instance with your data.
    # 2. add that instance object to your database session.
    # 3. commit the changes to the database (so that they are saved).
    # 4. refresh your instance (so that it contains any new data from the database, like the generated ID).
    def create_user(self, user: schemas.UserCreate) -> User:
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

    # Update a user in the database using the 'UserUpdate' schema. 
    def update_user(self, id: int, email: str = None, name: str = None, username: str = None) -> User:
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