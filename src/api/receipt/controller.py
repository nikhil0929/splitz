
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Depends, Body
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

        # get all receipts from all rooms for a given user
        @self.router.get("/receipts-list", response_model=List[schemas.ReceiptNoItems])
        def get_all_receipts(request: Request):
            usr = request.state.user
            return self.service.get_user_receipts(usr["id"])

        # this is for the AWS lambda function to use
        @self.router.post("/{room_code}/send-receipt")
        def receive_receipt(room_code: str, payload: dict = Body()):
            # Process the receipt data
            # Create into Item object for each item and add to new Receipt object
            # Then add receipt to room
            # Leave users field empty for now
            new_rct = self.service.create_receipt(room_code, "", payload)
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
        
        @self.router.get("/{room_code}/receipt/{receipt_id}")
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
            # (user, receipt, user_items, cost)
            return {"user": data[0], "receipt": data[1], "user_items": data[2], "user_total_cost": data[3]}
        
        @self.router.post("/{room_code}/upload-receipt")
        def upload_receipt_to_room(room_code: str, receipt_img: UploadFile = File(...)):
            success = self.service.add_receipt_to_s3_room(room_code, receipt_img)
            if success:
                receipt_dict = self.service.parse_receipt(room_code, receipt_img)
                new_rct = self.service.create_receipt(room_code, "", receipt_dict)
                print("NEW RCT: ", new_rct)
                return {"room_code": room_code, "receipt_img_url": f"/assets/{receipt_img.filename}", "receipt": new_rct}
            else:
                raise HTTPException(status_code=500, detail="Failed to upload receipt")

        @self.router.get("/{room_code}/download-receipts", response_model=List[str])
        def download_receipts_from_room(room_code: str):
            file_contents = self.service.download_receipts_from_s3_room(room_code)
            
            if not file_contents:
                raise HTTPException(status_code=404, detail="No receipts found for the room")

            # For simplicity, let's send the first file. You can modify this to send multiple files or zip them together.
            file_name, file_obj = file_contents[0]
            file_obj.seek(0)  # Reset the file pointer to the beginning
            return StreamingResponse(file_obj, media_type="image/jpeg", headers={"Content-Disposition": f"attachment; filename={file_name}"})
            
        
