from fastapi import HTTPException, APIRouter, Response
from sqlalchemy.orm import Session
from src.auth.verification import Authenticator
from . import schemas, services
from fastapi import Depends


router = APIRouter()


# intializes the user verification by sending an OTP to the provided phone number
@router.post("/users/phone-number")
def initialize_user_verification(
    user: schemas.UserCreate, auth: Authenticator = Depends()
):
    services.intialize_verification(user=user, auth=auth)
    return Response(content="Verification code has been sent", status_code=200)


# completes the user verification by verifiying the provided OTP and returns the user object on sucessful verification
#   - if the user does not exist -> creates a new user in the database
@router.post("/users/otp", response_model=schemas.User)
def complete_user_verification(
    user: schemas.UserLogin, db: Session = Depends(), auth: Authenticator = Depends()
):
    is_verified, usr = services.check_verification(user=user, auth=auth)
    if not is_verified:
        raise HTTPException(status_code=400, detail="OTP incorrect")
    return usr


@router.get("/users/", response_model=list[schemas.User])
def read_users(db: Session, skip: int = 0, limit: int = 100):
    users = services.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(db: Session, user_id: int):
    db_user = services.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
