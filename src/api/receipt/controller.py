
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import StreamingResponse, Response
from . import schemas
from typing import List
import logging

class ReceiptController:

    def __init__(self, service):
        self.service = service
        self.router = APIRouter(
            prefix="/receipts",
            tags=["receipts"],
        )
        self.initialize_routes()

    def initialize_routes(self):

        # this is for the AWS lambda function to use
        @self.router.post("/receive-receipt", response_model=bool)
        def receive_receipt(receipt: schemas.ReceiptCreate):
            # Process the receipt data
            # Create into Item object for each item and add to new Receipt object
            # Then add receipt to room
            # Leave users field empty for now
            
            did_create = self.service.create_receipt(receipt.room_code, receipt.name, receipt.items)
            if not did_create:
                raise HTTPException(status_code=500, detail="Error creating receipt")
            return did_create
        
        @self.router.get("/get-receipts/{room_code}", response_model=List[schemas.Receipt])
        def get_receipts(room_code: str, request: Request):
            # Get all receipts from room
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            rct = self.service.get_receipts(room_code)
            # print(rct)
            return rct
        
        @self.router.get("/get-items/{room_code}/{receipt_id}", response_model=List[schemas.Item])
        def get_items(receipt_id: int, room_code: str, request: Request):
            # Get all items from receipt
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            return self.service.get_items(receipt_id)

        
        @self.router.post("/user-selected-items")
        def user_selected_items(items: List[schemas.Item], request: Request):
            # Take in user selected items and add to users field in Item object
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(items[0].receipt_id):
                raise HTTPException(status_code=404, detail="User is not in room")
            return self.service.user_selected_items(items, usr["id"])
            
        
