from typing import Dict, Tuple, List
from pydantic import BaseModel
from src.api.user import MiniUser

class ItemBase(BaseModel):
    item_name: str
    item_quantity: int
    item_cost: float

class GetItem(ItemBase):
    receipt_id: int

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True

class ItemWithUsers(Item):
    users: List[MiniUser]

class UserItem(Item):
    split_cost: float

class ReceiptBase(BaseModel):
    room_code: str
    receipt_name: str

class ReceiptCreate(ReceiptBase):
    items: Dict[str, Tuple[float, int]]
    

class Receipt(ReceiptBase):
    id: int
    items: List[Item]

    class Config:
        from_attributes = True