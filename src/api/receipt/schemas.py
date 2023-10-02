from typing import Dict, Tuple, List
from pydantic import BaseModel
from src.api.user import MiniUser

class ItemBase(BaseModel):
    item_name: str
    item_quantity: int
    item_cost: float

class GetItems(BaseModel):
    item_id_list: List[int]

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True

class ItemWithUsers(Item):
    users: List[MiniUser]

class UserItem(Item):
    split_cost: float

class ReceiptBase(BaseModel):
    receipt_name: str

class ReceiptCreate(ReceiptBase):
    items: Dict[str, Tuple[float, int]]

class ReceiptNoItems(ReceiptBase):
    id: int
    room_code: str
    owner_id: int
    

class Receipt(ReceiptNoItems):
    items: List[ItemWithUsers]

    class Config:
        from_attributes = True