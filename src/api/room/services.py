from . import schemas
from db.models.room import Room
from db.models.user import User
from typing import Tuple
from argon2 import PasswordHasher
from typing import List


from sqlalchemy.orm import Session
from sqlalchemy import select
from psycopg2.errors import UniqueViolation
import logging, random, string

class RoomService:
    def __init__(self, db_engine):
        self.db_engine = db_engine.get_engine()
        self.ph = PasswordHasher()

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

    #### HELPER FUNCTIONS ####

    # Generate a random alphanumeric code of the given length.
    def generate_room_code(self, length=6):
        characters = string.ascii_uppercase + string.digits  # A-Z 0-9
        return ''.join(random.choice(characters) for _ in range(length))