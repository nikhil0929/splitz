import os
from src.auth.verification import Authenticator
from dotenv import load_dotenv
from fastapi import FastAPI

from db.database import Database
from src.api.user import services, controller, schemas


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

app = FastAPI()


def main():
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
    #     phone_number=phone_number,
    # )

    # usr = user_service.get_user(8)
    # print("USER: ", usr)
    # print("NAME: ", new_user.name)
    # user_service.intialize_verification(phone_number)
    # user_input = input("Enter verification code: ")
    # isValid, usr = user_service.check_verification(phone_number, user_input)
    # print("Is Valid: ", isValid)

    user_controller = controller.UserController(user_service)
    app.include_router(
        user_controller.router
    )


main()
