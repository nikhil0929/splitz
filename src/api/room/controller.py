# room.controller.py

from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from . import schemas
from typing import List

class RoomController:

    def __init__(self, service):
        self.service = service
        self.router = APIRouter(
            prefix="/room",
            tags=["rooms"]
        )
        self.initialize_routes()

    def initialize_routes(self):

        @self.router.post("/create", response_model=schemas.Room)
        def create_room(room: schemas.RoomCreate, request: Request):
            jwt_user = request.state.user
            print("USER ID: ", jwt_user["id"])
            new_room = self.service.create_room(room.room_name, room.room_password, jwt_user["id"])
            return new_room

        @self.router.get("/{room_code}", response_model=schemas.Room)
        def get_room_by_code(room_code: str):
            return self.service.get_room_by_code(room_code)

        @self.router.get("/user/{user_id}", response_model=List[schemas.Room])
        def get_rooms_by_user_id(user_id: int):
            return self.service.get_rooms_by_user_id(user_id)

        @self.router.get("/members/{room_id}", response_model=List[schemas.RoomUser])
        def get_users_by_room_id(room_id: int):
            return self.service.get_users_by_room_id(room_id)

        @self.router.post("/join")
        def join_room(room_code: str, room_password: str, request: Request):
            jwt_user = request.state.user
            return self.service.join_room(room_code, room_password, jwt_user["id"])

        @self.router.post("/{room_code}/upload-receipt", response_model=schemas.ReceiptUpload)
        def upload_receipt_to_room(room_code: str, receipt_img: UploadFile = File(...)):
            success = self.service.add_receipt_to_s3_room(room_code, receipt_img)
            if success:
                return {"room_code": room_code, "receipt_img_url": f"/assets/{receipt_img.filename}"}
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

