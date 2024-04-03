from fastapi import HTTPException, APIRouter, Response, status, Request
from sqlalchemy.orm import Session
from src.auth.sms_verification import TwilioAuthenticator
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
            self.service.intialize_verification(user.phone_number)
            return Response(content="Verification code has been sent", status_code=200)


        # completes the user verification by verifiying the provided OTP and returns the user object on sucessful verification
        #   - if the user does not exist -> creates a new user in the database
        @self.router.post("/complete-verification", response_model=schemas.Token)
        def complete_user_verification(user: schemas.UserLogin):
            # print("PHONE NUMBER AND OTP: ", user.phone_number, user.otp)
            # is_verified, usr = self.service.check_verification(user.phone_number, user.otp)
            jwt = self.service.verify(user.phone_number, user.otp)
            if not jwt:
                raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect OTP",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            return {"access_token": jwt, "token_type": "bearer"}

        @self.router.get("/", response_model=schemas.User)
        def get_current_active_user(request: Request):
            jwt_user = request.state.user
            usr = self.service.get_user(jwt_user["id"])
            if usr is None:
                raise HTTPException(status_code=404, detail="User not found")
            return usr
        
        # reads user jwt and updates either name or email based on passed body data
        @self.router.put("/update", response_model=schemas.User)
        def update_user(request: Request, user: schemas.UserUpdate):

            jwt_user = request.state.user

            db_user = self.service.update_user(jwt_user["id"], user.email, user.name, user.username)
            if db_user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return db_user
        

        # TODO: this should be a Admin level command. Should only be able to get user from given JWT. 
        @self.router.get("/list", response_model=list[schemas.User])
        def read_users(skip: int = 0, limit: int = 100):
            users = self.service.get_users(skip=skip, limit=limit)
            return users

        # TODO: Should only be able to get user from given JWT. 
        # i.e user should only be able to read their own data from given JWT
        @self.router.get("/{user_id}", response_model=schemas.User)
        def read_user_by_id(user_id: int):
            db_user = self.service.get_user(user_id)
            if db_user is None:
                raise HTTPException(status_code=400, detail="User not found")
            return db_user
        
        # TODO: Should only be able to get user from given JWT 
        # i.e user should only be able to read their own data from given JWT
        @self.router.get("/{phone_number}", response_model=schemas.User)
        def read_user_by_phone(phone_number: str):
            print(phone_number)
            db_user = self.service.get_user_by_phone_number(phone_number)
            if db_user is None:
                raise HTTPException(status_code=400, detail="User not found")
            return db_user
        

        @self.router.post("/add-friend", response_model=schemas.User)
        def add_friend(user: schemas.UserAddFriend):
            updated_user = self.service.add_friend(user.user_id, user.friend_id)
            if updated_user is None:
                raise HTTPException(status_code=400, detail="User or friend not found")
            return updated_user
        
        @self.router.post("/upload-profile-picture", response_model=bool)
        def upload_profile_picture(user: schemas.UserUploadProfilePicture):
            did_upload = self.service.upload_profile_picture(user.user_id, user.profile_picture)
            if not did_upload:
                raise HTTPException(status_code=400, detail="Error uploading profile picture")
            return did_upload

        @self.router.post("/get-profile-picture", response_model=str)
        def get_profile_picture(user: schemas.UserUploadProfilePicture):
            profile_picture = self.service.get_profile_picture(user.user_id)
            if profile_picture is None:
                raise HTTPException(status_code=400, detail="Error getting profile picture")
            return profile_picture