
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
        @self.router.post("/{room_code}/send-receipt")
        def receive_receipt(room_code: str, receipt: schemas.ReceiptCreate):
            # Process the receipt data
            # Create into Item object for each item and add to new Receipt object
            # Then add receipt to room
            # Leave users field empty for now
            
            new_rct = self.service.create_receipt(room_code, receipt.receipt_name, receipt.items)
            if not new_rct:
                raise HTTPException(status_code=500, detail="Error creating receipt")
            return new_rct
        
        @self.router.get("/{room_code}", response_model=List[schemas.ReceiptNoItems])
        def get_receipts(room_code: str, request: Request):
            # Get all receipts from room
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            rcts = self.service.get_receipts(room_code)
            # print(rct)
            return rcts
        
        @self.router.get("/{room_code}/receipt/{receipt_id}", response_model=schemas.Receipt)
        def get_receipt(receipt_id: int, room_code: str, request: Request):
            # Get all items from receipt
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            return self.service.get_receipt(receipt_id)

        
        @self.router.post("/{room_code}/select-items/{receipt_id}", response_model=bool)
        def user_select_items(items_data: schemas.GetItems, room_code: str, receipt_id: int,  request: Request):
            # Take in user selected items and add to users field in Item object
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            did_add = self.service.user_select_items(items_data.item_id_list, usr["id"], receipt_id, items_data.user_total_cost, room_code)
            
            if not did_add:
                raise HTTPException(status_code=500, detail="Error adding user to items")
            return did_add
        
        # Get users items for a given receipt_id
        @self.router.get("/{room_code}/get-user-items/{receipt_id}")
        def get_user_items(room_code: str, receipt_id: int, request: Request):
            # Get all items from receipt
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            data = self.service.get_user_and_receipt(receipt_id, usr["id"], room_code)
            if data is None:
                raise HTTPException(status_code=500, detail="Error getting user items - user is not in room code")
            return {"receipt": data[0], "user": data[1], "user_total_cost": data[2]}
        
        

            
        
