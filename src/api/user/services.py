from . import schemas
from db.models.user import User
from typing import Tuple


from sqlalchemy.orm import Session
from sqlalchemy import select

class UserService:
    def __init__(self, db_engine, authenticator):
        self.db_engine = db_engine.get_engine()
        self.authenticator = authenticator

    # Read a single user by ID
    def get_user(self, user_id: int):
        with Session(self.db_engine) as db:
            stmt = select(User).where(User.id == user_id)
            return db.scalars(stmt).one()

    # Read a single user by phone number
    def get_user_by_phone_number(self, phone_number: str):
        with Session(self.db_engine) as db:
            stmt = select(User).where(User.phone_number == phone_number)
            return db.scalars(stmt).one()


    # Read multiple users from the database with a given offset and limit
    def get_users(self, skip: int = 0, limit: int = 100):
        with Session(self.db_engine) as db:
            stmt = select(User).offset(skip).limit(limit)
            return db.scalars(stmt).all()


    # Initialize the sms verification for the given user (phone number)
    def intialize_verification(self, user: schemas.UserCreate):
        user_phone_number = user.phone_number
        self.authenticator.create_verification(user_phone_number)


    def check_verification(self, user: schemas.UserLogin) -> Tuple[bool, User]:
        status = self.authenticator.check_verification(user.phone_number, user.otp)
        if status != "approved":
            return False, None
        db_user = self.get_user_by_phone_number(user.phone_number)
        if not db_user:
            db_user = self.create_user(user)
        return status == "approved", db_user


    # Create a new user in the database using the 'UserCreate' schema. #     - The phone number is the only necessary field
    # Steps:
    # 1. Create a SQLAlchemy model instance with your data.
    # 2. add that instance object to your database session.
    # 3. commit the changes to the database (so that they are saved).
    # 4. refresh your instance (so that it contains any new data from the database, like the generated ID).
    def create_user(self, user: schemas.UserCreate):
        # db_user = user_model(**user.dict())

        with Session(self.db_engine) as db:
            db_user = User(phone_number=user.phone_number)
            db.add(db_user)
            db.commit()
            return db_user
