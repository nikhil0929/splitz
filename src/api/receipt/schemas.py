from typing import Dict, Tuple
from pydantic import BaseModel

class ReceiptBase(BaseModel):
    items: Dict[str, Tuple[float, int]]

class ReceiptCreate(ReceiptBase):
    room_code: str
    name: str

class Receipt(ReceiptCreate):
    id: int

    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    item_name: str
    item_quantity: int
    item_cost: float

class GetItem(ItemBase):
    receipt_id: int

class Item(GetItem):
    id: int

    class Config:
        from_attributes = True