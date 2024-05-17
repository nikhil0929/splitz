
from fastapi import APIRouter, Form, Request, HTTPException, status, UploadFile, File, Depends, Body
from fastapi.responses import StreamingResponse, Response

from src.api.receipt.services import ReceiptService

from . import schemas
from typing import List, Optional
import logging

class ReceiptController:

    def __init__(self, service: ReceiptService):
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

        @self.router.get("/one-off_receipt_list", response_model=List[schemas.ReceiptNoItems])
        def get_user_quick_split_receipts(request: Request):
            # Get all receipts from room
            # make sure user is part of this room
            usr = request.state.user
            # if not self.service.is_user_on_receipt(usr["id"], room_code):
            #     raise HTTPException(status_code=404, detail="User is not in room")
            rcts = self.service.get_one_off_receipts(usr["id"])
            if rcts is None:
                raise HTTPException(status_code=404, detail="Unable to get users for receipt. ")
            # print(rct)
            return rcts

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


        @self.router.get("/receipt/{receipt_id}")
        def get_one_off_receipt(receipt_id: int, request: Request):
            # Get all items from receipt
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_on_receipt(usr["id"], receipt_id=receipt_id):
                raise HTTPException(status_code=404, detail="User is not on receipt")
            return self.service.get_receipt(receipt_id)

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

        @self.router.post("/assign-items/{receipt_id}", response_model=bool)
        def user_select_items(items_data: schemas.AssignItems, receipt_id: int,  request: Request):
            # Take in user selected items and add to users field in Item object
            # make sure user is part of this receipt
            usr = request.state.user
            if not self.service.is_user_on_receipt(usr["id"], receipt_id=receipt_id):
                raise HTTPException(status_code=404, detail="User is not on receipt")
            did_add = self.service.user_select_items(items_data.item_id_list, items_data.user_id, receipt_id, items_data.user_total_cost, room_code=None)

            if not did_add:
                raise HTTPException(status_code=500, detail="Error adding user to items")
            return did_add



        @self.router.post("/add-users/{receipt_id}", response_model=bool)
        def add_users_to_receipt(users_list: List[int] ,receipt_id: int,  request: Request):

            usr = request.state.user

            did_add = self.service.receipt_add_users(receipt_id=receipt_id, users_list=users_list)

            if not did_add:
                raise HTTPException(status_code=500, detail="Error adding users to receipt")
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

        # rename receipt
        @self.router.put("/{room_code}/rename-receipt/{receipt_id}")
        def rename_receipt(room_code: str, receipt_id: int, receipt: schemas.ReceiptBase, request: Request):
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            did_rename = self.service.rename_receipt(receipt_id, receipt.receipt_name)
            if not did_rename:
                raise HTTPException(status_code=500, detail="Error renaming receipt")
            return did_rename

        @self.router.post("/create-empty-receipt")
        def create_empty_receipt(request: Request, data: schemas.UploadReceiptData):
            usr = request.state.user

            new_rct = self.service.create_empty_receipt(room_code=data.room_code, receipt_name=data.receipt_name, owner_id=usr["id"], user_list=data.user_list)
            return new_rct

        @self.router.post("/{room_code}/delete/{receipt_id}")
        def delete_receipt(room_code: str, receipt_id: int, request: Request):
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            self.service.delete_receipt(receipt_id)

        @self.router.post("/upload-receipt")
        async def upload_receipt_to_room(request: Request, receipt_img: UploadFile = File(...), data: schemas.UploadReceiptData = Depends(schemas.checker)):
            usr = request.state.user
            data = schemas.UploadReceiptData(**data.dict())
            # print(data.user_list)
            file_content = receipt_img.file.read()
            if data.room_code or usr["id"]:
                success = self.service.add_receipt_to_s3(room_code=data.room_code, user_id=usr["id"], file_content=file_content, img_filename=receipt_img.filename)
            else:
                raise HTTPException(status_code=400, detail="invalid room code or user_id")

            if success:
                receipt_dict = self.service.parse_receipt(file_content)
                rct_name = data.receipt_name if data.receipt_name else receipt_dict["merchant_name"],
                new_rct = self.service.create_receipt(room_code=data.room_code, receipt_name=rct_name, receipt_dict=receipt_dict, owner_id=usr["id"], user_list=data.user_list)
                return new_rct
            else:
                raise HTTPException(status_code=500, detail="Failed to upload receipt")

        @self.router.get("/{room_code}/download-receipts", response_model=List[str])
        async def download_receipts_from_room(room_code: str):
            file_contents = self.service.download_receipts_from_s3(room_code)

            if not file_contents:
                raise HTTPException(status_code=404, detail="No receipts found for the room")

            # For simplicity, let's send the first file. You can modify this to send multiple files or zip them together.
            file_name, file_obj = file_contents[0]
            file_obj.seek(0)  # Reset the file pointer to the beginning
            return StreamingResponse(file_obj, media_type="image/jpeg", headers={"Content-Disposition": f"attachment; filename={file_name}"})

        # function to add an item to a receipt given a receipt id
        @self.router.post("/{room_code}/add-item/{receipt_id}")
        def add_items_to_receipt(items: List[schemas.ItemBase], room_code: str, receipt_id: int, request: Request):
            # make sure user is part of this room
            usr = request.state.user
            if not self.service.is_user_in_room(usr["id"], room_code):
                raise HTTPException(status_code=404, detail="User is not in room")
            # check if receipt is in room
            if not self.service.is_receipt_in_room(receipt_id, room_code):
                raise HTTPException(status_code=404, detail="Receipt is not in room")
            items = self.service.add_items_to_receipt(items, receipt_id)
            if items is None:
                raise HTTPException(status_code=500, detail="Error adding items to receipt")
            return items



