# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client


## Can i use apache kafka with this? Once you create the verification, the application needs to wait
class TwilioAuthenticator:
    def __init__(self, account_sid: str, auth_token: str, service_sid: str):
        self.client = Client(account_sid, auth_token)
        self.service_sid = service_sid

    # Verifys a given phone number through Twilio using SMS messaging
    def create_verification(self, phone_number: str) -> str:
        verification = self.client.verify.v2.services(
            self.service_sid
        ).verifications.create(to=phone_number, channel="sms")

        return verification.sid

    # Checks the verification code for a given phone number through Twilio
    def check_verification(self, phone_number: str, code: str) -> str:
        check = self.client.verify.v2.services(
            self.service_sid
        ).verification_checks.create(to=phone_number, code=code)

        print(check.status)
        return check.status
