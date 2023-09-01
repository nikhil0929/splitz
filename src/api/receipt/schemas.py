from typing import Dict, Tuple, List
from pydantic import BaseModel

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