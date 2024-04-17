from typing import Dict, Optional, Tuple, List
from pydantic import BaseModel
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

class ReceiptUpload(BaseModel):
    room_code: str
    receipt_img_url: str
