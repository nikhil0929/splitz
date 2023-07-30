import os
from src.auth.verification import Authenticator
from dotenv import load_dotenv

from db.database import Database
from src.api.user import services, schemas


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

# app = FastAPI()


def main():
    phone_number = "+14085059394"
    auth = Authenticator(account_sid, auth_token, service_sid)

    # auth.create_verification(phone_number)
    # # # print(os.getenv("TEST_TWILIO_ACCOUNT_SID"))

    # user_input = input("Enter verification code: ")
    # auth.check_verification(phone_number, user_input)

    # def get_authenticator():
    #     return auth

    splitz_db = Database(db_user, db_password, db_host, db_port, db_name)
    # print("DB URL: ", splitz_db.database_url)
    splitz_db.run_migrations()

    user_service = services.UserService(splitz_db, auth)
    # new_user = schemas.UserCreate(
    #     # name="John Doe",
    #     phone_number="+14094058184",
    #     email="jdoe@gmail.com"
    # )

    # usr = user_service.get_user(8)
    # print("USER: ", usr)
    # print("NAME: ", new_user.name)
    # usr = user_service.create_user(new_user)
    # print(usr)


    # app.include_router(
    #     user_controller.router,
    #     dependencies=[Depends(splitz_db.get_db), Depends(get_authenticator)],
    # )


main()
