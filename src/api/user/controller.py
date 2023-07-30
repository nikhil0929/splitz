from fastapi import HTTPException, APIRouter, Response
from sqlalchemy.orm import Session
from src.auth.verification import Authenticator
from . import schemas
from fastapi import Depends



class UserController:

    def __init__(self, service):
        self.service = service
        self.router = APIRouter(
            prefix="/user",
            tags=["users"]
        )
        self.initialize_routes()


    def initialize_routes(self):
        # intializes the user verification by sending an OTP to the provided phone number
        @self.router.post("/initialize-verification")
        def initialize_user_verification(user: schemas.UserCreate):
            self.service.intialize_verification(user)
            return Response(content="Verification code has been sent", status_code=200)


        # completes the user verification by verifiying the provided OTP and returns the user object on sucessful verification
        #   - if the user does not exist -> creates a new user in the database
        @self.router.post("/complete-verification", response_model=schemas.User)
        def complete_user_verification(user: schemas.UserLogin):
            is_verified, usr = self.service.check_verification(user=user)
            if not is_verified:
                raise HTTPException(status_code=400, detail="OTP incorrect")
            return usr


        @self.router.get("/list", response_model=list[schemas.User])
        def read_users(skip: int = 0, limit: int = 100):
            users = self.service.get_users(skip=skip, limit=limit)
            return users


        @self.router.get("/{user_id}", response_model=schemas.User)
        def read_user(user_id: int):
            db_user = self.service.get_user(user_id)
            if db_user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return db_user
        

        @self.router.get("/{phone_number}", response_model=schemas.User)
        def read_user(phone_number: str):
            db_user = self.service.get_user_by_phone_number(phone_number)
            if db_user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return db_user
