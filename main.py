import os
from src.api.receipt.controller import ReceiptController
from src.api.receipt.services import ReceiptService
from src.auth.sms_verification import TwilioAuthenticator
from src.auth.jwt_auth import JWTAuthenticator
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from fastapi.security import OAuth2PasswordBearer

from db.database import Database
from src.api.user.services import UserService
from src.api.user.controller import UserController
from src.api.room.services import RoomService
from src.api.room.controller import RoomController
from src.api.middleware.middleware import JWTMiddleware
from src.api.receipt.receipt_parse import NanonetsReceiptParser
import logging

import imageio as iio
import io



# from fastapi import FastAPI, Depends
# from src.api.user import controller as user_controller

load_dotenv()

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
service_sid = os.getenv("TWILIO_SERVICE_SID")

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

jwt_secret = os.getenv("SECRET_KEY")
jwt_algorithm = "HS256"

s3_access_key = os.getenv("S3_ACCESS_KEY")
s3_secret_key = os.getenv("S3_SECRET_KEY")
s3_receipts_bucket_name = os.getenv("S3_RECEIPTS_BUCKET_NAME")
s3_profile_pictures_bucket_name = os.getenv("S3_PROFILE_PICTURES_BUCKET_NAME")

nanonets_url = os.getenv("NANONETS_URL")
nanonets_api_key = os.getenv("NANONETS_API_KEY")

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', encoding='utf-8', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

    twilio_auth = TwilioAuthenticator(account_sid, auth_token, service_sid)
    jwt_auth = JWTAuthenticator(jwt_secret, jwt_algorithm)
    receipt_parser = NanonetsReceiptParser(nanonets_url, nanonets_api_key)


    splitz_db = Database(db_user, db_password, db_host, db_port, db_name)
    # print("DB URL: ", splitz_db.database_url)
    splitz_db.run_migrations()

    user_service = UserService(splitz_db, twilio_auth, jwt_auth, bucket_name=s3_profile_pictures_bucket_name, s3_access_key=s3_access_key, s3_secret_key=s3_secret_key)
    room_service = RoomService(splitz_db, bucket_name=s3_profile_pictures_bucket_name, s3_access_key=s3_access_key, s3_secret_key=s3_secret_key)
    receipt_service = ReceiptService(splitz_db, s3_access_key, s3_secret_key, s3_receipts_bucket_name, receipt_parser)


    user_controller = UserController(user_service)
    room_controller = RoomController(room_service)
    receipt_controller = ReceiptController(receipt_service)
    app.include_router(user_controller.router)
    app.include_router(room_controller.router)
    app.include_router(receipt_controller.router)
    app.add_middleware(JWTMiddleware, jwt_authenticator=jwt_auth)


main()
