# room.controller.py

from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import StreamingResponse, Response

from src.api.room.services import RoomService
from . import schemas
from typing import List

class RoomController:

    def __init__(self, service: RoomService):
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
            # print("USER ID: ", jwt_user["id"])
            new_room = self.service.create_room(room.room_name, room.room_password, jwt_user["id"])
            return new_room

        @self.router.post("/delete/{room_code}")
        def delete_room_by_code(room_code: str):
            self.service.delete_room(room_code)

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
        def join_room(room_join: schemas.RoomJoin, request: Request):
            jwt_user = request.state.user
            did_join = self.service.join_room(room_join.room_code, room_join.room_password, jwt_user["id"])
            if not did_join:
                raise HTTPException(status_code=404, detail="Unable to join room")
            else:
                return Response(content="Successfully joined room", status_code=status.HTTP_200_OK)

        @self.router.get("/", response_model=List[schemas.Room])
        def get_current_active_user(request: Request):
            jwt_user = request.state.user
            return self.service.get_rooms_by_user_id(jwt_user["id"])

        @self.router.get("/{room_code}/user-costs", response_model=dict)
        def get_user_costs(room_code: str):
            """
            Get a list of users and their total costs due across all receipts in the given room.
            """
            try:
                user_costs = self.service.get_user_costs_by_room_code(room_code)
                if user_costs:
                    return user_costs
                else:
                    raise HTTPException(status_code=404, detail="Room not found or no users in room")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


        @self.router.post("/{room_code}/upload-room-picture", response_model=bool)
        def upload_room_picture(room_code: str, room_picture: UploadFile = File(...)):
            file_content = room_picture.file.read()
            did_upload = self.service.upload_room_picture(room_code, file_content)
            if not did_upload:
                raise HTTPException(status_code=400, detail="Error uploading room picture")
            return did_upload