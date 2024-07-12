
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Depends, Body
from fastapi.responses import StreamingResponse, Response

from src.api.receipt.services import ReceiptService

from . import schemas
from typing import List
import logging
## charge / pay
## https://account.venmo.com/pay?amount=$amountToPay&note=$userMessage&recipients=$user_name&txn=$payment_type
class VenmoController:

    def __init__(self, windows_venmo_url, ios_venmo_url):
        self.windows_venmo_url = windows_venmo_url
        self.ios_venmo_url = ios_venmo_url
        self.router = APIRouter(
            prefix="/payments/venmo",
            tags=["/payments/venmo"],
        )
        self.initialize_routes()

    def initialize_routes(self):
        #Generates URL for Windows
        @self.router.post("/create_window_payment", response_model=schemas.VenmoLink)
        async def generate_charge_for_windows(request: Request, venmo_args: schemas.VenmoBase):
            return schemas.VenmoLink(payment_url = self._generate_windows_url(venmo_args.payment_amount, venmo_args.note, venmo_args.username, venmo_args.payment_type))
          
        #Generates URL for iOS
        @self.router.post("/create_ios_payment", response_model=schemas.VenmoLink)
        async def generate_charge_for_ios(request: Request, venmo_args: schemas.VenmoBase):
            return schemas.VenmoLink(payment_url = self._generate_ios_url(venmo_args.payment_amount, venmo_args.note, venmo_args.username, venmo_args.payment_type))


    def _generate_windows_url(self, payment_amount: float, note:str, username: List[str], payment_type: str):
        return f'{self.windows_venmo_url}?amount={payment_amount}&note={note}&recipients={",".join(username)}&txn={payment_type}'
    
    def _generate_ios_url(self, payment_amount: float, note:str, username: List[str], payment_type: str):
        return f'{self.ios_venmo_url}?txn={payment_type}&recipients={payment_type}?amount={payment_amount}&note={note}&recipients={",".join(username)}&txn={payment_type}&amount={payment_amount}&note={note}&recipients={",".join(username)}&txn={payment_type}'