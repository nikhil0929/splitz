import json
from typing import Dict, Optional, Tuple, List
from fastapi import Form, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError, model_validator
from src.api.user import MiniUser

class ItemBase(BaseModel):
    item_name: str
    item_quantity: int
    item_price: float

class GetItems(BaseModel):
    item_id_list: List[int]
    user_total_cost: float

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True

class ItemWithUsers(Item):
    users: List[MiniUser]

class UserItem(Item):
    split_price: float

class ReceiptBase(BaseModel):
    receipt_name: str


class ReceiptCreate(BaseModel):
    merchant_name: str
    total_amount: float
    tax_amount: float
    tip_amount: float
    date: str
    items: List[ItemBase]


class ReceiptNoItems(ReceiptBase):
    id: int
    room_code: Optional[str]
    owner_id: int

class Receipt(ReceiptNoItems):
    items: List[ItemWithUsers]

    class Config:
        from_attributes = True

class UploadReceiptData(BaseModel):
    room_code: Optional[str] | None
    user_list: Optional[List[MiniUser]]
    receipt_name: Optional[str] | None

def checker(data: str = Form(...)):
    try:
        return UploadReceiptData.model_validate_json(data)
    except ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    